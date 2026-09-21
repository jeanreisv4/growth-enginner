# -*- coding: utf-8 -*-
"""Gerador dos templates de projeção (Inside Sales / E-commerce) no padrão V4.

Uso:
  python3 build_workbook.py [saida.xlsx]
      -> workbook demo com as duas abas (agência de viagens + e-commerce de tecidos), valores no código.
  python3 build_workbook.py --premissas premissas.json --modelo inside_sales|ecommerce --out saida.xlsx [--cliente NOME] [--cenario NOME]
      -> uma aba gerada a partir do premissas.json (saída do modo `projetar` do piloto breakeven_pilot.py).
         Células amarelas recebem premissas confirmadas e taxas efetivas; células brancas mantêm fórmulas vivas.

Cada métrica: (chave, rótulo, tipo projetado, fonte, formato, total, realizado)
  tipo projetado: 'input' (12 valores) | 'link' (premissa) | 'linkf' (fórmulas 1º mês / demais) | 'calc' | 'calcf' (1º mês / demais) | 'cum' (acumulado da chave)
  realizado:      'in' (você preenche) | 'proj' (puxa o projetado) | 'cum' | expressão com {c} (coluna do mês) e chaves de linha | '""' (sem realizado)
"""
import argparse, json, os, re, sys, unicodedata
from openpyxl import Workbook
from projecao_builder import *

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "logo.png")   # opcional: se o arquivo não existir, a planilha sai sem logo
MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()
def esc(s): return str(s).replace("{", "{{").replace("}", "}}")
def Ln(x, n): return (list(x) + [list(x)[-1]] * n)[:n] if isinstance(x, (list, tuple)) else [x] * n

USO_COMUM = ("• Projetado: edite as células amarelas (premissas gerais à esquerda e alavancas mês a mês). Indicadores, meta de breakeven e gráficos recalculam sozinhos. "
             "Linhas em amarelo-claro puxam a premissa geral; digite um número por cima para alterar só um mês.\n"
             "• Realizado: preencha as células de fundo vermelho-claro de cada mês (volumes e valores). Taxas, custos unitários, acumulados, resultado e ROI do realizado saem por fórmula "
             "e ficam em branco até o mês ter dado. Parâmetros de negócio do realizado (comissão, margem) puxam o projetado (vermelho mais claro) e podem ser sobrescritos. "
             "Preencha os meses em ordem para os acumulados fecharem.")

# ===================================================================== INSIDE SALES
def is_kpis(ctx):
    pb = kpi_payback_cards(ctx, cum_key='cum_cons')
    return [
      (f"RECEITA DA AGÊNCIA · {ctx.n} MESES", f"={ctx.tot('receita_cons')}", FMT_BRL, "realizado onde existe, projetado à frente"),
      (f"GMV GERADO · {ctx.n} MESES", f"={ctx.tot('gmv')}", FMT_BRL, "vendas × ticket médio"),
      (f"VENDAS · {ctx.n} MESES", f"={ctx.tot('vendas')}", FMT_INT, "vendas equivalentes"),
      (f"CUSTO TOTAL · {ctx.n} MESES", f"={ctx.tot('custo_cons')}", FMT_BRL, "fee + mídia"),
      (f"RESULTADO LÍQUIDO · {ctx.n} MESES", f"={ctx.tot('resultado_cons')}", FMT_BRL, "resultado MC − custos"),
      ("ROI DO PROJETO", f"=IFERROR({ctx.tot('resultado_cons')}/{ctx.tot('custo_cons')},0)", FMT_PCT1, "acumulado no período"),
      pb['azul'], pb['payback'], pb['exposicao'], pb['excedente'],
    ]

FMT_DEC = '#,##0.0'


def _simplificar_is(cfg, p):
    """Tira do inside sales as linhas que o cliente não tem. sem_lp: leads de formulário nativo ou planilha sem landing page
    (connect e visitas seriam 100% e zero, de enfeite). sem_conexao: a fonte não tem a linha Conexões.
    conexao_so_lead: a linha Conexões conta só leads conectados (loja de multimídia); MQLs conectados não são medidos."""
    tira, troca_ = set(), {}
    if p.get('verba_plano'):
        tira |= {'cresc', 'teto'}
        troca_['midia'] = dict(kind='input', src=Ln(p['verba_plano'], int(p.get('n_months', 12))))
    if float(p['prem'].get('margem', 0)) >= 0.999 and float(p['prem'].get('comissao', 1)) < 0.999:
        # a comissão já é a margem da agência (agência de viagens: 20% do valor vendido): a linha de margem 100% seria enfeite
        tira |= {'margem'}
        troca_['comissao'] = dict(label="COMISSÃO SOBRE O GMV (MARGEM DA AGÊNCIA)")
        troca_['mc'] = dict(label="RESULTADO MC (= RECEITA DA AGÊNCIA)", src="={c}{receita}", real="{c}{receita}")
        troca_['roas_be'] = dict(label="ROAS DE BREAKEVEN ((FEE + MÍDIA) ÷ MÍDIA)", src="=IFERROR(({c}{fee}+{c}{midia})/{c}{midia},0)")
        cfg['meta'] = lambda ctx, m: meta_block(ctx, m, p['target'], 'gmv', 'ticket', 'vendas', 'custo_cons', 'cum_cons', None, comissao_key='comissao', acum0_key='acum0')
        cfg['premises'] = [(k, "Comissão sobre o GMV (margem da agência)", v, f) if k == 'comissao' else (k, lab, v, f) for k, lab, v, f in cfg['premises']]
    if float(p['prem'].get('comissao', 1)) >= 0.999 and not p.get('crm'):
        # receita própria do cliente (consultoria, varejo de revestimentos, loja de multimídia): sem comissão nem GMV de agência; o faturamento (vendas × ticket) já é a receita
        tira |= {'comissao', 'receita'}
        troca_['gmv'] = dict(label="FATURAMENTO (VENDAS × TICKET)")
        troca_['margem'] = dict(tot='div:mc/gmv')
        troca_['mc'] = dict(label="RESULTADO MC (FATURAMENTO × MARGEM)", src="={c}{gmv}*{c}{margem}", real="{c}{gmv}*{c}{margem}")
        troca_['receita_cons'] = dict(label="FATURAMENTO CONSOLIDADO", src="=IF({HAS}=0,{c}{gmv},{r}{gmv})")
        troca_['roas'] = dict(label="ROAS (FATURAMENTO ÷ MÍDIA)", src="=IFERROR({c}{gmv}/{c}{midia},0)", tot='div:gmv/midia', real="{c}{gmv}/{c}{midia}")
        troca_['cresc_receita'] = dict(label="CRESCIMENTO DO FATURAMENTO (MÊS ANTERIOR)")
        cfg['meta'] = lambda ctx, m: meta_block(ctx, m, p['target'], 'gmv', 'ticket', 'vendas', 'custo_cons', 'cum_cons', 'margem', acum0_key='acum0')
        cfg['kpis'] = lambda ctx: [(k[0].replace("RECEITA DA AGÊNCIA", "FATURAMENTO"),) + tuple(k[1:]) for k in is_kpis(ctx) if not k[0].startswith("GMV")]
        cfg['charts'] = [dict(ch, title="Faturamento e crescimento mês a mês") if ch.get('type') == 'growth' else ch for ch in cfg['charts']]
    if p.get('sem_lp'):
        tira |= {'connect', 'visitas_pagas', 'custo_visita', 'organicas', 'visitas_lp'}
        troca_['conv_lp'] = dict(label="CLIQUE → LEAD", tot='div:leads/cliques', real="{c}{leads}/{c}{cliques}")
        troca_['leads'] = dict(src="={c}{cliques}*{c}{conv_lp}")
        troca_['visita_venda'] = dict(label="CLIQUE → VENDA", src="=IFERROR({c}{vendas}/{c}{cliques},0)", tot='div:vendas/cliques', real="{c}{vendas}/{c}{cliques}")
        cfg['funnel'] = [("Cliques", 'cliques')] + [f for f in cfg['funnel'] if f[1] != 'visitas_lp']
    if p.get('sem_conexao') or p.get('conexao_so_lead'):
        # conexão não medida: as linhas ficam (o usuário acompanha leads e MQLs conectados), mas sem taxa inventada.
        # A conexão fica em branco para preencher; enquanto estiver vazia, a linha é informativa e o funil segue MQL → SQL.
        # sem_conexao: nenhuma das duas é medida; conexao_so_lead: a conexão lead vem da fonte e só a de MQL fica em branco.
        brancas = ('con_lead', 'con_mql') if p.get('sem_conexao') else ('con_mql',)
        for k in brancas:
            f = f'=IF({{P_{k}}}="","",{{P_{k}}})'
            troca_[k] = dict(kind='linkf', src=(f, f))
        if 'con_lead' in brancas:
            troca_['leads_con'] = dict(src='=IF({P_con_lead}="","",{c}{leads}*{c}{con_lead})')
            troca_['custo_con_lead'] = dict(src='=IFERROR({c}{midia}/{c}{leads_con},"")')
        troca_['mql_con'] = dict(src='=IF({P_con_mql}="","",{c}{mqls}*{c}{con_mql})')
        troca_['custo_con_mql'] = dict(src='=IFERROR({c}{midia}/{c}{mql_con},"")')
        troca_['mql_sql'] = dict(label="MQL → SQL", tot='div:sqls/mqls', real="{c}{sqls}/{c}{mqls}")
        troca_['sqls'] = dict(src="={c}{mqls}*{c}{mql_sql}")
        rot_branca = {"con_lead": "Conexão lead (preencha quando medir)", "con_mql": "Conexão MQL (preencha quando medir)"}
        cfg['premises'] = [(k, rot_branca[k], None, f) if k in brancas else (k, lab, v, f) for k, lab, v, f in cfg['premises']]
    if p.get('con_lead_mensal') and not p.get('sem_conexao'):   # conexão com alvo de mercado: sobe mês a mês junto com lead → MQL
        troca_['con_lead'] = dict(kind='input', src=Ln(p['con_lead_mensal'], int(p.get('n_months', 12))))
        cfg['premises'] = [x for x in cfg['premises'] if x[0] != 'con_lead']
    if p.get('fee_plano'):   # fee mês a mês (ex.: sobe quando o CRM entra no fee)
        troca_['fee'] = dict(kind='input', src=Ln(p['fee_plano'], int(p.get('n_months', 12))))
        cfg['premises'] = [(k, "Fee mensal V4 (Mês 1; os demais meses estão na tabela)", v, f) if k == 'fee' else (k, lab, v, f) for k, lab, v, f in cfg['premises']]
    crm = p.get('crm')
    if crm:
        tx, b = crm['taxas'], crm['base']
        troca_.setdefault('gmv', {})['label'] = "[1] GMV · NOVOS LEADS (VENDAS × TICKET)"
        troca_['receita'] = dict(src="={c}{gmv_total}*{c}{comissao}", real="{c}{gmv_total}*{c}{comissao}")
        i = next(j for j, x in enumerate(cfg['premises']) if x[0] == 'lag')
        cfg['premises'][i:i] = [
          ("ticket_crm", "CRM · ticket da recompra e reativação (R$)", crm['ticket'], FMT_BRL),
          ("tx_rec", "CRM · recompra por mês, clientes de 6 a 12 meses", tx['recompra'], FMT_PCT2),
          ("tx_rec2", "CRM · recompra por mês, clientes recorrentes", tx['recompra_recorrentes'], FMT_PCT2),
          ("tx_cross", "CRM · cross-sell por campanha, clientes com menos de 6 meses", tx['cross_sell'], FMT_PCT2),
          ("n_cross", "CRM · campanhas de cross-sell por mês", tx['campanhas_cross_sell'], '0'),
          ("tx_email", "CRM · conversão por e-mail, leads sem compra", tx['email'], FMT_PCT2),
          ("n_email", "CRM · e-mails por mês para leads", tx['emails'], '0'),
          ("desc", "CRM · descadastro por e-mail (sai da base)", tx.get('descadastro', 0), FMT_PCT2),
          ("tx_reat", "CRM · reativação por campanha, inativos há mais de 12 meses", tx['reativacao'], FMT_PCT2),
          ("n_reat", "CRM · campanhas de reativação por mês", tx['campanhas_reativacao'], '0'),
          ("base_leads0", "CRM · leads sem compra na base (início do Mês 1)", b.get('leads_sem_compra'), FMT_INT),
          ("base_recentes0", "CRM · clientes históricos com menos de 6 meses (preencha)", b.get('recentes'), FMT_INT),
          ("base_ativos0", "CRM · clientes históricos de 6 a 12 meses (preencha)", b.get('ativos'), FMT_INT),
          ("base_inativos0", "CRM · clientes históricos inativos (preencha)", b.get('inativos'), FMT_INT),
          ("base_recorrentes", "CRM · clientes recorrentes (preencha)", b.get('recorrentes'), FMT_INT),
        ]
        orig_kpis = cfg['kpis']
        cfg['kpis'] = lambda ctx: [(f"GMV TOTAL · {ctx.n} MESES", f"={ctx.tot('gmv_total')}", x[2], "novos + recompra + reativação")
                                   if x[0].startswith("GMV GERADO") else x for x in orig_kpis(ctx)]
        cfg['charts'] = cfg['charts'] + [dict(type='line', title="Faturamento (GMV) por origem: novos leads, recompra e reativação",
                                              series=[('gmv', RED, False), ('gmv_recompra', GREEN, False), ('gmv_reativ', GRAY, False)], y_fmt=FMT_BRL)]
    org = p.get('organico')
    if org:
        # SEO: visitas orgânicas × conversão viram leads; o funil corre sobre os leads totais (pagos + orgânicos)
        troca_.setdefault('leads', {})['label'] = "LEADS PAGOS"   # mescla: sem LP, a fórmula de leads já foi trocada para cliques
        troca_['mqls'] = dict(src="={c}{leads_total}*{c}{lead_mql}")
        troca_['lead_mql'] = dict(tot='div:mqls/leads_total', real="{c}{mqls}/{c}{leads_total}")
        troca_['conv_funil'] = dict(label="CONV. FUNIL (LEAD TOTAL → VENDA)", src="=IFERROR({c}{vendas}/{c}{leads_total},0)",
                                    tot='div:vendas/leads_total', real="{c}{vendas}/{c}{leads_total}")
        troca_.setdefault('leads_con', {})['src'] = ('=IF({P_con_lead}="","",{c}{leads_total}*{c}{con_lead})' if p.get('sem_conexao')
                                                    else "={c}{leads_total}*{c}{con_lead}")
        troca_.setdefault('con_lead', {})['real'] = "{c}{leads_con}/{c}{leads_total}"
        cfg['funnel'] = [("Leads totais", 'leads_total') if f[1] == 'leads' else f for f in cfg['funnel']]
        i = next(j for j, x in enumerate(cfg['premises']) if x[0] == 'lag')
        cfg['premises'].insert(i, ("conv_seo", "Conversão visita orgânica → lead (SEO)", org['conversao'], FMT_PCT2))
    if not tira and not troca_:
        return cfg
    cfg['premises'] = [x for x in cfg['premises'] if x[0] not in tira]
    mets = []
    for m in cfg['metrics']:
        if m[0] == 'sec':
            mets.append(m); continue
        if m[0] in tira: continue
        t = troca_.get(m[0])
        if t:
            key, label, kind, src, fmt, tot, real = m
            m = (key, t.get('label', label), t.get('kind', kind), t.get('src', src), fmt, t.get('tot', tot), t.get('real', real))
        mets.append(m)
    if crm:
        n_ = int(p.get('n_months', 12)); proj = grade_colunas(n_)[0]
        lk = 'leads_total' if org else 'leads'
        blank = lambda k: f'IF({{P_{k}}}="",0,{{P_{k}}})'
        def coorte(k, lo, hi, hist):   # clientes com idade entre lo e hi meses no mês k (coortes da projeção + compras de antes do Mês 1)
            termos = [f"{proj[j]}{{novos_clientes}}" for j in range(k) if lo <= k - j <= hi]
            termos += [str(n_c) for idade, n_c in crm.get('coortes_pre', []) if lo <= idade + k <= hi]
            return "=" + "+".join(termos + [blank(hist)])
        base_f = ["={P_base_leads0}"] + [f"=MAX(0,{proj[k-1]}{{base_leads}}*(1-{{P_desc}}*{{P_n_email}})+{proj[k-1]}{{leads_cons}}-{proj[k-1]}{{vendas_cons}}-{proj[k-1]}{{v_email}})" for k in range(1, n_)]
        inicio = int(crm['inicio'])
        bloco = [
          ('sec', "CRM · RECOMPRA E REATIVAÇÃO DA BASE"),
          ('crm_on', "CRM ATIVO NO MÊS?  (1 = SIM)", 'input', [0 if k + 1 < inicio else 1 for k in range(n_)], '0', 'sum', '""'),
          ('leads_cons', "LEADS NOVOS NO MÊS (REALIZADO ONDE EXISTE)", 'calc', "=IF({HAS}=0,{c}{" + lk + "},{r}{" + lk + "})", FMT_INT, 'sum', '""'),
          ('vendas_cons', "VENDAS DE NOVOS LEADS (REALIZADO ONDE EXISTE)", 'calc', "=IF({HAS}=0,{c}{vendas},{r}{vendas})", FMT_INT, 'sum', '""'),
          ('base_leads', "LEADS SEM COMPRA NA BASE (INÍCIO DO MÊS)", 'mixed', base_f, FMT_INT, 'last', '""'),
          ('cli_recentes', "CLIENTES COM MENOS DE 6 MESES", 'mixed', [coorte(k, 1, 5, 'base_recentes0') for k in range(n_)], FMT_INT, 'last', '""'),
          ('cli_ativos', "CLIENTES DE 6 A 12 MESES", 'mixed', [coorte(k, 6, 12, 'base_ativos0') for k in range(n_)], FMT_INT, 'last', '""'),
          ('cli_inativos', "CLIENTES INATIVOS (MAIS DE 12 MESES)", 'mixed', [coorte(k, 13, 10 ** 6, 'base_inativos0') for k in range(n_)], FMT_INT, 'last', '""'),
          ('v_whats', "VENDAS · WHATSAPP (RECOMPRA DE CLIENTES)", 'calc', "={c}{crm_on}*({c}{cli_ativos}*{P_tx_rec}+" + blank('base_recorrentes') + "*{P_tx_rec2})", FMT_DEC, 'sum', 'in'),
          ('v_cross', "VENDAS · CROSS-SELL E NOVAS VIAGENS", 'calc', "={c}{crm_on}*{c}{cli_recentes}*{P_tx_cross}*{P_n_cross}", FMT_DEC, 'sum', 'in'),
          ('v_email', "VENDAS · E-MAIL (LEADS SEM COMPRA)", 'calc', "={c}{crm_on}*{c}{base_leads}*{P_tx_email}*{P_n_email}", FMT_DEC, 'sum', 'in'),
          ('v_reat', "VENDAS · CAMPANHAS DE REATIVAÇÃO (INATIVOS)", 'calc', "={c}{crm_on}*{c}{cli_inativos}*{P_tx_reat}*{P_n_reat}", FMT_DEC, 'sum', 'in'),
          ('novos_clientes', "NOVOS CLIENTES NO MÊS (NOVOS LEADS + E-MAIL)", 'calc', "={c}{vendas_cons}+{c}{v_email}", FMT_DEC, 'sum', '""'),
          ('gmv_recompra', "[2] GMV · RECOMPRA DA BASE (WHATSAPP + CROSS-SELL)", 'calc', "=({c}{v_whats}+{c}{v_cross})*{P_ticket_crm}", FMT_BRL, 'sum', "({c}{v_whats}+{c}{v_cross})*{P_ticket_crm}"),
          ('gmv_reativ', "[3] GMV · REATIVAÇÃO (E-MAIL PARA LEADS + INATIVOS)", 'calc', "=({c}{v_email}+{c}{v_reat})*{P_ticket_crm}", FMT_BRL, 'sum', "({c}{v_email}+{c}{v_reat})*{P_ticket_crm}"),
          ('gmv_total', "GMV TOTAL (NOVOS + RECOMPRA + REATIVAÇÃO)", 'calc', "={c}{gmv}+{c}{gmv_recompra}+{c}{gmv_reativ}", FMT_BRL, 'sum', "{c}{gmv}+{c}{gmv_recompra}+{c}{gmv_reativ}"),
        ]
        j = next(k for k, m in enumerate(mets) if m[0] == 'gmv') + 1
        mets[j:j] = bloco
    if org:
        n_ = int(p.get('n_months', 12)); j = next(k for k, m in enumerate(mets) if m[0] == 'leads') + 1
        mets[j:j] = [
          ('visitas_seo', "VISITAS ORGÂNICAS (SEO)", 'input', Ln(org['visitas'], n_), FMT_INT, 'sum', 'in'),
          ('conv_seo', "VISITA ORGÂNICA → LEAD", 'link', 'conv_seo', FMT_PCT2, 'div:leads_seo/visitas_seo', "{c}{leads_seo}/{c}{visitas_seo}"),
          ('leads_seo', "LEADS ORGÂNICOS (SEO)", 'calc', "={c}{visitas_seo}*{c}{conv_seo}", FMT_INT, 'sum', 'in'),
          ('leads_total', "LEADS TOTAIS (PAGOS + ORGÂNICOS)", 'calc', "={c}{leads}+{c}{leads_seo}", FMT_INT, 'sum', "{c}{leads}+{c}{leads_seo}"),
        ]
    cfg['metrics'] = mets
    return cfg


