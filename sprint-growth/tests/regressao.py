#!/usr/bin/env python3
"""Regressão da skill sprint-growth com dados sintéticos (sem rede). Rodar: python3 tests/regressao.py"""
import glob, json, os, re, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "scripts"))
import leads
from ads_auditoria import alertas
from gtm_auditoria import resolver
from termos_negativas import casa

falhas = []


def confere(nome, cond):
    print(("OK   " if cond else "FALHA ") + nome)
    if not cond:
        falhas.append(nome)


# leads
confere("telefone com +55 e sem 9 casam", leads.telefone("+55 (11) 97654-3210") == leads.telefone("11 7654-3210"))
confere("telefone curto vira None", leads.telefone("12345") is None)
confere("gmail sem pontos e +tag", leads.email("Fu.Lano+x@gmail.com") == leads.email("fulano@gmail.com"))
confere("teste por e-mail da agência", leads.e_teste(email_="joao@v4company.com"))
confere("teste por empresa", leads.e_teste(empresa="TESTE TECNICO - IGNORAR"))
confere("teste por telefone repetido", leads.e_teste(tel="(28) 00000-0000"))
confere("lead real não é teste", not leads.e_teste("Maria Souza", "maria.souza@gmail.com", "Construtora Alfa", "31988887777"))
confere("canal gclid = Google Ads", leads.canal({"gclid": "abc"}) == "Google Ads")
confere("canal utm_source 1202… = Meta Ads", leads.canal({"utm_source": "120200000000000001"}) == "Meta Ads")
confere("canal fbclid sem utm = Meta orgânico", leads.canal({"fbclid": "x", "referrer": "https://l.instagram.com/"}) == "Meta orgânico")
g = leads.pessoas([{"whatsapp": "11976543210", "email": "a@x.com"}, {"whatsapp": "", "email": "A@x.com"},
                   {"whatsapp": "(11) 7654-3210", "email": ""}, {"whatsapp": "21999999999", "email": ""}])
confere("pessoas agrupa por telefone OU e-mail", len(g) == 2)

# negativas: trava de palavra inteira
confere("negativa casa palavra inteira", casa("login", "sienge login"))
confere("negativa não casa pedaço", not casa("rdo", "saas-obra"))
confere("marca colada não casa produto", not casa("diariodeobra", "diario de obra online"))

# alertas do Ads com raw sintético
raw = {
    "conv_por_acao": [{"segments": {"conversionActionName": "00.4 MQL"}, "metrics": {"allConversions": 23}}],
    "conv_acoes": [
        {"conversionAction": {"name": "00.2 Lead", "category": "SUBMIT_LEAD_FORM", "type": "WEBPAGE", "primaryForGoal": True}},
        {"conversionAction": {"name": "00.4 MQL", "category": "SUBMIT_LEAD_FORM", "type": "WEBPAGE", "primaryForGoal": True}},
        {"conversionAction": {"name": "YouTube follow-on views", "category": "YOUTUBE_FOLLOW_ON_VIEWS", "type": "UNKNOWN", "primaryForGoal": True, "origin": "YOUTUBE_HOSTED"}}],
    "campanhas_todas": [{"campaign": {"name": f"HGG {i}", "startDateTime": "2026-07-31 16:0%d:00" % i}} for i in range(6)],
    "palavras_cassino": [{"campaign": {"name": "HGG 1"}, "adGroupCriterion": {"keyword": {"text": "Aviator"}}}],
    "campanhas_cfg": [{"campaign": {"name": "C01", "status": "ENABLED", "biddingStrategyType": "TARGET_SPEND", "targetSpend": {},
                                    "geoTargetTypeSetting": {"positiveGeoTargetType": "PRESENCE_OR_INTEREST"}},
                       "campaignBudget": {"amountMicros": "10000000"}}],
    "palavras": [], "parcela": [{"campaign": {"name": "C02"}, "segments": {"month": "2026-09-01"}, "metrics": {"searchRankLostImpressionShare": 0.58}}],
    "destinos": [{"landingPageView": {"unexpandedFinalUrl": "https://site.com.br"}, "metrics": {"costMicros": "5000000000"}},
                 {"landingPageView": {"unexpandedFinalUrl": "https://lp.site.com.br/"}, "metrics": {"costMicros": "849000000"}}],
    "gasto_diario": [{"segments": {"date": f"2026-09-{d:02d}"}, "metrics": {"costMicros": "97000000"}} for d in range(1, 15)],
}
cods = [c for c, _ in alertas(raw)]
for c in ("A1", "A2", "A3", "A4", "A5", "A7", "A9", "A10"):
    confere(f"alerta {c} dispara no caso sintético", c in cods)
