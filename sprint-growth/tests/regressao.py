#!/usr/bin/env python3
"""Regressão da skill sprint-growth com dados sintéticos (sem rede). Rodar: python3 tests/regressao.py"""
import json, os, subprocess, sys, tempfile

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

# README: todo script citado existe (publicar.py não vai para a cópia pública)
RAIZ = os.path.join(AQUI, "..")
readme = open(os.path.join(RAIZ, "README.md")).read()
import re
faltando = sorted(n for n in set(re.findall(r"\b([a-z_]+\.py)\b", readme)) if n != "publicar.py"
                  and not any(os.path.exists(os.path.join(RAIZ, d, n)) for d in ("scripts", "tests")))
confere("README só cita scripts que existem" + (f" (faltam: {faltando})" if faltando else ""), not faltando)

print(f"\n{'TUDO OK' if not falhas else str(len(falhas)) + ' FALHA(S)'}")
sys.exit(1 if falhas else 0)