def inside_sales_config(p):
    pr, mo = p['prem'], p['monthly']; n = int(p.get('n_months', 12))
    cfg = dict(
      sheet=p['sheet'], title=p['title'], subtitle=p['subtitle'], meta_line=p['meta_line'], footer=p['footer'],
      n_months=n,
      premises=[("fee", "Fee mensal V4 (R$)", pr['fee'], FMT_BRL), ("midia", "Mídia mensal (R$)", pr['midia'], FMT_BRL),
                ("comissao", "Comissão sobre o GMV", pr['comissao'], FMT_PCT1), ("margem", "Margem de contribuição", pr['margem'], FMT_PCT0),
                ("connect", "Connect rate (clique → visita)", pr['connect'], FMT_PCT0), ("organicas", "Visitas orgânicas por mês", pr['organicas'], FMT_INT),
                ("con_lead", "Conexão Lead", pr['con_lead'], FMT_PCT0), ("con_mql", "Conexão MQL", pr['con_mql'], FMT_PCT0),
                ("cresc", "Crescimento mensal da verba de mídia", pr.get('cresc', 0.0), FMT_PCT1),
                ("teto", "Teto da verba mensal (0 = sem teto)", pr.get('teto', 0) or 0, FMT_BRL),
                ("lag", "Lag comercial (fração das vendas no mês do lead)", pr['lag'], FMT_PCT0),
                ("acum0", "Acumulado inicial (déficit já existente, negativo)", pr['acum0'], FMT_BRL), ("dias", "Dias do mês (budget médio/dia)", pr['dias'], '0')],
      budget_day=('midia', 'dias'), acum0_key='acum0',
      metrics=[
        ('sec', "MARKETING · ATÉ O MQL"),
        ('fee', "FEE V4", 'link', 'fee', FMT_BRL, 'sum', 'in'),
        ('midia', "MÍDIA", 'linkf', ("={P_midia}", "=MIN({p}{midia}*(1+{P_cresc}),IF({P_teto}>0,{P_teto},{p}{midia}*(1+{P_cresc})))"), FMT_BRL, 'sum', 'in'),
        ('custo', "CUSTO TOTAL (FEE V4 + MÍDIA)", 'calc', "={c}{fee}+{c}{midia}", FMT_BRL, 'sum', "{c}{fee}+{c}{midia}"),
        ('cpm', "CPM", 'input', Ln(mo['cpm'], n), FMT_BRL2, 'div1000:midia/impress', "{c}{midia}/{c}{impress}*1000"),
        ('impress', "IMPRESSÕES", 'calc', "=IFERROR({c}{midia}/{c}{cpm}*1000,0)", FMT_INT, 'sum', 'in'),
        ('ctr', "CTR", 'input', Ln(mo['ctr'], n), FMT_PCT2, 'div:cliques/impress', "{c}{cliques}/{c}{impress}"),
        ('cliques', "CLIQUES", 'calc', "={c}{impress}*{c}{ctr}", FMT_INT, 'sum', 'in'),
        ('cpc', "CPC", 'calc', "=IFERROR({c}{midia}/{c}{cliques},0)", FMT_BRL2, 'div:midia/cliques', "{c}{midia}/{c}{cliques}"),
        ('connect', "CONNECT RATE", 'link', 'connect', FMT_PCT0, 'div:visitas_pagas/cliques', "{c}{visitas_pagas}/{c}{cliques}"),
        ('visitas_pagas', "VISITAS PAGAS", 'calc', "={c}{cliques}*{c}{connect}", FMT_INT, 'sum', 'in'),
        ('custo_visita', "CUSTO / VISITA", 'calc', "=IFERROR({c}{midia}/{c}{visitas_pagas},0)", FMT_BRL2, 'div:midia/visitas_pagas', "{c}{midia}/{c}{visitas_pagas}"),
        ('organicas', "VISITAS ORGÂNICAS", 'link', 'organicas', FMT_INT, 'sum', 'in'),
        ('visitas_lp', "VISITAS LP", 'calc', "={c}{visitas_pagas}+{c}{organicas}", FMT_INT, 'sum', "{c}{visitas_pagas}+{c}{organicas}"),
        ('conv_lp', "CONV. LP", 'input', Ln(mo['conv_lp'], n), FMT_PCT2, 'div:leads/visitas_lp', "{c}{leads}/{c}{visitas_lp}"),
        ('leads', "LEADS", 'calc', "={c}{visitas_lp}*{c}{conv_lp}", FMT_INT, 'sum', 'in'),
        ('cpl', "CPL", 'calc', "=IFERROR({c}{midia}/{c}{leads},0)", FMT_BRL2, 'div:midia/leads', "{c}{midia}/{c}{leads}"),
        ('lead_mql', "LEAD → MQL", 'input', Ln(mo['lead_mql'], n), FMT_PCT2, 'div:mqls/leads', "{c}{mqls}/{c}{leads}"),
        ('mqls', "MQLS", 'calc', "={c}{leads}*{c}{lead_mql}", FMT_INT, 'sum', 'in'),
        ('custo_mql', "CUSTO / MQL", 'calc', "=IFERROR({c}{midia}/{c}{mqls},0)", FMT_BRL2, 'div:midia/mqls', "{c}{midia}/{c}{mqls}"),
        ('sec', "VENDAS · DA CONEXÃO À RECEITA"),
        ('con_lead', "CONEXÃO LEAD", 'link', 'con_lead', FMT_PCT0, 'div:leads_con/leads', "{c}{leads_con}/{c}{leads}"),
        ('leads_con', "LEADS CONECTADOS", 'calc', "={c}{leads}*{c}{con_lead}", FMT_INT, 'sum', 'in'),
        ('custo_con_lead', "CUSTO / CONEXÃO LEAD", 'calc', "=IFERROR({c}{midia}/{c}{leads_con},0)", FMT_BRL2, 'div:midia/leads_con', "{c}{midia}/{c}{leads_con}"),
        ('con_mql', "CONEXÃO MQL", 'link', 'con_mql', FMT_PCT0, 'div:mql_con/mqls', "{c}{mql_con}/{c}{mqls}"),
        ('mql_con', "MQL CONECTADOS", 'calc', "={c}{mqls}*{c}{con_mql}", FMT_INT, 'sum', 'in'),
        ('custo_con_mql', "CUSTO / CONEXÃO MQL", 'calc', "=IFERROR({c}{midia}/{c}{mql_con},0)", FMT_BRL2, 'div:midia/mql_con', "{c}{midia}/{c}{mql_con}"),
        ('mql_sql', "MQL CON. → SQL", 'input', Ln(mo['mql_sql'], n), FMT_PCT2, 'div:sqls/mql_con', "{c}{sqls}/{c}{mql_con}"),
        ('sqls', "SQLS", 'calc', "={c}{mql_con}*{c}{mql_sql}", FMT_INT, 'sum', 'in'),
        ('custo_sql', "CUSTO / SQL", 'calc', "=IFERROR({c}{midia}/{c}{sqls},0)", FMT_BRL2, 'div:midia/sqls', "{c}{midia}/{c}{sqls}"),
        ('sql_venda', "SQL → VENDA", 'input', Ln(mo['sql_venda'], n), FMT_PCT2, 'div:vendas/sqls', "{c}{vendas}/{c}{sqls}"),
        ('vendas_ger', "VENDAS GERADAS NO MÊS (ANTES DO LAG)", 'calc', "={c}{sqls}*{c}{sql_venda}", FMT_INT, 'sum', '""'),
        ('vendas', "VENDAS", 'calcf', ("={c}{vendas_ger}*{P_lag}", "={c}{vendas_ger}*{P_lag}+{p}{vendas_ger}*(1-{P_lag})"), FMT_INT, 'sum', 'in'),
        ('custo_venda', "CUSTO / VENDA", 'calc', "=IFERROR({c}{midia}/{c}{vendas},0)", FMT_BRL2, 'div:midia/vendas', "{c}{midia}/{c}{vendas}"),
        ('conv_funil', "CONV. FUNIL (LEAD → VENDA)", 'calc', "=IFERROR({c}{vendas}/{c}{leads},0)", FMT_PCT1, 'div:vendas/leads', "{c}{vendas}/{c}{leads}"),
        ('visita_venda', "VISITA → VENDA", 'calc', "=IFERROR({c}{vendas}/{c}{visitas_lp},0)", FMT_PCT1, 'div:vendas/visitas_lp', "{c}{vendas}/{c}{visitas_lp}"),
        ('ticket', "TICKET MÉDIO", 'input', Ln(mo['ticket'], n), FMT_BRL2, 'div:gmv/vendas', "{c}{gmv}/{c}{vendas}"),
        ('gmv', "GMV (VENDAS × TICKET)", 'calc', "={c}{vendas}*{c}{ticket}", FMT_BRL, 'sum', 'in'),
        ('comissao', "COMISSÃO SOBRE O GMV", 'link', 'comissao', FMT_PCT1, 'div:receita/gmv', 'proj'),
        ('receita', "RECEITA DA AGÊNCIA (GMV × COMISSÃO)", 'calc', "={c}{gmv}*{c}{comissao}", FMT_BRL, 'sum', "{c}{gmv}*{c}{comissao}"),
        ('margem', "MARGEM DE CONTRIBUIÇÃO", 'link', 'margem', FMT_PCT0, 'div:mc/receita', 'proj'),
        ('sec', "FINANCEIRO · RESULTADO E PAYBACK"),
        ('mc', "RESULTADO MC (RECEITA × MARGEM)", 'calc', "={c}{receita}*{c}{margem}", FMT_BRL, 'sum', "{c}{receita}*{c}{margem}"),
        ('roas', "ROAS (RECEITA ÷ MÍDIA)", 'calc', "=IFERROR({c}{receita}/{c}{midia},0)", FMT_X, 'div:receita/midia', "{c}{receita}/{c}{midia}"),
        ('roas_be', "ROAS DE BREAKEVEN ((FEE + MÍDIA) ÷ MÍDIA ÷ MARGEM)", 'calc', "=IFERROR(({c}{fee}+{c}{midia})/({c}{midia}*{c}{margem}),0)", FMT_X, 'avg', '""'),
        ('mc_midia', "RETORNO DOS ANÚNCIOS APÓS A MARGEM (MC − MÍDIA)", 'calc', "={c}{mc}-{c}{midia}", FMT_BRL, 'sum', "{c}{mc}-{c}{midia}"),
        ('roi_midia', "ROI DA MÍDIA APÓS A MARGEM ((MC − MÍDIA) ÷ MÍDIA)", 'calc', "=IFERROR({c}{mc_midia}/{c}{midia},0)", FMT_PCT1, 'div:mc_midia/midia', "{c}{mc_midia}/{c}{midia}"),
        ('custo_acum', "CUSTO ACUMULADO (FEE + MÍDIA)", 'cum', 'custo', FMT_BRL, 'last', 'cum'),
        ('resultado', "RESULTADO LÍQUIDO (DEPOIS DO FEE V4)", 'calc', "={c}{mc}-{c}{custo}", FMT_BRL, 'sum', "{c}{mc}-{c}{custo}"),
        ('roi_mes', "ROI DO MÊS", 'calc', "=IFERROR({c}{resultado}/{c}{custo},0)", FMT_PCT1, 'div:resultado/custo', "{c}{resultado}/{c}{custo}"),
        ('cum', "RESULTADO ACUMULADO (PROJETADO)", 'cum', 'resultado', FMT_BRL, 'last', 'cum'),
        ('sec', "RESULTADO · REALIZADO ONDE EXISTE, PROJETADO À FRENTE"),
        ('receita_cons', "RECEITA CONSOLIDADA", 'calc', "=IF({HAS}=0,{c}{receita},{r}{receita})", FMT_BRL, 'sum', '""'),
        ('custo_cons', "CUSTO CONSOLIDADO (FEE + MÍDIA)", 'calc', "=IF({HAS}=0,{c}{custo},{r}{custo})", FMT_BRL, 'sum', '""'),
        ('mc_cons', "RESULTADO MC CONSOLIDADO", 'calc', "=IF({HAS}=0,{c}{mc},{r}{mc})", FMT_BRL, 'sum', '""'),
        ('resultado_cons', "RESULTADO LÍQUIDO DO MÊS", 'calc', "={c}{mc_cons}-{c}{custo_cons}", FMT_BRL, 'sum', '""'),
        ('cum_cons', "RESULTADO ACUMULADO", 'cum', 'resultado_cons', FMT_BRL, 'last', '""'),
        ('cresc_receita', "CRESCIMENTO DA RECEITA (MÊS ANTERIOR)", 'calcf', ('=""', '=IFERROR({c}{receita_cons}/{p}{receita_cons}-1,"")'), FMT_PCT1, 'avg', '""'),
        ('custo_acum_cons', "CUSTO ACUMULADO", 'cum', 'custo_cons', FMT_BRL, 'last', '""'),
        ('roi_projeto', "ROI DO PROJETO (ACUMULADO)", 'calc', "=IFERROR({c}{cum_cons}/{c}{custo_acum_cons},0)", FMT_PCT1, 'last', '""'),
        ('flag', "ACUMULADO ≥ 0?  (1 = SIM)", 'calc', "=IF({c}{cum_cons}>=0,1,0)", '0', 'sum', '""'),
        ('flag_mes', "MÊS NO AZUL?  (1 = SIM)", 'calc', "=IF({c}{resultado_cons}>=0,1,0)", '0', 'sum', '""'),
        ('flag_cont', "NO AZUL DAQUI ATÉ O FIM?  (1 = SIM)", 'calc', "=IF(COUNTIF({c}{flag_mes}:{L}{flag_mes},0)=0,1,0)", '0', 'sum', '""'),
      ],
      bold_rows={'resultado_cons', 'cum_cons', 'receita', 'receita_cons', 'gmv'}, espelho=['resultado_cons', 'receita_cons', 'cum_cons'],
      signed_rows=['resultado', 'roi_mes', 'cum', 'resultado_cons', 'cum_cons', 'roi_projeto', 'cresc_receita', 'mc_midia', 'roi_midia'], cum_key='cum_cons',
      kpis=is_kpis,
      meta=lambda ctx, m: meta_block(ctx, m, p['target'], 'gmv', 'ticket', 'vendas', 'custo_cons', 'cum_cons', 'margem', comissao_key='comissao', acum0_key='acum0'),
      metodologia=p.get('metodologia'), metodologia_fim=p.get('metodologia_fim'), historico=p.get('historico'), pilot_ref=p.get('pilot_ref'),
      real_prefill=p.get('real_prefill'), month_labels=p.get('month_labels'), envelope=p.get('envelope'), base_ref=p.get('base_ref'),
      charts=[
        dict(type='growth', title="Receita e crescimento mês a mês", bars='receita_cons', line='cresc_receita'),
        dict(type='line', title="Resultado acumulado mês a mês", series=[('cum_cons', GREEN, False)], y_fmt=FMT_BRL),
        dict(type='payback', title="Curva de payback"),
        dict(type='funnel', title="Funil de conversão · acumulado no período"),
      ],
      funnel=[("Visitas LP", 'visitas_lp'), ("Leads", 'leads'), ("MQLs", 'mqls'), ("SQLs", 'sqls'), ("Vendas", 'vendas')],
    )
    return _simplificar_is(cfg, p)

