"""
Corrige o container GTM-KG7X38D6 conforme auditoria:
- Variaveis JS: troca placeholders pelos seletores reais da LP
- API Transport: troca dominio placeholder pelo SSGTM stape (whhhlqap.sac.stape.io)
- Despausa tags CAPI e atribui triggers corretos
- Troca trigger Lead de gtm.formSubmit para /obrigado (trigger 37)
- Adiciona email (em) no Advanced Matching do Pixel Lead
- Adiciona trigger na tag GA4 WhatsApp
- Cria variaveis: ambiente, metragem, is_mql
- Cria trigger MQL e 4 novas tags MQL (Meta Pixel + CAPI + Google Ads + GA4)
"""
import json
import copy

SRC = r"C:\Users\User\Downloads\GTM-KG7X38D6_workspace4.json"
DST = r"C:\Users\User\Downloads\GTM-KG7X38D6_workspace4_FIXED.json"

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

cv = data["containerVersion"]
tags = cv["tag"]
triggers = cv["trigger"]
variables = cv["variable"]

ACC = "4226126032"
CONT = "248559899"

# ---------- 1) Corrigir variaveis JS placeholder ----------
JS_FIXES = {
    "4": (
        'cJS - nome - form',
        'function () {\n'
        '    var el = document.querySelector(\'input[name="seu-nome"]\');\n'
        '    return el ? el.value.trim() : undefined;\n'
        '}'
    ),
    "25": (
        'cJS - email - form',
        'function () {\n'
        '    var el = document.querySelector(\'input[name="seu-e-mail"]\');\n'
        '    return el ? el.value.trim().toLowerCase() : undefined;\n'
        '}'
    ),
    "27": (
        'cJS - telefone - form',
        'function () {\n'
        '    var el = document.querySelector(\'input[name="seu-telefonewhatsapp"]\');\n'
        '    if (!el) return undefined;\n'
        '    var num = el.value.replace(/\\D/g, "");\n'
        '    return num ? "55" + num : undefined;\n'
        '}'
    ),
}

for v in variables:
    vid = v["variableId"]
    if vid in JS_FIXES:
        _, new_js = JS_FIXES[vid]
        for p in v["parameter"]:
            if p["key"] == "javascript":
                p["value"] = new_js

# ---------- 2) API Transport: trocar dominio placeholder ----------
SSGTM_URL = "https://whhhlqap.sac.stape.io"
for v in variables:
    if v["variableId"] == "13":  # 00.1 - API Transport
        for p in v["parameter"]:
            if p["key"] == "value":
                p["value"] = SSGTM_URL

# ---------- 3) Criar novas variaveis: ambiente, metragem, is_mql ----------
def next_id(items, key):
    return str(max(int(x[key]) for x in items) + 1)

new_var_ambiente_id = next_id(variables, "variableId")
new_var_metragem_id = str(int(new_var_ambiente_id) + 1)
new_var_ismql_id = str(int(new_var_ambiente_id) + 2)

variables.append({
    "accountId": ACC, "containerId": CONT,
    "variableId": new_var_ambiente_id,
    "name": "cJS - ambiente - form",
    "type": "jsm",
    "parameter": [{
        "type": "TEMPLATE",
        "key": "javascript",
        "value": (
            'function () {\n'
            '    var el = document.querySelector(\'select[name="seu-ambiente"]\');\n'
            '    return el ? el.value : undefined;\n'
            '}'
        )
    }],
    "fingerprint": "1775508414999",
    "parentFolderId": "3",
    "formatValue": {}
})

variables.append({
    "accountId": ACC, "containerId": CONT,
    "variableId": new_var_metragem_id,
    "name": "cJS - metragem - form",
    "type": "jsm",
    "parameter": [{
        "type": "TEMPLATE",
        "key": "javascript",
        "value": (
            'function () {\n'
            '    var el = document.querySelector(\'select[name="sua-metragem"]\');\n'
            '    return el ? el.value : undefined;\n'
            '}'
        )
    }],
    "fingerprint": "1775508415000",
    "parentFolderId": "3",
    "formatValue": {}
})

