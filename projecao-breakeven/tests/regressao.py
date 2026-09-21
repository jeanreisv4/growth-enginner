# -*- coding: utf-8 -*-
"""Regressão da skill: roda piloto + gerador nos dados sintéticos e confere as regras que o usuário exigiu.

  python3 tests/regressao.py

Casos: inside sales, e-commerce sem GA4 e e-commerce com GA4 (Google e Meta separados), mais a planilha demo.
Confere em cada planilha, recalculando as fórmulas com pycel:
  1. nenhuma fórmula com erro;
  2. nenhuma célula azul;
  3. a receita projetada no template é a mesma do piloto, mês a mês (o template não pode inflar nem perder receita);
  4. nenhuma taxa de etapa passa de 100% (connect, CTR, cliques → sessões, sessão → view item...);
  5. o número de meses é o horizonte pedido.
Precisa de pandas, openpyxl e pycel (python3 -m pip install --user pandas openpyxl pycel).
"""
import json, os, subprocess, sys, tempfile, warnings
warnings.filterwarnings("ignore")
import openpyxl
from pycel import ExcelCompiler

SKILL = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIX = os.path.join(SKILL, "tests", "fixtures")
PILOTO = os.path.join(SKILL, "scripts", "breakeven_pilot.py")
GERADOR = os.path.join(SKILL, "scripts", "gerar_template.py")
AZUL = {"FF0000FF", "000000FF", "FF4472C4", "4472C4", "FF1F4E79", "FF2E75B6", "FF5B9BD5", "FF0070C0"}
HORIZONTE = 4
CASOS = [
    dict(nome="inside_sales", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="FATURAMENTO (VENDAS × TICKET)", extra_piloto=[], extra_gerador=[], exige=["LEADS CONECTADOS", "MQL CONECTADOS"]),
    dict(nome="inside_sales_irrealista", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="FATURAMENTO (VENDAS × TICKET)", fee="40000", extra_piloto=["--fixar", "clique_lead=0.05"], extra_gerador=[],
         metodologia=["CAMINHO PARA O BREAKEVEN"], sem=["VISITAS LP", "CONNECT RATE"], exige=["LEADS CONECTADOS", "MQL CONECTADOS"]),
    dict(nome="inside_sales_conexao_so_lead", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="FATURAMENTO (VENDAS × TICKET)", extra_piloto=[], extra_gerador=["--conexao-so-lead"],
         exige=["LEADS CONECTADOS", "MQL CONECTADOS", "MQL → SQL"], sem=["COMISSÃO SOBRE O GMV", "RECEITA DA AGÊNCIA (GMV × COMISSÃO)"]),
    dict(nome="inside_sales_mercado", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="FATURAMENTO (VENDAS × TICKET)", extra_piloto=["--alvo", "conexao=0.9", "--alvo", "sql_venda=0.5", "--verba-plano", "5000,6000,7000,8000"],
         extra_gerador=["--conexao-so-lead"], exige=["CONEXÃO LEAD", "LEADS CONECTADOS"]),
    dict(nome="inside_sales_sazonalidade", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="FATURAMENTO (VENDAS × TICKET)", extra_piloto=["--sazonalidade-demanda", "1,1,1.3", "--sazonalidade-cpm", "1,1,1.2", "--cpm-crescimento", "0.04", "--cpm-crescimento-ate", "3"], extra_gerador=[],
         metodologia=["CPM MÊS A MÊS", "SAZONALIDADE DA DEMANDA MÊS A MÊS"], exige=["CPM", "SQL → VENDA", "ROAS (FATURAMENTO ÷ MÍDIA)", "RETORNO DOS ANÚNCIOS APÓS A MARGEM (MC − MÍDIA)"],
         sem=["MULTIPLICADOR DO CPM (ELEIÇÃO, DATAS, REMARKETING)", "CPM EFETIVO (BASE × MULTIPLICADOR)", "SAZONALIDADE DA DEMANDA (× VENDAS)"]),
    dict(nome="inside_sales_extra", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="FATURAMENTO (VENDAS × TICKET)", extra_piloto=[], extra_gerador=["--extra", "premissas_inside_sales_extra.json|Cenário B|Cenário alternativo"],
         abas=["Cenário B", "Premissas · Cenário B"]),
    dict(nome="inside_sales_seo", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="FATURAMENTO (VENDAS × TICKET)", extra_piloto=["--organico-visitas", "0,500,1000,2000", "--organico-conversao", "0.05"], extra_gerador=[],
         exige=["VISITAS ORGÂNICAS (SEO)", "LEADS ORGÂNICOS (SEO)", "LEADS TOTAIS (PAGOS + ORGÂNICOS)", "LEADS CONECTADOS"]),
    dict(nome="inside_sales_crm", modelo="inside_sales", csv="indicadores_inside_sales.csv", aba="Inside Sales",
         receita="[1] GMV · NOVOS LEADS (VENDAS × TICKET)",
         extra_piloto=["--crm", os.path.join(FIX, "crm_inside_sales.json"), "--fee-plano", "1200,4200", "--organico-visitas", "0,500,1000,2000", "--organico-conversao", "0.05"],
         extra_gerador=[], series={"[2] GMV · RECOMPRA DA BASE (WHATSAPP + CROSS-SELL)": "receita_recompra",
                                   "[3] GMV · REATIVAÇÃO (E-MAIL PARA LEADS + INATIVOS)": "receita_reativacao"},
         exige=["LEADS SEM COMPRA NA BASE (INÍCIO DO MÊS)", "GMV TOTAL (NOVOS + RECOMPRA + REATIVAÇÃO)"]),
    dict(nome="ecommerce", modelo="ecommerce", csv="indicadores_ecommerce.csv", aba="E-commerce",
         receita="[R$] RECEITA ATRIBUÍDA À MÍDIA V4", extra_piloto=[], extra_gerador=["--sem-etapa-venda"]),
    dict(nome="ecommerce_ga4", modelo="ecommerce", csv="indicadores_ecommerce.csv", aba="E-commerce",
         receita="[R$] RECEITA ATRIBUÍDA À MÍDIA V4", extra_piloto=["--ga4", os.path.join(FIX, "ga4_ecommerce.json")],
         extra_gerador=["--sem-etapa-venda"], exige=["[R$] VERBA GOOGLE", "[R$] VERBA META", "[QNTD] SESSÕES - NÃO PAGAS"]),
]