# ===================================================================== E-COMMERCE
def ecommerce_config(p):
    """Flags: usa_margem (aplica margem no resultado), usa_venda (separa pedido de venda), share (participação da mídia no faturamento),
    margem_info (margem só informativa)."""
    pr = p['prem']; mo = p.get('monthly') or {}; n = int(p.get('n_months', 12))
    usa_margem = bool(p.get('usa_margem')); usa_venda = bool(p.get('usa_venda', True)); share = bool(p.get('share'))
    margem_info = p.get('margem_info')
    # funil_pago: as taxas do piloto são do tráfego pago, então o funil corre sobre as sessões pagas e as não pagas ficam só como
    # contexto do total do site. split: o GA4 separou Google (funil por CPM, CTR e connect) e Meta (verba ÷ custo por sessão).
    funil_pago, split = bool(p.get('funil_pago')), p.get('split')
    base_ses = 'sessoes_pago' if funil_pago else 'sessoes_total'
    rotulo_org = p.get('rotulo_org') or "[QNTD] SESSÕES - ORGÂNICO"
    rec = 'receita_fat' if usa_venda else 'receita_captada'
    vol = 'vendas' if usa_venda else 'pedidos'
    def lever(key, label, fmt, tot, real):
        return (key, label, 'input', Ln(mo[key], n), fmt, tot, real) if key in mo else (key, label, 'link', key, fmt, tot, real)

    prem = [("fee", "Fee mensal V4 (R$)", pr['fee'], FMT_BRL), ("midia1", "Verba de mídia — Mês 1 (R$)", pr['midia1'], FMT_BRL),
            ("cresc", "Crescimento mensal da verba de mídia", pr['cresc'], FMT_PCT1),
            ("teto", "Teto da verba mensal (0 = sem teto)", pr.get('teto', 0) or 0, FMT_BRL)]
    if split: prem += [("share_meta", "Participação do Meta na verba", split['share'], FMT_PCT1)]
    g = " do Google" if split else ""
    prem += [x for x in [("cpm", f"CPM{g} (R$)", pr['cpm'], FMT_BRL2), ("ctr", f"CTR{g}", pr['ctr'], FMT_PCT2),
                         ("connect", f"Connect rate{g} (clique → sessão)", pr['connect'], FMT_PCT0)] if x[0] not in mo]
    if split: prem += [x for x in [("cps_meta", "Custo por sessão Meta (R$)", split['cps'], FMT_BRL2)] if x[0] not in mo]
    rot_org_prem = "Sessões não pagas por mês" if 'NÃO PAGAS' in rotulo_org else "Sessões orgânicas por mês"
    prem += [("organicas", rot_org_prem, pr['organicas'], FMT_INT),
             ("s_vi", "Sessão paga → View Item" if funil_pago else "Sessão → View Item", pr['s_vi'], FMT_PCT0)]
    prem += [x for x in [("vi_cart", "View Item → adição ao carrinho", pr['vi_cart'], FMT_PCT0),
                         ("cart_ic", "Carrinho → Initiate Checkout", pr['cart_ic'], FMT_PCT0),
                         ("ic_ped", "Initiate Checkout → pedidos", pr['ic_ped'], FMT_PCT0),
                         ("ticket_ped", "Ticket médio do pedido (R$)", pr['ticket_ped'], FMT_BRL2)] if x[0] not in mo]
    if usa_venda:
        prem += [("ped_venda", "Pedido → venda", pr['ped_venda'], FMT_PCT0)]
        prem += [x for x in [("ticket_fat", "Ticket médio faturado (R$)", pr['ticket_fat'], FMT_BRL2)] if x[0] not in mo]
    if usa_margem: prem += [("margem", p.get('margem_label', "Margem de contribuição"), pr['margem'], FMT_PCT1)]
    if margem_info is not None: prem += [("margem_info", "Margem de contribuição (informativa, fora do resultado)", margem_info, FMT_PCT1)]
    if share: prem += [("base_nao_midia", "Faturamento mensal fora da mídia V4 (base, R$)", pr['base_nao_midia'], FMT_BRL)]
    prem += [("lag", "Lag comercial (fração dos pedidos no mês do clique)", pr['lag'], FMT_PCT0),
             ("acum0", "Acumulado inicial (déficit já existente, negativo)", pr['acum0'], FMT_BRL),
             ("dias", "Dias do mês (budget médio/dia)", pr['dias'], '0')]

    mets = [
      ('sec', "INVESTIMENTO"),
      ('fee', "[R$] FEE MENSAL", 'link', 'fee', FMT_BRL, 'sum', 'in'),
      ('midia', "[R$] VERBA DE MÍDIA", 'linkf', ("={P_midia1}", "=IF({P_teto}>0,MIN({p}{midia}*(1+{P_cresc}),{P_teto}),{p}{midia}*(1+{P_cresc}))"), FMT_BRL, 'sum', 'in'),
      ('custo_mes', "[R$] CUSTO V4 + MÍDIA", 'calc', "={c}{fee}+{c}{midia}", FMT_BRL, 'sum', "{c}{fee}+{c}{midia}"),
    ]
    org_row = ('sessoes_org', rotulo_org, 'mixed', p.get('organicas_cells') or ["={P_organicas}"] * n, FMT_INT, 'sum', 'in')
    if split:
        mets += [
          ('share_meta', "[%] PARTICIPAÇÃO DO META NA VERBA", 'link', 'share_meta', FMT_PCT1, 'div:verba_meta/midia', "{c}{verba_meta}/{c}{midia}"),
          ('sec', "TRÁFEGO PAGO · GOOGLE"),
          ('verba_google', "[R$] VERBA GOOGLE", 'calc', "={c}{midia}*(1-{c}{share_meta})", FMT_BRL, 'sum', 'in'),
          lever('cpm', "[R$] CPM GOOGLE", FMT_BRL2, 'div1000:verba_google/impress', "{c}{verba_google}/{c}{impress}*1000"),
          ('impress', "[QNTD] IMPRESSÕES GOOGLE", 'calc', "=IFERROR({c}{verba_google}/{c}{cpm}*1000,0)", FMT_INT, 'sum', 'in'),
          lever('ctr', "[%] CTR GOOGLE", FMT_PCT2, 'div:cliques/impress', "{c}{cliques}/{c}{impress}"),
          ('cliques', "[QNTD] CLIQUES GOOGLE", 'calc', "={c}{impress}*{c}{ctr}", FMT_INT, 'sum', 'in'),
          ('cpc', "[R$] CPC GOOGLE", 'calc', "=IFERROR({c}{verba_google}/{c}{cliques},0)", FMT_BRL2, 'div:verba_google/cliques', "{c}{verba_google}/{c}{cliques}"),
          lever('connect', "[%] CONNECT RATE", FMT_PCT0, 'div:sessoes_google/cliques', "{c}{sessoes_google}/{c}{cliques}"),
          ('sessoes_google', "[QNTD] SESSÕES - GOOGLE", 'calc', "={c}{cliques}*{c}{connect}", FMT_INT, 'sum', 'in'),
          ('sec', "TRÁFEGO PAGO · META"),
          ('verba_meta', "[R$] VERBA META", 'calc', "={c}{midia}*{c}{share_meta}", FMT_BRL, 'sum', "{c}{midia}-{c}{verba_google}"),
          lever('cps_meta', "[R$] CUSTO POR SESSÃO META", FMT_BRL2, 'div:verba_meta/sessoes_meta', "{c}{verba_meta}/{c}{sessoes_meta}"),
          ('sessoes_meta', "[QNTD] SESSÕES - META", 'calc', "=IFERROR({c}{verba_meta}/{c}{cps_meta},0)", FMT_INT, 'sum', 'in'),
          ('sec', "SESSÕES DO SITE"),
          ('sessoes_pago', "[QNTD] SESSÕES PAGAS (GOOGLE + META)", 'calc', "={c}{sessoes_google}+{c}{sessoes_meta}", FMT_INT, 'sum', "{c}{sessoes_google}+{c}{sessoes_meta}"),
        ]
    else:
        mets += [
          ('sec', "TRÁFEGO PAGO"),
          lever('cpm', "[R$] CPM", FMT_BRL2, 'div1000:midia/impress', "{c}{midia}/{c}{impress}*1000"),
          ('impress', "[QNTD] IMPRESSÕES", 'calc', "=IFERROR({c}{midia}/{c}{cpm}*1000,0)", FMT_INT, 'sum', 'in'),
          lever('ctr', "[%] CTR", FMT_PCT2, 'div:cliques/impress', "{c}{cliques}/{c}{impress}"),
          ('cliques', "[QNTD] CLIQUES", 'calc', "={c}{impress}*{c}{ctr}", FMT_INT, 'sum', 'in'),
          ('cpc', "[R$] CPC", 'calc', "=IFERROR({c}{midia}/{c}{cliques},0)", FMT_BRL2, 'div:midia/cliques', "{c}{midia}/{c}{cliques}"),
          lever('connect', "[%] CONNECT RATE", FMT_PCT0, 'div:sessoes_pago/cliques', "{c}{sessoes_pago}/{c}{cliques}"),
          ('sessoes_pago', "[QNTD] SESSÕES - PAGO", 'calc', "={c}{cliques}*{c}{connect}", FMT_INT, 'sum', 'in'),
        ]
    mets += [
      org_row,
      ('sessoes_total', "[QNTD] SESSÕES - TOTAL DO SITE" if funil_pago else "[QNTD] SESSÕES - TOTAL", 'calc', "={c}{sessoes_pago}+{c}{sessoes_org}", FMT_INT, 'sum', "{c}{sessoes_pago}+{c}{sessoes_org}"),
      ('custo_sessao_geral', "[R$] CUSTO POR SESSÃO PAGA" if funil_pago else "[R$] CUSTO POR SESSÃO", 'calc', "=IFERROR({c}{midia}/{c}{" + base_ses + "},0)", FMT_BRL2, 'div:midia/' + base_ses, "{c}{midia}/{c}{" + base_ses + "}"),
      ('sec', "FUNIL E-COMMERCE · TRÁFEGO PAGO" if funil_pago else "FUNIL E-COMMERCE"),
      lever('s_vi', "[%] SESSÃO PAGA → VIEW ITEM" if funil_pago else "[%] SESSÃO → VIEW ITEM", FMT_PCT0, 'div:view_item/' + base_ses, "{c}{view_item}/{c}{" + base_ses + "}"),
      ('view_item', "[QNTD] VIEW ITEM", 'calc', "={c}{" + base_ses + "}*{c}{s_vi}", FMT_INT, 'sum', 'in'),
      ('custo_vi', "[R$] CUSTO POR VIEW ITEM", 'calc', "=IFERROR({c}{midia}/{c}{view_item},0)", FMT_BRL2, 'div:midia/view_item', "{c}{midia}/{c}{view_item}"),
      lever('vi_cart', "[%] VIEW ITEM → CARRINHO", FMT_PCT0, 'div:cart/view_item', "{c}{cart}/{c}{view_item}"),
      ('cart', "[QNTD] ADIÇÃO AO CARRINHO", 'calc', "={c}{view_item}*{c}{vi_cart}", FMT_INT, 'sum', 'in'),
      ('custo_cart', "[R$] CUSTO POR CARRINHO", 'calc', "=IFERROR({c}{midia}/{c}{cart},0)", FMT_BRL2, 'div:midia/cart', "{c}{midia}/{c}{cart}"),
      lever('cart_ic', "[%] CARRINHO → CHECKOUT", FMT_PCT0, 'div:ic/cart', "{c}{ic}/{c}{cart}"),
      ('ic', "[QNTD] INITIATE CHECKOUT", 'calc', "={c}{cart}*{c}{cart_ic}", FMT_INT, 'sum', 'in'),
      ('custo_ic', "[R$] CUSTO POR CHECKOUT", 'calc', "=IFERROR({c}{midia}/{c}{ic},0)", FMT_BRL2, 'div:midia/ic', "{c}{midia}/{c}{ic}"),
      lever('ic_ped', "[%] CHECKOUT → PEDIDO", FMT_PCT0, 'div:pedidos/ic', "{c}{pedidos}/{c}{ic}"),
      ('pedidos_ger', "[QNTD] PEDIDOS GERADOS NO MÊS (ANTES DO LAG)", 'calc', "={c}{ic}*{c}{ic_ped}", FMT_INT, 'sum', '""'),
      ('pedidos', "[QNTD] PEDIDOS", 'calcf', ("={c}{pedidos_ger}*{P_lag}", "={c}{pedidos_ger}*{P_lag}+{p}{pedidos_ger}*(1-{P_lag})"), FMT_INT, 'sum', 'in'),
      ('custo_pedido', "[R$] CUSTO POR PEDIDO", 'calc', "=IFERROR({c}{midia}/{c}{pedidos},0)", FMT_BRL2, 'div:midia/pedidos', "{c}{midia}/{c}{pedidos}"),
      lever('ticket_ped', "[R$] TICKET MÉDIO DO PEDIDO", FMT_BRL2, 'div:receita_captada/pedidos', "{c}{receita_captada}/{c}{pedidos}"),
      ('receita_captada', "[R$] RECEITA ATRIBUÍDA À MÍDIA V4", 'calc', "={c}{pedidos}*{c}{ticket_ped}", FMT_BRL, 'sum', 'in'),
      ('tx_pedido', "[%] TAXA CONV. DA SESSÃO PAGA (PEDIDO)" if funil_pago else "[%] TAXA CONV. E-COM (PEDIDO)", 'calc', "=IFERROR({c}{pedidos}/{c}{" + base_ses + "},0)", FMT_PCT2, 'div:pedidos/' + base_ses, "{c}{pedidos}/{c}{" + base_ses + "}"),
    ]
    if usa_venda:
        mets += [
          lever('ped_venda', "[%] PEDIDO → VENDA", FMT_PCT0, 'div:vendas/pedidos', "{c}{vendas}/{c}{pedidos}"),
          ('vendas', "[QNTD] VENDAS", 'calc', "={c}{pedidos}*{c}{ped_venda}", FMT_INT, 'sum', 'in'),
          ('custo_venda', "[R$] CUSTO POR VENDA", 'calc', "=IFERROR({c}{midia}/{c}{vendas},0)", FMT_BRL2, 'div:midia/vendas', "{c}{midia}/{c}{vendas}"),
          lever('ticket_fat', "[R$] TICKET MÉDIO FATURADO", FMT_BRL2, 'div:receita_fat/vendas', "{c}{receita_fat}/{c}{vendas}"),
          ('receita_fat', "[R$] RECEITA FATURADA NO MÊS", 'calc', "={c}{vendas}*{c}{ticket_fat}", FMT_BRL, 'sum', 'in'),
          ('tx_venda', "[%] TAXA CONV. E-COM (VENDA)", 'calc', "=IFERROR({c}{vendas}/{c}{" + base_ses + "},0)", FMT_PCT2, 'div:vendas/' + base_ses, "{c}{vendas}/{c}{" + base_ses + "}"),
        ]
    mets += [('sec', "RESULTADO · REALIZADO ONDE EXISTE, PROJETADO À FRENTE")]
    if usa_margem:
        mets += [
          ('margem', "[%] MARGEM DE CONTRIBUIÇÃO", 'link', 'margem', FMT_PCT1, 'div:mc/' + rec, 'proj'),
          ('mc', "[R$] RESULTADO MC/MÊS", 'calc', "={c}" + "{" + rec + "}" + "*{c}{margem}", FMT_BRL, 'sum', "{c}" + "{" + rec + "}" + "*{c}{margem}"),
        ]
    if margem_info is not None:
        mc_info_row = ('mc_info', "[R$] MC INFORMATIVA (RECEITA × MARGEM INFORMATIVA, FORA DO RESULTADO)", 'calc', "={c}{receita_cons}*{P_margem_info}", FMT_BRL, 'sum', '""')
    base_res = 'mc' if usa_margem else rec
    mets += [
      ('receita_cons', "[R$] RECEITA CONSOLIDADA", 'calc', "=IF({HAS}=0,{c}{" + rec + "},{r}{" + rec + "})", FMT_BRL, 'sum', '""'),
      ('midia_cons', "[R$] MÍDIA CONSOLIDADA", 'calc', "=IF({HAS}=0,{c}{midia},{r}{midia})", FMT_BRL, 'sum', '""'),
      ('custo_cons', "[R$] CUSTO CONSOLIDADO (FEE + MÍDIA)", 'calc', "=IF({HAS}=0,{c}{custo_mes},{r}{custo_mes})", FMT_BRL, 'sum', '""'),
      ('resultado_cons', "[R$] RESULTADO LÍQUIDO DO MÊS", 'calc', "=IF({HAS}=0,{c}{" + base_res + "},{r}{" + base_res + "})-{c}{custo_cons}", FMT_BRL, 'sum', '""'),
      ('cum_cons', "[R$] RESULTADO ACUMULADO", 'cum', 'resultado_cons', FMT_BRL, 'last', '""'),
      ('cresc_receita', "[%] CRESCIMENTO DA RECEITA (MÊS ANTERIOR)", 'calcf', ('=""', '=IFERROR({c}{receita_cons}/{p}{receita_cons}-1,"")'), FMT_PCT1, 'avg', '""'),
      ('roas_cons', "ROAS DO MÊS", 'calc', "=IFERROR({c}{receita_cons}/{c}{midia_cons},0)", FMT_X, 'div:receita_cons/midia_cons', '""'),
      ('roi_mes', "[%] ROI DO MÊS", 'calc', "=IFERROR({c}{resultado_cons}/{c}{custo_cons},0)", FMT_PCT1, 'div:resultado_cons/custo_cons', '""'),
      ('custo_acum', "[R$] CUSTO ACUMULADO", 'cum', 'custo_cons', FMT_BRL, 'last', '""'),
      ('roi_projeto', "[%] ROI DO PROJETO (ACUMULADO)", 'calc', "=IFERROR({c}{cum_cons}/{c}{custo_acum},0)", FMT_PCT1, 'last', '""'),
      ('flag', "ACUMULADO ≥ 0?  (1 = SIM)", 'calc', "=IF({c}{cum_cons}>=0,1,0)", '0', 'sum', '""'),
      ('flag_mes', "MÊS NO AZUL?  (1 = SIM)", 'calc', "=IF({c}{resultado_cons}>=0,1,0)", '0', 'sum', '""'),
      ('flag_cont', "NO AZUL DAQUI ATÉ O FIM?  (1 = SIM)", 'calc', "=IF(COUNTIF({c}{flag_mes}:{L}{flag_mes},0)=0,1,0)", '0', 'sum', '""'),
    ]
    if margem_info is not None: mets += [mc_info_row]
    if share:
        mets += [
          ('sec', "PARTICIPAÇÃO DA MÍDIA NO FATURAMENTO DA LOJA"),
          ('fat_total', "[R$] FATURAMENTO TOTAL DA LOJA", 'mixed', p['fat_total_cells'], FMT_BRL, 'sum', '""'),
          ('cresc_fat_total', "[%] CRESCIMENTO DO FATURAMENTO TOTAL (MÊS ANTERIOR)", 'calcf', ('=""', '=IFERROR({c}{fat_total}/{p}{fat_total}-1,"")'), FMT_PCT1, 'avg', '""'),
          ('share_midia', "[%] PARTICIPAÇÃO DA MÍDIA V4 NO FATURAMENTO", 'calc', "=IFERROR({c}{receita_cons}/{c}{fat_total},0)", FMT_PCT1, 'div:receita_cons/fat_total', '""'),
          ('fat_sem_midia', "[R$] FATURAMENTO FORA DA MÍDIA V4", 'calc', "={c}{fat_total}-{c}{receita_cons}", FMT_BRL, 'sum', '""'),
        ]

    def kpis(ctx):
        pb = kpi_payback_cards(ctx, cum_key='cum_cons')
        out = [(f"RECEITA ATRIBUÍDA À MÍDIA · {ctx.n} MESES", f"={ctx.tot('receita_cons')}", FMT_BRL, "realizado onde existe, projetado à frente"),
               (f"RESULTADO LÍQUIDO · {ctx.n} MESES", f"={ctx.tot('resultado_cons')}", FMT_BRL, "receita − (fee + mídia)" if not usa_margem else "MC − (fee + mídia)"),
               (f"ROAS MÉDIO · {ctx.n} MESES", f"=IFERROR({ctx.tot('receita_cons')}/{ctx.tot('midia_cons')},0)", FMT_X, "receita ÷ mídia"),
               (f"PEDIDOS · {ctx.n} MESES", f"={ctx.tot(vol)}", FMT_INT, "pedidos atribuídos à mídia" if not usa_venda else "vendas atribuídas"),
               (f"CUSTO TOTAL · {ctx.n} MESES", f"={ctx.tot('custo_cons')}", FMT_BRL, "fee V4 + mídia")]
        if share:
            out += [("PARTICIPAÇÃO DA MÍDIA · MÊS 1", f"=IFERROR(INDEX({ctx.rng('share_midia')},1,1),0)", FMT_PCT1, "receita atribuída ÷ faturamento da loja"),
                    (f"PARTICIPAÇÃO DA MÍDIA · MÊS {ctx.n}", f"=IFERROR(INDEX({ctx.rng('share_midia')},1,{ctx.n}),0)", FMT_PCT1, "onde a mídia chega no fim do período")]
        out += [("ROI DO PROJETO", f"=IFERROR({ctx.tot('resultado_cons')}/{ctx.tot('custo_cons')},0)", FMT_PCT1, "acumulado no período"),
                pb['azul'], pb['payback'], pb['exposicao']]
        return out[:10]

    charts = [
      dict(type='growth', title="Receita da mídia e crescimento mês a mês", bars='receita_cons', line='cresc_receita'),
      dict(type='line', title="Resultado acumulado mês a mês", series=[('cum_cons', GREEN, False)], y_fmt=FMT_BRL),
      dict(type='payback', title="Curva de payback"),
    ]
    if share:
        charts += [dict(type='line', title="Participação da mídia V4 no faturamento da loja", series=[('share_midia', RED, False)], y_fmt='0%')]
    charts += [dict(type='funnel', title="Funil e-commerce · acumulado no período")]

    if p.get('verba_plano'):  # plano de verba mês a mês: cada mês é editável, crescimento e teto saem
        prem = [x for x in prem if x[0] not in ('cresc', 'teto')]
        mets = [('midia', "[R$] VERBA DE MÍDIA", 'input', Ln(p['verba_plano'], n), FMT_BRL, 'sum', 'in') if m[0] == 'midia' else m for m in mets]
    funnel = [("Sessões pagas" if funil_pago else "Sessões", base_ses), ("View Item", 'view_item'), ("Carrinho", 'cart'), ("Checkout", 'ic'), ("Pedidos", 'pedidos')]
    if usa_venda: funnel += [("Vendas", 'vendas')]
    return dict(
      sheet=p['sheet'], title=p['title'], subtitle=p['subtitle'], meta_line=p['meta_line'], footer=p['footer'],
      premises=prem, budget_day=('midia1', 'dias'), acum0_key='acum0', metrics=mets, n_months=n,
      bold_rows={'receita_captada', 'receita_fat', 'receita_cons', 'resultado_cons', 'cum_cons', 'share_midia', 'fat_total'},
      signed_rows=['resultado_cons', 'cum_cons', 'roi_mes', 'roi_projeto', 'cresc_receita', 'cresc_fat_total'], cum_key='cum_cons',
      kpis=kpis,
      meta=lambda ctx, m: meta_block(ctx, m, p['target'], rec, 'ticket_ped' if not usa_venda else 'ticket_fat', vol, 'custo_cons', 'cum_cons',
                                     'margem' if usa_margem else None, acum0_key='acum0'),
      metodologia=p.get('metodologia'), metodologia_fim=p.get('metodologia_fim'), historico=p.get('historico'), pilot_ref=p.get('pilot_ref'), base_ref=p.get('base_ref'),
      real_prefill=p.get('real_prefill'), month_labels=p.get('month_labels'), envelope=p.get('envelope'),
      charts=charts, funnel=funnel,
    )