confere("A1 aponta o Lead zerado e não o MQL", any("00.2 Lead" in t for c, t in alertas(raw) if c == "A1")
        and not any("00.4 MQL" in t for c, t in alertas(raw) if c == "A1"))

# GTM: resolve variável de rótulo
var = {"01 - Google Ads - Lead": {"parameter": [{"key": "value", "value": "AbCdEfGIjKlMnOpQr-"}]}}
confere("resolver lê o valor da variável", resolver("{{01 - Google Ads - Lead}}", var) == "AbCdEfGIjKlMnOpQr-")
confere("resolver mantém literal", resolver("abc", var) == "abc")
from gtm_auditoria import disparo_e_excecao
g5 = disparo_e_excecao([{"name": "02 - GADS - WhatsApp", "firingTriggerId": ["43"], "blockingTriggerId": ["43"]},
                        {"name": "01 - GAds - Cadastro", "firingTriggerId": ["24"], "blockingTriggerId": ["43"]}],
                       {"43": "POP UP - lead_whatsapp"})
confere("G5: mesmo acionador como disparo e exceção", len(g5) == 1 and "lead_whatsapp" in g5[0][1])

# termos_negativas ponta a ponta: recusa negativa que pega termo convertido
with tempfile.TemporaryDirectory() as d:
    raw_t = {"termos": [
        {"searchTermView": {"searchTerm": "sienge login"}, "metrics": {"costMicros": "50000000", "clicks": "10", "conversions": 0}},
        {"searchTermView": {"searchTerm": "diario de obra gratuito"}, "metrics": {"costMicros": "25000000", "clicks": "8", "conversions": 1}},
        {"searchTermView": {"searchTerm": "rdo digital"}, "metrics": {"costMicros": "90000000", "clicks": "30", "conversions": 5}}]}
    json.dump(raw_t, open(os.path.join(d, "raw.json"), "w"))
    json.dump({"acesso": ["login"], "armadilha": ["gratuito"]}, open(os.path.join(d, "neg.json"), "w"))
    subprocess.run([sys.executable, os.path.join(AQUI, "..", "scripts", "termos_negativas.py"), "--raw", os.path.join(d, "raw.json"),
                    "--negativas", os.path.join(d, "neg.json"), "--out", d], check=True, capture_output=True)
    res = json.load(open(os.path.join(d, "negativas.json")))
    confere("negativa sem conversão é aceita", [n["texto"] for n in res["negativas"]] == ["login"])
    confere("negativa que pega termo convertido é recusada", [n["texto"] for n in res["recusadas"]] == ["gratuito"])

