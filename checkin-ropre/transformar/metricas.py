# -*- coding: utf-8 -*-
"""O T do ETL: do modelo canônico para os números do check-in.

Nenhuma métrica aqui inventa dado. Quando a fonte não trouxe (mídia parada,
MQL não registrado), o campo vem `None` e o bloco imprime "não medido" — que é
informação, e diferente de zero.

Convenções que valem para todo cliente, aprendidas em campo:

* **Faturamento lê data de fechamento.** É o que o cliente reconhece como
  resultado do mês. Safra por data de criação responde outra pergunta ("o lead
  daquele mês virou o quê") e serve para eficiência de mídia, não para faturamento.
* **Novo e recorrente andam separados e somados.** A planilha do cliente costuma
  lançar só o novo; a recompra fica numa linha à parte e some do total. O
  check-in mostra os dois e a soma.
* **Break-even do período é proporcional aos dias.** Quinzena não se compara com
  meta mensal.
"""
import collections
import datetime
import statistics

from . import canonico


def _dias(p):
    de = datetime.date.fromisoformat(p["de"])
    ate = datetime.date.fromisoformat(p["ate"])
    return (ate - de).days + 1


def _dias_no_mes(p):
    de = datetime.date.fromisoformat(p["de"])
    return (canonico._fim_do_mes(de)).day


def _var(atual, anterior):
    """Variação relativa. None quando não dá para comparar (base zero ou ausente)."""
    if atual is None or anterior in (None, 0):
        return None
    return (atual - anterior) / anterior


def vendas_do_periodo(pacote, p, so_agencia=True):
    out = []
    for n in pacote["negocios"]:
        if n["status"] != "ganho" or not canonico.dentro(n.get("fechado_em"), p):
            continue
        if so_agencia and not n["atribuicao"]["agencia"]:
            continue
        if (n.get("valor") or 0) <= 0:
            continue
        out.append(n)
    return out


def cobertura_midia(pacote, cliente, p):
    """A mídia do período está completa?

    Sem isso o check-in publica ROAS inflado: aconteceu na primeira execução real,
    com a base de um canal parada — o mês ficou só com o outro canal e o ROAS
    saltou para 37. Métrica que depende de investimento só sai quando todo canal
    configurado tem dado até o fim do período.
    """
    canais = [a["canal"] for a in ((cliente.get("midia") or {}).get("abas") or [])]
    if not canais:
        canais = sorted({m["canal"] for m in pacote["midia"]})
    # Plataforma de anúncio consolida com atraso: exigir dado do próprio dia reprova todo
    # período corrente. A tolerância padrão é de um dia (D-1) e é configurável por cliente.
    tolerancia = int((cliente.get("midia") or {}).get("tolerancia_dias", 1))
    limite = (datetime.date.fromisoformat(p["ate"]) - datetime.timedelta(days=tolerancia)).isoformat()
    ultimo, faltando = {}, []
    for c in canais:
        dias = sorted({m["dia"] for m in pacote["midia"] if m["canal"] == c and canonico.dentro(m.get("dia"), p)})
        ultimo[c] = dias[-1] if dias else None
        if not dias or dias[-1] < limite:
            faltando.append(c)
    return {"canais": canais, "ultimo_dia": ultimo, "incompletos": faltando,
            "completa": not faltando, "exigido_ate": limite}


