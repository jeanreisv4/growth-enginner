# -*- coding: utf-8 -*-
"""Monta as seções de CRM (recompra e reativação da base) da aba Metodologia, para o --metodologia-extra do gerador.

  python3 scripts/metodologia_crm.py --crm crm.json --comissao 0.14 --margem 0.20 --custo-crm 3000 --out metodologia_crm.json

Usa os benchmarks verificados de referencias/crm_turismo_benchmarks.json (tabela Premissa | Fonte | Benchmark | Período | Taxa |
Justificativa, benchmarks descartados e fontes com link, que vão para o fim da aba). O texto da análise sai do crm.json do cliente:
base usada, ticket, cadência, quanto cada contato rende e que base pagaria o custo do CRM.
"""
import argparse, json, os

AQUI = os.path.dirname(os.path.abspath(__file__))


def br(x, d=0):
    return f"{x:,.{d}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crm", required=True)
    ap.add_argument("--comissao", type=float, required=True)
    ap.add_argument("--margem", type=float, required=True)
    ap.add_argument("--custo-crm", type=float, default=0.0, help="quanto o CRM acrescenta ao custo por mês (ex.: aumento do fee)")
    ap.add_argument("--benchmarks", default=os.path.join(AQUI, "..", "referencias", "crm_turismo_benchmarks.json"))
    ap.add_argument("--out", default="metodologia_crm.json")
    a = ap.parse_args()
    crm = json.load(open(a.crm, encoding="utf-8")); bm = json.load(open(a.benchmarks, encoding="utf-8"))
    tx, b, tk = crm["taxas"], crm["base"], float(crm["ticket"])
    mg = a.comissao * a.margem
    val = {"ativo": tx["recompra"] * tk * mg, "recente": tx["cross_sell"] * tx["campanhas_cross_sell"] * tk * mg,
           "inativo": tx["reativacao"] * tx["campanhas_reativacao"] * tk * mg, "lead": tx["email"] * tx["emails"] * tk * mg}
    vazios = [n for k, n in (("recentes", "clientes com menos de 6 meses"), ("ativos", "clientes de 6 a 12 meses"),
                             ("inativos", "inativos"), ("recorrentes", "recorrentes")) if b.get(k) in (None, 0)]
    analise = [
        f"O CRM entra no Mês {crm['inicio']} da projeção" + (f", com custo de R$ {br(a.custo_crm)} por mês." if a.custo_crm else ".")
        + " A projeção separa três origens de faturamento: [1] novos leads (mídia e SEO, pelo funil), [2] recompra da base (WhatsApp para clientes "
          "de 6 a 12 meses e cross-sell/novas viagens para clientes com menos de 6 meses) e [3] reativação (e-mail para leads que não compraram e "
          "campanhas para clientes inativos há mais de 12 meses).",
        "Cada frente atua sobre um grupo diferente da base, para a mesma venda não ser contada duas vezes. Os clientes envelhecem por coorte de compra: "
        "com menos de 6 meses recebem cross-sell, de 6 a 12 meses entram na recompra e, passados 12 meses, viram inativos.",
        crm.get("nota_base") or f"Base inicial: {br(b.get('leads_sem_compra') or 0)} leads sem compra.",
        (f"Campos da base histórica não informados ({', '.join(vazios)}): estão em branco nas premissas e podem ser preenchidos; a projeção recalcula sozinha."
         if vazios else "Base histórica informada pelo cliente."),
        f"A base de leads cresce todo mês com os leads novos que não compraram e perde {br(tx.get('descadastro', 0) * 100, 2)}% por e-mail enviado, por descadastro.",
        f"Ticket da recompra e da reativação: R$ {br(tk)}. O faturamento do CRM passa pela mesma comissão e margem da operação "
        f"({br(a.comissao * 100, 1)}% × {br(a.margem * 100, 1)}% = {br(mg * 100, 2)}% do valor vendido).",
        f"Quanto cada contato rende por mês, nessas taxas: cliente de 6 a 12 meses R$ {br(val['ativo'], 2)}; cliente com menos de 6 meses R$ {br(val['recente'], 2)}; "
        f"inativo R$ {br(val['inativo'], 2)}; lead sem compra R$ {br(val['lead'], 2)}."
        + (f" Para o CRM pagar sozinho os R$ {br(a.custo_crm)} por mês, seriam cerca de {br(a.custo_crm / val['ativo'])} clientes de 6 a 12 meses, "
           f"ou {br(a.custo_crm / val['inativo'])} inativos, ou {br(a.custo_crm / val['lead'])} leads na base." if a.custo_crm else ""),
        "Simplificações: as vendas do CRM caem no mês da campanha (sem lag); os clientes históricos informados nas premissas não envelhecem ao longo do "
        "horizonte; quem recompra não muda de grupo; leads que compram pelo e-mail passam a ser clientes novos.",
    ]
    linhas = [list(l) for l in bm["linhas"]] + [["Ticket da recompra e da reativação", "Informado pela operação", "—", "—", f"R$ {br(tk)}",
                                                  "Definido pela operação; a recompra costuma ser outro produto."]]
    out = {"secoes": [["RECOMPRA E REATIVAÇÃO DA BASE (CRM MARKETING)", analise],
                      ["PREMISSAS DE RECOMPRA E REATIVAÇÃO · FONTE E JUSTIFICATIVA",
                       {"colunas": bm["colunas"], "spans": bm["spans"], "linhas": linhas, "nota": bm["nota_tabela"]}],
                      ["BENCHMARKS PESQUISADOS E NÃO USADOS", bm["descartados"]]],
           "fim": [["FONTES · RECOMPRA E REATIVAÇÃO (PUBLICAÇÃO · DADO UTILIZADO · ANO · LINK)",
                    [{"texto": f["texto"] + " · " + f["link"], "link": f["link"]} for f in bm["fontes"]]]]}
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{a.out}: {len(linhas)} premissas, {len(bm['fontes'])} fontes")


if __name__ == "__main__":
    main()
