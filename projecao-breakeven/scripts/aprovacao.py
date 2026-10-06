#!/usr/bin/env python3
"""
aprovacao.py — texto da thread de aprovação e o bloco "Restrição mapeada até agora" da aba Premissas.

Lê o premissas.json de cada cenário (pessimista, desejado, otimista) e escreve:
  - aprovacao.md: mensagem curta, pronta para colar no Slack ou no ClickUp (veredito, os três cenários,
    onde está a restrição mapeada até agora, o que destrava e o que falta medir);
  - um JSON de metodologia com a chave 'topo', que o gerador põe no começo da aba Premissas de cada cenário.

A restrição é o que impede o breakeven HOJE, na ordem em que ela manda:
  1. estrutura (ticket × margem contra fee + verba): quando nem com fee zero a mídia se paga, nenhuma taxa resolve;
  2. retorno da mídia abaixo de 1: mais verba aumenta o prejuízo;
  3. funil: a alavanca que, sozinha, fecha o mês-alvo com o menor salto (e se esse nível já aconteceu);
  e, sempre, as lacunas de medição (premissa de mercado no lugar de dado, receita estimada, o que o usuário informar).

Uso:
  python3 aprovacao.py --desejado premissas_desejado.json --pessimista premissas_pessimista.json \
      --otimista premissas_otimista.json --cliente "indústria química B2B" --restricao "recompra não é medida" --out-md aprovacao.md --out-json topo.json
"""
import argparse, json
from datetime import date

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
NOMES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def br(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def rs(x, dec=0):
    return f"−R$ {br(-x, dec)}" if x < 0 else f"R$ {br(x, dec)}"


def calendario(d):
    """Rótulo do mês t (1 = Mês 1) a partir do --inicio do piloto ou do primeiro mês projetado."""
    pc = d["premissas_confirmadas"]
    ini = pc.get("inicio")
    if ini:
        m, a = ini.split("/")
        i0, ano = NOMES.index(m.strip().lower()), int(a)
    else:
        hist = [h for h in d.get("historico") or [] if h["status"] in ("fechado", "corrente")]
        corr = next((h for h in d.get("historico") or [] if h["status"] == "corrente"), None)
        h = corr or (hist[-1] if hist else None)
        i0, ano = (NOMES.index(h["mes"]) + (0 if corr else 1), int(h["ano"])) if h else (0, date.today().year)
    return lambda t: None if t is None else f"{MESES[(i0 + t - 1) % 12]}/{ano + (i0 + t - 1) // 12}"


def resumo(d):
    v, proj = d["veredito"], d.get("projecao") or []
    cal = calendario(d)
    alvo = int(d["premissas_confirmadas"]["mes_alvo"])
    return {"status": v["status"], "azul": cal(v.get("no_azul_continuo_desde")), "zera": cal(v.get("acumulado_zera_em")),
            "acum_fim": proj[-1]["acumulado"] if proj else None, "fim": cal(len(proj)),
            "res_alvo": proj[alvo - 1]["resultado_liquido"] if len(proj) >= alvo else None, "mes_alvo": cal(alvo),
            "vendas_alvo": v.get("vendas_projetadas_mes_alvo"), "vendas_nec": v.get("vendas_necessarias_mes_alvo")}


def restricao(d, manuais):
    pc, v, cam, det = d["premissas_confirmadas"], d["veredito"], d.get("caminho"), d["detectado"]
    fee = float(pc["fee"]); verba = float(pc["midia_mensal"]); margem = float(pc["margem"]) * float(pc.get("comissao", 1.0))
    alvo_ = int(pc["mes_alvo"]); tm = (d.get("rampa") or {}).get("taxas_mes_a_mes") or []
    ticket = float((tm[alvo_ - 1].get("ticket") if len(tm) >= alvo_ else None) or pc["ticket"])   # o ticket da rampa (inclui o fixado)
    mc_venda = ticket * margem
    nec_mes = (fee + verba) / mc_venda if mc_venda else None
    mc_real = (cam or {}).get("margem_por_real_de_midia_no_alvo")
    if mc_real is None:
        mc_real = v.get("mc_por_real_de_midia_taxas_atuais")
    proj = d.get("projecao") or []
    alvo = int(pc["mes_alvo"])
    vend = proj[alvo - 1]["vendas"] if len(proj) >= alvo else None
    linhas, tipo = [], None
    conta = (f"Cada venda deixa {rs(mc_venda)} ({rs(ticket)} de ticket × {br(margem * 100, 1)}% de margem); fee + verba "
             f"({rs(fee + verba)}/mês) pedem {br(nec_mes, 1)} vendas por mês, e o funil entrega {br(vend or 0, 1)} no mês-alvo.")
    if cam and cam.get("fee_que_fecha") is not None and cam["fee_que_fecha"] <= 0:
        tipo = "ESTRUTURA"
        linhas.append(f"Restrição principal: ESTRUTURA (ticket × margem contra fee + verba). Nem com fee zero o mês-alvo fecha: "
                      f"cada R$ 1 de mídia devolve R$ {br(mc_real or 0, 2)} de margem. Nenhuma taxa de funil resolve sozinha.")
    elif mc_real is not None and mc_real < 1:
        tipo = "RETORNO DA MÍDIA"
        linhas.append(f"Restrição principal: RETORNO DA MÍDIA abaixo de 1 (R$ {br(mc_real, 2)} de margem por R$ 1). "
                      "Mais verba aumenta o prejuízo; a conversa é de conversão, ticket ou margem antes de verba.")
    elif v["status"] == "REALISTA":
        tipo = "SEM RESTRIÇÃO BLOQUEANTE"
        linhas.append("Sem restrição bloqueante: o plano fecha com as taxas de hoje. O risco é não sustentar o funil atual na escala da verba.")
    else:
        tipo = "FUNIL"
        linhas.append("Restrição principal: FUNIL. A estrutura fecha (a mídia se paga), mas as taxas de hoje ainda não chegam ao breakeven no prazo.")
    linhas.append(conta)
    # a alavanca que, sozinha, fecha com o menor salto
    if cam:
        cands = []
        for a in cam.get("alavancas") or []:
            if a.get("necessario") is None or not a.get("atual"): continue
            salto = (a["atual"] / a["necessario"]) if a["alavanca"] in ("cpm", "custo_sessao_meta") else (a["necessario"] / a["atual"])
            cands.append((salto, a))
        if cands:
            salto, a = min(cands, key=lambda x: x[0])
            dinheiro = a["alavanca"] in ("cpm", "ticket", "custo_sessao_meta")
            f = (lambda x: rs(x, 2)) if dinheiro else (lambda x: f"{br(x * 100, 1)}%")
            visto = "já aconteceu num mês fechado" if a.get("ja_visto") else "nunca aconteceu num mês fechado"
            linhas.append(f"Alavanca que fecha o mês-alvo com o menor salto: {a['rotulo']}, de {f(a['atual'])} para {f(a['necessario'])} "
                          f"({br(salto, 1)}x; {visto}).")
        else:
            linhas.append("Nenhuma alavanca fecha o mês-alvo sozinha, nem no limite.")
        if cam.get("fee_que_fecha") is not None and cam["fee_que_fecha"] > 0:
            linhas.append(f"O mês-alvo fecharia com fee de {rs(cam['fee_que_fecha'])} (hoje {rs(fee)}).")
    # lacunas de medição
    lac = []
    for k, x in (pc.get("premissas_mercado") or {}).items():
        lac.append(f"{k.replace('_', ' ')} entra como premissa de mercado ({x['fonte']}), não medida no cliente")
    if det.get("receita_faturada_estimada"):
        lac.append("receita faturada estimada pelo ticket do pedido captado (a fonte não traz a receita faturada)")
    if "Conexões" in (det.get("etapas_ausentes_na_fonte") or []) and not (pc.get("premissas_mercado") or {}):
        lac.append("conexão (lead atendido) não medida")
    if (pc.get("ciclo_origem") or "").startswith("premissa"):
        lac.append(f"ciclo de vendas é {pc['ciclo_origem']}, não medido no CRM")
    for al in (det.get("taxas_efetivas") or {}).get("alertas") or []:
        if "frágil" in al:
            lac.append("amostra frágil — " + al.split(";")[0]); break
    lac += manuais
    return tipo, linhas, lac


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desejado", required=True)
    ap.add_argument("--pessimista")
    ap.add_argument("--otimista")
    ap.add_argument("--cliente", default="Cliente")
    ap.add_argument("--sufixo", default="", help="sufixo dos nomes dos três cenários (ex.: ' sem legado')")
    ap.add_argument("--extra", action="append", default=[], metavar="NOME=premissas.json", help="cenário a mais (ex.: cenário-meta), listado depois do otimista")
    ap.add_argument("--restricao", action="append", default=[], help="lacuna ou restrição que o usuário mapeou (repetível), ex.: 'recompra não é medida'")
    ap.add_argument("--breakeven", help="metodologia do cenário Breakeven (cenario_breakeven.py): entra na thread como 'o cenário que bate'")
    ap.add_argument("--out-md", default="aprovacao.md")
    ap.add_argument("--out-json", default="restricao_topo.json")
    a = ap.parse_args()
    suf = a.sufixo or ""
    cen = {"Pessimista" + suf: a.pessimista, "Desejado" + suf: a.desejado, "Otimista" + suf: a.otimista,
           **{x.split("=", 1)[0]: x.split("=", 1)[1] for x in a.extra}}
    dados = {k: json.load(open(p, encoding="utf-8")) for k, p in cen.items() if p}
    des = dados["Desejado" + suf]
    tipo, linhas, lac = restricao(des, a.restricao)
    hoje = date.today().strftime("%d/%m/%Y")
    res = {k: resumo(d) for k, d in dados.items()}

    def frase(k, r):
        azul = f"no azul a partir de {r['azul']}" if r['azul'] else "nenhum mês no azul em 48 meses"
        zera = f"acumulado zera em {r['zera']}" if r['zera'] else "acumulado não zera em 48 meses"
        return f"{k}: {r['status']} · {azul} · {zera} · acumulado em {r['fim']}: {rs(r['acum_fim'] or 0)}"

    md = [f"*Projeção de breakeven · {a.cliente} · para aprovação ({hoje})*", "",
          f"*Veredito (cenário desejado{suf}):* {res['Desejado' + suf]['status']} para {res['Desejado' + suf]['mes_alvo']}.", "",
          "*Cenários*"] + [f"• {frase(k, r)}" for k, r in res.items()] + ["",
          f"*Restrição mapeada até agora · {tipo}*"] + [f"• {x}" for x in linhas]
    if a.breakeven:
        sec_be = json.load(open(a.breakeven, encoding="utf-8"))["topo"][0]
        be = sec_be[1][1:]
        titulo_be = ("*O plano já bate: até onde o funil pode cair (aba Breakeven)*" if "JÁ BATE" in sec_be[0]
                     else "*O cenário que bate (o que precisa ser verdade)*")
        md += ["", titulo_be] + [f"• {x}" for x in be]
    if lac:
        md += ["", "*O que ainda não é medido (e pode mudar a leitura)*"] + [f"• {x}" for x in lac]
    md += ["", "Detalhe de cada cenário na aba Premissas da planilha. A restrição é revista a cada rodada da projeção."]
    open(a.out_md, "w", encoding="utf-8").write("\n".join(md) + "\n")

    tabela = {"colunas": ["Cenário", "Veredito", "No azul a partir de", "Acumulado zera em", "Acumulado no fim"],
              "linhas": [[k, r["status"], r["azul"] or "não acontece", r["zera"] or "não zera", rs(r["acum_fim"] or 0)] for k, r in res.items()],
              "nota": "Pessimista: taxas atuais, ou de volta à mediana onde a janela está acima dela. Desejado: rampa até a mediana do período (o plano). "
                      "Otimista: rampa até o melhor mês fechado ou o benchmark de mercado, o que for maior."}
    topo = {"topo": [[f"RESTRIÇÃO MAPEADA ATÉ AGORA ({hoje}) · {tipo}", linhas + ([f"Ainda não medido: {x}." for x in lac] if lac else [])],
                     ["OS TRÊS CENÁRIOS", tabela]]}
    json.dump(topo, open(a.out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(md))


if __name__ == "__main__":
    main()