def resultados(pacote, cliente, p, p_anterior=None):
    """Bloco R: o que aconteceu no período, contra o período anterior."""
    v = vendas_do_periodo(pacote, p)
    novos = [n for n in v if n["tipo"] == "novo"]
    recorrentes = [n for n in v if n["tipo"] == "recorrente"]
    receita = sum(n["valor"] for n in v)

    midia = [m for m in pacote["midia"] if canonico.dentro(m.get("dia"), p)]
    cobertura_m = cobertura_midia(pacote, cliente, p)
    investido = sum(m["investimento"] for m in midia) if midia else None
    leads = _soma(midia, "leads")
    impressoes = _soma(midia, "impressoes")
    cliques = _soma(midia, "cliques")
    if not cobertura_m["completa"]:
        # dado parcial não vira indicador: vira aviso nomeando o canal e o último dia
        investido = leads = impressoes = cliques = None

    # Leads têm cobertura própria: um canal pode trazer custo e não trazer lead
    # (foi o caso do Meta pelo Flow). Lead parcial estraga CPL e entrada no CRM.
    canais_sem_lead = [c for c in cobertura_m["canais"]
                       if not any(m.get("leads") is not None for m in midia if m["canal"] == c)]
    if canais_sem_lead and midia:
        leads = None

    contatos = [c for c in pacote["contatos"]
                if canonico.dentro(c.get("criado_em"), p) and c["atribuicao"]["agencia"]]

    economia = economia_do_periodo(cliente, p, receita, investido)

    bloco = {
        "periodo": p,
        "vendas": len(v),
        "receita": receita,
        "ticket": (receita / len(v)) if v else None,
        "novos": {"n": len(novos), "receita": sum(n["valor"] for n in novos),
                  "ticket": (sum(n["valor"] for n in novos) / len(novos)) if novos else None},
        "recorrentes": {"n": len(recorrentes), "receita": sum(n["valor"] for n in recorrentes),
                        "ticket": (sum(n["valor"] for n in recorrentes) / len(recorrentes)) if recorrentes else None},
        "participacao_recorrente": (len(recorrentes) / len(v)) if v else None,
        "investimento": investido,
        "leads_plataforma": leads,
        "contatos_no_crm": len(contatos),
        "entrada_no_crm": (len(contatos) / leads) if (leads and leads > 0) else None,
        "impressoes": impressoes,
        "cliques": cliques,
        "ctr": (cliques / impressoes) if (impressoes and cliques is not None) else None,
        "cpl": (investido / leads) if (investido and leads) else None,
        "roas": (receita / investido) if (investido and investido > 0) else None,
        "cac": (investido / len(novos)) if (investido and novos) else None,
        "por_canal": por_canal(v, midia),
        "cobertura_atribuicao": cobertura(pacote, p),
        "receita_com_canal": (sum(n["valor"] for n in v if n.get("canal")) / receita) if receita else None,
        "cobertura_midia": {**cobertura_m, "canais_sem_lead": canais_sem_lead},
        **economia,
    }
    if canais_sem_lead and leads is None and cobertura_m["completa"]:
        bloco["aviso_leads"] = (f"Contagem de leads sem medição: {', '.join(canais_sem_lead)} não trouxe lead no "
                                f"período. CPL e entrada no CRM ficam de fora; custo e ROAS seguem medidos.")
    if not cobertura_m["completa"]:
        faltas = ", ".join(f"{c} (último dia com dado: {cobertura_m['ultimo_dia'].get(c) or 'nenhum'})"
                           for c in cobertura_m["incompletos"])
        bloco["aviso_midia"] = (f"Mídia incompleta no período — {faltas}. Investimento, CPL, CTR, ROAS e CAC "
                                f"ficam sem medição até a base ser atualizada.")

    if p_anterior:
        ant = resultados(pacote, cliente, p_anterior)
        bloco["anterior"] = {k: ant.get(k) for k in
                             ("periodo", "vendas", "receita", "ticket", "investimento", "roas", "cac",
                              "leads_plataforma", "contatos_no_crm", "resultado")}
        bloco["variacao"] = {k: _var(bloco.get(k), ant.get(k))
                             for k in ("vendas", "receita", "ticket", "investimento", "roas", "cac",
                                       "leads_plataforma", "contatos_no_crm")}
    return bloco


def _soma(regs, campo):
    vals = [r[campo] for r in regs if r.get(campo) is not None]
    return sum(vals) if vals else None


def economia_do_periodo(cliente, p, receita, investido):
    """Break-even proporcional aos dias do período e resultado do cliente."""
    fee = cliente.get("fee")
    margem = cliente.get("margem_contribuicao")
    verba_bruta = cliente.get("midia_bruta")
    imposto = cliente.get("imposto_midia", 0.0)
    if not fee or not margem:
        return {"break_even_mes": None, "meta_periodo": None, "atingimento": None, "resultado": None}

    custo_mes = fee + (verba_bruta or 0.0)
    break_even_mes = custo_mes / margem
    fracao = _dias(p) / _dias_no_mes(p)
    meta = break_even_mes * fracao

    # Resultado do período: margem sobre a receita menos fee proporcional e mídia realmente gasta (bruta).
    if investido is not None and imposto < 1:
        midia_bruta, estimada = investido / (1 - imposto), False
    else:
        # sem gasto medido, usa a verba contratada proporcional — e diz que usou
        midia_bruta, estimada = (verba_bruta or 0.0) * fracao, True
    resultado = receita * margem - fee * fracao - midia_bruta
    return {
        "break_even_mes": break_even_mes,
        "meta_periodo": meta,
        "atingimento": (receita / meta) if meta else None,
        "resultado": resultado,
        "custo_periodo": fee * fracao + midia_bruta,
        "midia_estimada": estimada,
    }


def por_canal(vendas, midia):
    """Só existe canal onde a fonte marcou canal. Sem marcação, o bloco diz isso."""
    canais = collections.defaultdict(lambda: {"vendas": 0, "receita": 0.0, "investimento": 0.0})
    for n in vendas:
        c = n.get("canal") or "não identificado"
        canais[c]["vendas"] += 1
        canais[c]["receita"] += n["valor"]
    for m in midia:
        canais[m["canal"]]["investimento"] += m["investimento"]
    for c, d in canais.items():
        d["roas"] = (d["receita"] / d["investimento"]) if d["investimento"] else None
    return dict(sorted(canais.items(), key=lambda kv: -kv[1]["receita"]))


