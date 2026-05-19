"""
Gera o JSON do GTM Server (GTM-PNKWBGFC) com:
- 2 Folders (Configuracoes, Meta CAPI) com emojis
- 2 Variaveis: Pixel Id (preenchido) + Access Token (vazio para usuario colar)
- 4 Triggers (PageView, Lead, Contact/WhatsApp, MQL)
- 4 Tags Meta CAPI (uma por evento)
- Built-in variables uteis ativadas
- Mantem Cliente GA4 existente e template Facebook Conversion API
"""
import json

SRC = r"C:\Users\User\Downloads\GTM-PNKWBGFC_workspace2.json"
DST = r"C:\Users\User\Downloads\GTM-PNKWBGFC_workspace2_BUILT.json"

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

cv = data["containerVersion"]
ACC = "4226126032"
CONT = "252672677"
TEMPLATE_TYPE = "cvt_252672677_4"  # Facebook Conversion API (stape-io)
PIXEL_ID = "444617535160623"

# ---------- Built-in Variables uteis ----------
cv["builtInVariable"] = [
    {"accountId": ACC, "containerId": CONT, "type": "EVENT_NAME", "name": "Event Name"},
    {"accountId": ACC, "containerId": CONT, "type": "CLIENT_NAME", "name": "Client Name"},
    {"accountId": ACC, "containerId": CONT, "type": "CONTAINER_ID", "name": "Container ID"},
    {"accountId": ACC, "containerId": CONT, "type": "REQUEST_METHOD", "name": "Request Method"},
    {"accountId": ACC, "containerId": CONT, "type": "QUERY_STRING", "name": "Query String"},
]

# ---------- Folders ----------
cv["folder"] = [
    {
        "accountId": ACC, "containerId": CONT,
        "folderId": "1",
        "name": "⚙️ | Configurações",
        "fingerprint": "1778997824000"
    },
    {
        "accountId": ACC, "containerId": CONT,
        "folderId": "2",
        "name": "\U0001f535 | Meta CAPI",
        "fingerprint": "1778997824001"
    },
]

# ---------- Variables ----------
cv["variable"] = [
    {
        "accountId": ACC, "containerId": CONT,
        "variableId": "1",
        "name": "00 - Meta CAPI - Pixel Id",
        "type": "c",
        "parameter": [
            {"type": "TEMPLATE", "key": "value", "value": PIXEL_ID}
        ],
        "fingerprint": "1778997824100",
        "parentFolderId": "1",
        "formatValue": {}
    },
    {
        "accountId": ACC, "containerId": CONT,
        "variableId": "2",
        "name": "00 - Meta CAPI - Access Token",
        "type": "c",
        "parameter": [
            {"type": "TEMPLATE", "key": "value", "value": "COLE_O_TOKEN_AQUI"}
        ],
        "fingerprint": "1778997824101",
        "parentFolderId": "1",
        "formatValue": {},
        "notes": "Substitua 'COLE_O_TOKEN_AQUI' pelo Access Token gerado no Meta Events Manager (Conversions API)."
    },
    {
        "accountId": ACC, "containerId": CONT,
        "variableId": "3",
        "name": "00 - Meta CAPI - Test Event Code",
        "type": "c",
        "parameter": [
            {"type": "TEMPLATE", "key": "value", "value": "TEST36284"}
        ],
        "fingerprint": "1778997824102",
        "parentFolderId": "1",
        "formatValue": {},
        "notes": "Test Event Code do Meta. Apague o valor (deixe vazio) quando for para producao real."
    },
]

# ---------- Triggers (Custom Event filtrando pelo Event Name) ----------
def make_trigger(tid, name, event_value):
    return {
        "accountId": ACC, "containerId": CONT,
        "triggerId": tid,
        "name": name,
        "type": "CUSTOM_EVENT",
        "customEventFilter": [
            {
                "type": "EQUALS",
                "parameter": [
                    {"type": "TEMPLATE", "key": "arg0", "value": "{{_event}}"},
                    {"type": "TEMPLATE", "key": "arg1", "value": event_value}
                ]
            }
        ],
        "fingerprint": f"177899782430{tid}",
        "parentFolderId": "2"
    }