# ===================================================================== DEMO (valores dos painéis agência de viagens e e-commerce de tecidos)
DEMO_IS = dict(
  sheet="Inside Sales", title="Projeção Inside Sales",
  subtitle="agência de viagens   ·   Cenário Realista   ·   Projeção de 12 meses   ·   Breakeven Alvo M5 | comissão 15%",
  meta_line="Atualizado em {today}   ·   Modelo replicado do painel Projeção · Inside Sales e E-commerce   ·   Origem da base: histórico real (4 competências)",
  footer="Projeção Inside Sales · demonstração",
  prem=dict(fee=6900, midia=5000, comissao=0.15, margem=0.40, connect=1.0, organicas=0, con_lead=0.9, con_mql=0.8, cresc=0.0, teto=0, lag=1.0, acum0=0, dias=30),
  monthly=dict(cpm=[18.08, 10.2, 9.05, 9.79, 9.68] + [10.68]*7, ctr=[0.0075, 0.009, 0.0068, 0.0037, 0.0078] + [0.0078]*7,
               conv_lp=[0.3803, 0.1951, 0.074, 0.0937, 0.1437] + [0.1437]*7, lead_mql=[0.2593, 0.4181, 0.4938, 0.6667, 0.4237] + [0.4237]*7,
               mql_sql=[0.0714, 0.1799, 0.3125, 0.3334, 0.2968] + [0.2968]*6 + [0.299], sql_venda=[0.1716, 0.3385, 0.433, 0.5902, 0.7625] + [0.7625]*7,
               ticket=[5000, 9368, 9850, 7980, 8238.53, 8310.71, 8378.09, 8177.34, 8242.63, 8304.08, 8362.02, 8189.26]),
  target=5,
  metodologia=[("NOTAS DO CENÁRIO", [USO_COMUM + "\n"
    "• Fórmulas: Impressões = Mídia ÷ CPM × 1.000 · Leads = Visitas LP × Conv. LP · Vendas = SQLs × (SQL → Venda), com lag comercial · Receita da agência = GMV × Comissão · "
    "Resultado MC = Receita × Margem · Resultado líquido = Resultado MC − (Fee + Mídia) · ROI = Resultado ÷ Custo · Payback = 1º mês com acumulado ≥ 0.\n"
    "• Cenário replicado: Realista do painel Projeção · Inside Sales e E-commerce (agência de viagens), leitura de 11/09/2026, taxas com 2 casas como exibidas no painel. "
    "M12 não aparecia por inteiro no PDF: alavancas repetem o M11, exceto MQL con. → SQL (29,9%) e Ticket médio (R$ 8.189,26), da tabela 'Taxas efetivas'.\n"
    "• Meta de breakeven: coerente com a tabela (aplica comissão e margem). O painel original calculava essa meta só com a comissão, por isso mostrava 28 vendas no M5."])],
)
DEMO_EC = dict(
  sheet="E-commerce", title="Projeção E-commerce",
  subtitle="e-commerce de tecidos   ·   Cenário Realista   ·   Projeção de 12 meses   ·   Premissas manuais | curva linear",
  meta_line="Atualizado em {today}   ·   Modelo replicado do painel Projeção · Inside Sales e E-commerce   ·   Origem: premissas manuais (CSV exportado em 16/09/2026)",
  footer="Projeção E-commerce · demonstração",
  prem=dict(fee=5000, midia1=25000, cresc=0.05, teto=0, cpm=35, ctr=0.014, connect=0.85, organicas=5000, s_vi=0.48, vi_cart=0.12, cart_ic=0.55, ic_ped=0.52,
            ticket_ped=220, ped_venda=0.92, ticket_fat=220, margem=0.40, lag=1.0, acum0=0, dias=30),
  target=12,
  usa_margem=True, usa_venda=True,
  metodologia=[("NOTAS DO CENÁRIO", [USO_COMUM + "\n"
    "• Curva linear: as taxas puxam a premissa geral; a verba de mídia do Mês 1 vem da premissa e os meses seguintes crescem pelo percentual configurado. Digite um valor por cima para fixar um mês.\n"
    "• Fórmulas: Impressões = Mídia ÷ CPM × 1.000 · Sessões pagas = Cliques × Connect rate · Sessões total = pagas + orgânicas · View Item → Carrinho → Checkout → Pedidos pelas taxas de etapa (pedidos com lag) · "
    "Receita captada = Pedidos × Ticket do pedido · Vendas = Pedidos × (Pedido → Venda) · Receita faturada = Vendas × Ticket faturado · Resultado MC = Receita faturada × Margem · "
    "Resultado líquido = Resultado MC − (Fee + Mídia) · ROAS = Receita faturada ÷ Mídia · ROI = Resultado ÷ Custo · Payback = 1º mês com acumulado ≥ 0.\n"
    "• Cenário replicado: Realista do painel Projeção · Inside Sales e E-commerce (e-commerce de tecidos), premissas manuais, CSV exportado em 16/09/2026; os valores batem com o CSV. "
    "Neste cenário o acumulado não fica positivo em 12 meses (payback após M12), igual ao painel."])],
)

