#!/usr/bin/env python3
"""Auditoria do Google Ads (somente leitura) com os alertas que já pegaram cliente real.

  python3 scripts/ads_auditoria.py --conta 1234567890 --inicio 2026-07-01 --fim 2026-09-28 \
      --out clientes/<cliente>/ads [--mcp googleads_diretas] [--site https://dominio.com.br/]

Grava <out>/ads_raw.json (tudo que veio da API) e <out>/ads_resumo.md (alertas + tabelas).
Alertas:
  A1 conversão principal sem nenhum registro no período (rótulo errado no GTM — SaaS de diário de obra)
  A2 mais de uma conversão principal na mesma categoria (lead contado 2 vezes)
  A3 conversão principal de YouTube/chamada/importação sem uso
  A4 campanhas com nome estranho, criadas em rajada ou com palavras de cassino (conta invadida — SaaS de diário de obra)
  A5 Maximizar cliques sem teto de CPC; segmentação "presença ou interesse"
  A6 palavra com índice de qualidade <= 3 e gasto relevante
  A7 parcela de impressões perdida por classificação > 40%
  A8 sitelink apontando para âncora que não existe no site (--site)
  A9 anúncios levando para mais de um domínio/página (troca de destino no meio do período)
  A10 orçamento diário muito abaixo do gasto médio recente
"""
import argparse, json, os, re, sys, urllib.request
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_http import MCP

M = lambda v: int(v or 0) / 1e6
CASSINO = re.compile(r"aviator|sugar ?rush|crash|coin ?flip|dice|slot|casino|cassino|bet\b|towers? game|bonanza|jackpot", re.I)


def consultas(ini, fim):
    per = f"segments.date >= '{ini}' AND segments.date <= '{fim}'"
    return {
        "conta": "SELECT customer.descriptive_name, customer.currency_code, customer.time_zone, customer.auto_tagging_enabled FROM customer",
        "campanhas_mes": f"SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, campaign.bidding_strategy_type, segments.month, metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions FROM campaign WHERE {per} AND metrics.impressions > 0",
        "campanhas_cfg": "SELECT campaign.id, campaign.name, campaign.status, campaign.start_date_time, campaign.bidding_strategy_type, campaign.target_spend.cpc_bid_ceiling_micros, campaign_budget.amount_micros, campaign.geo_target_type_setting.positive_geo_target_type, campaign.tracking_url_template, campaign.final_url_suffix FROM campaign WHERE campaign.status != 'REMOVED'",
        "campanhas_todas": "SELECT campaign.id, campaign.name, campaign.status, campaign.start_date_time FROM campaign",
        "conv_acoes": "SELECT conversion_action.id, conversion_action.name, conversion_action.type, conversion_action.category, conversion_action.status, conversion_action.primary_for_goal, conversion_action.origin, conversion_action.counting_type FROM conversion_action WHERE conversion_action.status = 'ENABLED'",
        "conv_por_acao": f"SELECT segments.conversion_action_name, metrics.conversions, metrics.all_conversions FROM campaign WHERE {per}",
        "metas_campanha": "SELECT campaign.name, campaign_conversion_goal.category, campaign_conversion_goal.origin, campaign_conversion_goal.biddable FROM campaign_conversion_goal WHERE campaign.status = 'ENABLED'",
        "parcela": f"SELECT campaign.name, segments.month, metrics.search_impression_share, metrics.search_budget_lost_impression_share, metrics.search_rank_lost_impression_share, metrics.average_cpc FROM campaign WHERE {per} AND campaign.advertising_channel_type = 'SEARCH' AND campaign.status != 'REMOVED' AND metrics.impressions > 0",
        "palavras": f"SELECT campaign.name, ad_group.name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.status, ad_group_criterion.quality_info.quality_score, ad_group_criterion.quality_info.post_click_quality_score, ad_group_criterion.quality_info.search_predicted_ctr, ad_group_criterion.quality_info.creative_quality_score, metrics.cost_micros, metrics.clicks, metrics.conversions FROM keyword_view WHERE {per}",
        "termos": f"SELECT campaign.name, search_term_view.search_term, metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions FROM search_term_view WHERE {per}",
        "destinos": f"SELECT landing_page_view.unexpanded_final_url, segments.week, metrics.cost_micros, metrics.clicks, metrics.conversions FROM landing_page_view WHERE {per}",
        "sitelinks": "SELECT campaign.name, asset.id, asset.sitelink_asset.link_text, asset.final_urls, campaign_asset.status FROM campaign_asset WHERE campaign_asset.field_type = 'SITELINK' AND campaign_asset.status != 'REMOVED' AND campaign.status = 'ENABLED'",
        "acessos": "SELECT customer_user_access.email_address, customer_user_access.access_role, customer_user_access.access_creation_date_time, customer_user_access.inviter_user_email_address FROM customer_user_access",
        "palavras_cassino": "SELECT campaign.name, campaign.status, ad_group_criterion.keyword.text FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD'",
        "gasto_diario": f"SELECT segments.date, metrics.cost_micros FROM customer WHERE {per}",
    }


