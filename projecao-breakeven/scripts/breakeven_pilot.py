#!/usr/bin/env python3
"""
breakeven_pilot.py — piloto da skill de projeção de breakeven (V4).

Dois modos:
  detectar  lê a fonte da verdade (aba "Indicadores" da planilha padrão V4) e devolve
            o que encontrou: meses fechados, fee, mídia planejada, margem, taxas efetivas.
            A skill usa esse JSON para CONFIRMAR com o usuário antes de projetar.
  projetar  recebe as premissas confirmadas (fee, mídia, margem, comissão, mês-alvo,
            modelo) e devolve o veredito de realismo + o JSON que alimenta os templates
            (inside_sales ou ecommerce) já construídos.

Exemplos:
  python breakeven_pilot.py detectar --fonte indicadores.xlsx --aba Indicadores --modelo inside_sales
  python breakeven_pilot.py projetar --fonte indicadores.xlsx --aba Indicadores --modelo inside_sales \
      --fee 1200 --midia 5000 --margem 0.30 --mes-alvo 5 --horizonte 12 --out premissas.json

A fonte pode ser .xlsx, .csv ou uma URL de Google Sheets (usa export CSV do gid).
"""
import argparse, json, math, re, sys, unicodedata
from datetime import date

import pandas as pd

# ----------------------------------------------------------------------------- modelos
# Cadeia de etapas por modelo. Cada etapa é o rótulo da linha na planilha padrão V4.
# A primeira etapa é sempre o investimento; a última é o volume que gera receita.
MODELOS = {
    "inside_sales": {
        "etapas": ["Investimento", "Impressões", "Cliques", "Visitas", "Leads", "Conexões", "MQLs", "SQLs", "Vendas"],
        "opcionais": ["Visitas", "Conexões"],  # se a fonte não tiver a linha, a etapa sai da cadeia (nada é inventado)
        "receita": "Faturamento V4",
        "ticket": "Ticket Médio",
    },
    "ecommerce": {
        "etapas": ["Investimento", "Impressões", "Cliques", "Sessões", "Add to Cart", "Check Out", "Transações Captada"],
        "opcionais": [],
        "receita": "Receita Captada",
        "ticket": "Ticket Médio",
    },
}
# Rótulos alternativos encontrados na planilha padrão V4 (bloco "Indicadores V4"); o primeiro que existir na aba é usado.
SINONIMOS = {
    "MQLs": ["MQLs", "MQLs (manual)", "MQL (manual)"],
    "SQLs": ["SQLs", "SQLs (manual)", "SQL (manual)"],
    "Vendas": ["Vendas", "Vendas (manual)"],
    "Faturamento V4": ["Faturamento V4", "Faturamento V4 (manual)", "Valor de venda (manual)", "Total de Faturamento (manual)"],
    "Receita Captada": ["Receita Captada V4", "Receita Captada", "Receita Captada (manual)", "Receita Captada  (captado)"],
    "Sessões": ["Sessões", "Sessões Tráfego V4", "Sessões - Pago", "Sessões Pagas"],
    "Transações Captada": ["Transações Captada", "Vendas Captados V4", "Transações", "Pedidos (captado)", "Purchase"],
    "Check Out": ["Check Out", "Initiate Checkout", "Checkout"],
    "Conexões": ["Conexões", "Conexões (manual)"],
    # visitas na landing page (connect rate = visitas ÷ cliques); sem essa linha o funil vai do clique direto ao lead.
    # Só rótulos inequívocos de LP: "Sessões*" é do bloco GA4 e conta o site inteiro, o que capturaria a linha errada.
    "Visitas": ["Visitas", "Visitas LP", "Visitas na LP", "Visitas na Página de Destino",
                "Visualizações da Página de Destino", "Visualizações da página de destino"],
    "Sessões Orgânicas": ["Sessões Orgânicas", "Sessões Organicas", "Sessões - Orgânico"],
    "Sessões Gerais": ["Sessões Gerais", "Sessões Totais"],
}
LINHAS_FIXAS = {"fee": "Fee V4", "midia_plano": "Plano de Mídia Mês", "margem": "Gross Margin"}
EXTRAS = {  # lidas da fonte só para informação/premissa; não fazem parte da cadeia de conversão
    "inside_sales": [],
    "ecommerce": ["Sessões Orgânicas", "Sessões Gerais"],
}
MESES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
            "agosto", "setembro", "outubro", "novembro", "dezembro"]
MESES_NORM = [unicodedata.normalize("NFKD", m).encode("ascii", "ignore").decode() for m in MESES_PT]  # "marco" casa com "março" normalizado
MIN_EVENTOS = 30  # abaixo disso a taxa da etapa é sinalizada como amostra pequena
RAMPA_ATE = None    # mês em que a rampa chega ao alvo (--rampa-ate); sem isso, o mês-alvo
REALIZADO = {}      # {mês da projeção: resultado realizado}: meses já vividos entram pelo realizado, como na linha consolidada da planilha
ORGANICO = None     # {'visitas': [por mês a partir do M1], 'conversao': taxa, 'origem': str, 'metrica': str}:
                    # leads orgânicos (SEO, social, indicação) somados aos pagos antes de lead → MQL
CRM = None          # recompra e reativação da base (inside sales); ver crm_json no --help
VOL_REAL = {}       # {mês da projeção: {"Leads", "Vendas"}} realizados, para a base do CRM andar com o que aconteceu
FEE_PLANO = None    # fee mês a mês (--fee-plano); ex.: fee sobe quando entra o CRM
CPM_CRESC = None    # (crescimento mensal, teto, último mês): o CPM base sobe com a saturação do público enquanto a verba escala (premissa do usuário, sem benchmark)
SAZ = None          # {'demanda': [...], 'cpm': [...]} multiplicadores mês a mês (Black Friday, Natal); depois da lista, 1
VERBA_PLANO = None  # verba mês a mês (--verba-plano); depois do último mês do plano, repete o último valor
TAXA_MAX = 1.0    # taxa de etapa não pode passar de 100%: quando a fonte dá mais, o denominador está subcontado