# ===================================================================== premissas.json -> config
HIST_ROWS = {
  "inside_sales": [("Fee V4", FMT_BRL), ("Plano de Mídia Mês", FMT_BRL), ("Investimento", FMT_BRL), ("Impressões", FMT_INT), ("Cliques", FMT_INT), ("Leads", FMT_INT),
                   ("Conexões", FMT_INT), ("MQLs", FMT_INT), ("SQLs", FMT_INT), ("Vendas", FMT_INT), ("Faturamento V4", FMT_BRL), ("Ticket Médio", FMT_BRL2), ("Gross Margin", FMT_PCT1)],
  "ecommerce": [("Fee V4", FMT_BRL), ("Plano de Mídia Mês", FMT_BRL), ("Investimento", FMT_BRL), ("Investimento Google", FMT_BRL), ("Investimento Meta", FMT_BRL),
                ("Impressões", FMT_INT), ("Cliques", FMT_INT), ("Sessões Google", FMT_INT), ("Sessões Meta", FMT_INT), ("Sessões", FMT_INT), ("Sessões Orgânicas", FMT_INT), ("Sessões Gerais", FMT_INT),
                ("Add to Cart", FMT_INT), ("Check Out", FMT_INT), ("Transações Captada", FMT_INT), ("Receita Captada", FMT_BRL), ("Ticket Médio", FMT_BRL2), ("Gross Margin", FMT_PCT1)],
}
PREFILL = {  # métrica do template <- rótulo lido da fonte
  "inside_sales": {'fee': "Fee V4", 'midia': "Investimento", 'impress': "Impressões", 'cliques': "Cliques", 'visitas_pagas': "Cliques", 'leads': "Leads",
                   'mqls': "MQLs", 'leads_con': "Conexões", 'mql_con': "MQLs", 'sqls': "SQLs", 'vendas': "Vendas", 'gmv': "Faturamento V4"},
  "ecommerce": {'fee': "Fee V4", 'midia': "Investimento", 'impress': "Impressões", 'cliques': "Cliques", 'sessoes_pago': "Sessões", 'view_item': "Sessões",
                'cart': "Add to Cart", 'ic': "Check Out", 'pedidos': "Transações Captada", 'receita_captada': "Receita Captada"},
}