# termos_negativas: "_nota" no arquivo do cliente é comentário, não grupo (quebrava com TypeError)
with tempfile.TemporaryDirectory() as d:
    json.dump({"termos": [{"searchTermView": {"searchTerm": "curso de pintura"}, "metrics": {"costMicros": "10000000", "clicks": "3", "conversions": 0}}]},
              open(os.path.join(d, "raw.json"), "w"))
    json.dump({"emprego": ["curso"]}, open(os.path.join(d, "neg.json"), "w"))
    json.dump({"_nota": "negativas do cliente", "fora": ["eletrostatica"]}, open(os.path.join(d, "extra.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(AQUI, "..", "scripts", "termos_negativas.py"), "--raw", os.path.join(d, "raw.json"),
                        "--negativas", os.path.join(d, "neg.json"), "--extra", os.path.join(d, "extra.json"), "--out", d], capture_output=True)
    confere("termos_negativas ignora \"_nota\" no --extra", r.returncode == 0 and os.path.exists(os.path.join(d, "negativas.json")))

# gtm_auditoria: o dump bruto nunca guarda segredo (token da CAPI, parâmetro accessToken)
from gtm_auditoria import mascarar
_m = mascarar({"server": {"variables": [{"name": "00 - Token CAPI", "parameter": [{"key": "value", "value": "EAAB" + "x" * 40}]},
                                         {"name": "00 - Pixel Id", "parameter": [{"key": "value", "value": "111122223333444"}]}],
                          "tags": [{"name": "CAPI Lead", "parameter": [{"key": "accessToken", "value": "segredo"}, {"key": "pixelId", "value": "{{00 - Pixel Id}}"}]}]}})
confere("gtm_auditoria mascara variável com nome de token", _m["server"]["variables"][0]["parameter"][0]["value"] == "***")
confere("gtm_auditoria mascara parâmetro accessToken", _m["server"]["tags"][0]["parameter"][0]["value"] == "***")
confere("gtm_auditoria mantém ID do Pixel e referências", _m["server"]["variables"][1]["parameter"][0]["value"] == "111122223333444"
        and _m["server"]["tags"][0]["parameter"][1]["value"] == "{{00 - Pixel Id}}")
confere("gtm_auditoria mascara token do Meta em qualquer campo", mascarar({"x": "EAAB" + "y" * 40}) == {"x": "***"})

# preflight: lógica do pré-voo, sem rede
import preflight as _pf
_b = _pf.briefing_pendentes("## 1. Dinheiro\n\n| Pergunta | Resposta | Onde |\n| --- | --- | --- |\n| Fee | R$ 4 mil | |\n| Margem | | DRE |\n")
confere("preflight conta respondidas e em branco no briefing", _b == {"1. Dinheiro": (1, 2)})
_modelo = _pf.briefing_pendentes(open(os.path.join(AQUI, "..", "templates", "cliente", "briefing.md")).read())
confere("modelo de briefing tem os 5 blocos, todos em branco", len(_modelo) == 5 and all(v[0] == 0 and v[1] > 0 for v in _modelo.values()))
confere("preflight: campanhas suspensas viram atenção",
        _pf.status_ads("1", {"descriptiveName": "X"}, [("c", "ENABLED", "SUSPENDED")], 0)["status"] == "atencao")
confere("preflight: conta não encontrada vira falta", _pf.status_ads("1", None, [], 0)["status"] == "falta")
confere("preflight: conta veiculando com gasto é ok",
        _pf.status_ads("1", {"descriptiveName": "X"}, [("c", "ENABLED", "SERVING")], 150.0)["status"] == "ok")
confere("preflight: LP sem GTM nem GA4 no HTML vira atenção (banner de cookies)",
        _pf.status_pagina("LP", "u", 200, "<html>greatpages</html>")["status"] == "atencao")
confere("preflight: GA4 de outra conta no site vira atenção",
        _pf.status_pagina("site", "u", 200, "gtag('config','G-SITE0000XX') GTM-ABC1234", ["G-LPLP0000YY"], False)["status"] == "atencao")
confere("preflight: página com GTM e GA4 conhecido é ok",
        _pf.status_pagina("LP", "u", 200, "GTM-ABC1234 G-LPLP0000YY", ["G-LPLP0000YY"])["status"] == "ok")
confere("preflight: 401 do CRM vira falta", _pf.status_http("CRM", "Kommo", 401)["status"] == "falta")
_md = _pf.render("cli", [_pf.r("CRM", "k", "ok", "200"), _pf.r("GA4", "site", "atencao", "sem propriedade")], _b)
confere("preflight: relatório lista o que expira e o briefing", "Pedir hoje (expira)" in _md and "1. Dinheiro" in _md and "1 ok" in _md)
_sk = open(os.path.join(AQUI, "..", "SKILL.md")).read()
confere("SKILL.md manda rodar o pré-voo e o briefing", "preflight.py" in _sk and "briefing.md" in _sk and "entrevista.md" in _sk)
confere("referencias/entrevista.md existe com perecíveis e formatos", all(x in open(os.path.join(AQUI, "..", "referencias", "entrevista.md")).read()
        for x in ("## O que expira", "## Formato dos exports", "90 dias")))

# publicar: IDs dos config.json de clientes nunca vão para a cópia pública (nome anonimizado não basta)
import publicar as _pub
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "clientes", "x"))
    json.dump({"_nota": "123456789", "ga4": {"fluxo": "G-ABCD1234EF"}, "meta": {"conjunto_de_dados": "999988887777666"}, "site": "https://x.com"},
              open(os.path.join(d, "clientes", "x", "config.json"), "w"))
    _ids = _pub.ids_de_clientes(d)
    confere("publicar coleta IDs dos configs de clientes (e ignora _nota e URLs)", _ids == ["999988887777666", "G-ABCD1234EF"])