def puxar(ads, conta, ini, fim):
    raw = {}
    for nome, q in consultas(ini, fim).items():
        try:
            raw[nome] = ads.gaql(conta, q)
        except Exception as e:  # uma consulta falhar não derruba a auditoria
            raw[nome] = {"erro": str(e)[:300]}
    return raw


def linhas(raw, k):
    v = raw.get(k)
    return v if isinstance(v, list) else []


def ancoras_do_site(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Chrome/126"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        return set(re.findall(r'\sid="([^"]+)"', html))
    except Exception:
        return None


def alertas(raw, site=None):
    out = []
    # A1/A2/A3 conversões
    registros = defaultdict(float)
    for x in linhas(raw, "conv_por_acao"):
        registros[x["segments"]["conversionActionName"]] += float(x["metrics"].get("allConversions", 0))
    principais = [x["conversionAction"] for x in linhas(raw, "conv_acoes") if x["conversionAction"].get("primaryForGoal")]
    for c in principais:
        if registros.get(c["name"], 0) == 0:
            out.append(("A1", f"Conversão principal \"{c['name']}\" ({c['category']}) sem nenhum registro no período. Conferir rótulo e disparo no GTM."))
        if c["type"] in ("UNKNOWN", "UPLOAD_CALLS") or c.get("origin") in ("YOUTUBE_HOSTED",):
            out.append(("A3", f"\"{c['name']}\" ({c['type']}) está como principal e não é conversão de negócio."))
    por_cat = defaultdict(list)
    for c in principais:
        por_cat[c["category"]].append(c["name"])
    for cat, nomes in por_cat.items():
        if len(nomes) > 1:
            out.append(("A2", f"{len(nomes)} conversões principais na categoria {cat}: {', '.join(nomes)}. O mesmo lead pode contar mais de uma vez."))
    # A4 invasão
    datas = defaultdict(list)
    for x in linhas(raw, "campanhas_todas"):
        c = x["campaign"]
        datas[(c.get("startDateTime") or "")[:13]].append(c["name"])
    for hora, nomes in datas.items():
        if len(nomes) >= 5:
            out.append(("A4", f"{len(nomes)} campanhas criadas na mesma hora ({hora}h): {', '.join(nomes[:4])}… Conferir se é invasão."))
    cassino = [x for x in linhas(raw, "palavras_cassino") if CASSINO.search(x["adGroupCriterion"]["keyword"]["text"])]
    if cassino:
        camps = sorted({x["campaign"]["name"] for x in cassino})
        out.append(("A4", f"{len(cassino)} palavras de cassino/apostas em {len(camps)} campanhas ({', '.join(camps[:3])}…). Revisar acessos e 2 etapas."))
    # A5 lances e local
    for x in linhas(raw, "campanhas_cfg"):
        c = x["campaign"]
        if c["status"] != "ENABLED":
            continue
        if c.get("biddingStrategyType") == "TARGET_SPEND" and not int(c.get("targetSpend", {}).get("cpcBidCeilingMicros", 0) or 0):
            out.append(("A5", f"\"{c['name']}\": Maximizar cliques sem teto de CPC."))
        if c.get("geoTargetTypeSetting", {}).get("positiveGeoTargetType") == "PRESENCE_OR_INTEREST":
            out.append(("A5", f"\"{c['name']}\": segmentação por \"presença ou interesse\"."))
    # A6 índice de qualidade
    kw = defaultdict(lambda: [0.0, 0.0, None])
    for x in linhas(raw, "palavras"):
        k = x["adGroupCriterion"]
        a = kw[(x["campaign"]["name"], k["keyword"]["text"])]
        a[0] += M(x["metrics"].get("costMicros"))
        a[1] += float(x["metrics"].get("conversions", 0))
        a[2] = k.get("qualityInfo", {}).get("qualityScore") or a[2]
    total_kw = sum(v[0] for v in kw.values()) or 1
    for (camp, texto), (custo, conv, qs) in sorted(kw.items(), key=lambda z: -z[1][0]):
        if qs and qs <= 3 and custo / total_kw > 0.05:
            out.append(("A6", f"\"{texto}\" ({camp[:20]}): nota {qs}, R$ {custo:,.0f} ({custo/total_kw:.0%} do gasto), {conv:g} conv."))
    # A7 parcela
    for x in linhas(raw, "parcela"):
        perdida = float(x["metrics"].get("searchRankLostImpressionShare", 0) or 0)
        if perdida > 0.40:
            out.append(("A7", f"\"{x['campaign']['name'][:30]}\" em {x['segments']['month'][:7]}: {perdida:.0%} das impressões perdidas por classificação."))
    # A8 sitelinks
    if site:
        ids = ancoras_do_site(site)
        if ids is not None:
            for x in linhas(raw, "sitelinks"):
                for u in x["asset"].get("finalUrls", []):
                    if "#" in u and u.split("#", 1)[1] not in ids:
                        out.append(("A8", f"Sitelink \"{x['asset']['sitelinkAsset']['linkText']}\" aponta para #{u.split('#',1)[1]}, que não existe no site."))
    # A9 destinos
    dom = defaultdict(float)
    for x in linhas(raw, "destinos"):
        u = x["landingPageView"].get("unexpandedFinalUrl", "")
        d = re.sub(r"^https?://", "", u).split("/")[0]
        dom[d] += M(x["metrics"].get("costMicros"))
    principais_dom = [d for d, v in dom.items() if v > 50]
    if len(principais_dom) > 1:
        out.append(("A9", "Anúncios levaram para mais de um destino no período: " + ", ".join(f"{d} R$ {dom[d]:,.0f}" for d in principais_dom) + ". Comparar conversão por destino."))
    # A10 orçamento
    gasto = sorted((x["segments"]["date"], M(x["metrics"].get("costMicros"))) for x in linhas(raw, "gasto_diario"))
    media14 = sum(v for _, v in gasto[-14:]) / max(len(gasto[-14:]), 1)
    orc = sum(M(x["campaignBudget"]["amountMicros"]) for x in linhas(raw, "campanhas_cfg") if x["campaign"]["status"] == "ENABLED")
    if orc and media14 and orc < 0.6 * media14:
        out.append(("A10", f"Orçamento diário somado R$ {orc:,.0f} contra gasto médio de R$ {media14:,.0f}/dia nos últimos 14 dias."))
    return out


def resumo(raw, al, conta):
    nome = (linhas(raw, "conta") or [{}])[0].get("customer", {}).get("descriptiveName", conta)
    L = [f"# Auditoria Google Ads · {nome} ({conta})", "", "## Alertas", ""]
    L += [f"- **{c}** {t}" for c, t in al] or ["- Nenhum alerta."]
    mes = defaultdict(float)
    for x in linhas(raw, "campanhas_mes"):
        mes[(x["campaign"]["name"][:45], x["segments"]["month"][:7])] += M(x["metrics"].get("costMicros"))
    L += ["", "## Gasto por campanha e mês (R$)", "", "| Campanha | Mês | Gasto |", "| --- | --- | --- |"]
    L += [f"| {c} | {m} | {v:,.2f} |" for (c, m), v in sorted(mes.items())]
    L += ["", "## Acessos à conta", ""]
    L += [f"- {x['customerUserAccess'].get('emailAddress')} · {x['customerUserAccess'].get('accessRole')} · desde {x['customerUserAccess'].get('accessCreationDateTime','')[:10]}" for x in linhas(raw, "acessos")]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conta", required=True)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fim", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mcp", default="googleads_diretas", help="googleads_diretas | googleads_squad | googleads_nayara")
    ap.add_argument("--site", help="URL do site para conferir as âncoras dos sitelinks")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    raw = puxar(MCP(a.mcp), a.conta, a.inicio, a.fim)
    json.dump(raw, open(os.path.join(a.out, "ads_raw.json"), "w"), ensure_ascii=False, indent=1)
    al = alertas(raw, a.site)
    open(os.path.join(a.out, "ads_resumo.md"), "w").write(resumo(raw, al, a.conta))
    erros = [k for k, v in raw.items() if isinstance(v, dict)]
    print(f"{len(al)} alertas · consultas com erro: {erros or 'nenhuma'} · {a.out}/ads_resumo.md")
    for c, t in al:
        print(f"  {c} {t}")


if __name__ == "__main__":
    main()