variables.append({
    "accountId": ACC, "containerId": CONT,
    "variableId": new_var_ismql_id,
    "name": "cJS - is_mql",
    "type": "jsm",
    "parameter": [{
        "type": "TEMPLATE",
        "key": "javascript",
        "value": (
            'function () {\n'
            '    var amb = document.querySelector(\'select[name="seu-ambiente"]\');\n'
            '    var met = document.querySelector(\'select[name="sua-metragem"]\');\n'
            '    if (!amb || !met) return false;\n'
            '    var a = amb.value || "";\n'
            '    var m = met.value || "";\n'
            '    var ambOk = a && a.indexOf("Residencial") === -1 && a.indexOf("Seu Ambiente") === -1;\n'
            '    var metOk = m === "Entre 50 e 75 m\\u00b2" || m === "Entre 75 e 100 m\\u00b2" || m === "Acima de 100 m\\u00b2";\n'
            '    return !!(ambOk && metOk);\n'
            '}'
        )
    }],
    "fingerprint": "1775508415001",
    "parentFolderId": "3",
    "formatValue": {}
})

# Variavel placeholder para Google Ads MQL label (usuario preenche)
new_var_gads_mql_label_id = str(int(new_var_ismql_id) + 1)
variables.append({
    "accountId": ACC, "containerId": CONT,
    "variableId": new_var_gads_mql_label_id,
    "name": "01 - Google Ads - MQL",
    "type": "c",
    "parameter": [{
        "type": "TEMPLATE", "key": "value",
        "value": "SUBSTITUIR_PELA_LABEL_DE_CONVERSAO_MQL"
    }],
    "fingerprint": "1775508415002",
    "parentFolderId": "5",
    "formatValue": {}
})

# ---------- 4) Trocar trigger de Lead para /obrigado (37) ----------
LEAD_TAG_IDS = {"30", "34", "41", "43"}  # Meta Pixel, Google Ads, CAPI, GA4
for t in tags:
    if t["tagId"] in LEAD_TAG_IDS:
        t["firingTriggerId"] = ["37"]

# ---------- 5) Despausar tags CAPI ----------
PAUSE_REMOVE = {"19", "24", "41"}
for t in tags:
    if t["tagId"] in PAUSE_REMOVE and t.get("paused"):
        t.pop("paused", None)

# ---------- 6) Atribuir triggers as tags que estavam sem ----------
# Tag 24 = CAPI WhatsApp -> triggers 7, 8
# Tag 36 = GA4 WhatsApp -> triggers 7, 8
for t in tags:
    if t["tagId"] in ("24", "36"):
        t["firingTriggerId"] = ["7", "8"]

# ---------- 7) Adicionar 'em' no Advanced Matching da Tag 30 (Meta Pixel Lead) ----------
for t in tags:
    if t["tagId"] == "30":
        for p in t["parameter"]:
            if p["key"] == "advancedMatchingList":
                # adiciona email
                p["list"].append({
                    "type": "MAP",
                    "map": [
                        {"type": "TEMPLATE", "key": "name", "value": "em"},
                        {"type": "TEMPLATE", "key": "value", "value": "{{cJS - email - form}}"}
                    ]
                })

# ---------- 8) Criar trigger MQL: pageview /obrigado AND is_mql == true ----------
new_trigger_mql_id = str(max(int(tr["triggerId"]) for tr in triggers) + 1)

triggers.append({
    "accountId": ACC, "containerId": CONT,
    "triggerId": new_trigger_mql_id,
    "name": "Page URL /obrigado AND is_mql",
    "type": "PAGEVIEW",
    "filter": [
        {
            "type": "CONTAINS",
            "parameter": [
                {"type": "TEMPLATE", "key": "arg0", "value": "{{Page URL}}"},
                {"type": "TEMPLATE", "key": "arg1", "value": "/obrigado"}
            ]
        },
        {
            "type": "EQUALS",
            "parameter": [
                {"type": "TEMPLATE", "key": "arg0", "value": "{{cJS - is_mql}}"},
                {"type": "TEMPLATE", "key": "arg1", "value": "true"}
            ]
        }
    ],
    "fingerprint": "1775508415100",
    "parentFolderId": "6"
})

