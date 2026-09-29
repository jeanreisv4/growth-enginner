#!/usr/bin/env python3
"""Auditoria do GTM (web e servidor) contra as conversões do Google Ads. Somente leitura.

  python3 scripts/gtm_auditoria.py --conta-gtm 1112223334 --web 100000001 [--server 100000002] \
      --ads 1234567890 [--mcp-ads googleads_diretas] --out clientes/<c>/gtm

Alertas:
  G1 tag de conversão do Google Ads com rótulo que NÃO existe na conta (um caractere a menos zerou o Lead da SaaS de diário de obra)
  G2 tag do GA4 no servidor disparando em nome de evento do Meta (PageView/Lead/Contact/MQL...) → evento duplicado no GA4
  G3 tag pausada ou sem acionador
  G4 duas tags de conversão do Ads apontando para o mesmo rótulo
  G5 o mesmo acionador como disparo e como exceção da tag: a exceção vence e a tag nunca dispara nele
     (pop-up de WhatsApp da distribuidora de peças: a tag do Google Ads tinha o evento do pop-up nos dois campos)
Lembrete que o script não enxerga: se o GTM é injetado por construtor de página (GreatPages etc.), ver se está
preso no banner de cookies — use scripts/teste_formulario.py na página.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_http import MCP

def disparo_e_excecao(tags, nomes_trig):
    """G5: acionador que está em firingTriggerId e em blockingTriggerId da mesma tag."""
    al = []
    for t in tags:
        for tid in sorted(set(t.get("firingTriggerId", [])) & set(t.get("blockingTriggerId", []))):
            al.append(("G5", f"\"{t['name']}\" tem \"{nomes_trig.get(tid, tid)}\" como disparo e como exceção: "
                             "a exceção vence e a tag nunca dispara nesse acionador."))
    return al


EVENTOS_META = {"PageView", "Lead", "Contact", "MQL", "CompleteRegistration", "Purchase", "InitiateCheckout",
                "AddToCart", "ViewContent", "Schedule", "SubmitApplication", "Subscribe", "StartTrial"}


def workspace(gtm, conta, cont):
    ws = gtm.call("gtm_list_workspaces", {"accountId": conta, "containerId": cont}).get("workspace", [])
    return ws[0]["workspaceId"] if ws else None


def resolver(valor, variaveis):
    m = re.fullmatch(r"\{\{(.+)\}\}", str(valor or "").strip())
    if not m:
        return valor
    v = variaveis.get(m.group(1))
    if not v:
        return valor
    p = {x["key"]: x.get("value") for x in v.get("parameter", [])}
    return p.get("value", valor)


def rotulos_ads(ads, conta):
    r = ads.call("ads_conversion_actions", {"customerId": str(conta)})
    out = {}
    for x in (r.get("results", []) if isinstance(r, dict) else []):
        c = x["conversionAction"]
        for sn in c.get("tagSnippets", []):
            for rot in re.findall(r"AW-\d+/([A-Za-z0-9_\-]+)", sn.get("eventSnippet", "")):
                out[rot] = c["name"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conta-gtm", required=True)
    ap.add_argument("--web", required=True, help="id interno do container web")
    ap.add_argument("--server", help="id interno do container de servidor")
    ap.add_argument("--ads", help="conta do Google Ads para conferir os rótulos")
    ap.add_argument("--mcp-ads", default="googleads_diretas")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    gtm = MCP("gtm")
    al, raw = [], {}
    for papel, cont in (("web", a.web), ("server", a.server)):
        if not cont:
            continue
        ws = workspace(gtm, a.conta_gtm, cont)
        base = {"accountId": a.conta_gtm, "containerId": cont, "workspaceId": ws}
        tags = gtm.call("gtm_list_tags", base).get("tag", [])
        trig = {t["triggerId"]: t for t in gtm.call("gtm_list_triggers", base).get("trigger", [])}
        var = {v["name"]: v for v in gtm.call("gtm_list_variables", base).get("variable", [])}
        raw[papel] = {"workspace": ws, "tags": tags, "triggers": list(trig.values()), "variables": list(var.values())}
        al += [(c, f"[{papel}] {m}") for c, m in disparo_e_excecao(tags, {k: v["name"] for k, v in trig.items()})]
        for t in tags:
            if t.get("paused"):
                al.append(("G3", f"[{papel}] tag pausada: {t['name']}"))
            elif not t.get("firingTriggerId"):
                al.append(("G3", f"[{papel}] tag sem acionador: {t['name']}"))
            if papel == "server" and t["type"] in ("sgtmgaaw", "gaawe") and not t.get("paused"):
                nomes = set()
                for tid in t.get("firingTriggerId", []):
                    for f in trig.get(tid, {}).get("customEventFilter", []) + trig.get(tid, {}).get("filter", []):
                        for p in f.get("parameter", []):
                            if p.get("key") == "arg1":
                                nomes.add(p.get("value"))
                if nomes & EVENTOS_META:
                    al.append(("G2", f"[server] \"{t['name']}\" manda ao GA4 eventos com nome do Meta ({', '.join(sorted(nomes & EVENTOS_META))}): duplica eventos no GA4."))
        if papel == "web" and a.ads:
            validos = rotulos_ads(MCP(a.mcp_ads), a.ads)
            vistos = {}
            for t in tags:
                if t["type"] != "awct":
                    continue
                p = {x["key"]: x.get("value") for x in t.get("parameter", [])}
                rot = resolver(p.get("conversionLabel"), var)
                if rot in vistos:
                    al.append(("G4", f"\"{t['name']}\" e \"{vistos[rot]}\" usam o mesmo rótulo {rot}."))
                vistos[rot] = t["name"]
                if validos and rot not in validos:
                    parecido = [r for r in validos if len(r) and sum(1 for x, y in zip(r, rot) if x == y) >= len(r) - 3]
                    dica = f" Parecido com {parecido[0]} ({validos[parecido[0]]})." if parecido else ""
                    al.append(("G1", f"\"{t['name']}\" envia o rótulo {rot}, que não existe na conta {a.ads}.{dica}"))
    os.makedirs(a.out, exist_ok=True)
    json.dump(raw, open(os.path.join(a.out, "gtm_raw.json"), "w"), ensure_ascii=False, indent=1)
    md = ["# Auditoria GTM", "", "## Alertas", ""] + ([f"- **{c}** {t}" for c, t in al] or ["- Nenhum alerta."])
    for papel, d in raw.items():
        md += ["", f"## Tags ({papel}, workspace {d['workspace']})", ""]
        md += [f"- {t['tagId']} · {t['type']} · {t['name']}{' · PAUSADA' if t.get('paused') else ''}" for t in d["tags"]]
    open(os.path.join(a.out, "gtm_resumo.md"), "w").write("\n".join(md) + "\n")
    print(f"{len(al)} alertas · {a.out}/gtm_resumo.md")
    for c, t in al:
        print(f"  {c} {t}")


if __name__ == "__main__":
    main()