# cnpj: validação e classificação (sem rede)
import cnpj
confere("CNPJ válido passa no dígito", cnpj.valida("11.222.333/0001-81"))
confere("CNPJ com dígito errado falha", not cnpj.valida("11.222.333/0001-82"))
confere("CNPJ repetido falha", not cnpj.valida("11111111111111"))
ativa = {"descricao_situacao_cadastral": "ATIVA", "cnae_fiscal": 4120400, "opcao_pelo_mei": False}
confere("construtora ativa = Qualificado", cnpj.classifica("11.222.333/0001-81", ativa)[0] == "Qualificado")
confere("MEI de construção = Parcial", cnpj.classifica("11.222.333/0001-81", dict(ativa, opcao_pelo_mei=True))[0] == "Parcial")
confere("setor só no secundário = Parcial", cnpj.classifica("11.222.333/0001-81", dict(ativa, cnae_fiscal=8121400,
        cnaes_secundarios=[{"codigo": 4399103}]))[0] == "Parcial")
confere("CNPJ baixado = Fora do perfil", cnpj.classifica("11.222.333/0001-81", dict(ativa, descricao_situacao_cadastral="BAIXADA"))[0] == "Fora do perfil")
confere("CPF no campo = Fora do perfil", cnpj.classifica("123.456.789-09", {})[1] == "CPF no lugar do CNPJ")
confere("texto no campo = Fora do perfil", cnpj.classifica("Sim", {})[1] == "sem CNPJ válido")
confere("tira CPF do nome do MEI", cnpj.limpa_nome("JOAO DA SILVA 12345678901") == "JOAO DA SILVA"
        and cnpj.limpa_nome("62.906.080 IZAQUE CARVALHO") == "IZAQUE CARVALHO")

# datacrazy: lead novo x cliente antigo, e credencial fora do arquivo
import datacrazy
neg = {"createdAt": "2026-09-10T15:00:00Z"}
confere("negócio no dia do cadastro = novo", datacrazy.novo_ou_antigo(neg, {"createdAt": "2026-09-10T14:00:00Z"}) == "novo")
confere("negócio de lead antigo = antigo", datacrazy.novo_ou_antigo(neg, {"createdAt": "2026-05-01T14:00:00Z"}) == "antigo")
conv = datacrazy.sem_credencial({"instance": {"id": "i", "name": "Oficial", "provider": "WHATSAPP_CLOUD_API",
                                              "config": {"token": "token-ficticio-segredo"}}, "contact": {"externalInfo": {"x": 1}}})
confere("conversa gravada sem token do WhatsApp", "segredo" not in json.dumps(conv))
negs = [{"createdAt": "2026-09-10T15:00:00Z", "leadId": "a", "status": "won", "statusChangedAt": "2026-09-10T16:00:00Z",
         "total": 100, "stage": {"pipeline": {"name": "Vendas"}}},
        {"createdAt": "2026-09-11T15:00:00Z", "leadId": "b", "status": "lost", "stage": {"pipeline": {"name": "Vendas"}}}]
