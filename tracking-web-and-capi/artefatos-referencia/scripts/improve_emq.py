"""
Quick wins de EMQ no GTM Server:
- Cria 2 variaveis de Event Data: client_id e event_location.region
- Adiciona userDataList nas tags Meta CAPI Lead e MQL com external_id, country=br, state
"""
import json

PATH = r"C:\Users\User\Downloads\GTM-PNKWBGFC_workspace2_BUILT.json"

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

cv = data["containerVersion"]
ACC = "4226126032"
CONT = "252672677"

# ---------- 1) Criar variaveis Event Data ----------
# Procura proximo variableId
next_var_id = str(max(int(v["variableId"]) for v in cv["variable"]) + 1)
var_client_id = next_var_id
var_state_id = str(int(next_var_id) + 1)

# Verifica se ja existem (idempotencia)
exists_cid = any(v.get("name") == "ED - client_id" for v in cv["variable"])
exists_state = any(v.get("name") == "ED - state" for v in cv["variable"])

if not exists_cid:
    cv["variable"].append({
        "accountId": ACC, "containerId": CONT,
        "variableId": var_client_id,
        "name": "ED - client_id",
        "type": "ed",
        "parameter": [
            {"type": "TEMPLATE", "key": "keyPath", "value": "client_id"}
        ],
        "fingerprint": "1779100000001",
        "parentFolderId": "1",
        "formatValue": {}
    })

if not exists_state:
    cv["variable"].append({
        "accountId": ACC, "containerId": CONT,
        "variableId": var_state_id,
        "name": "ED - state",
        "type": "ed",
        "parameter": [
            {"type": "TEMPLATE", "key": "keyPath", "value": "event_location.region"}
        ],
        "fingerprint": "1779100000002",
        "parentFolderId": "1",
        "formatValue": {}
    })

# ---------- 2) Adicionar userDataList nas tags Lead (id=2) e MQL (id=4) ----------
USER_DATA_LIST = {
    "type": "LIST",
    "key": "userDataList",
    "list": [
        {"type": "MAP", "map": [
            {"type": "TEMPLATE", "key": "name", "value": "external_id"},
            {"type": "TEMPLATE", "key": "value", "value": "{{ED - client_id}}"}
        ]},
        {"type": "MAP", "map": [
            {"type": "TEMPLATE", "key": "name", "value": "country"},
            {"type": "TEMPLATE", "key": "value", "value": "br"}
        ]},
        {"type": "MAP", "map": [
            {"type": "TEMPLATE", "key": "name", "value": "st"},
            {"type": "TEMPLATE", "key": "value", "value": "{{ED - state}}"}
        ]}
    ]
}

count = 0
for t in cv["tag"]:
    # Aplica em Lead, MQL, PageView, Contact
    if t["tagId"] in ("1", "2", "3", "4"):
        # Remove existente se houver
        t["parameter"] = [p for p in t["parameter"] if p.get("key") != "userDataList"]
        t["parameter"].append(json.loads(json.dumps(USER_DATA_LIST)))
        count += 1

# Salvar
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Variaveis criadas: ED - client_id (id={var_client_id}), ED - state (id={var_state_id})")
print(f"userDataList adicionado em {count} tags CAPI")
print(f"Arquivo: {PATH}")
