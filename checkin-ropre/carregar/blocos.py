# -*- coding: utf-8 -*-
"""O L do ETL: carrega os números nos cinco blocos do ROPRE.

  R — Resultados          o que aconteceu no período, contra o anterior
  O — Objetivos           avanço das OKRs e o step do projeto
  P — Premissas e Riscos  o que estamos assumindo e o que pode quebrar
  E — Entregas            realizadas, previstas e pendências
  E — Próximos Passos     o que vem, com dono e data

  python3 carregar/blocos.py --cliente clientes/<c>/cliente.json --dados canonico.json \\
      --cadencia mensal --referencia 2026-09-21 --saida checkin.json

O que este módulo NÃO faz: escolher número bonito. Ele carrega o que o
transformar/ calculou, marca o que não foi medido e guarda a regra de
atribuição junto, para o check-in poder ser defendido linha por linha.
"""
import argparse, datetime, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from transformar import canonico, metricas  # noqa: E402

STATUS = {"atingido": "✅", "em_andamento": "⏳", "fora": "❌", "sem_dado": "—"}


def _ler_json(caminho, padrao=None):
    if not caminho or not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _meses_ate(p, quantos=9):
    """Os últimos N meses fechados até o fim do período, para a série e a safra."""
    fim = datetime.date.fromisoformat(p["ate"]).replace(day=1)
    meses = []
    for _ in range(quantos):
        meses.append(fim.isoformat()[:7])
        fim = (fim - datetime.timedelta(days=1)).replace(day=1)
    return list(reversed(meses))


# --------------------------------------------------------------- O: objetivos

def objetivos(cliente, resultados, calls):
    okrs = []
    for kr in (cliente.get("okrs") or []):
        realizado = _realizado(kr, resultados)
        meta = kr.get("meta")
        if realizado is None or meta is None:
            status = "sem_dado"
        else:
            ok = realizado >= meta if kr.get("comparador", ">=") == ">=" else realizado <= meta
            if ok:
                status = "atingido"
            else:
                margem = kr.get("tolerancia", 0.15)
                perto = (realizado >= meta * (1 - margem)) if kr.get("comparador", ">=") == ">=" \
                    else (realizado <= meta * (1 + margem))
                status = "em_andamento" if perto else "fora"
        okrs.append({"kr": kr.get("kr"), "metrica": kr.get("metrica"), "meta": meta, "realizado": realizado,
                     "formato": kr.get("formato", "numero"), "status": status, "icone": STATUS[status],
                     "fonte": kr.get("fonte", "CRM, por data de fechamento")})
    acordos = [a for c in calls for a in c.get("acordos") or []]
    return {"objetivo_smart": cliente.get("objetivo_smart"), "step": cliente.get("step_projeto"),
            "okrs": okrs, "acordado_nas_calls": acordos}


def _realizado(kr, resultados):
    """Lê a métrica do bloco R pelo caminho declarado no cliente.json (ex.: 'novos.n')."""
    atual = resultados
    for parte in str(kr.get("metrica", "")).split("."):
        if not isinstance(atual, dict):
            return None
        atual = atual.get(parte)
    return atual


# --------------------------------------------- P: premissas e riscos