saf, fec = datacrazy.resumo(negs, [{"id": "a", "createdAt": "2026-03-01T10:00:00Z"}, {"id": "b", "createdAt": "2026-09-11T14:00:00Z"}], ["Vendas"])
confere("resumo separa safra novo x antigo", saf["2026-09"]["antigo"] == [1, 1] and saf["2026-09"]["novo"] == [1, 0])
confere("resumo soma valor ganho de cliente antigo", fec["2026-09"]["antigo"][1] == 100)

# consolidar: validação, faixa de impacto, ordem, divergência entre frentes
import consolidar
base_ach = {"id": "X-01", "titulo": "t", "evidencia": "e", "etapa": "trafego", "tipo": "otimizacao", "confianca": "alta",
            "correcao": "c", "esforco": "1 h", "verificacao": "v", "impacto": None}
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "achados"))
    def grava(nome, obj):
        json.dump(obj, open(os.path.join(d, "achados", nome), "w"))
    grava("google-ads.json", {"frente": "google-ads", "fontes": [], "numeros": {"leads_google": {"valor": 212, "unidade": "conversões", "fonte": "Ads"}},
          "achados": [dict(base_ach, id="ADS-01", impacto={"volume": 100, "ganho_min": 0.1, "ganho_max": 0.2, "taxas_seguintes": 0.5, "ticket": 1000}),
                      dict(base_ach, id="ADS-02", tipo="medicao", etapa="medicao")],
          "nao_medido": ["offline"], "perguntas": ["qual conta?"]})
    grava("fontes.json", {"frente": "fontes", "numeros": {"leads_google": {"valor": 131, "unidade": "pessoas", "fonte": "backup"}}, "achados": []})
    grava("meta-ads.json", {"frente": "meta-ads", "achados": [dict(base_ach, id="META-01", esforco="rápido")]})
    res = consolidar.consolidar(d, ["fontes", "google-ads", "meta-ads", "comercial"])
    confere("consolidar recusa esforço fora da lista", any("META-01" in p and "esforço" in p for p in res["problemas"]))
    confere("consolidar lista frente faltando", set(res["faltando"]) == {"meta-ads", "comercial"})
    confere("consolidar põe medição antes de impacto", [a["id"] for a in res["achados"]] == ["ADS-02", "ADS-01"])
    confere("consolidar calcula faixa de impacto", res["achados"][1]["impacto_rs"] == (5000.0, 10000.0))
    confere("consolidar aponta divergência plataforma × backup", [v["numero"] for v in res["divergencias"]] == ["leads_google"])
    confere("consolidar junta não medido e perguntas", len(res["nao_medido"]) == 1 and len(res["perguntas"]) == 1)
    confere("markdown do consolidado sai com ranking", "| 1 | ADS-02 |" in consolidar.markdown(res))
confere("impacto sem base = None", consolidar.faixa(None) is None)

# clarity: leitura tolerante e alertas C1–C6 (sem rede)
import clarity
resp = [{"metricName": "Traffic", "information": [
            {"totalSessionCount": "1000", "totalBotSessionCount": "400", "distantUserCount": "900", "PagesPerSessionPercentage": 1.4}]}]
resp_url = [{"metricName": "Traffic", "information": [{"totalSessionCount": "200", "totalBotSessionCount": "0", "URL": "https://lp.x/"},
                                                      {"totalSessionCount": "10", "totalBotSessionCount": "0", "URL": "https://x/pouca"}]},
            {"metricName": "Rage Click Count", "information": [{"sessionsWithMetricPercentage": 7.5, "URL": "https://lp.x/"},
                                                               {"sessionsWithMetricPercentage": 50, "URL": "https://x/pouca"}]},
            {"metricName": "QuickbackClick", "information": [{"sessionsWithMetricPercentage": 12, "sessionsWithoutMetricPercentage": 88, "URL": "https://lp.x/"}]},
            {"metricName": "DeadClickCount", "information": [{"campoNovo": 3, "URL": "https://lp.x/"}]}]
resp_disp = [{"metricName": "Traffic", "information": [{"totalSessionCount": "700", "Device": "Mobile"}, {"totalSessionCount": "300", "Device": "PC"}]},
             {"metricName": "ScrollDepth", "information": [{"averageScrollDepth": 30, "Device": "Mobile"}, {"averageScrollDepth": 60, "Device": "PC"}]}]
