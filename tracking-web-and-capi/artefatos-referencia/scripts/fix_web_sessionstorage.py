"""
Corrige Problema 1: variaveis JS dependiam do form que so existe na LP,
mas as tags Lead/MQL disparam na /obrigado (sem form).

Solucao: persistir dados do form no sessionStorage no submit, e reler
do sessionStorage nas variaveis ao chegar na /obrigado.

Aplica em cima do JSON ja corrigido (GTM-KG7X38D6_workspace4_FIXED.json):
- Cria 1 tag HTML custom 'cHTML - Persist Form Data' (trigger All Pages)
- Reescreve 6 variaveis JS para ler do sessionStorage:
  cJS - nome, cJS - email, cJS - telefone, cJS - ambiente, cJS - metragem, cJS - is_mql
"""
import json

PATH = r"C:\Users\User\Downloads\GTM-KG7X38D6_workspace4_FIXED.json"

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

cv = data["containerVersion"]
ACC = "4226126032"
CONT = "248559899"

# ============================================================
# 1) Reescrever variaveis JS para ler do sessionStorage
# ============================================================
JS_OVERRIDES = {
    "cJS - nome - form": (
        'function() {\n'
        '  try {\n'
        '    var raw = sessionStorage.getItem("wk_lead_data");\n'
        '    if (!raw) return undefined;\n'
        '    var d = JSON.parse(raw);\n'
        '    return d.nome || undefined;\n'
        '  } catch(e) { return undefined; }\n'
        '}'
    ),
    "cJS - email - form": (
        'function() {\n'
        '  try {\n'
        '    var raw = sessionStorage.getItem("wk_lead_data");\n'
        '    if (!raw) return undefined;\n'
        '    var d = JSON.parse(raw);\n'
        '    return d.email || undefined;\n'
        '  } catch(e) { return undefined; }\n'
        '}'
    ),
    "cJS - telefone - form": (
        'function() {\n'
        '  try {\n'
        '    var raw = sessionStorage.getItem("wk_lead_data");\n'
        '    if (!raw) return undefined;\n'
        '    var d = JSON.parse(raw);\n'
        '    return d.telefone ? "55" + d.telefone : undefined;\n'
        '  } catch(e) { return undefined; }\n'
        '}'
    ),
    "cJS - ambiente - form": (
        'function() {\n'
        '  try {\n'
        '    var raw = sessionStorage.getItem("wk_lead_data");\n'
        '    if (!raw) return undefined;\n'
        '    var d = JSON.parse(raw);\n'
        '    return d.ambiente || undefined;\n'
        '  } catch(e) { return undefined; }\n'
        '}'
    ),
    "cJS - metragem - form": (
        'function() {\n'
        '  try {\n'
        '    var raw = sessionStorage.getItem("wk_lead_data");\n'
        '    if (!raw) return undefined;\n'
        '    var d = JSON.parse(raw);\n'
        '    return d.metragem || undefined;\n'
        '  } catch(e) { return undefined; }\n'
        '}'
    ),
    "cJS - is_mql": (
        'function() {\n'
        '  try {\n'
        '    var raw = sessionStorage.getItem("wk_lead_data");\n'
        '    if (!raw) return false;\n'
        '    var d = JSON.parse(raw);\n'
        '    var a = d.ambiente || "";\n'
        '    var m = d.metragem || "";\n'
        '    var ambOk = a && a.indexOf("Residencial") === -1 && a.indexOf("Seu Ambiente") === -1;\n'
        '    var metOk = m === "Entre 50 e 75 m\\u00b2" || m === "Entre 75 e 100 m\\u00b2" || m === "Acima de 100 m\\u00b2";\n'
        '    return !!(ambOk && metOk);\n'
        '  } catch(e) { return false; }\n'
        '}'
    ),
}

updated_vars = 0
for v in cv["variable"]:
    name = v.get("name", "")
    if name in JS_OVERRIDES:
        for p in v["parameter"]:
            if p["key"] == "javascript":
                p["value"] = JS_OVERRIDES[name]
                updated_vars += 1
                break

# ============================================================
# 2) Criar tag HTML que persiste dados no sessionStorage
# ============================================================
html_persist = (
    '<script>\n'
    '(function() {\n'
    '  function captureFormData() {\n'
    '    var nome = document.querySelector(\'input[name="seu-nome"]\');\n'
    '    var email = document.querySelector(\'input[name="seu-e-mail"]\');\n'
    '    var telefone = document.querySelector(\'input[name="seu-telefonewhatsapp"]\');\n'
    '    var ambiente = document.querySelector(\'select[name="seu-ambiente"]\');\n'
    '    var metragem = document.querySelector(\'select[name="sua-metragem"]\');\n'
    '    if (!nome && !email && !telefone) return;\n'
    '    var data = {\n'
    '      nome: nome ? nome.value.trim() : "",\n'
    '      email: email ? email.value.trim().toLowerCase() : "",\n'
    '      telefone: telefone ? telefone.value.replace(/\\D/g, "") : "",\n'
    '      ambiente: ambiente ? ambiente.value : "",\n'
    '      metragem: metragem ? metragem.value : ""\n'
    '    };\n'
    '    try { sessionStorage.setItem("wk_lead_data", JSON.stringify(data)); } catch(e) {}\n'
    '  }\n'
    '  function attach() {\n'
    '    var form = document.querySelector(\'form.e_formulario\');\n'
    '    var btn = document.querySelector(\'.gpc_botao.e_formulario\');\n'
    '    if (!form && !btn) { setTimeout(attach, 500); return; }\n'
    '    if (form) form.addEventListener("submit", captureFormData, true);\n'
    '    if (btn) btn.addEventListener("click", captureFormData, true);\n'
    '  }\n'
    '  if (document.readyState === "loading") {\n'
    '    document.addEventListener("DOMContentLoaded", attach);\n'
    '  } else {\n'
    '    attach();\n'
    '  }\n'
    '})();\n'
    '</script>'
)

# Verifica se a tag ja existe (idempotencia)
TAG_NAME = "cHTML - Persist Form Data"
existing = next((t for t in cv["tag"] if t.get("name") == TAG_NAME), None)
if existing:
    # atualiza HTML
    for p in existing["parameter"]:
        if p["key"] == "html":
            p["value"] = html_persist
            break
    new_tag_id = existing["tagId"]
    print(f"Tag ja existia (id={new_tag_id}), HTML atualizado.")
else:
    new_tag_id = str(max(int(t["tagId"]) for t in cv["tag"]) + 1)
    cv["tag"].append({
        "accountId": ACC, "containerId": CONT,
        "tagId": new_tag_id,
        "name": TAG_NAME,
        "type": "html",
        "parameter": [
            {"type": "TEMPLATE", "key": "html", "value": html_persist},
            {"type": "BOOLEAN", "key": "supportDocumentWrite", "value": "false"}
        ],
        "fingerprint": "1779000000001",
        "firingTriggerId": ["2147479553"],  # All Pages
        "parentFolderId": "3",  # JavaScript folder
        "tagFiringOption": "ONCE_PER_LOAD",
        "monitoringMetadata": {"type": "MAP"},
        "consentSettings": {"consentStatus": "NOT_SET"}
    })
    print(f"Tag HTML criada com id={new_tag_id}")

# Salvar
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"\nVariaveis JS atualizadas: {updated_vars}")
print(f"Tag HTML persiste sessionStorage: id={new_tag_id}")
print(f"Arquivo salvo: {PATH}")