def rodar(cmd, cwd):
    r = subprocess.run([sys.executable] + cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"falhou: {' '.join(cmd[:2])}\n{r.stderr[-1500:]}")
    return r.stdout


def conferir_planilha(path, aba, rot_receita=None, projecao=None, exige=(), metodologia=(), sem=(), series=None):
    wb = openpyxl.load_workbook(path); exc = ExcelCompiler(filename=path); falhas = []
    for nome in wb.sheetnames:
        ws = wb[nome]
        for row in ws.iter_rows():
            for c in row:
                if c.fill is not None and c.fill.fgColor is not None and str(c.fill.fgColor.rgb) in AZUL:
                    falhas.append(f"{nome}!{c.coordinate}: célula azul")
                if isinstance(c.value, str) and c.value.startswith("="):
                    try:
                        v = exc.evaluate(f"'{nome}'!{c.coordinate}")
                    except Exception as e:
                        falhas.append(f"{nome}!{c.coordinate}: {type(e).__name__}"); continue
                    if isinstance(v, str) and v.startswith("#"):
                        falhas.append(f"{nome}!{c.coordinate}: {v}")
    ws = wb[aba]
    linhas = {ws.cell(r, 2).value.strip(): r for r in range(1, ws.max_row + 1) if isinstance(ws.cell(r, 2).value, str)}
    cabec = next(r for r in range(1, ws.max_row + 1) if ws.cell(r, 3).value == "Projetado" or ws.cell(r, 4).value == "Realizado")
    def e_total(c):  # o par de totais também tem cabeçalho Projetado | Realizado
        acima = ws.cell(cabec - 1, c).value
        if acima is None:  # cabeçalho mesclado: o texto fica na célula à esquerda
            acima = ws.cell(cabec - 1, c - 1).value
        return isinstance(acima, str) and "TOTAL" in acima.upper()
    cols = [ws.cell(cabec, c).column_letter for c in range(3, ws.max_column + 1)
            if ws.cell(cabec, c).value == "Projetado" and not e_total(c)]
    for rot in exige:
        if rot not in linhas: falhas.append(f"linha ausente: {rot}")
    for rot in sem:
        if rot in linhas: falhas.append(f"linha que não devia aparecer: {rot}")
    if metodologia:
        met = next((wb[n] for n in wb.sheetnames if n.startswith("Premissas")), None)
        textos = {c.value for row in met.iter_rows() for c in row if isinstance(c.value, str)} if met else set()
        for t in metodologia:
            if not any(x.startswith(t) for x in textos): falhas.append(f"Premissas sem a seção {t}")
    for rot, r in linhas.items():
        if r <= cabec: continue  # só a tabela de projeção; o topo tem blocos de premissas lado a lado
        up = rot.upper()
        if "→" in rot or "CONNECT" in up or "CTR" in up:
            for c in range(3, 3 + 2 * len(cols)):
                v = exc.evaluate(f"'{aba}'!{ws.cell(r, c).coordinate}")
                if isinstance(v, (int, float)) and v > 1.0001:
                    falhas.append(f"{rot} = {v:.1%} em {ws.cell(r, c).coordinate}: taxa acima de 100%")
    for rot, chave in (series or {}).items():   # outras linhas que precisam bater com o piloto (ex.: GMV do CRM)
        r = linhas.get(rot)
        if r is None:
            falhas.append(f"linha ausente: {rot}"); continue
        for k, (col, lin) in enumerate(zip(cols, projecao or [])):
            v = exc.evaluate(f"'{aba}'!{col}{r}") or 0
            if abs(v - lin.get(chave, 0)) > max(1.0, 0.005 * abs(lin.get(chave, 0))):
                falhas.append(f"M{k + 1}: {rot[:30]} do template {v:,.2f} ≠ piloto {lin.get(chave, 0):,.2f}")
    if projecao is not None:
        if len(cols) != len(projecao):
            falhas.append(f"template tem {len(cols)} meses, piloto tem {len(projecao)}")
        r = linhas.get(rot_receita)
        if r is None:
            falhas.append(f"linha de receita não encontrada: {rot_receita}")
        else:
            for k, (col, lin) in enumerate(zip(cols, projecao)):
                v = exc.evaluate(f"'{aba}'!{col}{r}") or 0
                if abs(v - lin["receita"]) > max(1.0, 0.005 * abs(lin["receita"])):
                    falhas.append(f"M{k + 1}: receita do template R$ {v:,.2f} ≠ piloto R$ {lin['receita']:,.2f}")
    return falhas