cv["trigger"] = [
    make_trigger("1", "Event Name = PageView", "PageView"),
    make_trigger("2", "Event Name = Lead", "Lead"),
    make_trigger("3", "Event Name = Contact", "Contact"),
    make_trigger("4", "Event Name = MQL", "MQL"),
]

# ---------- Tags Meta CAPI ----------
def make_meta_tag(tag_id, name, trigger_id, event_kind, event_name):
    """
    event_kind: 'standard' or 'custom'
    event_name: 'PageView', 'Lead', 'Contact', 'MQL'
    Define manualmente eventNameStandard/Custom (inherit nao funciona neste template).
    """
    params = [
        {"type": "TEMPLATE", "key": "pixelId", "value": "{{00 - Meta CAPI - Pixel Id}}"},
        {"type": "TEMPLATE", "key": "accessToken", "value": "{{00 - Meta CAPI - Access Token}}"},
        {"type": "TEMPLATE", "key": "actionSource", "value": "website"},
        {"type": "TEMPLATE", "key": "inheritEventName", "value": "override"},
        {"type": "TEMPLATE", "key": "eventName", "value": event_kind},
        {"type": "BOOLEAN", "key": "useOptimisticScenario", "value": "false"},
        {"type": "BOOLEAN", "key": "enableEventEnhancement", "value": "true"},
        {"type": "BOOLEAN", "key": "enableMultipixelSetup", "value": "false"},
        {"type": "BOOLEAN", "key": "useAppSecretProof", "value": "false"},
        {"type": "BOOLEAN", "key": "useHttpOnlyCookie", "value": "false"},
        {"type": "BOOLEAN", "key": "overrideCookieDomain", "value": "false"},
        {"type": "BOOLEAN", "key": "generateFbp", "value": "true"},
        {"type": "TEMPLATE", "key": "logType", "value": "no"},
        {"type": "TEMPLATE", "key": "bigQueryLogType", "value": "no"},
        {"type": "TEMPLATE", "key": "testId", "value": "{{00 - Meta CAPI - Test Event Code}}"},
    ]
    if event_kind == "standard":
        params.append({"type": "TEMPLATE", "key": "eventNameStandard", "value": event_name})
    else:
        params.append({"type": "TEMPLATE", "key": "eventNameCustom", "value": event_name})

    return {
        "accountId": ACC, "containerId": CONT,
        "tagId": tag_id,
        "name": name,
        "type": TEMPLATE_TYPE,
        "parameter": params,
        "fingerprint": f"177899782440{tag_id}",
        "firingTriggerId": [trigger_id],
        "parentFolderId": "2",
        "tagFiringOption": "ONCE_PER_EVENT",
        "monitoringMetadata": {"type": "MAP"},
        "consentSettings": {"consentStatus": "NOT_SET"}
    }

cv["tag"] = [
    make_meta_tag("1", "00.1 | Meta CAPI - PageView", "1", "standard", "PageView"),
    make_meta_tag("2", "00.2 | Meta CAPI - Lead",     "2", "standard", "Lead"),
    make_meta_tag("3", "00.3 | Meta CAPI - Contact",  "3", "standard", "Contact"),
    make_meta_tag("4", "00.4 | Meta CAPI - MQL",      "4", "custom",   "MQL"),
]

# Salvar
with open(DST, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("=" * 60)
print("JSON do GTM SERVER gerado:")
print(DST)
print("=" * 60)
print(f"Folders:   {len(cv['folder'])}")
print(f"Variables: {len(cv['variable'])}")
print(f"Triggers:  {len(cv['trigger'])}")
print(f"Tags:      {len(cv['tag'])}")
print(f"Built-in:  {len(cv['builtInVariable'])}")
print()
print("Conteudo:")
for v in cv["variable"]:
    val = next((p["value"] for p in v["parameter"] if p["key"]=="value"), "")
    marker = " <-- COLE O TOKEN AQUI" if v["name"].endswith("Access Token") else ""
    print(f"  [VAR]  {v['name']:40s} = \"{val}\"{marker}")
for tr in cv["trigger"]:
    print(f"  [TRIG] {tr['name']}")
for t in cv["tag"]:
    print(f"  [TAG]  {t['name']:40s} trigger={t['firingTriggerId']}")
