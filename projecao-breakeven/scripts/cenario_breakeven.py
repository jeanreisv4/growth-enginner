#!/usr/bin/env python3
"""
cenario_breakeven.py — monta, sozinho, o cenário em que o projeto BATE o breakeven. Roda em todo projeto.

Pessimista, desejado e otimista só usam o histórico do próprio cliente e a verba de hoje. Quando nenhum fecha, a
pergunta seguinte é sempre a mesma ("o que precisa ser verdade para bater?"), e a resposta não pode depender de o
usuário pedir. A busca, em ordem:

  1. Funil no nível de MERCADO onde o cliente está abaixo dele (referencias/mercado_alavancas.json). A etapa que já
     está acima do mercado fica onde está; o alvo é o maior entre o mercado e a mediana do próprio cliente.
  2. Verba em degraus (+50% da verba atual por mês, no mínimo R$ 500) até o menor teto em que o mês fica no azul e o
     acumulado zera em até 24 meses; senão, o menor teto em que o mês vira. Só vale quando a mídia se paga.
  3. Ainda sem fechar e em inside sales: recompra (o motor da assinatura, com vocabulário de recompra), do menor número
     de pedidos por cliente para o maior.
  4. Nada fecha: o cenário sai com a melhor tentativa e diz o fee, a verba e a recompra que faltariam.

Saída: o premissas.json do cenário, o JSON de metodologia (topo da aba Premissas: o que precisa ser verdade, fontes,
sensibilidade à verba, riscos) e um resumo em JSON no stdout.

Uso (normalmente chamado pelo tres_cenarios.py):
  python3 cenario_breakeven.py --base premissas_desejado.json --piloto "<args do projetar>" --out premissas_breakeven.json \
      --metodologia metodologia_breakeven.json [--mercado arquivo.json --setor b2b_industria] [--teto-verba 6000] [--churn 0.2]
"""
import argparse, json, math, os, shlex, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PILOTO = os.path.join(AQUI, "breakeven_pilot.py")
MERCADO_PADRAO = os.path.join(AQUI, "..", "referencias", "mercado_alavancas.json")
sys.path.insert(0, AQUI)
from aprovacao import calendario, rs, br   # noqa: E402

TAXAS = ("ctr", "connect", "visita_lead", "clique_lead", "lead_mql", "conexao", "conexao_sql", "mql_sql", "sql_venda")
CHURNS = [0.25, 0.20, 0.17, 0.15, 0.12, 0.10]


def tirar(args, flag):
    """Remove todas as ocorrências de `flag VALOR`."""
    out, i = [], 0
    while i < len(args):
        if args[i] == flag:
            i += 2; continue
        out.append(args[i]); i += 1
    return out