def _mes_idx(nome): return MESES.index(norm(nome))
def _rotulo(mes, ano): return f"{ABREV[_mes_idx(mes)]}/{ano}"
def _chave(mes, ano): return f"{norm(mes)}/{ano}"

def parse_valores(txt):
    """'agosto/2026=143309.07,setembro/2026=82.148,21' -> {'agosto/2026': 143309.07, ...}"""
    out = {}
    for parte in (txt or '').split(','):
        if '=' not in parte: continue
        k, v = parte.split('=', 1); v = v.strip()
        if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.')
        elif ',' in v: v = v.replace(',', '.')
        out[norm(k).replace(' ', '')] = float(v)
    return out

def month_labels(det, hist, inicio_contrato=None, n=12):
    """Devolve (rótulos de calendário, chaves normalizadas, origem do Mês 1)."""
    if inicio_contrato:
        alvo = norm(inicio_contrato).replace(' ', '')
        h = next((x for x in hist if _chave(x['mes'], x['ano']).replace(' ', '') == alvo), None)
        if h is None: sys.exit(f"--inicio-contrato {inicio_contrato}: mês não encontrado no histórico da fonte.")
        i, ano, origem = _mes_idx(h['mes']), int(h['ano']), 'contrato'
    else:
        mc = det.get('mes_corrente'); fechados = det.get('meses_fechados') or []
        base = mc or (fechados[-1] if fechados else None)
        if not base: return None, None, None
        nome, ano = base.split('/'); i = _mes_idx(nome); ano = int(ano); origem = 'corrente' if mc else 'seguinte'
        if not mc: i += 1
    labels = [f"{ABREV[(i + k) % 12]}/{ano + (i + k) // 12}" for k in range(n)]
    chaves = [f"{MESES[(i + k) % 12]}/{ano + (i + k) // 12}" for k in range(n)]
    return labels, chaves, origem