# ---------- 9) Criar 4 novas tags MQL ----------
next_tag_id_int = max(int(t["tagId"]) for t in tags) + 1

# Tag MQL Meta Pixel (custom event "MQL")
tag_meta_pixel_mql_id = str(next_tag_id_int); next_tag_id_int += 1
tags.append({
    "accountId": ACC, "containerId": CONT,
    "tagId": tag_meta_pixel_mql_id,
    "name": "00.4 | Meta Ads - MQL",
    "type": "cvt_248559899_28",
    "parameter": [
        {"type": "BOOLEAN", "key": "disablePushState", "value": "false"},
        {"type": "TEMPLATE", "key": "pixelId", "value": "{{00 - Meta Ads - Pixel Id}}"},
        {"type": "TEMPLATE", "key": "eventId", "value": "{{00.1 - API Event Id}}"},
        {"type": "TEMPLATE", "key": "customEventName", "value": "MQL"},
        {"type": "BOOLEAN", "key": "disableAutoConfig", "value": "false"},
        {"type": "BOOLEAN", "key": "enhancedEcommerce", "value": "false"},
        {"type": "BOOLEAN", "key": "dpoLDU", "value": "false"},
        {
            "type": "LIST", "key": "advancedMatchingList",
            "list": [
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "name", "value": "ph"},
                    {"type": "TEMPLATE", "key": "value", "value": "{{cJS - telefone - form}}"}
                ]},
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "name", "value": "fn"},
                    {"type": "TEMPLATE", "key": "value", "value": "{{cJS - nome - form}}"}
                ]},
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "name", "value": "em"},
                    {"type": "TEMPLATE", "key": "value", "value": "{{cJS - email - form}}"}
                ]}
            ]
        },
        {"type": "TEMPLATE", "key": "eventName", "value": "custom"},
        {"type": "BOOLEAN", "key": "objectPropertiesFromVariable", "value": "false"},
        {"type": "BOOLEAN", "key": "consent", "value": "true"},
        {"type": "BOOLEAN", "key": "advancedMatching", "value": "true"}
    ],
    "fingerprint": "1775508415200",
    "firingTriggerId": [new_trigger_mql_id],
    "parentFolderId": "21",
    "tagFiringOption": "ONCE_PER_LOAD",
    "monitoringMetadata": {"type": "MAP"},
    "consentSettings": {"consentStatus": "NOT_SET"}
})

# Tag MQL Meta CAPI (gaawe routed via SSGTM)
tag_meta_capi_mql_id = str(next_tag_id_int); next_tag_id_int += 1
tags.append({
    "accountId": ACC, "containerId": CONT,
    "tagId": tag_meta_capi_mql_id,
    "name": "00.4 | CAPI - MQL",
    "type": "gaawe",
    "parameter": [
        {"type": "BOOLEAN", "key": "sendEcommerceData", "value": "false"},
        {
            "type": "LIST", "key": "eventSettingsTable",
            "list": [
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "parameter", "value": "event_id"},
                    {"type": "TEMPLATE", "key": "parameterValue", "value": "{{00.1 - API Event Id}}"}
                ]},
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "parameter", "value": "transport_url"},
                    {"type": "TEMPLATE", "key": "parameterValue", "value": "{{00.1 - API Transport}}"}
                ]},
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "parameter", "value": "first_party_collection"},
                    {"type": "TEMPLATE", "key": "parameterValue", "value": "true"}
                ]},
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "parameter", "value": "user_data.phone_number"},
                    {"type": "TEMPLATE", "key": "parameterValue", "value": "{{cJS - telefone - form}}"}
                ]},
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "parameter", "value": "user_data.address.first_name"},
                    {"type": "TEMPLATE", "key": "parameterValue", "value": "{{cJS - nome - form}}"}
                ]},
                {"type": "MAP", "map": [
                    {"type": "TEMPLATE", "key": "parameter", "value": "user_data.email_address"},
                    {"type": "TEMPLATE", "key": "parameterValue", "value": "{{cJS - email - form}}"}
                ]}
            ]
        },
        {"type": "TEMPLATE", "key": "eventName", "value": "MQL"},
        {"type": "TEMPLATE", "key": "measurementIdOverride", "value": "{{00 - GA4 - Tag Id}}"}
    ],
    "fingerprint": "1775508415201",
    "firingTriggerId": [new_trigger_mql_id],
    "parentFolderId": "14",
    "tagFiringOption": "ONCE_PER_LOAD",
    "monitoringMetadata": {"type": "MAP"},
    "consentSettings": {"consentStatus": "NOT_SET"}
})