def rodar(args, out):
    r = subprocess.run([sys.executable, PILOTO, "projetar", *args, "--out", out], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.load(open(out, encoding="utf-8"))


def ler(d, n_real, limite_zera):
    v, pr = d["veredito"], d["projecao"]
    zera, azul = v.get("acumulado_zera_em"), v.get("no_azul_continuo_desde")
    return {"azul": azul, "zera": zera, "fecha": bool(zera and zera <= n_real + limite_zera), "vira": bool(azul),
            "pior": min(l["acumulado"] for l in pr), "res_fim": pr[-1]["resultado_liquido"]}


def de_pe(d, lim):
    """O acumulado que zerou continua positivo no prazo e no fim da projeção (o mês do fim pode cair num vale sazonal)."""
    pr = d["projecao"]
    no_prazo = next((l["acumulado"] for l in pr if l["mes"] == lim), pr[-1]["acumulado"])
    return no_prazo >= 0 and pr[-1]["acumulado"] >= 0


def piso(a, base, args0, r0, k, env, n_real, verba0):
    """O plano de hoje já bate: procura o menor valor da última conversão do funil (e do ticket) com que o acumulado
    ainda zera no mesmo prazo (12 meses depois do último mês vivido), com e sem a recompra."""
    pc = base["premissas_confirmadas"]
    lim = n_real + 12

    def roda(args, v=None, chave=k):
        d = rodar(args + (["--fixar", f"{chave}={v:.6f}"] if v is not None else []), a.out + ".tmp")
        r = ler(d, 0, lim) if d else None
        if r:   # no piso, "fecha" é zerar no prazo e continuar de pé: acumulado positivo no prazo e no fim da projeção
            r["fecha"] = r["fecha"] and de_pe(d, lim)
        return d, r

    def procurar(args, chave, hi):
        lo_, hi_ = 0.0, hi   # hi fecha; quando nem um valor perto de zero derruba a conta, o piso é zero
        _, r_lo = roda(args, hi * 0.001, chave)
        if r_lo and r_lo["fecha"]:
            return 0.0
        for _ in range(14):
            mid = (lo_ + hi_) / 2
            _, r = roda(args, mid, chave)
            if r and r["fecha"]: hi_ = mid
            else: lo_ = mid
        return hi_

    def media_vendas(d):
        xs = [l["vendas"] for l in d["projecao"] if n_real < l["mes"] <= lim]
        return sum(xs) / len(xs) if xs else 0.0

    plano_k = env[k].get("alvo") or env[k]["atual"]
    piso_k = math.ceil(procurar(args0, k, plano_k) * 1000) / 1000
    ticket0 = float((env.get("ticket") or {}).get("alvo") or (env.get("ticket") or {}).get("atual") or pc.get("ticket") or 0)
    piso_t = math.ceil(procurar(args0, "ticket", ticket0) / 10) * 10 if ticket0 else None
    sem_rc = None
    if pc.get("recompra"):   # a recompra não é medida: quanto o piso depende dela
        args_s = tirar(args0, "--recompra")
        _, r_s = roda(args_s, plano_k)
        sem_rc = math.ceil(procurar(args_s, k, plano_k) * 1000) / 1000 if r_s and r_s["fecha"] else None
    d0, _ = roda(args0)
    sens = []
    for f in (1.0, 0.75, 0.5):
        v = plano_k * f
        if v > piso_k:
            d_, r_ = roda(args0, v); sens.append((v, d_, r_))
    d, r = roda(args0, piso_k)
    sens.append((piso_k, d, r))
    d = rodar(args0 + ["--fixar", f"{k}={piso_k:.6f}"], a.out)
    if os.path.exists(a.out + ".tmp"): os.remove(a.out + ".tmp")
    cal = calendario(d)
    rot_k = env[k]["rotulo"]
    pct = lambda x: f"{br(x * 100, 1)}%"
    linhas = [f"Gerado automaticamente em toda projeção. Aqui o plano de hoje já bate o breakeven{(' (' + a.rotulo + ')') if a.rotulo else ''}: "
              f"com a verba de {rs(verba0)} e o funil do desejado, o acumulado zera em {cal(r0['zera'])}, sem nível de mercado nem verba a mais. "
              f"Por isso este cenário mostra o PISO: até onde o funil pode cair e a conta ainda fecha no mesmo prazo (acumulado zerado até {cal(lim)}).",
              (f"Piso: {rot_k} pode cair de {pct(plano_k)} (plano) para {pct(piso_k)} — {br(media_vendas(d), 1)} vendas por mês em média, "
               f"contra {br(media_vendas(d0), 1)} no plano — e o acumulado ainda zera em {cal(r['zera'])} e fica de pé. Abaixo disso, a conta deixa de fechar até {cal(lim)}."
               if piso_k > 0 else
               f"Piso: mesmo sem venda nova ({rot_k} perto de zero) a recompra da base de clientes já conquistados fecha a conta até {cal(lim)}. "
               "Confira a recompra antes de apresentar: é ela, não o funil, que sustenta o plano.")]
    if piso_t and piso_t < ticket0:
        linhas.append(f"Ticket: com o funil do plano, o ticket médio pode cair de {rs(ticket0)} para {rs(piso_t)} no mesmo prazo.")
    linhas.append(f"Verba: fica em {rs(verba0)}.")
    if pc.get("recompra"):
        rc_ = pc["recompra"]
        linhas.append(f"Recompra (premissa da projeção principal, não medida): reposição a cada {rc_['intervalo']:g} meses por {rc_['vida']:g} meses. "
                      + (f"Sem ela, o piso de {rot_k} sobe para {pct(sem_rc)}." if sem_rc else
                         f"Sem ela, nem o plano zera o acumulado até {cal(lim)}: a recompra é o que segura a conta e a primeira coisa a medir."))
    linhas.append("Resultado no piso: " + (f"mês no azul a partir de {cal(r['azul'])}" if r["azul"] else "nenhum mês fica no azul")
                  + (f"; acumulado zera em {cal(r['zera'])}." if r["zera"] else "; o acumulado não zera em 48 meses."))
    linhas.append("Riscos: o piso de cada alavanca vale com as outras no plano — se duas caem juntas, o piso de cada uma sobe; "
                  "margem, recompra e sazonalidade são as premissas da aba.")
    secoes = [[f"CENÁRIO BREAKEVEN{(' · ' + a.rotulo.upper()) if a.rotulo else ''} · O PLANO JÁ BATE: ATÉ ONDE O FUNIL PODE CAIR", linhas],
              ["SENSIBILIDADE · " + rot_k.upper() + " COM O RESTO DO PLANO",
               {"colunas": [rot_k, "Vendas por mês (média)", "Mês no azul a partir de", "Acumulado zera em", "Pior ponto do acumulado"],
                "linhas": [[pct(v) + (" (plano)" if v == plano_k else " (piso, este cenário)" if v == piso_k else ""),
                            br(media_vendas(d_), 1) if d_ else "-", (cal(r_["azul"]) if r_ else None) or "não acontece",
                            (cal(r_["zera"]) if r_ else None) or "não zera em 48 meses", rs(r_["pior"]) if r_ else "-"] for v, d_, r_ in sens],
                "nota": f"Verba de {rs(verba0)} em todas as linhas; o valor de {rot_k} fica constante a partir do Mês 1 projetado."}]]
    json.dump({"topo": secoes}, open(a.metodologia, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"tipo": "piso", "teto_verba": verba0, "churn": None, "azul": r["azul"], "zera": r["zera"], "piso": {k: piso_k, "ticket": piso_t},
                      "args": shlex.join(args0 + ["--fixar", f"{k}={piso_k:.6f}"]), "recompra": False}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="premissas.json do cenário desejado desta leitura (envelope, verba, realizado)")
    ap.add_argument("--piloto", required=True, help="argumentos do projetar desta leitura, numa string")
    ap.add_argument("--out", required=True)
    ap.add_argument("--metodologia", required=True)
    ap.add_argument("--mercado", default=MERCADO_PADRAO)
    ap.add_argument("--setor", help="setor do arquivo de mercado (padrão: o do modelo)")
    ap.add_argument("--teto-verba", type=float, help="usa este teto em vez de procurar (a outra leitura já escolheu)")
    ap.add_argument("--churn", type=float, help="usa esta recompra em vez de procurar (a outra leitura já escolheu)")
    ap.add_argument("--rotulo", default="", help="leitura (ex.: 'sem legado'), para o título")
    a = ap.parse_args()

    base = json.load(open(a.base, encoding="utf-8"))
    pc, det, env = base["premissas_confirmadas"], base["detectado"], base["envelope"]
    modelo = det.get("modelo") or "inside_sales"
    n_real = len(pc.get("realizado_usado") or {})
    verba0 = float(pc["midia_mensal"])
    merc = json.load(open(a.mercado, encoding="utf-8"))
    setor = a.setor or merc.get("padrao_por_modelo", {}).get(pc.get("perfil") or modelo)
    alav_m = (merc["setores"].get(setor) or {}).get("alavancas", {}) if setor else {}

    # 1. funil de mercado onde o cliente está abaixo
    alvos, linhas_m = [], []
    for k in TAXAS:
        e, m = env.get(k), alav_m.get(k)
        if not e or e.get("atual") is None:
            continue
        atual = e["atual"]
        if m and atual < m["valor"]:
            alvo = max(m["valor"], e.get("mediana") or 0)
            alvos += ["--alvo", f"{k}={alvo:.4f}"]
            linhas_m.append([e["rotulo"], f"{br(atual * 100, 1)}%", f"{br(m['valor'] * 100, 1)}%", m["fonte"], f"{br(alvo * 100, 1)}%"])
        elif m:
            linhas_m.append([e["rotulo"], f"{br(atual * 100, 1)}%", f"{br(m['valor'] * 100, 1)}%", m["fonte"], "fica (já está acima)"])
    t = env.get("ticket") or {}
    if t.get("mediana") and t.get("atual") and t["mediana"] > t["atual"]:
        alvos += ["--alvo", f"ticket={t['mediana']:.2f}"]
        linhas_m.append(["Ticket médio", rs(t["atual"]), "sem benchmark publicado", "mediana do próprio cliente", rs(t["mediana"])])

    pil = shlex.split(a.piloto)
    for f in ("--horizonte", "--mes-alvo", "--rampa-desde", "--rampa-ate", "--verba-plano", "--crescimento-midia", "--midia-teto", "--cenario"):
        pil = tirar(pil, f)
    rampa = (["--rampa-desde", str(n_real + 1)] if n_real else []) + ["--rampa-ate", str(min(n_real + 6, 18))]
    comum = pil + ["--horizonte", "18", "--mes-alvo", "18"] + rampa + alvos
    passo = max(500.0, round(verba0 * 0.5 / 500) * 500)

    def plano(teto):
        degraus, x = [], verba0
        while x < teto - 1e-6:
            x = min(x + passo, teto); degraus.append(x)
        return [verba0] * max(n_real, 0) + [verba0] + degraus

    def tentar(teto, churn=None, tmp=a.out):
        args = comum + ["--verba-plano", ",".join(f"{x:g}" for x in plano(teto))]
        if churn:
            args += ["--recorrencia", "--churn", str(churn), "--ticket", f"{float(pc['ticket']):.2f}"]
        return rodar(args, tmp), args

    # 0. o plano de hoje já bate (sem mercado, sem verba a mais)? Então repetir o desejado com 18 meses não responde
    # nada: o cenário vira o PISO — o quanto a última conversão (e o ticket) pode cair e o acumulado ainda zera no
    # mesmo prazo. brindes corporativos B2B: um único mês bom (setembro) sustentava o plano inteiro; a pergunta era "e se não se repetir?".
    if a.churn is None and a.teto_verba is None:
        args0 = pil + ["--horizonte", "18", "--mes-alvo", "18"] + rampa + ["--verba-plano", ",".join(f"{x:g}" for x in plano(verba0))]
        d0 = rodar(args0, a.out + ".tmp")
        r0 = ler(d0, 0, n_real + 12) if d0 else None
        conv = [k for k in TAXAS if env.get(k) and env[k].get("atual") and not env[k].get("fixada")]
        if r0 and r0["fecha"] and de_pe(d0, n_real + 12) and conv:
            return piso(a, base, args0, r0, conv[-1], env, n_real, verba0)
    sens, escolhido = [], None
    tetos = [verba0 + passo * i for i in range(0, 16) if verba0 + passo * i <= verba0 * 8 + 1e-6]
    if a.teto_verba is not None:
        tetos = [a.teto_verba]
    if a.churn is None:
        # critério em dois degraus: a menor verba que zera o acumulado em até 12 meses depois do último mês vivido;
        # sem nenhuma, em até 24; sem nenhuma, a menor que vira o mês. Aceitar 24 de cara deixava a verba de hoje
        # zerando em 18 meses quando um degrau a mais zerava em 8 (escritório de arquitetura).
        for teto in tetos:
            d, args = tentar(teto, tmp=a.out + ".tmp")
            if d is None: continue
            r = ler(d, 0, n_real + 24); r["teto"] = teto
            r["rapido"] = bool(r["zera"] and r["zera"] <= n_real + 12); sens.append(r)
            if a.teto_verba is not None: break
            rap = [x for x in sens if x["rapido"]]
            if rap and len([x for x in sens if x["teto"] > rap[0]["teto"]]) >= 2:
                break
        escolha = (next((x for x in sens if x["rapido"]), None) or next((x for x in sens if x["fecha"]), None)
                   or next((x for x in sens if x["vira"]), None))
        if a.teto_verba is not None and sens:
            escolha = sens[0]
        if escolha:
            escolhido = ("verba", escolha["teto"], None)
    recompra = []
    if escolhido is None and modelo == "inside_sales" and not pc.get("recorrencia") and not pc.get("recompra"):
        # recompra: do menor número de pedidos por cliente para o maior e, em cada um, da menor verba para a maior;
        # vale a primeira combinação em que o acumulado zera; sem nenhuma, a primeira em que o mês vira
        verbas_r = [a.teto_verba] if a.teto_verba else [verba0 * f for f in (1, 2, 3)]
        primeiro_vira = None
        for ch in ([a.churn] if a.churn else CHURNS):
            for teto_r in verbas_r:
                d, args = tentar(teto_r, ch, tmp=a.out + ".tmp")
                if d is None: continue
                r = ler(d, 0, n_real + 36); r["churn"] = ch; r["teto"] = teto_r
                if teto_r == verbas_r[-1] or r["fecha"]: recompra.append(r)
                if r["fecha"]:
                    escolhido = ("recompra", teto_r, ch); break
                if r["vira"] and primeiro_vira is None: primeiro_vira = ("recompra", teto_r, ch)
            if escolhido: break
        escolhido = escolhido or primeiro_vira
    if escolhido is None:   # nada fecha: entrega a melhor tentativa (o maior teto testado)
        escolhido = ("nada", tetos[-1], None)
    tipo, teto, churn = escolhido
    d, args = tentar(teto, churn)
    if os.path.exists(a.out + ".tmp"): os.remove(a.out + ".tmp")
    if d is None:
        sys.exit("cenário breakeven: o piloto falhou na tentativa final")
    r = ler(d, n_real, 24)
    cal = calendario(d)

    # --- metodologia (topo da aba Premissas)
    pl = plano(teto)[n_real:] if n_real else plano(teto)
    verba_txt = " → ".join(rs(x) for x in pl) if len(pl) > 1 else rs(pl[0])
    pr = d["projecao"]; ult = pr[-1]
    leads_k = "Leads" if "Leads" in ult else None
    lv_hoje = None
    tx = det.get("taxas_efetivas") or {}
    vj = tx.get("volumes_janela") or {}
    if vj.get("Leads"):
        lv_hoje = (vj.get(det["cadeia_usada"][-1]) or 0) / vj["Leads"]
    lv_proj = (ult.get("vendas_originadas") or ult["vendas"]) / ult[leads_k] if (leads_k and ult.get(leads_k)) else None
    linhas = [f"Gerado automaticamente em toda projeção: é o cenário em que o projeto bate o breakeven{(' (' + a.rotulo + ')') if a.rotulo else ''}. "
              "Pessimista, desejado e otimista usam só o histórico do cliente e a verba de hoje; este leva ao nível de mercado as etapas que estão abaixo dele e procura a verba que fecha a conta."]
    mud = [x for x in linhas_m if not x[4].startswith("fica")]
    if mud:
        linhas.append("O que precisa ser verdade (rampa até " + (cal(min(n_real + 6, 18)) or "M6") + "): "
                      + "; ".join(f"{x[0]} de {x[1]} para {x[4]}" for x in mud) + ".")
    else:
        linhas.append("Nenhuma etapa do funil está abaixo do mercado: a alavanca é verba (e, se preciso, recompra).")
    linhas.append(f"Verba: {verba_txt}, subindo um degrau por mês e só quando o custo por lead e os SQLs do mês anterior confirmarem." if teto > verba0
                  else f"Verba: fica em {rs(verba0)} — com o funil de mercado a conta fecha sem subir a verba.")
    if pc.get("recompra"):
        rc_ = pc["recompra"]
        linhas.append(f"Recompra (premissa da projeção principal): reposição a cada {rc_['intervalo']:g} meses por {rc_['vida']:g} meses, "
                      f"com pedido de {rc_.get('fator', 1):.0%} do primeiro.")
    if tipo == "recompra":
        linhas.append(f"Recompra: o funil de mercado com verba não basta; entra cliente comprando todo mês, com {br(churn * 100, 0)}% dos clientes ativos "
                      f"parando a cada mês — cerca de {br(1 / churn, 1)} pedidos por cliente. Não é medido hoje: confirme com o cliente antes de apresentar.")
    if tipo == "nada":
        cam = base.get("caminho") or {}
        linhas.append("NENHUMA combinação testada fecha (funil de mercado, verba até 8x e recompra até 10 pedidos por cliente). "
                      + (f"Nem com fee zero o mês fecha. " if (cam.get("fee_que_fecha") or 0) <= 0 else f"O mês fecharia com fee de {rs(cam['fee_que_fecha'])}. ")
                      + "A conversa é de estrutura: margem, ticket ou fee.")
    linhas.append("Resultado: " + (f"mês no azul a partir de {cal(r['azul'])}" if r["azul"] else "nenhum mês fica no azul em 48 meses")
                  + (f"; acumulado zera em {cal(r['zera'])}." if r["zera"] else "; o acumulado não zera em 48 meses."))
    riscos = []
    if lv_hoje and lv_proj:
        riscos.append(f"lead → venda resultante de {br(lv_proj * 100, 1)}% no fim, contra {br(lv_hoje * 100, 1)}% hoje"
                      + (" — o dobro ou mais: só se sustenta se as etapas fortes não caírem quando as fracas subirem" if lv_proj > 2 * lv_hoje else ""))
    if d["veredito"].get("alerta_teto_receita"):
        fontes_dif = ["funil de mercado"] + (["verba maior"] if teto > verba0 else []) + (["recompra"] if (pc.get("recompra") or tipo == "recompra") else [])
        riscos.append("trava de sanidade: " + d["veredito"]["alerta_teto_receita"].replace(" Diga de onde vem a diferença antes de apresentar.", "")
                      + " A diferença vem de " + " + ".join(fontes_dif))
    if teto > verba0:
        riscos.append("o CPM fica constante; escalar a verba satura o público e pode encarecer o lead — por isso os degraus sobem só com o mês anterior confirmado")
    riscos.append("margem e benchmarks são os da aba; benchmark de setor é aproximação para o cliente")
    linhas.append("Riscos: " + "; ".join(riscos) + ".")
    secoes = [[f"CENÁRIO BREAKEVEN{(' · ' + a.rotulo.upper()) if a.rotulo else ''} · O QUE PRECISA SER VERDADE PARA BATER", linhas]]
    if linhas_m:
        secoes.append(["PREMISSAS DE MERCADO · ONDE O CLIENTE ESTÁ E O QUE SOBE",
                       {"colunas": ["Etapa", "Cliente hoje", "Mercado", "Fonte", "Usado no cenário"],
                        "spans": [["B", "B"], ["C", "D"], ["E", "F"], ["G", "L"], ["M", "N"]], "linhas": linhas_m,
                        "nota": f"Setor de referência: {setor} ({os.path.basename(a.mercado)}). Só sobe o que está abaixo do mercado; o alvo é o maior entre o mercado e a mediana do próprio cliente."}])
    if sens:
        secoes.append(["SENSIBILIDADE À VERBA · MESMO FUNIL DE MERCADO",
                       {"colunas": ["Teto da verba", "Mês no azul a partir de", "Acumulado zera em", "Resultado do mês no fim", "Pior ponto do acumulado"],
                        "linhas": [[rs(s["teto"]) + (" (este cenário)" if s["teto"] == teto and tipo == "verba" else ""),
                                    cal(s["azul"]) or "não acontece", cal(s["zera"]) or "não zera em 48 meses", rs(s["res_fim"]), rs(s["pior"])] for s in sens],
                        "nota": f"Degraus de {rs(passo)} por mês a partir de {rs(verba0)}."}])
    if recompra:
        secoes.append(["SENSIBILIDADE À RECOMPRA · FUNIL DE MERCADO",
                       {"colunas": ["Param de comprar por mês", "Pedidos por cliente", "Mês no azul a partir de", "Acumulado zera em", "Pior ponto do acumulado"],
                        "linhas": [[f"{br(s['churn'] * 100, 0)}%" + (" (este cenário)" if (s["churn"], s["teto"]) == (churn, teto) else ""), br(1 / s["churn"], 1),
                                    cal(s["azul"]) or "não acontece", cal(s["zera"]) or "não zera em 48 meses", rs(s["pior"])] for s in recompra],
                        "nota": "Recompra modelada como cliente ativo comprando todo mês (motor da assinatura)."}])
    json.dump({"topo": secoes}, open(a.metodologia, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"tipo": tipo, "teto_verba": teto, "churn": churn, "azul": r["azul"], "zera": r["zera"],
                      "args": shlex.join(args), "recompra": tipo == "recompra"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