def config_from_premissas(path, modelo, cliente, cenario, obs=None, inicio_contrato=None, marca=None,
                          faturamento_total=None, base_nao_midia=None, margem_informativa=None, sem_etapa_venda=False, extra_met=None,
                          conexao_so_lead=False):
    d = json.load(open(path, encoding='utf-8'))
    pc, det, v = d['premissas_confirmadas'], d['detectado'], d['veredito']
    tx = det['taxas_efetivas']; t = tx['taxas']
    if 'rampa' not in d or 'envelope' not in d:
        sys.exit("premissas.json sem 'rampa'/'envelope': gere-o com a versão atual do piloto (modo projetar).")
    n = len(d.get('projecao') or [])
    if not 1 <= n <= 12:
        sys.exit(f"premissas.json traz {n} meses de projeção; o template aceita de 1 a 12.")
    if det.get('modelo') not in (None, modelo):
        sys.exit(f"premissas.json foi gerado para o modelo {det.get('modelo')}, não {modelo}.")
    faltam = [k for k in ('fee', 'midia_mensal', 'margem', 'comissao', 'ticket', 'mes_alvo') if pc.get(k) is None]
    if faltam: sys.exit(f"premissas.json sem campos necessários: {faltam}")

    cliente = cliente or "Cliente"; cenario = cenario or "Realista"
    mes_alvo = int(pc['mes_alvo']); lag = float(pc.get('lag', 1.0)); acum0 = float(pc.get('acumulado_inicial', 0.0))
    ticket = float(pc['ticket']); cresc = float(pc.get('crescimento_midia', 0.0) or 0.0); teto = float(pc.get('midia_teto') or 0.0)
    env, rampa = d['envelope'], d['rampa']; taxas = rampa['taxas_mes_a_mes']
    verba_plano = pc.get('verba_plano')
    sp = d.get('split') if modelo == 'ecommerce' and 'custo_sessao_meta' in env else None   # GA4 separou Google e Meta
    ga4 = det.get('ga4') or {}
    col = lambda k: [row.get(k) for row in taxas]
    hist = d.get('historico') or []
    labels, chaves, origem = month_labels(det, hist, inicio_contrato, n)
    janela = tx.get('janela_meses') or []
    por_chave = {_chave(h['mes'], h['ano']): h for h in hist}
    realizados = {k: por_chave.get(ch) for k, ch in enumerate(chaves or [])
                  if por_chave.get(ch) and por_chave[ch]['status'] in ('fechado', 'corrente')}

    # --- histórico (bloco na aba do cliente)
    historico = None
    if hist:
        jan = {x.split(' ')[0] for x in janela}; ref = rampa.get('mes_referencia')
        ini = None
        if inicio_contrato:
            alvo = norm(inicio_contrato).replace(' ', '')
            ini = next((i for i, h in enumerate(hist) if _chave(h['mes'], h['ano']).replace(' ', '') == alvo), None)
        meses = [{'rotulo': _rotulo(h['mes'], h['ano']), 'status': h['status'], 'janela': _chave(h['mes'], h['ano']) in jan,
                  'referencia': _chave(h['mes'], h['ano']) == ref, 'pre': ini is not None and i < ini} for i, h in enumerate(hist)][:24]
        linhas = [(lab, fmt, [h.get(lab) for h in hist][:24]) for lab, fmt in HIST_ROWS[modelo] if any(h.get(lab) is not None for h in hist)]
        hr = {x['mes']: x for x in d.get('historico_resultado') or []}
        if hr:
            linhas.append(("Resultado (receita − fee − mídia)" if float(pc['margem']) >= 0.999 else "Resultado (MC − fee − mídia)", FMT_BRL,
                           [hr.get(_chave(h['mes'], h['ano']), {}).get('resultado_mc') for h in hist][:24]))
        nota = f"Contrato com a V4 desde {inicio_contrato}: os meses anteriores ficam fora da janela de taxas, do mês de referência e do resultado do projeto." if inicio_contrato else None
        historico = {'meses': meses, 'linhas': linhas, **({'nota': nota} if nota else {})}

    # --- realizado pré-preenchido em todos os meses já vividos
    prefill = {}
    for k, h in realizados.items():
        linha = {mk: h.get(src) for mk, src in PREFILL[modelo].items()}
        if modelo == 'inside_sales':
            linha['organicas'] = 0
            if "Conexões" in (det.get('etapas_ausentes_na_fonte') or []):
                linha.pop('mql_con', None); linha.pop('leads_con', None)
            elif conexao_so_lead:
                linha.pop('mql_con', None)   # a linha Conexões da fonte é de leads conectados; MQL conectado não é medido
        elif sp and h.get("Sessões Google") is not None:
            linha.pop('sessoes_pago', None)                                    # no split, sessões pagas = Google + Meta (fórmula)
            linha['verba_google'] = h.get("Investimento Google")
            linha['sessoes_google'] = h.get("Sessões Google")
            linha['sessoes_meta'] = h.get("Sessões Meta")
            linha['view_item'] = h.get("Sessões")
            linha['sessoes_org'] = h.get("Sessões Orgânicas")
        else:
            cliq = h.get("Cliques") or 0; sess = h.get("Sessões") or 0; geral = h.get("Sessões Gerais") or 0
            pagas = min(sess, cliq) if (sess and cliq) else (sess or cliq)     # sessão paga nunca passa do clique
            linha['sessoes_pago'] = pagas or None
            linha['view_item'] = pagas or None
            linha['sessoes_org'] = max(geral - pagas, 0) if geral else (h.get("Sessões Orgânicas") or 0)
        prefill[k] = {a: b for a, b in linha.items() if b is not None}

    pilot_ref = {'header': "PILOTO", 'status': v['status'],
                 'valores': {5: v.get('vendas_necessarias_mes_alvo'), 6: v.get('vendas_projetadas_mes_alvo'), 7: v.get('gap_vendas')}}
    ordem = ['cpm'] + (['ctr', 'clique_lead', 'lead_mql', 'mql_sql', 'sql_venda'] if modelo == 'inside_sales'
                       else ['custo_sessao_meta', 'ctr', 'clique_sessao', 'sessao_cart', 'cart_checkout', 'checkout_trans']) + ['ticket']
    fmt_of = lambda k: FMT_BRL2 if k in ('cpm', 'ticket', 'custo_sessao_meta') else FMT_PCT1
    mercado = [env[k]['rotulo'] for k in ordem if k in env and env[k].get('alvo_mercado')]
    envelope = {'linhas': [(env[k]['rotulo'] + (" · alvo de mercado" if env[k].get('alvo_mercado') else ""), fmt_of(k), env[k]['atual'], env[k]['mediana'], env[k]['melhor'], env[k].get('melhor_mes'), env[k].get('referencia'), env[k].get('alvo')) for k in ordem if k in env],
                'alvo_em': f"M{rampa['atinge_alvo_em']}",
                'nota': (f"O alvo da rampa é a mediana do período comparável em cada alavanca, e nunca é pior que a taxa atual; a rampa caminha linearmente até M{rampa['atinge_alvo_em']}. "
                         f"Evidência de que o nível é atingível: {rampa.get('motivo')}."
                         + (f" Alvo por benchmark de mercado, porque o histórico é curto demais: {', '.join(mercado)} (fontes na seção de benchmarks)." if mercado else ""))}
    pb = d.get('projecao_base') or []
    base_ref = {'titulo': "CENÁRIO DE REFERÊNCIA · TAXAS ATUAIS SEM RAMPA (VALORES DO PILOTO)",
                'nota': f"O que aconteceria mantendo as taxas da janela e a verba do Mês 1 nos {len(pb)} meses. É a linha de base; a tabela do cliente traz a rampa.",
                'linhas': [("Receita", FMT_BRL, [l['receita'] for l in pb]), ("Resultado líquido", FMT_BRL, [l['resultado_liquido'] for l in pb]),
                           ("Acumulado", FMT_BRL, [l['acumulado'] for l in pb])]}

    totais = parse_valores(faturamento_total)
    share = bool(totais or base_nao_midia is not None)
    fat_cells = None
    if share:
        rec_real = {}
        for k, h in realizados.items():
            rec_real[k] = h.get("Receita Captada" if modelo == 'ecommerce' else "Faturamento V4") or 0
        if base_nao_midia is None:
            cand = [(k, totais[chaves[k].replace(' ', '')] - rec_real.get(k, 0)) for k in realizados
                    if chaves[k].replace(' ', '') in totais and realizados[k]['status'] == 'fechado']
            base_nao_midia = round(sum(x for _, x in cand) / len(cand), 2) if cand else 0.0
        fat_cells = []
        for k in range(n):
            ch = chaves[k].replace(' ', '') if chaves else ''
            fat_cells.append(totais[ch] if ch in totais else "=IFERROR({P_base_nao_midia}+{c}{receita_cons},0)")

    # datas do veredito sobre a linha consolidada: realizado nos meses vividos, projeção do piloto nos demais (48 meses)
    longo = bool(v.get('resultados_48m'))   # premissas antigos só têm os meses da planilha
    cons = list(v.get('resultados_48m') or [l['resultado_liquido'] for l in d.get('projecao') or []])
    for k, h in realizados.items():
        if k < len(cons):
            rec = h.get("Receita Captada" if modelo == 'ecommerce' else "Faturamento V4") or 0
            cons[k] = rec * float(pc['comissao']) * float(pc['margem']) - (h.get("Fee V4") or 0) - (h.get("Investimento") or 0)
    acc, azul_cont, zera = acum0, None, None
    for t_, r_ in enumerate(cons, 1):
        acc += r_
        if zera is None and acc >= 0: zera = t_
    azul_cont = next((t_ for t_ in range(1, len(cons) + 1) if all(x >= 0 for x in cons[t_ - 1:])), None)
    nunca = "não acontece em 48 meses" if longo else f"não acontece até {labels[-1]}"
    def rot_mes(t):  # rótulo de calendário do mês t, inclusive depois do horizonte
        if t is None: return "—"
        if t <= len(labels): return labels[t - 1]
        mes0, ano0 = labels[0].split('/'); i = ABREV.index(mes0) + t - 1
        return f"{ABREV[i % 12]}/{int(ano0) + i // 12}"
    m1_txt = {'contrato': f"Mês 1 = {labels[0]} (início do contrato com a V4).",
              'corrente': f"Mês 1 = {labels[0]} (mês corrente da fonte).",
              'seguinte': f"Mês 1 = {labels[0]} (mês seguinte ao último fechado)."}.get(origem, "Mês 1 = próximo mês.")
    if realizados:
        m1_txt += (" Meses já vividos entram pela coluna Realizado (" +
                   ", ".join(labels[k] + (" parcial" if h['status'] == 'corrente' else "") for k, h in sorted(realizados.items())) +
                   "); a linha de resultado consolidado usa o realizado nesses meses e o projetado nos demais.")
    alertas = tx.get('alertas') or []
    usa_margem = float(pc['margem']) < 0.999
    org_real, org_base, extra_org = {}, 0, ["={P_organicas}"] * n
    if modelo == 'ecommerce':
        for k, h in realizados.items():
            if sp and h.get("Sessões Google") is not None:
                org_real[k] = h.get("Sessões Orgânicas") or 0
                continue
            cliq = h.get("Cliques") or 0; sess = h.get("Sessões") or 0; geral = h.get("Sessões Gerais") or 0
            pagas = min(sess, cliq) if (sess and cliq) else (sess or cliq)
            org_real[k] = max(geral - pagas, 0) if geral else (h.get("Sessões Orgânicas") or 0)
        fech = [v for k, v in org_real.items() if realizados[k]['status'] == 'fechado'] or list(org_real.values())
        org_base = round(sum(fech) / len(fech)) if fech else 0
        extra_org = [org_real[k] if k in org_real else "={P_organicas}" for k in range(n)]
    if modelo == 'inside_sales':
        if "Leads → Conexões" in t and "Conexões → MQLs" in t:
            con_lead, conex = t["Leads → Conexões"], "conexão lead = taxa da janela (informativa; SQLs saem dos MQLs)"
        else:
            con_lead, conex = 1.0, "a fonte não tem a linha Conexões: conexão lead 100% (informativa)"
        sem_conexao = "Conexões" in (det.get('etapas_ausentes_na_fonte') or [])
        conexao_so_lead = conexao_so_lead and not sem_conexao
        assum = ("leads vêm direto dos cliques (a planilha padrão não mede landing page, então connect e visitas não aparecem); "
                 + ("a fonte não tem a linha Conexões, então o funil segue MQL → SQL; " if sem_conexao else
                    f"a linha Conexões da fonte conta leads conectados: {conex}; MQLs conectados não são medidos, então a conexão MQL fica em branco "
                    "para preencher e o funil segue MQL → SQL; " if conexao_so_lead else f"{conex}; conexão MQL 100%; ")
                 + "dias do mês 30; taxas e ticket seguem a rampa do piloto, mês a mês, nas células amarelas.")
        prem = dict(fee=pc['fee'], midia=pc['midia_mensal'], comissao=pc['comissao'], margem=pc['margem'], connect=1.0, organicas=0,
                    con_lead=con_lead, con_mql=1.0, cresc=cresc, teto=teto, lag=lag, acum0=acum0, dias=30)
        saz_ = pc.get('sazonalidade') or {}
        mult_cpm = (list(saz_.get('cpm') or []) + [1.0] * n)[:n]
        mult_dem = (list(saz_.get('demanda') or []) + [1.0] * n)[:n]
        cpm_base, sql_base = col('cpm'), col('sql_venda')
        cpm_usado = [c * m if c is not None else None for c, m in zip(cpm_base, mult_cpm)]
        sql_usado = [min(v * m, 1.0) if v is not None else None for v, m in zip(sql_base, mult_dem)]   # a demanda do mês entra na taxa usada
        monthly = dict(cpm=cpm_usado, ctr=col('ctr'), conv_lp=col('clique_lead'), lead_mql=col('lead_mql'), mql_sql=col('mql_sql'), sql_venda=sql_usado, ticket=col('ticket'))
        title, rotulo = "Projeção Inside Sales", "Inside Sales"
        propria = float(pc['comissao']) >= 0.999 and not pc.get('crm')
        formulas = ("Impressões = Mídia ÷ CPM × 1.000 · Cliques = Impressões × CTR · Leads = Cliques × (Clique → Lead) · Vendas = SQLs × (SQL → Venda), com lag · "
                    + ("Faturamento = Vendas × Ticket · Resultado MC = Faturamento × Margem · " if propria else
                       "GMV = Vendas × Ticket · Receita = GMV × Comissão · Resultado MC = Receita × Margem · ")
                    + "Resultado do mês = MC − (Fee + Mídia) · Payback = 1º mês com acumulado ≥ 0.")
        extra = dict(sem_lp=True, sem_conexao=sem_conexao, conexao_so_lead=conexao_so_lead)
    else:
        if sp:
            assum = (f"Funil pago: carrinho, checkout e pedido correm só sobre as sessões pagas (Google + Meta); as sessões não pagas "
                     f"(orgânico, direto, referência) aparecem como contexto do total do site e não geram receita atribuída à V4. "
                     f"Google: CPM, CTR e connect rate de {min(env['clique_sessao']['atual'], 1.0):.0%} medidos no GA4 (sessões Google ÷ cliques do Google Ads). "
                     f"Meta: verba = verba da fonte − custo do Google Ads no GA4 ({sp['participacao_meta_na_verba']:.0%} da verba na janela, mantido constante), "
                     f"sessões pela verba ÷ custo por sessão (R$ {env['custo_sessao_meta']['atual']:,.2f} na janela). "
                     f"Carrinho e checkout do tráfego pago medidos no GA4; pedidos e receita da fonte (atribuição das plataformas). "
                     f"Sessão paga → view item 100%, porque o GA4 conta eventos de view item, não sessões. "
                     f"Sessões não pagas por mês nos meses projetados: {org_base:,.0f}, média dos meses fechados. Dias do mês 30. "
                     "Taxas e ticket seguem a rampa do piloto, mês a mês, nas células amarelas.")
        else:
            assum = (f"connect rate (clique → sessão) de {min(env['clique_sessao']['atual'], 1.0):.0%}"
                     + (" informado manualmente, porque a linha de cliques da fonte não soma todos os canais e dava mais sessões que cliques" if pc.get('connect_rate') else "")
                     + f"; sessões orgânicas vindas da linha 'Sessões Orgânicas' da fonte (média de {org_base:,.0f} nos meses projetados); sessão → view item 100%; dias do mês 30; carrinho e checkout pagos vêm das taxas do GA4 aplicadas às sessões pagas; "
                     "funil pago: as taxas valem só para as sessões pagas, as orgânicas ficam como contexto; "
                     "taxas e ticket seguem a rampa do piloto, mês a mês, nas células amarelas.")
        if sem_etapa_venda: assum += " Pedido e venda são o mesmo evento nesta fonte, então a etapa de venda não aparece."
        prem = dict(fee=pc['fee'], midia1=pc['midia_mensal'], cresc=cresc, teto=teto, cpm=env['cpm']['atual'], ctr=env['ctr']['atual'],
                    connect=min(env['clique_sessao']['atual'], 1.0), organicas=org_base, s_vi=min(env.get('s_vi', {}).get('atual', 1.0) or 1.0, 1.0),
                    vi_cart=env['sessao_cart']['atual'],
                    cart_ic=env['cart_checkout']['atual'], ic_ped=env['checkout_trans']['atual'], ticket_ped=ticket,
                    ped_venda=1.0, ticket_fat=ticket, margem=pc['margem'], lag=lag, acum0=acum0, dias=30,
                    base_nao_midia=base_nao_midia or 0.0)
        monthly = dict(cpm=col('cpm'), ctr=col('ctr'), connect=col('clique_sessao'), vi_cart=col('sessao_cart'),
                       cart_ic=col('cart_checkout'), ic_ped=col('checkout_trans'), ticket_ped=col('ticket'))
        if sp: monthly['cps_meta'] = col('custo_sessao_meta')
        if not sem_etapa_venda: monthly['ticket_fat'] = col('ticket')
        title, rotulo = "Projeção E-commerce", "E-commerce"
        formulas = (("Verba Google = Mídia × (1 − participação do Meta) · Impressões = Verba Google ÷ CPM × 1.000 · Sessões Google = Cliques × Connect rate · "
                     "Sessões Meta = Verba Meta ÷ custo por sessão · Sessões pagas = Google + Meta · " if sp else
                     "Impressões = Mídia ÷ CPM × 1.000 · Sessões = Cliques × Connect rate · ")
                    + "Carrinho → Checkout → Pedidos pelas taxas de etapa sobre as sessões pagas (pedidos com lag) · "
                    "Receita = Pedidos × Ticket · Resultado do mês = Receita − (Fee + Mídia) · ROAS = Receita ÷ Mídia · Payback = 1º mês com acumulado ≥ 0.")
        extra = dict(usa_margem=usa_margem, usa_venda=not sem_etapa_venda, share=share, margem_info=margem_informativa,
                     fat_total_cells=fat_cells, organicas_cells=extra_org, funil_pago=True,
                     split=({'share': sp['participacao_meta_na_verba'], 'cps': env['custo_sessao_meta']['atual']} if sp else None),
                     rotulo_org="[QNTD] SESSÕES - NÃO PAGAS" if sp else "[QNTD] SESSÕES - ORGÂNICO")

    metodologia = [
      ("VEREDITO E LEITURA", [f"{v['status']} para a meta de {rot_mes(mes_alvo)} (M{mes_alvo}). "
                              + "Considerando o realizado dos meses já vividos e a projeção à frente: "
                              + (f"no azul de forma contínua a partir de {rot_mes(azul_cont)} (M{azul_cont}); " if azul_cont else f"nenhum mês fica no azul de forma contínua ({nunca}); ")
                              + (f"acumulado zera em {rot_mes(zera)} (M{zera})" + (", depois do horizonte da planilha." if zera > n else ".")
                                 if zera else f"o acumulado não zera ({nunca})."),
                              v.get('leitura', '')]),
      ("FONTE E JANELA", [f"Fonte: {det.get('fonte')} (aba {det.get('aba')}).",
                          f"Meses fechados na fonte: {', '.join(det.get('meses_fechados') or []) or 'nenhum'}.",
                          f"Janela das taxas atuais: {', '.join(janela) or 'n/d'}.",
                          *([f"GA4: {ga4.get('propriedade')}, extraído em {ga4.get('extraido_em')}, cobrindo {', '.join(ga4.get('meses') or [])}. "
                             "Sessões por plataforma, sessões não pagas, carrinho, checkout e custo, cliques e impressões do Google Ads vêm do GA4; "
                             "verba total, pedidos e receita vêm da planilha de indicadores."] if ga4.get('meses') else []),
                          f"Definição de breakeven: {pc.get('definicao_breakeven')}.", f"Regra das taxas: {pc.get('regra_taxas')}."]),
      ("CURVA DA PROJEÇÃO", [("Verba mês a mês (plano): " + " → ".join(f"R$ {float(x):,.0f}".replace(',', '.') for x in verba_plano[:n])
                              + "; depois do último mês do plano, repete o último valor." if verba_plano else
                              f"Verba do Mês 1: R$ {float(pc['midia_mensal']):,.0f}, crescendo {cresc:.0%} por mês" + (f" até o teto de R$ {teto:,.0f}." if teto else " sem teto.")),
                             "Alvo da rampa: mediana do período comparável em cada alavanca, nunca pior que a taxa atual"
                             + (f"; nas etapas sem histórico suficiente, o alvo vem do mercado ({', '.join(mercado)}), com as fontes na seção de dados de mercado." if mercado else "."),
                             f"Evidência do nível atingível: {rampa.get('motivo')}", m1_txt,
                             (f"Acumulado inicial de R$ {acum0:,.0f} entra no Mês 1." if acum0 else "Sem acumulado inicial."),
                             ("Atenção: o mês corrente entra parcial, então o crescimento do primeiro mês projetado contra ele fica superestimado." if any(h['status'] == 'corrente' for h in realizados.values()) else "Todos os meses realizados estão fechados."),
                             f"Fórmulas: {formulas}"]),
      ("ALERTAS DE AMOSTRA", alertas or ["Nenhum alerta de amostra frágil na janela."]),
      ("PREMISSAS ASSUMIDAS PELO GERADOR", [assum]),
    ]
    def br(x, dec=0):  # número no padrão brasileiro
        return f"{x:,.{dec}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    def rs(x, dec=0):
        return f"−R$ {br(-x, dec)}" if x < 0 else f"R$ {br(x, dec)}"
    cam = d.get('caminho')
    if cam:
        def fx(chave, x):
            if x is None: return "n/d"
            if chave == 'ticket': return rs(x)
            return rs(x, 2) if chave in ('cpm', 'custo_sessao_meta') else f"{br(x * 100, 1)}%"
        linhas_cam = [f"Critério: o mês-alvo (M{mes_alvo}) fechar no zero, mexendo em uma alavanca por vez e mantendo as demais na rampa. "
                      f"Na rampa, o M{mes_alvo} fecha em {rs(cam['resultado_mes_alvo_na_rampa'])} e o acumulado em {rs(cam['acumulado_mes_alvo_na_rampa'])}."]
        for a in cam['alavancas']:
            ch = a['alavanca']
            if a['necessario'] is None:
                linhas_cam.append(f"{a['rotulo']}: hoje {fx(ch, a['atual'])}; nem no limite fecha o mês.")
            else:
                visto = "já aconteceu num mês fechado" if a['ja_visto'] else "nunca aconteceu num mês fechado"
                linhas_cam.append(f"{a['rotulo']}: hoje {fx(ch, a['atual'])}; precisaria de {fx(ch, a['necessario'])}; melhor mês fechado {fx(ch, a['melhor_mes_fechado'])} ({visto}).")
        linhas_cam.append(f"Fee: o M{mes_alvo} fecharia com fee de {rs(cam['fee_que_fecha'])}." if cam['fee_que_fecha'] > 0
                          else f"Fee: nem com fee zero o M{mes_alvo} fecha; a mídia não se paga nesse mês.")
        mr = cam['margem_por_real_de_midia_no_alvo']
        linhas_cam.append(f"Verba: cada R$ 1 de mídia devolve R$ {br(mr, 2)} de margem nas taxas da rampa; "
                          + (f"cobrir o fee exigiria {rs(cam['verba_que_cobre_o_fee'])} por mês de verba, supondo que as taxas se mantêm nessa escala"
                             + (", mais de cinco vezes a verba atual e fora de qualquer escala testada." if cam['verba_que_cobre_o_fee'] > 5 * max(float(pc['midia_mensal']), teto or 0) else ".")
                             if cam['verba_que_cobre_o_fee'] else "mais verba não cobre o fee."))
        pm = cam['primeiro_mes_positivo_sem_teto']
        linhas_cam.append(f"Crescendo a verba sem teto, o primeiro mês positivo seria o M{pm}" + (f" e o payback o M{cam['payback_sem_teto']}." if cam['payback_sem_teto'] else ".")
                          if pm else "Crescendo a verba sem teto, nenhum mês fica positivo em 48 meses.")
        metodologia.insert(1, ("CAMINHO PARA O BREAKEVEN", linhas_cam))
    if modelo == 'inside_sales' and any(abs(m - 1) > 1e-9 for m in mult_dem):
        letras = [chr(ord('B') + i) for i in range(n + 1)]
        metodologia.append(("SAZONALIDADE DA DEMANDA MÊS A MÊS · TAXA BASE, MULTIPLICADOR E TAXA USADA",
                            {'colunas': [""] + labels[:n], 'spans': [[l, l] for l in letras],
                             'linhas': [["SQL → venda da rampa"] + [f"{br(v * 100, 1)}%" for v in sql_base],
                                        ["Sazonalidade da demanda"] + [f"{br(m, 2)}x" for m in mult_dem],
                                        ["SQL → venda usado na projeção"] + [f"{br(v * 100, 1)}%" for v in sql_usado]],
                             'nota': "A projeção mostra só a taxa usada em cada mês. A sazonalidade da demanda (Black Friday, Natal, férias) "
                                     "entra multiplicando a conversão de SQL em venda, e a fonte do índice está na tabela de premissas de mercado."}))
    if modelo == 'inside_sales' and (pc.get('cpm_crescimento') or any(abs(m - 1) > 1e-9 for m in mult_cpm)):
        letras = [chr(ord('B') + i) for i in range(n + 1)]
        cc = pc.get('cpm_crescimento') or [0, None, None]
        nota = ("A projeção mostra só o CPM usado em cada mês; aqui está de onde ele vem. "
                + (f"O CPM base parte de {rs(cpm_base[0], 2)} e sobe {br(cc[0] * 100, 1)}% ao mês até o Mês {cc[2] or n} pela saturação do público "
                   f"(premissa do usuário, sem benchmark), estável depois. " if cc[0] else "")
                + "O multiplicador soma eleição, datas comemorativas e remarketing (fontes na tabela de premissas de mercado).")
        metodologia.append(("CPM MÊS A MÊS · BASE, MULTIPLICADOR E CPM USADO NA PROJEÇÃO",
                            {'colunas': [""] + labels[:n], 'spans': [[l, l] for l in letras],
                             'linhas': [["CPM base (saturação do público)"] + [rs(x, 2) for x in cpm_base],
                                        ["Multiplicador (eleição, datas, remarketing)"] + [f"{br(m, 2)}x" for m in mult_cpm],
                                        ["CPM usado na projeção"] + [rs(x, 2) for x in cpm_usado]],
                             'nota': nota}))
    xm = json.load(open(extra_met, encoding='utf-8')) if extra_met else {}
    for titulo, conteudo in xm.get('secoes', []):   # seções de análise (ex.: recompra e reativação da base, com tabela de premissas)
        metodologia.append((titulo, conteudo))
    if obs: metodologia.append(("OBSERVAÇÕES", list(obs)))

    p = dict(sheet=rotulo, title=title, verba_plano=verba_plano, sazonalidade=pc.get('sazonalidade'), cpm_crescimento=pc.get('cpm_crescimento'), con_lead_mensal=col('con_lead') if any(col('con_lead')) else None, organico=pc.get('organico'), crm=pc.get('crm'), fee_plano=pc.get('fee_plano'),
             subtitle=(f"{esc(cliente)}   ·   Cenário {esc(cenario)}   ·   {labels[0]} a {labels[-1]}   ·   Meta de breakeven: {rot_mes(mes_alvo)}   ·   {v['status']}"
                       f"   ·   no azul a partir de: {rot_mes(azul_cont) if azul_cont else nunca}"
                       f"   ·   acumulado zera: {rot_mes(zera) if zera else nunca}"),
             meta_line=f"Atualizado em {{today}}   ·   Fonte: planilha de indicadores (aba {esc(det.get('aba'))})" + (" e GA4" if ga4.get('meses') else "") + f"   ·   Janela das taxas: {esc(', '.join(janela))}   ·   Detalhes na aba Premissas",
             footer=f"Projeção {rotulo} · {cliente}" + (f" · {marca}" if marca else ""), prem=prem, monthly=monthly, target=mes_alvo,
             metodologia=metodologia, historico=historico, pilot_ref=pilot_ref, base_ref=base_ref, n_months=n,
             real_prefill=prefill, month_labels=labels, envelope=envelope, metodologia_fim=[tuple(x) for x in xm.get('fim', [])], **extra)
    return (inside_sales_config if modelo == 'inside_sales' else ecommerce_config)(p), d