tab, estranhos = clarity.linhas(resp_url)
lp = tab[(("URL", "https://lp.x/"),)]
confere("clarity normaliza nome de métrica com espaço", lp.get("clique_raiva") == 7.5)
confere("clarity ignora o percentual 'without'", lp.get("volta_rapida") == 12)
confere("clarity lista campo não reconhecido", "DeadClickCount.campoNovo" in estranhos)
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "raw"))
    for dia, nome, r in (("2026-09-28", "total", resp), ("2026-09-29", "total", resp), ("2026-09-29", "url", resp_url),
                         ("2026-09-29", "dispositivo", resp_disp)):
        json.dump({"coletado_em": dia + "T12:00:00+00:00", "dias": 1, "dimensoes": [], "resposta": r},
                  open(os.path.join(d, "raw", f"{dia}_{nome}.json"), "w"))
    planos, _, datas = clarity.acumular(d)
    confere("clarity soma sessões de coletas diárias", planos["total"][()]["sessoes"] == 2000)
    cods = [c for c, _ in clarity.alertas(planos)]
    confere("clarity C1 robôs acima de 30%", "C1" in cods)
    confere("clarity C2 raiva e C4 volta rápida na LP", "C2" in cods and "C4" in cods)
    confere("clarity ignora página com poucas sessões", not any("pouca" in t for _, t in clarity.alertas(planos)))
    confere("clarity C6 rolagem do celular", "C6" in cods)
    clarity.resumo(d, 30)
    confere("clarity grava resumo com campo não reconhecido", "campoNovo" in open(os.path.join(d, "clarity_resumo.md")).read())

# agentes: frontmatter, somente leitura, scripts citados e cópia instalada
RAIZ = os.path.join(AQUI, "..")
ESCRITA = re.compile(r"__\w*(create|update|delete|publish|activate|mutate|upload|trash|send|boost|finalize)", re.I)
agentes = sorted(glob.glob(os.path.join(RAIZ, "agentes", "sprint-*.md")))
confere("8 agentes de frente", len(agentes) == 8)
FRENTES_AG = {"sprint-" + f for f in consolidar.FRENTES}
for p in agentes:
    txt = open(p, encoding="utf-8").read()
    nome = os.path.basename(p)[:-3]
    fm = txt.split("---")[1] if txt.startswith("---") else ""
    campos = dict(l.split(":", 1) for l in fm.strip().splitlines() if ":" in l)
    confere(f"{nome}: name bate com o arquivo e com uma frente", campos.get("name", "").strip() == nome and nome in FRENTES_AG)
    confere(f"{nome}: tem description e tools", campos.get("description", "").strip() and campos.get("tools", "").strip())
    confere(f"{nome}: nenhuma ferramenta de escrita liberada", not ESCRITA.search(campos.get("tools", "")))
    faltam = [n for n in set(re.findall(r"scripts/([a-z_]+\.py)", txt)) if not os.path.exists(os.path.join(RAIZ, "scripts", n))]
    confere(f"{nome}: scripts citados existem" + (f" (faltam {faltam})" if faltam else ""), not faltam)
    confere(f"{nome}: grava achados no contrato", f"achados/{nome[7:]}.json" in txt)
if os.path.basename(os.path.dirname(os.path.abspath(RAIZ))) == "skills":  # só na instalação local, não na cópia pública
    import instalar_agentes
    dif = instalar_agentes.diferencas(instalar_agentes.destino_padrao())
    confere("agentes instalados batem com a fonte" + (f" ({dif})" if dif else ""), not dif)

