"""
Adiciona value + currency nas tags do GTM web (Modelo A - lucro como proxy).
Valores diferenciados por canal:
- Google Ads: Lead R$190 / MQL R$630
- Meta Pixel + CAPI: Lead R$120 / MQL R$400
- GA4: Lead R$150 / MQL R$500
"""
import json

PATH = r"C:\Users\User\Downloads\GTM-KG7X38D6_workspace4_FIXED.json"

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

tags = data["containerVersion"]["tag"]

# Mapeamento: tag_id -> (canal, evento, value)
TAG_VALUES = {
    # Lead
    "30": ("meta_pixel", "Lead", "120"),    # 00.2 - Meta Ads - Lead
    "41": ("meta_capi", "Lead", "120"),     # 00.2 | CAPI - Lead
    "34": ("google_ads", "Lead", "190"),    # 00.2 | Google Ads - Lead
    "43": ("ga4", "Lead", "150"),           # 00.2 | GA4 - Lead
    # MQL (novas tags criadas)
    "44": ("meta_pixel", "MQL", "400"),     # 00.4 | Meta Ads - MQL
    "45": ("meta_capi", "MQL", "400"),      # 00.4 | CAPI - MQL
    "46": ("google_ads", "MQL", "630"),     # 00.4 | Google Ads - MQL
    "47": ("ga4", "MQL", "500"),            # 00.4 | GA4 - MQL
}

def add_meta_pixel_value(tag, value):
    """Adiciona value + currency nas tags Meta Pixel (cvt_248559899_28)
       usando objectProperties (List type)."""
    # Remove se ja existe
    tag["parameter"] = [p for p in tag["parameter"] if p.get("key") != "objectProperties"]
    # Habilita objectPropertiesFromVariable=false (ja esta) e adiciona properties
    tag["parameter"].append({
        "type": "LIST",
        "key": "objectProperties",
        "list": [
            {"type": "MAP", "map": [
                {"type": "TEMPLATE", "key": "property", "value": "value"},
                {"type": "TEMPLATE", "key": "value", "value": value}
            ]},
            {"type": "MAP", "map": [
                {"type": "TEMPLATE", "key": "property", "value": "currency"},
                {"type": "TEMPLATE", "key": "value", "value": "BRL"}
            ]}
        ]
    })

def add_event_settings_kv(tag, key, value):
    """Adiciona linha em eventSettingsTable para gaawe (GA4/CAPI roteado)."""
    target_list = None
    for p in tag["parameter"]:
        if p.get("key") == "eventSettingsTable":
            target_list = p["list"]
            break
    if target_list is None:
        new_p = {"type": "LIST", "key": "eventSettingsTable", "list": []}
        tag["parameter"].append(new_p)
        target_list = new_p["list"]
    # remove duplicata
    target_list[:] = [m for m in target_list
                      if not any(x.get("key") == "parameter" and x.get("value") == key for x in m.get("map", []))]
    target_list.append({
        "type": "MAP",
        "map": [
            {"type": "TEMPLATE", "key": "parameter", "value": key},
            {"type": "TEMPLATE", "key": "parameterValue", "value": value}
        ]
    })

def add_google_ads_value(tag, value):
    """Adiciona conversionValue + currencyCode nas tags Google Ads (awct)."""
    # remove se existem
    tag["parameter"] = [p for p in tag["parameter"]
                        if p.get("key") not in ("conversionValue", "currencyCode")]
    tag["parameter"].append({"type": "TEMPLATE", "key": "conversionValue", "value": value})
    tag["parameter"].append({"type": "TEMPLATE", "key": "currencyCode", "value": "BRL"})

count = 0
for t in tags:
    tid = t["tagId"]
    if tid not in TAG_VALUES:
        continue
    canal, evento, valor = TAG_VALUES[tid]

    if canal == "meta_pixel":
        add_meta_pixel_value(t, valor)
    elif canal == "google_ads":
        add_google_ads_value(t, valor)
    elif canal in ("meta_capi", "ga4"):
        add_event_settings_kv(t, "value", valor)
        add_event_settings_kv(t, "currency", "BRL")
    count += 1
    print(f"  [{tid}] {t['name']:50s} -> {canal:12s} {evento:5s} value=R${valor}")

# Salva
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"\n{count} tags atualizadas com value+currency.")
print(f"Arquivo: {PATH}")