def comparar_cenarios(wb, abas_info, n):
    """No gráfico "Resultado acumulado mês a mês" de cada aba de projeção entram as linhas das outras abas (plano base × cenários),
    para o payback de cada cenário aparecer no mesmo gráfico. Lê as abas de apoio, então acompanha as premissas de cada aba."""
    from openpyxl.chart.series import SeriesLabel
    cores = {0: BLACK, 1: RED, 2: GRAY, 3: GREEN}
    for ws, info, nome_aba in abas_info:
        alvo = next((ch for ch in ws._charts if ch.title and ch.title.tx and ch.title.tx.rich
                     and ch.title.tx.rich.p[0].r and ch.title.tx.rich.p[0].r[0].t.startswith("Resultado acumulado")), None)
        if alvo is None: continue
        propria = next(j for j, (w, _, _) in enumerate(abas_info) if w is ws)
        alvo.series[0].tx = SeriesLabel(v="Plano base" if propria == 0 else nome_aba)
        for j, (_ws, inf, nome) in enumerate(abas_info):
            if _ws is ws or 'cum_cons' not in inf['M']: continue
            sup = wb[inf['support']]
            alvo.add_data(Reference(sup, min_col=3, max_col=2 + n, min_row=inf['M']['cum_cons'], max_row=inf['M']['cum_cons']), from_rows=True, titles_from_data=False)
            s = alvo.series[-1]; cor = cores.get(j, GRAY)
            s.tx = SeriesLabel(v="Plano base" if j == 0 else nome); s.smooth = False
            s.graphicalProperties.line.solidFill = cor; s.graphicalProperties.line.width = 22000; s.graphicalProperties.line.dashStyle = 'sysDash'
            s.marker.symbol = 'circle'; s.marker.size = 5
            s.marker.graphicalProperties = GraphicalProperties(solidFill=cor, ln=LineProperties(solidFill=cor))
        alvo.title = "Resultado acumulado mês a mês · plano base × " + ", ".join(nm for k, (_w, _i, nm) in enumerate(abas_info) if k > 0)


# ===================================================================== CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('saida', nargs='?', help="caminho do xlsx (modo demo)")
    ap.add_argument('--premissas', help="premissas.json gerado pelo modo projetar do piloto")
    ap.add_argument('--modelo', choices=['inside_sales', 'ecommerce'])
    ap.add_argument('--out', help="caminho do xlsx gerado")
    ap.add_argument('--cliente', help="nome do cliente para título e rodapé")
    ap.add_argument('--cenario', default="Realista")
    ap.add_argument('--marca', help="nome da agência no rodapé da planilha (ex.: sua agência)")
    ap.add_argument('--inicio-contrato', help="mês/ano em que o cliente entrou na V4 (ex.: agosto/2026); o Mês 1 passa a ser esse mês")
    ap.add_argument('--faturamento-total', help='faturamento total da loja por mês: "agosto/2026=143309.07,setembro/2026=82148.21"')
    ap.add_argument('--base-nao-midia', type=float, help='faturamento mensal fora da mídia V4 (base para projetar o total); calculado dos meses fechados se omitido')
    ap.add_argument('--margem-informativa', type=float, help='margem de contribuição só informativa (ex.: 0.05), fora do resultado')
    ap.add_argument('--sem-etapa-venda', action='store_true', help='e-commerce: pedido e venda são o mesmo evento na fonte')
    ap.add_argument('--metodologia-extra', help="JSON com seções extras da Metodologia: {'secoes': [[título, linhas ou tabela]], 'fim': [...]} (fim = depois de todas as tabelas, ex.: fontes)")
    ap.add_argument('--obs', action='append', help="observação extra para as notas do template (repetível)")
    ap.add_argument('--extra', action='append',
                    help='cenário extra em outra aba do mesmo arquivo: "premissas.json|Nome da aba|Nome do cenário|metodologia_extra.json" (repetível; os dois últimos campos são opcionais)')
    ap.add_argument('--conexao-so-lead', action='store_true',
                    help="inside sales: a linha Conexões da fonte conta só leads conectados; a conexão MQL fica em branco para preencher (sem taxa suposta)")
    a = ap.parse_args()
    wb = Workbook()
    if a.premissas:
        if not a.modelo: sys.exit("--premissas exige --modelo inside_sales|ecommerce")
        cfg, d = config_from_premissas(a.premissas, a.modelo, a.cliente, a.cenario, a.obs, a.inicio_contrato, a.marca,
                                      a.faturamento_total, a.base_nao_midia, a.margem_informativa, a.sem_etapa_venda, a.metodologia_extra,
                                      a.conexao_so_lead)
        ws = wb.active; ws.title = cfg['sheet']
        info = build_sheet(ws, cfg, LOGO)
        abas_info = [(ws, info, cfg['sheet'])]
        for ex in a.extra or []:   # cenários extras: cada um vira uma aba de projeção com a própria aba de premissas
            partes = ex.split('|')
            path2, aba2 = partes[0], partes[1]
            cen2 = partes[2] if len(partes) > 2 and partes[2] else a.cenario
            met2 = partes[3] if len(partes) > 3 and partes[3] else None
            cfg2, _ = config_from_premissas(path2, a.modelo, a.cliente, cen2, a.obs, a.inicio_contrato, a.marca, a.faturamento_total, a.base_nao_midia,
                                            a.margem_informativa, a.sem_etapa_venda, met2, a.conexao_so_lead)
            cfg2['sheet'], cfg2['title'] = aba2, f"{cfg2['title']} · {aba2}"
            ws2 = wb.create_sheet(); ws2.title = aba2
            abas_info.append((ws2, build_sheet(ws2, cfg2, LOGO), aba2))
        if len(abas_info) > 1:
            comparar_cenarios(wb, abas_info, int(cfg.get('n_months', 12)))
        out = a.out or f"Projecao_{a.modelo}_{re.sub(r'[^A-Za-z0-9]+', '_', a.cliente or 'cliente')}.xlsx"
        wb.save(out)
        print(json.dumps({"arquivo": out, "aba": cfg['sheet'], "veredito": d['veredito']['status'], "mes_alvo": d['premissas_confirmadas']['mes_alvo'],
                          "linhas_tabela": [info['HDR2'] + 1, info['LAST_TABLE']], "meta_top": info['META_TOP']}, ensure_ascii=False))
        return
    for i, cfg in enumerate([inside_sales_config(DEMO_IS), ecommerce_config(DEMO_EC)]):
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = cfg['sheet']
        info = build_sheet(ws, cfg, LOGO)
        print(cfg['sheet'], {k: info[k] for k in ('HDR2', 'META_TOP', 'LAST_TABLE', 'LAST_ROW', 'support')})
    wb.active = 0
    out = a.saida or a.out or os.path.join(os.path.dirname(HERE), "Projecao_Inside_Sales_e_Ecommerce.xlsx")
    wb.save(out); print("saved", out)

if __name__ == "__main__":
    main()