# Tag MQL Google Ads
tag_gads_mql_id = str(next_tag_id_int); next_tag_id_int += 1
tags.append({
    "accountId": ACC, "containerId": CONT,
    "tagId": tag_gads_mql_id,
    "name": "00.4 | Google Ads - MQL",
    "type": "awct",
    "parameter": [
        {"type": "BOOLEAN", "key": "enableNewCustomerReporting", "value": "false"},
        {"type": "BOOLEAN", "key": "enableConversionLinker", "value": "true"},
        {"type": "BOOLEAN", "key": "enableProductReporting", "value": "false"},
        {"type": "TEMPLATE", "key": "conversionCookiePrefix", "value": "_gcl"},
        {"type": "BOOLEAN", "key": "enableShippingData", "value": "false"},
        {"type": "TEMPLATE", "key": "conversionId", "value": "{{00 - Google Ads - Tag Id}}"},
        {"type": "TEMPLATE", "key": "conversionLabel", "value": "{{01 - Google Ads - MQL}}"},
        {"type": "BOOLEAN", "key": "rdp", "value": "false"}
    ],
    "fingerprint": "1775508415202",
    "firingTriggerId": [new_trigger_mql_id],
    "parentFolderId": "5",
    "tagFiringOption": "ONCE_PER_LOAD",
    "monitoringMetadata": {"type": "MAP"},
    "consentSettings": {"consentStatus": "NOT_SET"}
})

# Tag MQL GA4
tag_ga4_mql_id = str(next_tag_id_int); next_tag_id_int += 1
tags.append({
    "accountId": ACC, "containerId": CONT,
    "tagId": tag_ga4_mql_id,
    "name": "00.4 | GA4 - MQL",
    "type": "gaawe",
    "parameter": [
        {"type": "BOOLEAN", "key": "sendEcommerceData", "value": "false"},
        {"type": "TEMPLATE", "key": "eventName", "value": "mql_qualified"},
        {"type": "TEMPLATE", "key": "measurementIdOverride", "value": "{{00 - GA4 - Tag Id}}"}
    ],
    "fingerprint": "1775508415203",
    "firingTriggerId": [new_trigger_mql_id],
    "parentFolderId": "17",
    "tagFiringOption": "ONCE_PER_LOAD",
    "monitoringMetadata": {"type": "MAP"},
    "consentSettings": {"consentStatus": "NOT_SET"}
})

# ---------- Salvar ----------
with open(DST, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

# Resumo
print("=" * 60)
print("JSON CORRIGIDO SALVO EM:")
print(DST)
print("=" * 60)
print(f"Tags totais: {len(tags)}")
print(f"Triggers totais: {len(triggers)}")
print(f"Variaveis totais: {len(variables)}")
print()
print("IDs criados:")
print(f"  Variavel ambiente:        {new_var_ambiente_id}")
print(f"  Variavel metragem:        {new_var_metragem_id}")
print(f"  Variavel is_mql:          {new_var_ismql_id}")
print(f"  Variavel Google Ads MQL:  {new_var_gads_mql_label_id}")
print(f"  Trigger MQL:              {new_trigger_mql_id}")
print(f"  Tag Meta Pixel MQL:       {tag_meta_pixel_mql_id}")
print(f"  Tag Meta CAPI MQL:        {tag_meta_capi_mql_id}")
print(f"  Tag Google Ads MQL:       {tag_gads_mql_id}")
print(f"  Tag GA4 MQL:              {tag_ga4_mql_id}")