def premissas_riscos(cliente, pacote, calls, resultados):
    premissas = list(cliente.get("premissas") or [])
    if cliente.get("margem_contribuicao"):
        premissas.append({"premissa": "Margem de contribuição",
                          "valor": f"{cliente['margem_contribuicao']:.0%}",
                          "origem": cliente.get("origem_margem", "confirmada com o cliente")})
    if cliente.get("midia_bruta"):
        premissas.append({"premissa": "Verba de mídia (bruta)",
                          "valor": f"R$ {cliente['midia_bruta']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                          "origem": "contrato"})
    regra = cliente.get("atribuicao") or {}
    premissas.append({"premissa": "Regra de atribuição",
                      "valor": regra.get("resumo") or "tag da agência ou origem de mídia paga",
                      "origem": regra.get("fechada_em") and f"fechada em {regra['fechada_em']}" or "a confirmar"})

    riscos = []
    for r in (cliente.get("riscos") or []):
        p, i = r.get("probabilidade", 0), r.get("impacto", 0)
        riscos.append({**r, "score": p * i})
    for c in calls:
        for r in c.get("riscos") or []:
            riscos.append({"causa": f"levantado na call de {c['dia']}", "risco": r, "efeito": None,
                           "probabilidade": None, "impacto": None, "score": None})

    # Risco que o próprio dado denuncia, sem ninguém precisar lembrar.
    if resultados.get("entrada_no_crm") is not None and resultados["entrada_no_crm"] < 0.8:
        riscos.append({"causa": "lead da plataforma não vira contato no CRM",
                       "risco": f"apenas {resultados['entrada_no_crm']:.0%} dos leads entraram no CRM no período",
                       "efeito": "verba comprando lead que o comercial nunca vê",
                       "probabilidade": None, "impacto": None, "score": None})
    for aviso in pacote.get("avisos") or []:
        if "parada" in aviso or "não tem linha no período" in aviso:
            riscos.append({"causa": "base de dados desatualizada", "risco": aviso,
                           "efeito": "indicador do período fica sem medição",
                           "probabilidade": None, "impacto": None, "score": None})

    riscos.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    return {"premissas": premissas, "riscos": riscos}


# ------------------------------------------------------ E: entregas

def entregas(cliente, pacote, entradas, p):
    realizadas = list((entradas or {}).get("realizadas") or [])
    previstas = list((entradas or {}).get("previstas") or [])
    pendencias = [{"dia": c["dia"], "canal": c.get("canal"), "pendencia": c.get("pendencia") or c.get("assunto")}
                  for c in pacote.get("conversas") or []
                  if c.get("pendencia") and canonico.dentro(c.get("dia"), p)]
    for c in pacote.get("calls") or []:
        for pend in c.get("pendencias") or []:
            pendencias.append({"dia": c["dia"], "canal": "call", "pendencia": pend})
    return {"realizadas": realizadas, "previstas": previstas, "pendencias": pendencias,
            "horas": (entradas or {}).get("horas")}


# ------------------------------------------------- montagem

def montar(cliente, pacote, p, entradas=None):
    p_ant = canonico.periodo_anterior(p)
    res = metricas.resultados(pacote, cliente, p, p_ant)
    meses = _meses_ate(p)
    res["serie_mensal"] = metricas.serie_mensal(pacote, cliente, meses)
    res["safra"] = metricas.safra(pacote, cliente, meses)
    res["perdas"] = metricas.perdas(pacote, p)
    res["ticket_distribuicao"] = metricas.distribuicao_ticket(pacote, p)
    if cliente.get("lancamento_manual"):
        res["ponte_planilha"] = metricas.ponte_com_a_planilha(res["serie_mensal"], cliente["lancamento_manual"])

    calls = [c for c in pacote.get("calls") or [] if canonico.dentro(c.get("dia"), p)]

    return {
        "cliente": cliente.get("cliente"),
        "cadencia": p["cadencia"],
        "periodo": p,
        "gerado_em": datetime.date.today().isoformat(),
        "fonte": pacote.get("fonte"),
        "extraido_em": pacote.get("extraido_em"),
        "regra_atribuicao": cliente.get("atribuicao"),
        "resultados": res,
        "objetivos": objetivos(cliente, res, calls),
        "premissas_riscos": premissas_riscos(cliente, pacote, calls, res),
        "entregas": entregas(cliente, pacote, entradas, p),
        "proximos_passos": _proximos(cliente, entradas, calls),
        "avisos": _avisos(pacote, res, p),
    }


def _avisos(pacote, res, p):
    """O que o check-in não conseguiu medir. Sai impresso — indicador sem medição é informação."""
    avisos = list(pacote.get("avisos") or [])
    if res.get("aviso_midia"):
        avisos.insert(0, res["aviso_midia"])
    if res.get("aviso_leads"):
        avisos.insert(0, res["aviso_leads"])
    if res.get("midia_estimada"):
        avisos.append("Resultado do período calculado com a verba contratada proporcional, e não com o gasto "
                      "realizado — a base de mídia não cobriu o período inteiro.")
    if p.get("parcial"):
        avisos.append(f"Período parcial: fechado em {p['ate']}. Meta e comparações são proporcionais aos dias corridos.")
    if res.get("receita_com_canal") is not None and res["receita_com_canal"] < 0.7:
        avisos.append(f"Só {res['receita_com_canal']:.0%} da receita tem canal identificado no CRM — "
                      f"a leitura por canal é parcial por natureza, não por erro de cálculo.")
    return avisos


def _proximos(cliente, entradas, calls):
    passos = list((entradas or {}).get("proximos_passos") or cliente.get("proximos_passos") or [])
    for c in calls:
        for a in c.get("acordos") or []:
            passos.append({"passo": a, "origem": f"call de {c['dia']}", "dono": None, "prazo": None})
    return passos


def main():
    ap = argparse.ArgumentParser(description="Monta o check-in ROPRE a partir do modelo canônico")
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--dados", required=True, nargs="+",
                    help="um ou mais pacotes canônicos (CRM, mídia, conversas); são unidos antes de carregar")
    ap.add_argument("--cadencia", default="mensal", choices=["quinzenal", "mensal", "quarter"])
    ap.add_argument("--referencia", default=datetime.date.today().isoformat())
    ap.add_argument("--fim", help="corta o período (check-in parcial)")
    ap.add_argument("--entradas", help="entradas/entregas.json (realizadas, previstas, horas, próximos passos)")
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()

    cliente = _ler_json(a.cliente)
    pacote = canonico.juntar(*[canonico.ler(caminho) for caminho in a.dados])
    p = canonico.periodo(a.referencia, a.cadencia, fim=a.fim)
    checkin = montar(cliente, pacote, p, _ler_json(a.entradas, {}))
    with open(a.saida, "w", encoding="utf-8") as f:
        json.dump(checkin, f, ensure_ascii=False, indent=1)
    r = checkin["resultados"]
    print(f"{a.saida}: {p['rotulo']}{' (parcial)' if p['parcial'] else ''} — "
          f"{r['vendas']} vendas, R$ {r['receita']:,.2f}, "
          f"{'atingimento ' + format(r['atingimento'], '.0%') if r.get('atingimento') else 'sem meta'}.")
    for aviso in checkin["avisos"]:
        print(f"  aviso: {aviso}")


if __name__ == "__main__":
    main()
