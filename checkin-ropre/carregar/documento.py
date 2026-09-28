# -*- coding: utf-8 -*-
"""Check-in ROPRE em markdown — a versão de revisão, e a base do documento vivo.

  python3 carregar/documento.py --checkin checkin.json --saida checkin.md

O deck é para a reunião; o documento é para conferir antes dela e para ficar de
registro depois. Os dois saem do mesmo `checkin.json`, então não existe versão
com número diferente.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from carregar.formato import moeda, numero, percentual, variacao, valor, mes_curto  # noqa: E402


def _linha_kpi(rotulo, atual, anterior, var, fmt=moeda):
    return f"| {rotulo} | {fmt(atual)} | {fmt(anterior)} | {variacao(var)} |"


def montar(c):
    r = c["resultados"]
    p = c["periodo"]
    ant = r.get("anterior") or {}
    var = r.get("variacao") or {}
    L = []

    L.append(f"# Check-in {p['cadencia']} · {c['cliente']}")
    L.append("")
    L.append(f"**{p['rotulo']}**{' · período parcial, fechado em ' + p['ate'] if p['parcial'] else ''} · "
             f"gerado em {c['gerado_em']} · fonte: {c.get('fonte')} (extraído em {c.get('extraido_em')})")
    L.append("")

    # ---------------------------------------------------------------- R
    L.append("## R · Resultados")
    L.append("")
    frase = (f"O período fechou **{numero(r['vendas'])} vendas** e **{moeda(r['receita'])}**, "
             f"{variacao(var.get('receita'))} contra {ant.get('periodo', {}).get('rotulo', 'o período anterior')}.")
    if r.get("atingimento") is not None:
        base = (f"{moeda(r['meta_periodo'])}, proporcional ao break-even de {moeda(r['break_even_mes'])}/mês"
                if p["parcial"] or p["cadencia"] == "quinzenal"
                else f"o break-even de {moeda(r['break_even_mes'])}/mês")
        frase += f" São {percentual(r['atingimento'])} da meta do período ({base})."
    L.append(frase)
    L.append("")
    L.append("| Indicador | Período | Anterior | Variação |")
    L.append("| --- | --- | --- | --- |")
    L.append(_linha_kpi("Receita", r["receita"], ant.get("receita"), var.get("receita")))
    L.append(_linha_kpi("Vendas", r["vendas"], ant.get("vendas"), var.get("vendas"), lambda v: numero(v)))
    L.append(_linha_kpi("Ticket médio", r["ticket"], ant.get("ticket"), var.get("ticket")))
    L.append(_linha_kpi("Investimento", r["investimento"], ant.get("investimento"), var.get("investimento")))
    L.append(_linha_kpi("ROAS", r["roas"], ant.get("roas"), var.get("roas"), lambda v: numero(v, 2)))
    L.append(_linha_kpi("CAC (venda nova)", r["cac"], ant.get("cac"), var.get("cac")))
    L.append(_linha_kpi("Leads nas plataformas", r["leads_plataforma"], ant.get("leads_plataforma"),
                        var.get("leads_plataforma"), lambda v: numero(v)))
    L.append(_linha_kpi("Contatos criados no CRM", r["contatos_no_crm"], ant.get("contatos_no_crm"),
                        var.get("contatos_no_crm"), lambda v: numero(v)))
    L.append(f"| Entrada no CRM | {percentual(r['entrada_no_crm'])} | — | — |")
    L.append(f"| Resultado do período | {moeda(r.get('resultado'))} | {moeda(ant.get('resultado'))} | — |")
    L.append("")

    L.append("### Novo contra recorrente")
    L.append("")
    L.append("| | Vendas | Receita | Ticket |")
    L.append("| --- | --- | --- | --- |")
    L.append(f"| Novos | {numero(r['novos']['n'])} | {moeda(r['novos']['receita'])} | {moeda(r['novos']['ticket'])} |")
    L.append(f"| Recorrentes | {numero(r['recorrentes']['n'])} | {moeda(r['recorrentes']['receita'])} | "
             f"{moeda(r['recorrentes']['ticket'])} |")
    L.append(f"| **Total** | **{numero(r['vendas'])}** | **{moeda(r['receita'])}** | **{moeda(r['ticket'])}** |")
    L.append("")
    if r.get("participacao_recorrente") is not None:
        L.append(f"Recorrência é {percentual(r['participacao_recorrente'])} das vendas do período.")
        L.append("")

    if r.get("serie_mensal"):
        L.append("### Mês a mês, por data de fechamento")
        L.append("")
        L.append("| Mês | Vendas | Receita | Novos | Recorrentes |")
        L.append("| --- | --- | --- | --- | --- |")
        for mes, d in r["serie_mensal"].items():
            L.append(f"| {mes_curto(mes)} | {numero(d['vendas'])} | {moeda(d['receita'])} | "
                     f"{numero(d['novos'])} | {numero(d['recorrentes'])} |")
        L.append("")

    if r.get("ponte_planilha"):
        L.append("### Planilha do cliente contra CRM")
        L.append("")
        L.append("A planilha lança só a venda nova; a recompra fica em linha separada e some do total. "
                 "Por isso o check-in mostra mais venda que o lançamento manual.")
        L.append("")
        L.append("| Mês | Planilha (novas) | Planilha (recorrentes) | CRM (novas) | CRM (recorrentes) | Diferença |")
        L.append("| --- | --- | --- | --- | --- | --- |")
        for l in r["ponte_planilha"]:
            L.append(f"| {mes_curto(l['mes'])} | {numero(l['planilha_novas'])} · {moeda(l['planilha_receita_novas'])} | "
                     f"{numero(l['planilha_recorrentes'])} · {moeda(l['planilha_receita_recorrentes'])} | "
                     f"{numero(l['crm_novas'])} · {moeda(l['crm_receita_novas'])} | "
                     f"{numero(l['crm_recorrentes'])} · {moeda(l['crm_receita_recorrentes'])} | "
                     f"{moeda(l['diferenca_receita'])} |")
        L.append("")

    if r.get("safra"):
        L.append("### Eficiência da mídia, por safra de criação")
        L.append("")
        L.append("| Safra | Criadas | Resolvidas | Ganhas | Taxa de ganho | Investimento | Eficiência |")
        L.append("| --- | --- | --- | --- | --- | --- | --- |")
        for mes, d in r["safra"].items():
            L.append(f"| {mes_curto(mes)} | {numero(d['criadas'])} | {percentual(d['maturidade'])} | "
                     f"{numero(d['ganhas'])} | {percentual(d['taxa_ganho'], 1)} | {moeda(d['investimento'])} | "
                     f"{numero(d['eficiencia'], 1)} |")
        L.append("")

    if r.get("por_canal"):
        L.append("### Por canal")
        L.append("")
        L.append("| Canal | Vendas | Receita | Investimento | ROAS |")
        L.append("| --- | --- | --- | --- | --- |")
        for canal, d in r["por_canal"].items():
            L.append(f"| {canal} | {numero(d['vendas'])} | {moeda(d['receita'])} | {moeda(d['investimento'])} | "
                     f"{numero(d['roas'], 2) if d['roas'] is not None else '—'} |")
        L.append("")

    if r.get("cobertura_atribuicao"):
        L.append("### Como as vendas do período estão marcadas")
        L.append("")
        L.append(f"Regra: {(c.get('regra_atribuicao') or {}).get('resumo', 'não declarada')}"
                 f"{' (fechada em ' + c['regra_atribuicao']['fechada_em'] + ')' if (c.get('regra_atribuicao') or {}).get('fechada_em') else ''}.")
        L.append("")
        L.append("| Marca no CRM | Vendas |")
        L.append("| --- | --- |")
        for marca, n in r["cobertura_atribuicao"].items():
            L.append(f"| {marca} | {numero(n)} |")
        L.append("")

    # ---------------------------------------------------------------- O
    o = c["objetivos"]
    L.append("## O · Objetivos")
    L.append("")
    if o.get("objetivo_smart"):
        L.append(f"**Objetivo:** {o['objetivo_smart']}")
        L.append("")
    if o.get("step"):
        L.append(f"**Step do projeto:** {o['step']}")
        L.append("")
    if o.get("okrs"):
        L.append("| | Key result | Meta | Realizado |")
        L.append("| --- | --- | --- | --- |")
        for kr in o["okrs"]:
            L.append(f"| {kr['icone']} | {kr['kr']} | {valor(kr['meta'], kr['formato'])} | "
                     f"{valor(kr['realizado'], kr['formato'])} |")
        L.append("")
    if o.get("acordado_nas_calls"):
        L.append("**Acordado com o cliente nas calls do período:**")
        L.append("")
        for a in o["acordado_nas_calls"]:
            L.append(f"- {a}")
        L.append("")

    # ---------------------------------------------------------------- P
    pr = c["premissas_riscos"]
    L.append("## P · Premissas e Riscos")
    L.append("")
    if pr.get("premissas"):
        L.append("| Premissa | Valor | Origem |")
        L.append("| --- | --- | --- |")
        for pm in pr["premissas"]:
            L.append(f"| {pm['premissa']} | {pm['valor']} | {pm.get('origem', '—')} |")
        L.append("")
    if pr.get("riscos"):
        L.append("| Causa | Risco | Efeito | P × I |")
        L.append("| --- | --- | --- | --- |")
        for risco in pr["riscos"]:
            pi = (f"{risco['probabilidade']} × {risco['impacto']} = {risco['score']}"
                  if risco.get("score") else "—")
            L.append(f"| {risco.get('causa', '—')} | {risco.get('risco', '—')} | {risco.get('efeito') or '—'} | {pi} |")
        L.append("")

    # ---------------------------------------------------------------- E
    e = c["entregas"]
    L.append("## E · Entregas")
    L.append("")
    if e.get("realizadas"):
        L.append("**Realizadas no período**")
        L.append("")
        for item in e["realizadas"]:
            L.append(f"- ✅ {item if isinstance(item, str) else item.get('entrega')}")
        L.append("")
    if e.get("previstas"):
        L.append("**Previstas**")
        L.append("")
        for item in e["previstas"]:
            if isinstance(item, str):
                L.append(f"- ⏳ {item}")
            else:
                prazo = f" · {item['prazo']}" if item.get("prazo") else ""
                L.append(f"- ⏳ {item.get('entrega')}{prazo}")
        L.append("")
    if e.get("pendencias"):
        L.append("**Pendências abertas (calls e conversas)**")
        L.append("")
        for pend in e["pendencias"]:
            L.append(f"- {pend['dia']} · {pend.get('canal', '—')} · {pend['pendencia']}")
        L.append("")
    if e.get("horas"):
        L.append(f"Horas dedicadas ao projeto no período: {e['horas']}.")
        L.append("")

    # ---------------------------------------------------------------- E
    L.append("## E · Próximos Passos")
    L.append("")
    if c.get("proximos_passos"):
        for passo in c["proximos_passos"]:
            if isinstance(passo, str):
                L.append(f"- {passo}")
            else:
                dono = f" · {passo['dono']}" if passo.get("dono") else ""
                prazo = f" · {passo['prazo']}" if passo.get("prazo") else ""
                origem = f" _(({passo['origem']}))_" if passo.get("origem") else ""
                L.append(f"- {passo.get('passo')}{dono}{prazo}{origem}")
    else:
        L.append("_Sem próximos passos registrados para o período._")
    L.append("")

    # ------------------------------------------------------- metodologia
    L.append("## Fontes e o que não foi medido")
    L.append("")
    L.append("Faturamento lê data de fechamento no CRM. Safra e eficiência leem data de criação. "
             "Recompra é o funil de recorrência, não o campo do CRM.")
    L.append("")
    if c.get("avisos"):
        for aviso in c["avisos"]:
            L.append(f"- {aviso}")
    else:
        L.append("- Sem lacunas de medição no período.")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Renderiza o check-in ROPRE em markdown")
    ap.add_argument("--checkin", required=True)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    with open(a.checkin, encoding="utf-8") as f:
        checkin = json.load(f)
    texto = montar(checkin)
    with open(a.saida, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"{a.saida}: {len(texto.splitlines())} linhas.")


if __name__ == "__main__":
    main()