# catálogo de auditoria e correção: cobertura de 100%, README e agentes coerentes
import catalogo
cat = catalogo.carregar()
prob = catalogo.conferir(cat)
confere("catálogo íntegro (todo item de auditoria tem correção)" + (f" ({prob[:3]})" if prob else ""), not prob)
confere("catálogo cobre as 8 frentes", {a["Frente"] for a in cat["auditoria"].values()} == set(catalogo.FRENTES))
confere("README traz a tabela de cobertura do catálogo", catalogo.resumo(cat) in open(os.path.join(RAIZ, "README.md")).read())
for f in catalogo.FRENTES:
    confere(f"agente sprint-{f} lista os itens pelo catálogo",
            f"catalogo.py --frente {f}" in open(os.path.join(RAIZ, "agentes", f"sprint-{f}.md"), encoding="utf-8").read())
with tempfile.TemporaryDirectory() as d:
    open(os.path.join(d, "x.md"), "w").write(
        "# X\n\n## Auditoria\n\n| " + " | ".join(catalogo.COLS_AUD) + " |\n|" + " --- |" * 6 + "\n"
        "| X1 | a | fontes | b | c | alta |\n| X2 | a | fontes | b | c | baixa |\n\n## Correção\n\n| "
        + " | ".join(catalogo.COLS_COR) + " |\n|" + " --- |" * 8 + "\n| CX-X1 | a | X1, X9 | b | c | R4 | d | e |\n")
    p2 = catalogo.conferir(catalogo.carregar(d))
    confere("catálogo reprova item sem correção", any("X2 sem nenhuma correção" in x for x in p2))
    confere("catálogo reprova risco fora de R1–R3 e id inexistente",
            any("risco 'R4'" in x for x in p2) and any("X9, que não existe" in x for x in p2))
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "achados"))
    itens = catalogo.por_frente(cat, "google-ads")
    cob = {i: "ok" for i in itens if i != "A1"}
    json.dump({"frente": "google-ads", "cobertura": cob, "achados": []}, open(os.path.join(d, "achados", "google-ads.json"), "w"))
    json.dump({"frente": "clarity", "cobertura": {"C1": "ok", "A2": "ok", "C2": "talvez"},
               "achados": [dict(base_ach, id="CLA-01", item="C9", correcao_id="CX-C99")]},
              open(os.path.join(d, "achados", "clarity.json"), "w"))
    res = consolidar.consolidar(d, ["google-ads", "clarity"])
    c = res["cobertura"].get("google-ads", {})
    confere("consolidado conta a cobertura da frente", c.get("itens") == len(itens) and c.get("nao_verificados") == ["A1"])
    confere("consolidado destaca crítico sem status", c.get("criticos_sem_status") == ["A1"])
    confere("consolidado recusa id de outra frente, status inválido, item e correção inexistentes",
            any("A2 é da frente google-ads" in x for x in res["problemas"]) and any("'talvez'" in x for x in res["problemas"])
            and any("item C9" in x for x in res["problemas"]) and any("CX-C99" in x for x in res["problemas"]))
    confere("markdown do consolidado mostra a cobertura", "Cobertura do catálogo" in consolidar.markdown(res))

# desenhos: os SVG de assets/ são os que o gerador produz hoje (ninguém edita à mão, nada fica velho)
import desenhos
for nome, fn in (("capa.svg", desenhos.capa), ("fluxo.svg", desenhos.fluxo), ("agentes.svg", desenhos.agentes)):
    arq = os.path.join(RAIZ, "assets", nome)
    confere(f"assets/{nome} bate com scripts/desenhos.py", os.path.exists(arq) and open(arq, encoding="utf-8").read() == fn())
confere("desenho de agentes lista as 8 frentes", len(desenhos.AGENTES) == 8 and len(desenhos.FRENTES_ONDA2) == 7)

# README: todo script citado existe (publicar.py não vai para a cópia pública)
readme = open(os.path.join(RAIZ, "README.md")).read()
import re
faltando = sorted(n for n in set(re.findall(r"\b([a-z_]+\.py)\b", readme)) if n != "publicar.py"
                  and not any(os.path.exists(os.path.join(RAIZ, d, n)) for d in ("scripts", "tests")))
confere("README só cita scripts que existem" + (f" (faltam: {faltando})" if faltando else ""), not faltando)

print(f"\n{'TUDO OK' if not falhas else str(len(falhas)) + ' FALHA(S)'}")
sys.exit(1 if falhas else 0)