def main():
    tmp = tempfile.mkdtemp(prefix="regressao_breakeven_")
    total = 0
    for caso in CASOS:
        prem = os.path.join(tmp, f"premissas_{caso['nome']}.json"); xlsx = os.path.join(tmp, f"{caso['nome']}.xlsx")
        try:
            rodar([PILOTO, "projetar", "--fonte", os.path.join(FIX, caso["csv"]), "--aba", "Indicadores", "--modelo", caso["modelo"],
                   "--fee", caso.get("fee", "1200"), "--midia", "5000", "--margem", "0.3", "--comissao", "1", "--mes-alvo", "3",
                   "--horizonte", str(HORIZONTE), "--crescimento-midia", "0.05", "--out", prem] + caso["extra_piloto"], tmp)
            rodar([GERADOR, "--premissas", prem, "--modelo", caso["modelo"], "--cliente", "Teste", "--out", xlsx] + caso["extra_gerador"], tmp)
            d = json.load(open(prem, encoding="utf-8"))
            falhas = conferir_planilha(xlsx, caso["aba"], caso["receita"], d["projecao"], caso.get("exige", ()), caso.get("metodologia", ()), caso.get("sem", ()), caso.get("series"))
            if caso.get("abas"):   # cenário extra em outra aba do mesmo arquivo
                nomes = openpyxl.load_workbook(xlsx).sheetnames
                falhas += [f"aba ausente: {a}" for a in caso["abas"] if a not in nomes]
                if "Cenário B" in nomes: falhas += conferir_planilha(xlsx, "Cenário B", caso["receita"], d["projecao"])
        except RuntimeError as e:
            falhas = [str(e)]
        total += len(falhas)
        print(f"{'OK   ' if not falhas else 'FALHA'} {caso['nome']}" + "".join(f"\n      - {f}" for f in falhas[:12]))
    demo = os.path.join(tmp, "demo.xlsx")
    try:
        rodar([os.path.join(SKILL, "gerador", "build_workbook.py"), demo], tmp)
        falhas = conferir_planilha(demo, "E-commerce") + conferir_planilha(demo, "Inside Sales")
    except RuntimeError as e:
        falhas = [str(e)]
    total += len(falhas)
    print(f"{'OK   ' if not falhas else 'FALHA'} demo" + "".join(f"\n      - {f}" for f in falhas[:12]))
    print(f"\n{'Tudo certo.' if not total else f'{total} falha(s).'}  Arquivos em {tmp}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