def cobertura(pacote, p):
    """Como as vendas do período estão marcadas — a tabela que evita briga de número."""
    c = collections.Counter()
    for n in pacote["negocios"]:
        if n["status"] == "ganho" and canonico.dentro(n.get("fechado_em"), p) and (n.get("valor") or 0) > 0:
            c[n["atribuicao"]["marca"]] += 1
    return dict(c.most_common())


def safra(pacote, cliente, meses):
    """Eficiência da mídia por safra de criação — a leitura certa para ROAS de campanha."""
    linhas = {}
    for mes in meses:
        criadas = [n for n in pacote["negocios"]
                   if n["atribuicao"]["agencia"] and (n.get("criado_em") or "").startswith(mes)]
        resolvidas = [n for n in criadas if n["status"] in ("ganho", "perdido")]
        ganhas = [n for n in criadas if n["status"] == "ganho" and (n.get("valor") or 0) > 0]
        investido = sum(m["investimento"] for m in pacote["midia"] if (m.get("dia") or "").startswith(mes)) or None
        receita = sum(n["valor"] for n in ganhas)
        linhas[mes] = {
            "criadas": len(criadas), "resolvidas": len(resolvidas), "ganhas": len(ganhas), "receita": receita,
            "taxa_ganho": (len(ganhas) / len(resolvidas)) if resolvidas else None,
            "maturidade": (len(resolvidas) / len(criadas)) if criadas else None,
            "investimento": investido,
            "eficiencia": (receita / investido) if investido else None,
        }
    return linhas


def perdas(pacote, p, limite=8):
    c = collections.Counter()
    for n in pacote["negocios"]:
        if n["status"] == "perdido" and n["atribuicao"]["agencia"] and canonico.dentro(n.get("criado_em"), p):
            c[n.get("motivo_perda") or "sem motivo registrado"] += 1
        # perdas do período também contam pelo fechamento, quando a fonte traz
    total = sum(c.values())
    return {"total": total, "motivos": [{"motivo": m, "n": n, "share": (n / total) if total else None}
                                        for m, n in c.most_common(limite)]}


def serie_mensal(pacote, cliente, meses):
    """Faturamento mês a mês por data de fechamento — a série que vai ao gráfico."""
    out = {}
    for mes in meses:
        p = {"de": f"{mes}-01", "ate": canonico._fim_do_mes(datetime.date.fromisoformat(f"{mes}-01")).isoformat()}
        v = [n for n in pacote["negocios"]
             if n["status"] == "ganho" and n["atribuicao"]["agencia"]
             and (n.get("fechado_em") or "").startswith(mes) and (n.get("valor") or 0) > 0]
        novos = [n for n in v if n["tipo"] == "novo"]
        rec = [n for n in v if n["tipo"] == "recorrente"]
        out[mes] = {"vendas": len(v), "receita": sum(n["valor"] for n in v),
                    "novos": len(novos), "receita_novos": sum(n["valor"] for n in novos),
                    "recorrentes": len(rec), "receita_recorrentes": sum(n["valor"] for n in rec)}
    return out


def ponte_com_a_planilha(serie, lancamento_manual):
    """Compara o CRM com o que o cliente lança na planilha.

    A pergunta "por que tem mais venda na apresentação do que na planilha?" aparece
    em toda reunião. Ela se responde uma vez, com a linha de recompra do lado.
    """
    linhas = []
    for mes, manual in (lancamento_manual or {}).items():
        crm = serie.get(mes)
        if not crm:
            continue
        linhas.append({
            "mes": mes,
            "planilha_novas": manual.get("vendas_novas"),
            "planilha_receita_novas": manual.get("receita_novas"),
            "planilha_recorrentes": manual.get("vendas_recorrentes"),
            "planilha_receita_recorrentes": manual.get("receita_recorrentes"),
            "crm_novas": crm["novos"], "crm_receita_novas": crm["receita_novos"],
            "crm_recorrentes": crm["recorrentes"], "crm_receita_recorrentes": crm["receita_recorrentes"],
            "diferenca_receita": crm["receita"] - ((manual.get("receita_novas") or 0)
                                                   + (manual.get("receita_recorrentes") or 0)),
        })
    return linhas


def distribuicao_ticket(pacote, p, faixas=(1000, 1500, 2500, 4500, 10000)):
    v = [n["valor"] for n in vendas_do_periodo(pacote, p)]
    if not v:
        return None
    limites = list(faixas)
    nomes, cont = [], []
    anterior = 0
    for lim in limites:
        nomes.append(f"R$ {anterior:,.0f} a {lim:,.0f}".replace(",", "."))
        cont.append(sum(1 for x in v if anterior <= x < lim))
        anterior = lim
    nomes.append(f"acima de R$ {limites[-1]:,.0f}".replace(",", "."))
    cont.append(sum(1 for x in v if x >= limites[-1]))
    return {"media": statistics.mean(v), "mediana": statistics.median(v),
            "faixas": [{"faixa": n, "n": c} for n, c in zip(nomes, cont)]}