# ----------------------------------------------------------------------------- utilidades
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def num(v):
    """Converte 'R$ 4.576,23', '$1.200,00', '20,91%', '-' em float (percentual vira fração)."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ("", "-", "—", "#DIV/0!", "#VALUE!", "#REF!"):
        return None
    pct = s.endswith("%")
    s = re.sub(r"[R$\s%]", "", s).replace(".", "").replace(",", ".")
    try:
        x = float(s)
    except ValueError:
        return None
    return x / 100 if pct else x


def carregar(fonte, aba):
    if fonte.startswith("http") and "docs.google.com" in fonte:
        m = re.search(r"/d/([\w-]+)", fonte)
        gid = re.search(r"gid=(\d+)", fonte)
        url = f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"
        if gid:
            url += f"&gid={gid.group(1)}"
        return pd.read_csv(url, header=None, dtype=str)
    if fonte.lower().endswith(".csv"):
        return pd.read_csv(fonte, header=None, dtype=str)
    return pd.read_excel(fonte, sheet_name=aba, header=None, dtype=str)


def achar_linha(df, rotulo, apos=None):
    """Primeira linha cujo rótulo (3 primeiras colunas) bate com `rotulo`; com `apos`, só procura depois da linha com esse rótulo de seção."""
    alvo = norm(rotulo)
    inicio = 0
    if apos is not None:
        a = achar_linha(df, apos)
        if a is None:
            return None
        inicio = a + 1
    for i, row in df.iloc[inicio:].iterrows():
        for v in row.values[:3]:  # rótulo costuma estar nas primeiras colunas
            if v is not None and norm(v) == alvo:
                return i
    return None


def colunas_de_mes(df):
    """Localiza a linha 'Mês' e devolve [(col, 'abril', ano)] para cada coluna com nome de mês.
    O ano vem da linha 'Data Inicial' (dd/mm/aaaa) quando existir; senão da linha 'Ano'."""
    i = achar_linha(df, "Mês")
    if i is None:
        sys.exit("Não achei a linha 'Mês' na aba. Confira a aba (--aba) ou a fonte.")
    ano_row = achar_linha(df, "Ano")
    data_row = achar_linha(df, "Data Inicial")
    cols = []
    for c in range(df.shape[1]):
        v = df.iat[i, c]
        if v is not None and norm(v) in MESES_NORM:
            ano = None
            if data_row is not None:
                m = re.search(r"\d{2}/\d{2}/(\d{4})", str(df.iat[data_row, c]))
                if m:
                    ano = int(m.group(1))
            if ano is None and ano_row is not None:
                a = num(df.iat[ano_row, c])
                ano = int(a) if a else None
            cols.append((c, norm(v), ano))
    return cols


def serie(df, rotulo, cols):
    for alt in SINONIMOS.get(rotulo, [rotulo]):
        i = achar_linha(df, alt)
        if i is not None:
            return [num(df.iat[i, c]) for c, _, _ in cols]
    return None


# ----------------------------------------------------------------------------- leitura
def ler_historico(df, modelo, ga4=None):
    cfg = MODELOS[modelo]
    cols = colunas_de_mes(df)
    hoje = date.today()
    dados = {}
    cfg.setdefault("etapas_todas", list(cfg["etapas"]))   # cadeia completa; "etapas" é o que sobra depois das opcionais ausentes
    cfg["etapas"] = list(cfg["etapas_todas"])
    for rot in cfg["etapas"] + [cfg["receita"], cfg["ticket"]] + list(LINHAS_FIXAS.values()) + EXTRAS.get(modelo, []):
        s = serie(df, rot, cols)
        if s is not None:
            dados[rot] = s
    if ga4 and modelo == "ecommerce":
        aplicar_ga4(dados, cols, ga4, cfg)
    # etapa opcional sem nenhum valor é ausente: a linha homônima de outro bloco (Meta, Google) pode existir vazia
    # (turismo: sem "Conexões" na aba principal, o piloto achava a do bloco Meta, vazia, e zerava lead → MQL)
    for e in cfg.get("opcionais", []):
        if e in dados and not any((v or 0) > 0 for v in dados[e]):
            del dados[e]
    faltando = [e for e in cfg["etapas"] if e not in dados]
    ausentes_ok = [e for e in faltando if e in cfg.get("opcionais", [])]
    faltando = [e for e in faltando if e not in ausentes_ok]
    if faltando and not (modelo == "ecommerce" and set(faltando) <= {"Add to Cart", "Check Out"}):
        sys.exit(f"Linhas ausentes na aba para o modelo {modelo}: {faltando}")
    cfg["etapas"] = [e for e in cfg["etapas_todas"] if e not in ausentes_ok]
    cfg["etapas_ausentes"] = ausentes_ok

    # E-commerce: carrinho e checkout pagos raramente existem na fonte; quando as linhas diretas não têm dado e o bloco GA4 (site inteiro)
    # existe, estimamos: carrinho pago = sessões pagas × (Add To Cart ÷ Sessões Gerais do GA4); checkout pago = carrinho pago × (Initiate Checkout ÷ Add To Cart do GA4).
    cfg["etapas_estimadas"] = []
    cfg.setdefault("split_meta", False)
    if modelo == "ecommerce":
        bloco = {r: None for r in ("Sessões Gerais", "Add To Cart", "Initiate Checkout")}
        for r in bloco:
            i = achar_linha(df, r, apos="GA4")
            bloco[r] = [num(df.iat[i, c]) for c, _, _ in cols] if i is not None else None
        def vazio(rot): return rot not in dados or not any((v or 0) > 0 for v in dados[rot])
        if all(bloco.values()) and "Sessões" in dados and (vazio("Add to Cart") or vazio("Check Out")) and not cfg.get("split_meta"):
            cart, chk = [], []
            for k in range(len(cols)):
                sg, ac, ic, sp = bloco["Sessões Gerais"][k] or 0, bloco["Add To Cart"][k] or 0, bloco["Initiate Checkout"][k] or 0, dados["Sessões"][k] or 0
                cart.append(sp * ac / sg if sg else None)
                chk.append((sp * ac / sg) * (ic / ac) if sg and ac else None)
            dados["Add to Cart"], dados["Check Out"] = cart, chk
            cfg["etapas_estimadas"] = ["Add to Cart", "Check Out"]
            faltando = [e for e in faltando if e not in ("Add to Cart", "Check Out")]
            if faltando:
                sys.exit(f"Linhas ausentes na aba para o modelo {modelo}: {faltando}")
    meses = []
    for k, (c, nome, ano) in enumerate(cols):
        inv = dados["Investimento"][k] or 0
        idx = MESES_NORM.index(nome) + 1
        corrente = (ano == hoje.year and idx == hoje.month) if ano else False
        futuro = (ano and (ano > hoje.year or (ano == hoje.year and idx > hoje.month))) or inv == 0
        status = "corrente" if corrente else ("futuro" if futuro else "fechado")
        meses.append({"col": c, "mes": nome, "ano": ano, "status": status,
                      **{rot: dados[rot][k] for rot in dados}})
    return meses, dados


def aplicar_ga4(dados, cols, ga4, cfg):
    """Sobrepõe a fonte com o GA4 nos meses cobertos (resumo do ga4_resumo.py). A fonte da V4 soma Google e Meta na verba,
    mas traz cliques e impressões só do Google; o GA4 separa as sessões pagas por plataforma e mede carrinho e checkout do pago.
    Verba Meta = verba da fonte − custo do Google Ads no GA4. Pedidos e receita continuam da fonte (atribuição das plataformas)."""
    por_mes = {norm(k).replace(" ", ""): v for k, v in (ga4.get("meses") or {}).items()}
    n = len(cols)
    for rot in ("Investimento Google", "Investimento Meta", "Sessões Google", "Sessões Meta"):
        dados.setdefault(rot, [None] * n)
    for rot in ("Sessões", "Cliques", "Impressões", "Add to Cart", "Check Out", "Sessões Orgânicas", "Sessões Gerais"):
        dados.setdefault(rot, [None] * n)
    cobertos, alertas = [], []
    for k, (_, nome, ano) in enumerate(cols):
        g = por_mes.get(f"{nome}/{ano}")
        if not g:
            continue
        inv = dados["Investimento"][k] or 0
        meta_ses = (g.get("sessoes_meta") or 0) + (g.get("sessoes_outros_pagos") or 0)
        dados["Investimento Google"][k] = g["google_investimento"]
        dados["Investimento Meta"][k] = max(inv - g["google_investimento"], 0.0)
        dados["Impressões"][k] = g["google_impressoes"]
        dados["Cliques"][k] = g["google_cliques"]
        dados["Sessões Google"][k] = g["sessoes_google"]
        dados["Sessões Meta"][k] = meta_ses
        dados["Sessões"][k] = g["sessoes_google"] + meta_ses
        dados["Add to Cart"][k] = g["carrinho_pago"]
        dados["Check Out"][k] = g["checkout_pago"]
        dados["Sessões Orgânicas"][k] = g["sessoes_nao_pagas"]
        dados["Sessões Gerais"][k] = g["sessoes_total"]
        cobertos.append(f"{nome}/{ano}")
        if g.get("alerta"): alertas.append(f"{nome}/{ano}: {g['alerta']} (somado ao Meta)")
        if inv < g["google_investimento"]:
            alertas.append(f"{nome}/{ano}: o custo do Google Ads no GA4 (R$ {g['google_investimento']:,.2f}) passa a verba da fonte (R$ {inv:,.2f}); verba Meta zerada.")
    cfg["ga4"] = {"propriedade": ga4.get("propriedade"), "extraido_em": ga4.get("extraido_em"), "meses": cobertos, "alertas": alertas}
    cfg["split_meta"] = bool(cobertos)


def split(modelo):
    """Verdadeiro quando o GA4 separou Google e Meta: o funil do Google vai até as sessões e o Meta entra por custo por sessão."""
    return modelo == "ecommerce" and bool(MODELOS[modelo].get("split_meta"))


def inv_cpm(m, modelo):
    """Verba que compra as impressões da fonte: com split, só a do Google (impressões e cliques da fonte são do Google)."""
    return (m.get("Investimento Google") if split(modelo) else m.get("Investimento")) or 0


def janela_meses(meses, janela, incluir_corrente=False):
    """Meses da janela de taxas: últimos `janela` fechados e, se pedido explicitamente, o mês corrente (parcial) junto."""
    sel = [m for m in meses if m["status"] == "fechado"][-janela:]
    if incluir_corrente:
        sel += [m for m in meses if m["status"] == "corrente" and (m.get("Investimento") or 0) > 0]
    return sel


def taxas_efetivas(meses, modelo, janela, incluir_corrente=False):
    """Taxas ponderadas por volume na janela (meses fechados; mês corrente só se pedido). Devolve taxas, CPM, ticket, alertas."""
    cfg = MODELOS[modelo]
    fechados = janela_meses(meses, janela, incluir_corrente)
    if not fechados:
        sys.exit("Nenhum mês fechado com investimento na fonte.")
    et = cfg["etapas"]
    extra = ["Investimento Google", "Investimento Meta", "Sessões Google", "Sessões Meta"] if split(modelo) else []
    soma = {e: sum((m.get(e) or 0) for m in fechados) for e in et + extra}
    taxas, alertas = {}, []
    pares = ([("Impressões", "Cliques"), ("Cliques", "Sessões Google"), ("Sessões", "Add to Cart"), ("Add to Cart", "Check Out"),
              ("Check Out", "Transações Captada")] if split(modelo) else list(zip(et[1:-1], et[2:])))
    for a, b in pares:
        bruta = (soma[b] / soma[a]) if soma[a] else 0.0
        taxas[f"{a} → {b}"] = min(bruta, TAXA_MAX)
        if bruta > TAXA_MAX:
            alertas.append(f"{a} → {b}: a fonte dá {bruta:.0%} (mais {b.lower()} do que {a.lower()}), o que é impossível; "
                           f"a taxa foi travada em 100% e a diferença deve estar em outra origem (outro canal ou tráfego orgânico).")
        if soma[a] < MIN_EVENTOS or soma[b] < 10:
            alertas.append(f"{a} → {b}: {int(soma[a])} → {int(soma[b])} eventos na janela; "
                           f"taxa estatisticamente frágil, tratar como hipótese.")
    base_cpm = soma["Investimento Google"] if split(modelo) else soma["Investimento"]
    cpm = base_cpm / soma["Impressões"] * 1000 if soma["Impressões"] else None
    extras = {}
    if split(modelo):
        extras = {"custo_sessao_meta": (soma["Investimento Meta"] / soma["Sessões Meta"]) if soma["Sessões Meta"] else None,
                  "participacao_meta_na_verba": (soma["Investimento Meta"] / soma["Investimento"]) if soma["Investimento"] else 0.0}
        if soma["Sessões Meta"] < MIN_EVENTOS:
            alertas.append(f"Sessões Meta: {int(soma['Sessões Meta'])} na janela; custo por sessão frágil, tratar como hipótese.")
        alertas += (cfg.get("ga4") or {}).get("alertas", [])
    rec = sum((m.get(cfg["receita"]) or 0) for m in fechados)
    ticket = rec / soma[et[-1]] if soma[et[-1]] else None
    if ticket is None:
        alertas.append("Sem vendas na janela: ticket médio precisa ser informado manualmente.")
    return {"janela_meses": [f"{m['mes']}/{m['ano']}" + (" (parcial)" if m["status"] == "corrente" else "") for m in fechados], "cpm": cpm,
            "taxas": taxas, "ticket": ticket, "volumes_janela": soma, "alertas": alertas, **extras}


# ----------------------------------------------------------------------------- envelope histórico e rampa
MIN_DEN = 5  # meses com menos eventos no denominador não entram no "melhor mês"

def _guardar_visitas(meses, a):
    """Decide se a etapa Visitas entra na cadeia do inside sales. Ela só entra quando o connect rate é mensurável:
    a fonte tem a linha com dado em toda a janela e visitas ≤ cliques. Fora disso o funil volta a clique → lead,
    porque travar a taxa em 100% (ou em zero) encolheria o funil projetado sem que ninguém percebesse.
    Com --connect-rate e sem a linha na fonte, as visitas são sintetizadas (cliques × taxa) e marcadas como tal."""
    cfg, avisos = MODELOS["inside_sales"], []
    win = janela_meses(meses, a.janela, a.incluir_corrente)
    tem_linha = "Visitas" in cfg["etapas"]
    if tem_linha:
        cli = sum((m.get("Cliques") or 0) for m in win)
        vis = sum((m.get("Visitas") or 0) for m in win)
        furos = [f"{m['mes']}/{m['ano']}" for m in win if (m.get("Cliques") or 0) > 0 and not (m.get("Visitas") or 0) > 0]
        motivo = None
        if vis <= 0 or furos:
            motivo = (f"a linha de visitas está vazia em {', '.join(furos)}" if furos else "a linha de visitas está zerada na janela")
        elif vis > cli:
            motivo = (f"a fonte dá {vis / cli:.0%} de visitas sobre os cliques (mais visitas do que cliques), o que significa que a página "
                      f"também recebe tráfego de outra origem e o denominador não é comparável")
        if motivo:
            cfg["etapas"] = [e for e in cfg["etapas"] if e != "Visitas"]
            cfg["etapas_ausentes"] = sorted(set(cfg.get("etapas_ausentes", []) + ["Visitas"]))
            for m in meses:
                m.pop("Visitas", None)
            avisos.append(f"Connect rate não entra na projeção: {motivo}. O funil volta a clique → lead, medido direto na fonte; "
                          f"informe a taxa com --connect-rate se quiser a etapa de visitas.")
            tem_linha = False
    if a.connect_rate is not None and not tem_linha:
        # tem landing page, mas a fonte não traz a linha utilizável: o connect rate informado cria a etapa
        # (visitas = cliques × taxa) e a conversão da página passa a ser leads ÷ visitas, não leads ÷ cliques
        for m in meses:
            m["Visitas"] = (m.get("Cliques") or 0) * a.connect_rate
        cfg["etapas"] = [e for e in cfg["etapas_todas"] if e not in [x for x in cfg.get("etapas_ausentes", []) if x != "Visitas"]]
        cfg["etapas_ausentes"] = [e for e in cfg.get("etapas_ausentes", []) if e != "Visitas"]
        cfg["visitas_sinteticas"] = True
        avisos.append(f"Connect rate de {a.connect_rate:.0%} informado manualmente: a fonte não tem a linha de visitas da página. "
                      f"As visitas do histórico são calculadas (cliques × taxa), não medidas, e a conversão da página é medida sobre elas.")
    elif a.connect_rate is not None and tem_linha:
        sys.exit("--connect-rate: a fonte já tem a linha de visitas, então o connect rate é medido, não informado. "
                 "Para sobrescrever a taxa medida use --fixar connect=VALOR.")
    return avisos


def alavancas(modelo):
    """Alavancas da rampa, na ordem da cadeia: (chave, rótulo, numerador, denominador). CPM e ticket têm tratamento próprio."""
    if modelo == "inside_sales":
        # com a linha de visitas na fonte (ou com --connect-rate), o clique vira visita e a visita vira lead;
        # sem ela, o elo é o clique → lead de sempre, sem inventar connect rate
        if "Visitas" in MODELOS["inside_sales"]["etapas"]:
            meio = [("connect", "Cliques → Visitas (connect rate)", "Visitas", "Cliques"), ("visita_lead", "Visitas → Leads", "Leads", "Visitas")]
        else:
            meio = [("clique_lead", "Cliques → Leads", "Leads", "Cliques")]
        # Quem vira oportunidade é quem o time conectou, tenha sido marcado MQL ou não: a linha Conexões é a etapa real.
        # O MQL é qualificação de marketing (critério do formulário) e fica fora da multiplicação, como informativa.
        # Sem a linha Conexões na fonte não há como medir conexão: o funil volta a lead → MQL → SQL.
        if "Conexões" in MODELOS["inside_sales"]["etapas"]:
            fim = [("conexao", "Leads → Conexões (lead ou MQL)", "Conexões", "Leads"),
                   ("conexao_sql", "Conexões → SQLs", "SQLs", "Conexões")]
        else:
            fim = [("lead_mql", "Leads → MQLs", "MQLs", "Leads"), ("mql_sql", "MQLs → SQLs", "SQLs", "MQLs")]
        return [("ctr", "Impressões → Cliques", "Cliques", "Impressões")] + meio + fim + [("sql_venda", "SQLs → Vendas", "Vendas", "SQLs")]
    if split(modelo):
        return [("ctr", "Impressões → Cliques (Google)", "Cliques", "Impressões"), ("clique_sessao", "Cliques → Sessões Google (connect)", "Sessões Google", "Cliques"),
                ("sessao_cart", "Sessões pagas → Add to Cart", "Add to Cart", "Sessões"), ("cart_checkout", "Add to Cart → Check Out", "Check Out", "Add to Cart"),
                ("checkout_trans", "Check Out → Transações Captada", "Transações Captada", "Check Out")]
    return [("ctr", "Impressões → Cliques", "Cliques", "Impressões"), ("clique_sessao", "Cliques → Sessões", "Sessões", "Cliques"),
            ("sessao_cart", "Sessões → Add to Cart", "Add to Cart", "Sessões"), ("cart_checkout", "Add to Cart → Check Out", "Check Out", "Add to Cart"),
            ("checkout_trans", "Check Out → Transações Captada", "Transações Captada", "Check Out")]


def informativas(modelo):
    """Taxas medidas e mostradas na planilha, mas fora da multiplicação do funil (não geram volume)."""
    if modelo == "inside_sales" and "Conexões" in MODELOS["inside_sales"]["etapas"]:
        return [("lead_mql", "Leads → MQLs (qualidade do lead)", "MQLs", "Leads")]
    return []


def todas_alavancas(modelo):
    return alavancas(modelo) + informativas(modelo)


def _mediana(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _rot(m): return f"{m['mes']}/{m['ano']}"

def _rs(v):
    """R$ no padrão brasileiro, para os textos que o cliente lê na aba Premissas."""
    return "R$ " + f"{v:,.0f}".replace(",", "·").replace(".", ",").replace("·", ".")

def _levers_do_mes(m, modelo):
    """Alavancas observadas em um mês (None quando o denominador não existe)."""
    lv = {}
    inv, imp = inv_cpm(m, modelo), (m.get("Impressões") or 0)
    lv["cpm"] = inv / imp * 1000 if imp and inv else None
    if split(modelo):
        sm = m.get("Sessões Meta") or 0
        lv["custo_sessao_meta"] = (m.get("Investimento Meta") or 0) / sm if sm else None
    for key, _, num_, den_ in todas_alavancas(modelo):
        d = m.get(den_) or 0
        lv[key] = ((m.get(num_) or 0) / d) if d else None
    rec, vendas = MODELOS[modelo]["receita"], MODELOS[modelo]["etapas"][-1]
    v = m.get(vendas) or 0
    lv["ticket"] = ((m.get(rec) or 0) / v) if v and (m.get(rec) or 0) > 0 else None
    return lv


def envelope(meses, modelo, janela, desde=None, incluir_corrente=False):
    """Para cada alavanca: atual (último quarter, ponderado), mediana e melhor mês do período de referência, e o valor do
    'mês de referência' (o mês fechado do período com mais vendas por R$ de mídia: um mês real e coerente, não uma
    combinação de melhores taxas de meses diferentes). Ticket de referência = mediana dos tickets mensais com venda."""
    fechados = [m for m in meses if m["status"] == "fechado"]
    win = janela_meses(meses, janela, incluir_corrente)
    periodo = fechados + ([m for m in meses if m["status"] == "corrente"] if incluir_corrente else [])
    if desde:
        alvo = norm(desde).replace(" ", "")
        idx = next((i for i, m in enumerate(periodo) if f"{m['mes']}/{m['ano']}".replace(" ", "") == alvo), None)
        if idx is None:
            sys.exit(f"--desde {desde}: mês não encontrado entre {[_rot(m) for m in periodo]}")
        periodo = periodo[idx:]
    vendas_key = MODELOS[modelo]["etapas"][-1]
    cand = [m for m in periodo if m["status"] == "fechado"] or periodo   # mês parcial não serve de referência
    ref = max(cand, key=lambda m: ((m.get(vendas_key) or 0) / m["Investimento"]) if (m.get("Investimento") or 0) > 0 else -1)
    ref_lv = _levers_do_mes(ref, modelo)
    ref_motivo = (f"{_rot(ref)}: {int(ref.get(vendas_key) or 0)} venda(s) com R$ {ref['Investimento']:,.0f} de mídia, "
                  f"a melhor eficiência entre os meses fechados do período ({', '.join(_rot(m) for m in cand)})"
                  + ("" if ref["status"] == "fechado" else " — atenção: não havia mês fechado no período, a referência é um mês parcial"))
    env = {}
    def agg(ms, num_, den_):
        a = sum((m.get(den_) or 0) for m in ms); b = sum((m.get(num_) or 0) for m in ms)
        return (b / a) if a else None
    # CPM (menor é melhor)
    serie = [(_levers_do_mes(m, modelo)["cpm"], _rot(m)) for m in periodo if (m.get("Impressões") or 0) >= MIN_DEN and inv_cpm(m, modelo) > 0]
    best = min(serie, key=lambda x: x[0]) if serie else (None, None)
    inv = sum(inv_cpm(m, modelo) for m in win); imp = sum((m["Impressões"] or 0) for m in win)
    env["cpm"] = {"rotulo": "CPM (Google)" if split(modelo) else "CPM", "atual": inv / imp * 1000 if imp else None, "mediana": _mediana([v for v, _ in serie]),
                  "melhor": best[0], "melhor_mes": best[1], "referencia": ref_lv["cpm"], "sentido": "menor"}
    if split(modelo):
        serie = [(_levers_do_mes(m, modelo)["custo_sessao_meta"], _rot(m)) for m in periodo if (m.get("Sessões Meta") or 0) >= MIN_DEN]
        best = min(serie, key=lambda x: x[0]) if serie else (None, None)
        im, sm = sum((m.get("Investimento Meta") or 0) for m in win), sum((m.get("Sessões Meta") or 0) for m in win)
        env["custo_sessao_meta"] = {"rotulo": "Custo por sessão Meta", "atual": im / sm if sm else None, "mediana": _mediana([v for v, _ in serie]),
                                    "melhor": best[0], "melhor_mes": best[1], "referencia": ref_lv.get("custo_sessao_meta"), "sentido": "menor"}
        iv = sum((m.get("Investimento") or 0) for m in win)
        env["_split"] = {"participacao_meta_na_verba": im / iv if iv else 0.0}
    for key, label, num_, den_ in todas_alavancas(modelo):
        serie = [((m.get(num_) or 0) / m[den_], _rot(m)) for m in periodo if (m.get(den_) or 0) >= MIN_DEN]
        best = max(serie, key=lambda x: x[0]) if serie else (None, None)
        env[key] = {"rotulo": label, "atual": agg(win, num_, den_) or 0.0, "mediana": _mediana([v for v, _ in serie]),
                    "melhor": best[0], "melhor_mes": best[1], "referencia": ref_lv[key], "sentido": "maior"}
    rec = MODELOS[modelo]["receita"]
    serie = [(_levers_do_mes(m, modelo)["ticket"], _rot(m)) for m in periodo if _levers_do_mes(m, modelo)["ticket"]]
    best = max(serie, key=lambda x: x[0]) if serie else (None, None)
    env["ticket"] = {"rotulo": "Ticket médio", "atual": agg(win, rec, vendas_key), "mediana": _mediana([v for v, _ in serie]),
                     "melhor": best[0], "melhor_mes": best[1], "referencia": _mediana([v for v, _ in serie]), "sentido": "maior"}
    for k, e in env.items():  # taxas de etapa não passam de 100%
        if k in ("cpm", "ticket", "custo_sessao_meta") or k.startswith("_"): continue
        for campo in ("atual", "mediana", "melhor", "referencia"):
            if e.get(campo) is not None: e[campo] = min(e[campo], TAXA_MAX)
    for e in [x for k, x in env.items() if not k.startswith("_")]:  # alvo da rampa = mediana do período, nunca pior que o atual
        alvo = e["mediana"] if e["mediana"] is not None else e["atual"]
        if e["atual"] is not None and alvo is not None:
            alvo = min(alvo, e["atual"]) if e["sentido"] == "menor" else max(alvo, e["atual"])
        e["alvo"] = alvo
    # Teto histórico de receita: o melhor mês do período de referência. Serve de trava de sanidade —
    # uma projeção que pede muito mais do que o cliente já entregou alguma vez precisa dizer com que verba.
    # O mês corrente entra quando o usuário pediu --incluir-corrente, marcado como parcial: receita parcial já
    # aconteceu, então serve de piso do teto. Deixá-lo de fora fazia o alerta disparar contra o próprio melhor mês
    # (cliente de climatização: melhor mês fechado US$ 350, corrente US$ 12.680 — a trava acusava "79x" em toda projeção).
    rec_key = MODELOS[modelo]["receita"]
    serie_rec = [(m.get(rec_key) or 0, _rot(m), m.get("Investimento") or 0, m["status"] == "corrente")
                 for m in periodo if (m.get(rec_key) or 0) > 0]
    if serie_rec:
        melhor = max(serie_rec, key=lambda x: x[0])
        env["_teto_receita"] = {"receita": melhor[0], "mes": melhor[1], "midia": melhor[2],
                                "parcial": melhor[3], "meses_fechados": len(fechados)}
    else:
        env["_teto_receita"] = None
    env["_referencia"] = {"mes": _rot(ref), "motivo": ref_motivo, "periodo": [_rot(m) for m in periodo]}
    return env


def K_rampa(mes_alvo):
    return RAMPA_ATE or mes_alvo


def curva_alavancas(env, modelo, alpha, K, horizonte, ticket_manual=None):
    """Valor de cada alavanca mês a mês: rampa linear do atual até atual + alpha·(alvo − atual), atingindo o alvo em M{K}.
    alvo = mediana do período comparável (nunca pior que o atual); alpha = 1 percorre todo o caminho."""
    chaves = ["cpm"] + [k for k, *_ in todas_alavancas(modelo)] + ["ticket"] + (["custo_sessao_meta"] if split(modelo) else [])
    linhas = []
    for t in range(1, horizonte + 1):
        f = min(t, K) / K if K > 0 else 1.0
        row = {}
        for k in chaves:
            e = env[k]
            atual = e["atual"] if e["atual"] is not None else (ticket_manual if k == "ticket" else None)
            alvo = e.get("alvo") if e.get("alvo") is not None else atual
            if atual is None:
                row[k] = None; continue
            alvo = atual + alpha * (alvo - atual)
            row[k] = atual + (alvo - atual) * f
        if CPM_CRESC and row.get("cpm"):   # saturação do público: o CPM base cresce todo mês a partir do Mês 2, até o teto
            g, teto, ate = CPM_CRESC
            row["cpm"] = row["cpm"] * (1 + g) ** (min(t, ate or t) - 1)
            if teto: row["cpm"] = min(row["cpm"], teto)
        linhas.append(row)
    return linhas


def projetar_curva(levers, modelo, fee, midia, margem, comissao, acumulado_inicial=0.0, lag=1.0, crescimento_midia=0.0, midia_teto=None):
    """Cadeia mês a mês com alavancas variáveis.
    lag = fração das vendas que cai no mês do lead; crescimento_midia = crescimento mensal da verba (0.10 = +10%/mês)."""
    cadeia = alavancas(modelo)
    linhas, acum, pend = [], acumulado_inicial, 0.0
    if CRM:   # coortes de clientes por mês de compra (s = 1 é o Mês 1); compras de antes do Mês 1 entram pela idade no Mês 1
        base_leads = float(CRM["base"].get("leads_sem_compra") or 0)
        coortes = {1 - int(i): float(n_) for i, n_ in CRM.get("coortes_pre", [])}
    for t, lv in enumerate(levers, start=1):
        if VERBA_PLANO:
            midia_t = VERBA_PLANO[min(t, len(VERBA_PLANO)) - 1]
        else:
            midia_t = midia * (1 + crescimento_midia) ** (t - 1)
            if midia_teto: midia_t = min(midia_t, midia_teto)
        sp = MODELOS[modelo].get("participacao_meta", 0.0) if split(modelo) else 0.0
        midia_g, midia_m = midia_t * (1 - sp), midia_t * sp
        saz_d = SAZ["demanda"][t - 1] if SAZ and t <= len(SAZ["demanda"]) else 1.0
        saz_c = SAZ["cpm"][t - 1] if SAZ and t <= len(SAZ["cpm"]) else 1.0
        vol = midia_g / (lv["cpm"] * saz_c) * 1000 if lv["cpm"] else 0.0
        volumes = {"Impressões": vol}
        for key, _, num_, den_ in cadeia:
            if ORGANICO and den_ == "Leads":   # orgânico: entradas × conversão entram como leads, junto com os pagos
                vis = ORGANICO["visitas"][min(t, len(ORGANICO["visitas"])) - 1]
                lo = vis * ORGANICO["conversao"]
                volumes["Leads pagos"], volumes["Visitas orgânicas"], volumes["Leads orgânicos"] = vol, vis, lo
                vol += lo
                volumes["Leads"] = vol
            if split(modelo) and key == "sessao_cart":   # sessões pagas = Google (funil) + Meta (verba ÷ custo por sessão)
                ses_m = midia_m / lv["custo_sessao_meta"] if lv.get("custo_sessao_meta") else 0.0
                volumes["Sessões Meta"] = ses_m
                vol = volumes["Sessões Google"] + ses_m
                volumes["Sessões"] = vol
            vol *= (lv[key] or 0.0)
            volumes[num_] = vol
        if split(modelo):
            volumes["midia_google"], volumes["midia_meta"] = midia_g, midia_m
        geradas = vol * saz_d   # sazonalidade de demanda: mais (ou menos) vendas com o mesmo funil
        vendas = geradas * lag + pend
        pend = geradas * (1 - lag)
        receita = vendas * (lv["ticket"] or 0.0)
        extra = {}
        receita_total = receita
        if CRM:
            b, tx = CRM["base"], CRM["taxas"]
            on = 1.0 if t >= int(CRM["inicio"]) else 0.0
            soma = lambda lo, hi: sum(n_ for s_, n_ in coortes.items() if lo <= t - s_ <= hi)
            recentes = soma(1, 5) + float(b.get("recentes") or 0)
            ativos = soma(6, 12) + float(b.get("ativos") or 0)
            inativos = soma(13, 10 ** 6) + float(b.get("inativos") or 0)
            v_whats = on * (ativos * tx["recompra"] + float(b.get("recorrentes") or 0) * tx["recompra_recorrentes"])
            v_cross = on * recentes * tx["cross_sell"] * tx["campanhas_cross_sell"]
            v_email = on * base_leads * tx["email"] * tx["emails"]
            v_reat = on * inativos * tx["reativacao"] * tx["campanhas_reativacao"]
            vendas_c = VOL_REAL[t]["Vendas"] if t in VOL_REAL else vendas
            leads_c = VOL_REAL[t]["Leads"] if t in VOL_REAL else volumes.get("Leads", 0.0)
            coortes[t] = vendas_c + v_email
            g_rec = (v_whats + v_cross) * CRM["ticket"]; g_reat = (v_email + v_reat) * CRM["ticket"]
            extra = {"base_leads": round(base_leads, 2), "clientes_recentes": round(recentes, 2), "clientes_ativos": round(ativos, 2),
                     "clientes_inativos": round(inativos, 2), "vendas_whatsapp": round(v_whats, 4), "vendas_cross_sell": round(v_cross, 4),
                     "vendas_email": round(v_email, 4), "vendas_reativacao": round(v_reat, 4),
                     "receita_recompra": round(g_rec, 2), "receita_reativacao": round(g_reat, 2)}
            base_leads = max(0.0, base_leads * (1 - tx.get("descadastro", 0.0) * tx["emails"]) + leads_c - vendas_c - v_email)
            receita_total = receita + g_rec + g_reat
        mc = receita_total * comissao * margem
        fee_t = FEE_PLANO[min(t, len(FEE_PLANO)) - 1] if FEE_PLANO else fee
        liquido = mc - fee_t - midia_t
        if t in REALIZADO:
            liquido = REALIZADO[t]
        acum += liquido
        linhas.append({"mes": t, **{k: round(v, 2) for k, v in volumes.items()}, "midia": round(midia_t, 2), "vendas": round(vendas, 2),
                       "receita": round(receita, 2), "receita_total": round(receita_total, 2), **extra, "receita_cobre_custo": bool(receita_total >= fee + midia_t), "resultado_mc": round(mc, 2),
                       "custo": round(fee_t + midia_t, 2), "fee": round(fee_t, 2), "roas": round(receita / midia_t, 2) if midia_t else None,
                       "resultado_liquido": round(liquido, 2), "acumulado": round(acum, 2),
                       **({"saz_demanda": saz_d, "saz_cpm": saz_c} if SAZ else {})})
    return linhas


def payback(linhas):
    return next((l["mes"] for l in linhas if l["acumulado"] >= 0), None)


def quarters(linhas):
    out = []
    for q in range(0, len(linhas), 3):
        bloco = linhas[q:q + 3]
        out.append({"quarter": f"Q{q // 3 + 1}", "meses": f"M{bloco[0]['mes']}–M{bloco[-1]['mes']}", "vendas": round(sum(l["vendas"] for l in bloco), 2),
                    "receita": round(sum(l["receita"] for l in bloco), 2), "resultado_liquido": round(sum(l["resultado_liquido"] for l in bloco), 2),
                    "acumulado_fim": bloco[-1]["acumulado"]})
    return out


def veredito(env, modelo, fee, midia, margem, comissao, mes_alvo, horizonte, acumulado_inicial, lag, ticket_manual=None, crescimento_midia=0.0, midia_teto=None):
    """Compara o cenário de taxas atuais com rampas dentro do envelope histórico e diz em que mês o breakeven fica realista.
    O cenário entregue é sempre a rampa completa até o mês de referência (alpha = 1), com a verba crescendo pelo percentual informado."""
    def cen(alpha):
        return projetar_curva(curva_alavancas(env, modelo, alpha, K_rampa(mes_alvo), horizonte, ticket_manual), modelo, fee, midia, margem, comissao, acumulado_inicial, lag, crescimento_midia, midia_teto)
    base, cheio = cen(0.0), cen(1.0)
    pay_base, pay_cheio = payback(base), payback(cheio)
    alpha_star = None
    for i in range(0, 201):  # 0% a 200% do caminho até o melhor mês
        a = i / 100
        if (payback(cen(a)) or 99) <= mes_alvo:
            alpha_star = a; break
    if pay_base is not None and pay_base <= mes_alvo:
        status = "REALISTA"
    elif alpha_star is not None and alpha_star <= 1.0:
        status = "REALISTA COM RAMPA"
    else:
        status = "IRREALISTA"
    cenario, alpha_usado = cheio, 1.0   # o template sempre recebe a rampa completa até o mês de referência
    alvo_l = cenario[mes_alvo - 1]
    acum_ant = cenario[mes_alvo - 2]["acumulado"] if mes_alvo > 1 else acumulado_inicial
    mc_nec = (fee + midia) - acum_ant
    ticket_alvo = curva_alavancas(env, modelo, alpha_usado, K_rampa(mes_alvo), horizonte, ticket_manual)[mes_alvo - 1]["ticket"] or 1
    receita_nec = mc_nec / (comissao * margem)
    vendas_nec = max(0, math.ceil(receita_nec / ticket_alvo))
    gap = max(0.0, vendas_nec - alvo_l["vendas"])
    upside = {}
    for k, e in env.items():
        if k.startswith("_"): continue
        if e["atual"] and e.get("alvo"):
            upside[e["rotulo"]] = round((e["atual"] / e["alvo"]) if e["sentido"] == "menor" else (e["alvo"] / e["atual"]), 2)
    decisiva = max(upside, key=upside.get) if upside else None
    v = {"status": status, "mes_alvo": mes_alvo, "payback_taxas_atuais": pay_base, "payback_melhor_historico": pay_cheio,
         "mes_realista": pay_cheio, "alpha_necessario_para_mes_alvo": alpha_star, "alpha_usado_no_cenario": alpha_usado,
         "vendas_projetadas_mes_alvo": round(alvo_l["vendas"], 1), "vendas_necessarias_mes_alvo": vendas_nec, "gap_vendas": round(gap, 1),
         "mc_por_real_de_midia_taxas_atuais": round(base[0]["resultado_mc"] / midia, 3) if midia else None,
         "maior_exposicao_caixa": min(l["acumulado"] for l in cenario), "alavanca_com_mais_folga_no_historico": decisiva, "folga_por_alavanca": upside}
    # a pergunta "em que mês fica realista?" tem resposta mesmo depois do horizonte: estende a mesma rampa por 48 meses
    longo = projetar_curva(curva_alavancas(env, modelo, 1.0, K_rampa(mes_alvo), 48, ticket_manual), modelo, fee, midia, margem, comissao,
                           acumulado_inicial, lag, crescimento_midia, midia_teto)
    res = [l["resultado_liquido"] for l in longo]
    v["resultados_48m"] = [round(x, 2) for x in res]   # o gerador troca os meses já vividos pelo realizado e refaz as datas
    v["primeiro_mes_no_azul"] = next((t for t, x in enumerate(res, 1) if x >= 0), None)
    v["no_azul_continuo_desde"] = next((t for t in range(1, len(res) + 1) if all(x >= 0 for x in res[t - 1:])), None)
    v["acumulado_zera_em"] = next((l["mes"] for l in longo if l["acumulado"] >= 0), None)
    v["horizonte"] = horizonte
    v["mes_referencia"] = env["_referencia"]["mes"]; v["mes_referencia_motivo"] = env["_referencia"]["motivo"]
    # Trava de sanidade: a projeção do mês-alvo contra o melhor mês que o cliente já entregou.
    # O teto é de receita, não de capacidade: se a verba subiu, passar dele é legítimo — por isso o alerta diz as duas coisas.
    tr = env.get("_teto_receita") or {}
    v["teto_receita_historico"], v["teto_receita_mes"] = tr.get("receita"), tr.get("mes")
    v["alerta_teto_receita"] = None
    if tr.get("receita"):
        alvo = next((l for l in cenario if l["mes"] == mes_alvo), None)
        rec_alvo = (alvo or {}).get("receita_total", (alvo or {}).get("receita", 0))
        mult = rec_alvo / tr["receita"] if tr["receita"] else 0
        v["teto_receita_multiplo"] = round(mult, 2)
        if mult > 1.2:
            mid = (alvo or {}).get("midia", 0); mid_teto = tr.get("midia") or 0
            verba = (f"com {mid / mid_teto:.1f}x a verba daquele mês" if mid_teto and mid > mid_teto * 1.05
                     else (f"com a mesma verba" if mid_teto and mid <= mid_teto * 1.05 else ""))
            frouxo = " O histórico tem poucos meses fechados, então o teto é frágil." if tr.get("meses_fechados", 0) < 4 else ""
            parc = " (mês ainda em curso, então o valor dele tende a subir)" if tr.get("parcial") else ""
            v["alerta_teto_receita"] = (f"a projeção pede {_rs(rec_alvo)} no mês-alvo, {mult:.1f}x o melhor mês já realizado "
                                        f"({_rs(tr['receita'])} em {tr['mes']}{parc}){', ' + verba if verba else ''}."
                                        f" Diga de onde vem a diferença antes de apresentar.{frouxo}")
    v["leitura"] = leitura(v, env, mes_alvo, horizonte)
    return v, {"base": base, "cheio": cheio, "cenario": cenario, "alpha": alpha_usado}


def caminho(env, modelo, meses_ref, fee, midia, margem, comissao, mes_alvo, horizonte, acumulado_inicial, lag, ticket, crescimento_midia, midia_teto):
    """Quando a meta não fecha: o valor de cada alavanca, sozinha, que faz o mês-alvo fechar no zero (resultado do mês ≥ 0),
    comparado com o melhor mês fechado do período; mais o fee que fecha, a verba que cobre o fee e o 1º mês positivo sem teto."""
    import copy
    def rodar(e, fee_=fee, teto=midia_teto, h=horizonte):
        lv = curva_alavancas(e, modelo, 1.0, K_rampa(mes_alvo), h, ticket)
        return projetar_curva(lv, modelo, fee_, midia, margem, comissao, acumulado_inicial, lag, crescimento_midia, teto)
    base = rodar(env)
    if base[mes_alvo - 1]["resultado_liquido"] >= 0:
        return None
    def melhor_fechado(chave):
        vals = [v for v in (_levers_do_mes(m, modelo).get(chave) for m in meses_ref) if v is not None]
        if not vals: return None
        return min(vals) if env[chave]["sentido"] == "menor" else max(vals)
    linhas = []
    for chave, e in [(k, x) for k, x in env.items() if not k.startswith("_")]:
        atual = e.get("atual")
        if not atual: continue
        teto_busca = TAXA_MAX if chave not in ("ticket", "cpm", "custo_sessao_meta") else atual * 10
        passos = [atual + (teto_busca - atual) * i / 2000 for i in range(1, 2001)] if e["sentido"] == "maior" else [atual * (1 - i / 2000) for i in range(1, 2000)]
        nec = None
        for x in passos:
            e2 = copy.deepcopy(env); e2[chave]["alvo"] = x
            if rodar(e2)[mes_alvo - 1]["resultado_liquido"] >= 0:
                nec = x; break
        mf = melhor_fechado(chave)
        visto = None if nec is None or mf is None else (nec <= mf if e["sentido"] == "maior" else nec >= mf)
        linhas.append({"alavanca": chave, "rotulo": e["rotulo"], "atual": atual, "alvo_rampa": e.get("alvo"), "necessario": nec,
                       "melhor_mes_fechado": mf, "ja_visto": visto})
    ult = base[mes_alvo - 1]
    lv = curva_alavancas(env, modelo, 1.0, K_rampa(mes_alvo), horizonte, ticket)[mes_alvo - 1]
    por_real = 1000 / lv["cpm"] if lv.get("cpm") else 0.0
    for k, *_ in alavancas(modelo):
        por_real *= (lv.get(k) or 0.0)
    mc_real = por_real * (lv.get("ticket") or 0.0) * comissao * margem
    longo = rodar(env, teto=None, h=48)
    return {"criterio": f"resultado do M{mes_alvo} ≥ 0 (cada alavanca sozinha, as demais na rampa)",
            "resultado_mes_alvo_na_rampa": ult["resultado_liquido"], "acumulado_mes_alvo_na_rampa": ult["acumulado"],
            "alavancas": linhas, "fee_que_fecha": ult.get("fee", fee) + ult["resultado_liquido"],
            "margem_por_real_de_midia_no_alvo": mc_real, "verba_que_cobre_o_fee": (fee / (mc_real - 1)) if mc_real > 1 else None,
            "primeiro_mes_positivo_sem_teto": next((l["mes"] for l in longo if l["resultado_liquido"] >= 0), None),
            "payback_sem_teto": next((l["mes"] for l in longo if l["acumulado"] >= 0), None)}


def leitura(v, env, mes_alvo, horizonte):
    pb, pc, a = v["payback_taxas_atuais"], v["payback_melhor_historico"], v["alpha_necessario_para_mes_alvo"]
    ref = env["_referencia"]
    txt = (f"Com as taxas atuais o acumulado zera em M{pb}. " if pb else f"Com as taxas atuais o acumulado não zera em {horizonte} meses. ")
    if v["status"] == "REALISTA":
        txt += f"A meta de M{mes_alvo} é realista sem melhorar nenhuma taxa. "
    elif pc:
        txt += (f"Levando cada alavanca gradualmente até a mediana do período comparável (rampa até M{K_rampa(mes_alvo)}), o acumulado zera em M{pc}: "
                f"é a partir daí que a meta fica realista. ")
    else:
        txt += f"Nem levando todas as alavancas à mediana do período o acumulado zera em {horizonte} meses. "
    if v["status"] == "REALISTA COM RAMPA":
        txt += f"Para bater M{mes_alvo} basta percorrer {a:.0%} do caminho entre a taxa atual e a mediana."
    elif v["status"] == "IRREALISTA" and a is not None:
        txt += f"Para bater M{mes_alvo} seria preciso ir {a - 1:.0%} além da mediana do período; a meta em M{mes_alvo} é irrealista."
    elif v["status"] == "IRREALISTA":
        txt += f"Nem dobrando a distância até a mediana a meta de M{mes_alvo} fecha; ela é irrealista com este fee, mídia e margem."
    azul, zera = v.get("no_azul_continuo_desde"), v.get("acumulado_zera_em")
    txt += (f" Com o realizado dos meses já vividos e a projeção à frente, o resultado fica no azul de forma contínua a partir do M{azul}" if azul
            else " Com o realizado dos meses já vividos e a projeção à frente, nenhum mês fica no azul de forma contínua em 48 meses")
    if azul:
        txt += (f" e o acumulado zera no M{zera}" + (" (depois do horizonte da planilha)" if zera > horizonte else "") + "." if zera
                else ", mas o acumulado não zera em 48 meses.")
    else:
        txt += "."
    txt += f" Evidência de que o nível é atingível: {ref['motivo']}."
    if v["alavanca_com_mais_folga_no_historico"]:
        txt += f" A alavanca com mais folga até a mediana é {v['alavanca_com_mais_folga_no_historico']} ({v['folga_por_alavanca'][v['alavanca_com_mais_folga_no_historico']]}x)."
    if v.get("teto_receita_historico"):
        txt += f" Melhor mês já realizado: {_rs(v['teto_receita_historico'])} em {v['teto_receita_mes']}."
    if v.get("alerta_teto_receita"):
        txt += " Trava de sanidade: " + v["alerta_teto_receita"]
    return txt


# ----------------------------------------------------------------------------- CLI
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("modo", choices=["detectar", "projetar"])
    p.add_argument("--fonte", required=True, help="xlsx, csv ou URL do Google Sheets")
    p.add_argument("--aba", default="Indicadores")
    p.add_argument("--modelo", choices=MODELOS.keys(), default="inside_sales")
    p.add_argument("--janela", type=int, default=3, help="meses fechados usados nas taxas efetivas")
    p.add_argument("--fee", type=float)
    p.add_argument("--midia", type=float)
    p.add_argument("--margem", type=float, help="margem de contribuição (0.30 = 30%%)")
    p.add_argument("--comissao", type=float, default=1.0, help="take rate sobre o GMV; 1.0 se a receita já é do cliente")
    p.add_argument("--ticket", type=float, help="sobrescreve o ticket calculado")
    p.add_argument("--mes-alvo", type=int)
    p.add_argument("--horizonte", type=int, default=12)
    p.add_argument("--acumulado-inicial", type=float, default=0.0, help="déficit já acumulado (negativo)")
    p.add_argument("--crescimento-midia", type=float, default=0.0, help="crescimento mensal da verba de mídia (0.10 = +10%%/mês)")
    p.add_argument("--connect-rate", type=float, help="connect rate (cliques -> visitas na página; ex.: 0.80) quando o cliente tem landing page mas a fonte não traz a linha de visitas")
    p.add_argument("--fee-historico", type=float, help="fee real do contrato nos meses da fonte, quando a linha Fee V4 da planilha está errada (ex.: 6901)")
    p.add_argument("--rampa-ate", type=int, help="mês em que as alavancas chegam ao alvo da rampa (padrão: o mês-alvo); use quando a meta fica depois do fim da rampa")
    p.add_argument("--inicio", help="mês/ano do Mês 1 da projeção (padrão: o mês corrente da fonte); igual ao --inicio-contrato do gerador")
    p.add_argument("--organico-visitas", help="inside sales: entradas orgânicas por mês a partir do Mês 1, separadas por vírgula; depois do último valor, repete")
    p.add_argument("--organico-conversao", type=float, default=None, help="conversão da entrada orgânica → lead (ex.: 0.0615 = taxa clique → lead atual)")
    p.add_argument("--organico-origem", default="SEO", help="de onde vem o tráfego orgânico: SEO, social orgânico, indicação... (entra no rótulo das linhas)")
    p.add_argument("--organico-metrica", default="visitas orgânicas",
                   help="o que é contado na entrada do funil orgânico: 'visitas orgânicas' (site), 'cliques no link da bio' (social), 'conversas iniciadas'...")
    p.add_argument("--crm", help="inside sales: JSON com o CRM (início, ticket, taxas de recompra/cross-sell/e-mail/reativação, base inicial e coortes)")
    p.add_argument("--fee-plano", help="fee mês a mês a partir do Mês 1, separado por vírgula (ex.: 6901,9901 quando o CRM entra no fee); repete o último")
    p.add_argument("--verba-plano", help="verba mês a mês separada por vírgula, a partir do Mês 1 (ex.: 2000,4000,5000,5000); substitui crescimento e teto")
    p.add_argument("--midia-teto", type=float, help="teto da verba mensal; o crescimento para ao atingir esse valor")
    p.add_argument("--lag", type=float, default=1.0, help="fração das vendas no mês do lead (1 = sem lag)")
    p.add_argument("--definicao-breakeven", default="margem de contribuição cobrindo fee + mídia", help="texto da definição usada; mude só com o usuário ciente (ex.: receita atribuída cobrindo fee + mídia)")
    p.add_argument("--incluir-corrente", action="store_true", help="inclui o mês corrente (parcial) na janela de taxas e no período de referência; só quando o usuário pedir")
    p.add_argument("--desde", help="primeiro mês fechado comparável (ex.: maio/2026); limita o período de referência da rampa")
    p.add_argument("--alvo", action="append", default=[], metavar="ALAVANCA=VALOR",
                   help="alvo da rampa vindo de benchmark de mercado, quando o histórico não basta (ex.: sql_venda=0.25); "
                        "a rampa vai do atual até esse valor no mês-alvo; nunca pior que o atual; o alerta fica registrado. "
                        "Inside sales aceita conexao=0.69 (atendimento): com a linha Conexões na fonte é etapa da cadeia; sem ela, sobe leads → MQLs na mesma proporção")
    p.add_argument("--cpm-crescimento", type=float, help="crescimento mensal do CPM base pela saturação do público (ex.: 0.03 = +3%%/mês a partir do Mês 2); premissa do usuário")
    p.add_argument("--cpm-teto", type=float, help="teto do CPM base com o crescimento (ex.: mediana do mercado)")
    p.add_argument("--cpm-crescimento-ate", type=int, help="último mês em que o CPM base cresce (ex.: o mês em que a verba para de subir); depois fica estável")
    p.add_argument("--sazonalidade-demanda", help="multiplicador de vendas mês a mês a partir do Mês 1, ex.: 1,1,1.3,1.15 (Black Friday em novembro); depois da lista, 1")
    p.add_argument("--sazonalidade-cpm", help="multiplicador de CPM mês a mês a partir do Mês 1, ex.: 1,1,1.25,1; depois da lista, 1")
    p.add_argument("--fixar", action="append", default=[], metavar="ALAVANCA=VALOR",
                   help="fixa uma alavanca (atual e alvo) quando o histórico mistura campanhas diferentes; ex.: clique_lead=0.0615. Chaves: cpm, ctr, clique_lead (ou connect e visita_lead, quando há linha de visitas), lead_mql, mql_sql, sql_venda, ticket (inside sales); cpm, ctr, clique_sessao, sessao_cart, cart_checkout, checkout_trans, ticket, custo_sessao_meta (e-commerce)")
    p.add_argument("--ga4", help="resumo mensal do GA4 (saída do ga4_resumo.py): separa Google e Meta e mede carrinho e checkout do pago")
    p.add_argument("--out", default="premissas.json")
    a = p.parse_args()

    global VERBA_PLANO, RAMPA_ATE, ORGANICO, CRM, FEE_PLANO, SAZ, CPM_CRESC
    if a.crm:
        if a.modelo != "inside_sales": sys.exit("--crm vale para inside sales")
        CRM = json.load(open(a.crm, encoding="utf-8"))
    if a.fee_plano:
        FEE_PLANO = [float(x) for x in a.fee_plano.split(",") if x.strip()]
    RAMPA_ATE = a.rampa_ate
    if a.organico_visitas:
        if a.modelo != "inside_sales" or a.organico_conversao is None:
            sys.exit("--organico-visitas vale para inside sales e exige --organico-conversao")
        ORGANICO = {"visitas": [float(x) for x in a.organico_visitas.split(",") if x.strip()], "conversao": a.organico_conversao,
                    "origem": a.organico_origem, "metrica": a.organico_metrica}
    if a.verba_plano:
        VERBA_PLANO = [float(x) for x in a.verba_plano.split(",") if x.strip()]
        a.midia = VERBA_PLANO[0]
    if a.cpm_crescimento:
        CPM_CRESC = (a.cpm_crescimento, a.cpm_teto, a.cpm_crescimento_ate)
    if a.sazonalidade_demanda or a.sazonalidade_cpm:
        lista = lambda x: [float(v) for v in x.split(",") if v.strip()] if x else []
        SAZ = {"demanda": lista(a.sazonalidade_demanda), "cpm": lista(a.sazonalidade_cpm)}
    df = carregar(a.fonte, a.aba)
    ga4 = json.load(open(a.ga4, encoding="utf-8")) if a.ga4 else None
    meses, _ = ler_historico(df, a.modelo, ga4)
    avisos = []
    if a.modelo == "inside_sales":
        avisos += _guardar_visitas(meses, a)
    if a.fee_historico is not None:   # a linha Fee V4 da fonte diverge do contrato: vale o fee informado em todo o histórico
        for m in meses:
            if m.get(LINHAS_FIXAS["fee"]) is not None:
                m[LINHAS_FIXAS["fee"] + " (fonte)"] = m[LINHAS_FIXAS["fee"]]
                m[LINHAS_FIXAS["fee"]] = a.fee_historico
    tx = taxas_efetivas(meses, a.modelo, a.janela, a.incluir_corrente)
    tx["alertas"] += avisos
    if a.fee_historico is not None:
        fonte = sorted({m.get(LINHAS_FIXAS["fee"] + " (fonte)") for m in meses if m.get(LINHAS_FIXAS["fee"] + " (fonte)")})
        tx["alertas"].append(f"Fee da fonte ({', '.join(f'R$ {x:,.0f}' for x in fonte)}) substituído por R$ {a.fee_historico:,.0f}, o fee do contrato informado pelo usuário, em todo o histórico.")
    ult = [m for m in meses if m["status"] == "fechado"][-1]
    detectado = {
        "modelo": a.modelo, "fonte": a.fonte, "aba": a.aba,
        "meses_fechados": [f"{m['mes']}/{m['ano']}" for m in meses if m["status"] == "fechado"],
        "mes_corrente": next((f"{m['mes']}/{m['ano']}" for m in meses if m["status"] == "corrente"), None),
        "fee_detectado": ult.get(LINHAS_FIXAS["fee"]),
        "midia_planejada_detectada": ult.get(LINHAS_FIXAS["midia_plano"]),
        "midia_realizada_media_janela": tx["volumes_janela"]["Investimento"] / len(tx["janela_meses"]),
        "margem_detectada": ult.get(LINHAS_FIXAS["margem"]),
        "taxas_efetivas": tx,
        "cadeia_usada": MODELOS[a.modelo]["etapas"],
        "etapas_ausentes_na_fonte": MODELOS[a.modelo].get("etapas_ausentes", []),
        "etapas_estimadas_pelo_ga4": MODELOS[a.modelo].get("etapas_estimadas", []),
        "janela_inclui_mes_corrente": a.incluir_corrente,
        "ga4": MODELOS[a.modelo].get("ga4"),
        "split_google_meta": split(a.modelo),
    }
    if a.modo == "detectar":
        print(json.dumps(detectado, ensure_ascii=False, indent=2, default=str))
        return

    faltam = [k for k in ("fee", "midia", "margem", "mes_alvo") if getattr(a, k) is None]
    if faltam:
        sys.exit(f"projetar exige confirmação explícita de: {faltam} (a skill deve perguntar ao usuário).")
    ticket = a.ticket or tx["ticket"]
    if not ticket:
        sys.exit("Ticket médio indisponível: informe --ticket.")
    env = envelope(meses, a.modelo, a.janela, a.desde, a.incluir_corrente)
    # calendário do Mês 1 e realizado dos meses já vividos (entra no lugar da projeção, como na linha consolidada da planilha)
    rot_ = lambda m: f"{m['mes']}/{m['ano']}".replace(" ", "")
    if a.inicio:
        i0 = next((i for i, m in enumerate(meses) if rot_(m) == norm(a.inicio).replace(" ", "")), None)
        if i0 is None: sys.exit(f"--inicio {a.inicio}: mês não encontrado na fonte")
    else:
        i0 = next((i for i, m in enumerate(meses) if m["status"] == "corrente"), None)
        if i0 is None: i0 = max(i for i, m in enumerate(meses) if m["status"] == "fechado") + 1
    rec_key_ = MODELOS[a.modelo]["receita"]
    for t in range(1, len(meses) - i0 + 1):
        m = meses[i0 + t - 1]
        if m["status"] in ("fechado", "corrente") and (m.get("Investimento") or 0) > 0:
            REALIZADO[t] = (m.get(rec_key_) or 0) * a.comissao * a.margem - (m.get(LINHAS_FIXAS["fee"]) or 0) - (m.get("Investimento") or 0)
            VOL_REAL[t] = {"Leads": float(m.get("Leads") or 0), "Vendas": float(m.get(MODELOS[a.modelo]["etapas"][-1]) or 0)}
            tx["alertas"].append(f"M{t} ({m['mes']}/{m['ano']}{', parcial' if m['status'] == 'corrente' else ''}) entra pelo realizado: resultado de R$ {REALIZADO[t]:,.0f}.")
    if split(a.modelo):  # a divisão da verba fica constante na projeção (premissa comercial editável no template)
        MODELOS[a.modelo]["participacao_meta"] = env["_split"]["participacao_meta_na_verba"]
    if a.connect_rate is not None and a.modelo == "ecommerce":
        chave = "clique_sessao"
        if chave in env:
            for campo in ("atual", "mediana", "melhor", "referencia", "alvo"):
                if env[chave].get(campo) is not None: env[chave][campo] = a.connect_rate
            env[chave]["fixada"] = True
            tx["taxas"][env[chave]["rotulo"]] = a.connect_rate
            tx["alertas"].append(f"{env[chave]['rotulo']}: taxa informada manualmente ({a.connect_rate:.0%}); "
                                 f"a fonte não permite medi-la porque a linha de cliques não soma todos os canais.")
    for item in a.fixar:
        chave, valor = item.split("=", 1); chave = chave.strip(); valor = float(valor)
        if chave not in env or chave.startswith("_"):
            sys.exit(f"--fixar {chave}: alavanca inexistente; use uma de {[k for k in env if not k.startswith('_')]}")
        antes = env[chave]["atual"]
        for campo in ("atual", "alvo"):
            env[chave][campo] = valor
        env[chave]["fixada"] = True
        tx["alertas"].append(f"{env[chave]['rotulo']}: fixada em {valor:.2%} a pedido do usuário (a janela dava {antes:.2%}); o histórico mistura campanhas diferentes nessa etapa."
                             if chave not in ("cpm", "ticket", "custo_sessao_meta") else
                             f"{env[chave]['rotulo']}: fixado em {valor:,.2f} a pedido do usuário (a janela dava {antes:,.2f}).")
    conexao = None   # (conexão atual, lead → MQL atual) quando a conexão tem alvo de mercado
    for item in a.alvo:   # benchmark de mercado como alvo da rampa (histórico curto demais para dar a mediana)
        chave, valor = item.split("=", 1); chave = chave.strip(); valor = float(valor)
        if chave == "conexao" and "conexao" not in env:
            # fonte sem a linha Conexões: não há etapa de atendimento para receber o alvo, então ele sobe o lead → MQL
            # na mesma proporção, que é o elo seguinte do funil, e o resto fica igual
            con = tx["taxas"].get("Leads → Conexões")
            if a.modelo != "inside_sales" or not con:
                sys.exit("--alvo conexao exige inside sales com a linha Conexões na fonte")
            e = env["lead_mql"]; lm = e["atual"]; valor = max(min(valor, TAXA_MAX), con)
            e["alvo"], e["alvo_mercado"] = min(lm * valor / con, TAXA_MAX), True
            conexao = (con, lm)
            tx["alertas"].append(f"Conexão (leads contatados): alvo da rampa em {valor:.0%} por benchmark de mercado (a janela dava {con:.1%}); "
                                 f"leads → MQLs sobe na mesma proporção, de {lm:.1%} para {e['alvo']:.1%}, e o resto do funil fica igual. A fonte está na aba Premissas.")
            continue
        if chave not in env or chave.startswith("_"):
            sys.exit(f"--alvo {chave}: alavanca inexistente; use uma de {[k for k in env if not k.startswith('_')]}")
        e = env[chave]; antes = e["alvo"]
        if chave not in ("cpm", "ticket", "custo_sessao_meta"): valor = min(valor, TAXA_MAX)
        if e["atual"] is not None:
            valor = min(valor, e["atual"]) if e["sentido"] == "menor" else max(valor, e["atual"])
        e["alvo"], e["alvo_mercado"] = valor, True
        eh_taxa = chave not in ("cpm", "ticket", "custo_sessao_meta")
        f_ = (lambda x: f"{x:.2%}") if eh_taxa else (lambda x: f"{x:,.2f}")
        tx["alertas"].append(f"{e['rotulo']}: alvo da rampa em {f_(valor)} por dado de mercado (o histórico dava {f_(antes)}); "
                             "o histórico é curto demais para esta etapa, e a fonte está na aba Premissas.")
    if env["ticket"]["atual"] is None:
        env["ticket"]["atual"] = ticket
    v, cen = veredito(env, a.modelo, a.fee, a.midia, a.margem, a.comissao, a.mes_alvo, a.horizonte, a.acumulado_inicial, a.lag, ticket, a.crescimento_midia, a.midia_teto)
    taxas_mes = curva_alavancas(env, a.modelo, cen["alpha"], K_rampa(a.mes_alvo), a.horizonte, ticket)
    if conexao:   # conexão mês a mês, coerente com lead → MQL (a planilha mostra os leads conectados subindo junto)
        for row in taxas_mes:
            row["con_lead"] = min(row["lead_mql"] * conexao[0] / conexao[1], TAXA_MAX)
    ref_labels = set(env["_referencia"]["periodo"])
    meses_ref = [m for m in meses if m["status"] == "fechado" and _rot(m) in ref_labels]
    cam = caminho(env, a.modelo, meses_ref, a.fee, a.midia, a.margem, a.comissao, a.mes_alvo, a.horizonte, a.acumulado_inicial,
                  a.lag, ticket, a.crescimento_midia, a.midia_teto)
    hist_fechado = [m for m in meses if m["status"] == "fechado" or (a.incluir_corrente and m["status"] == "corrente")]
    rec_key, vendas_key = MODELOS[a.modelo]["receita"], MODELOS[a.modelo]["etapas"][-1]
    hist_result = [{"mes": f"{m['mes']}/{m['ano']}", "parcial": m["status"] == "corrente", "faturamento": m.get(rec_key) or 0, "fee_mais_midia": (m.get(LINHAS_FIXAS["fee"]) or 0) + (m.get("Investimento") or 0),
                    "mc": (m.get(rec_key) or 0) * a.comissao * a.margem,
                    "resultado_mc": (m.get(rec_key) or 0) * a.comissao * a.margem - (m.get(LINHAS_FIXAS["fee"]) or 0) - (m.get("Investimento") or 0),
                    "faturamento_cobre_custo": (m.get(rec_key) or 0) >= (m.get(LINHAS_FIXAS["fee"]) or 0) + (m.get("Investimento") or 0)} for m in hist_fechado]
    saida = {
        "premissas_confirmadas": {"fee": a.fee, "midia_mensal": a.midia, "margem": a.margem, "comissao": a.comissao,
                                  "ticket": ticket, "mes_alvo": a.mes_alvo, "horizonte": a.horizonte,
                                  "lag": a.lag, "acumulado_inicial": a.acumulado_inicial, "crescimento_midia": a.crescimento_midia, "midia_teto": a.midia_teto, "connect_rate": a.connect_rate,
                                  "definicao_breakeven": a.definicao_breakeven, "fixadas": a.fixar, "alvos_mercado": a.alvo, "verba_plano": VERBA_PLANO, "sazonalidade": SAZ, "cpm_crescimento": list(CPM_CRESC) if CPM_CRESC else None, "rampa_ate": K_rampa(a.mes_alvo), "inicio": a.inicio, "organico": ORGANICO, "fee_historico": a.fee_historico, "crm": CRM, "fee_plano": FEE_PLANO,
                                  "realizado_usado": {str(k): round(x, 2) for k, x in REALIZADO.items()},
                                  "regra_taxas": (f"janela de {a.janela} mês(es) fechado(s)" + (" + mês corrente parcial" if a.incluir_corrente else "") + ", ponderada por volume; rampa até a mediana do período comparável")},
        "detectado": detectado, "historico": meses, "historico_resultado": hist_result,
        "teto_receita": env.get("_teto_receita"),
        "envelope": {k: e for k, e in env.items() if not k.startswith("_")},
        "split": ({"participacao_meta_na_verba": env["_split"]["participacao_meta_na_verba"]} if split(a.modelo) else None),
        "rampa": {"alpha": cen["alpha"], "crescimento_midia": a.crescimento_midia, "midia_teto": a.midia_teto, "connect_rate": a.connect_rate, "midia_teto": a.midia_teto, "atinge_alvo_em": K_rampa(a.mes_alvo), "mes_referencia": env["_referencia"]["mes"], "motivo": env["_referencia"]["motivo"],
                  "periodo_referencia": env["_referencia"]["periodo"], "taxas_mes_a_mes": taxas_mes},
        "projecao": cen["cenario"], "projecao_base": cen["base"], "projecao_melhor_historico": cen["cheio"],
        "quarters": quarters(cen["cenario"]), "veredito": v, "caminho": cam,
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"veredito": v, "arquivo": a.out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
