#!/usr/bin/env python3
"""Retroativos da devolução: as etapas de SQL e venda que aconteceram ANTES de a devolução ligar e que ainda cabem na
janela de cada plataforma. Só o Kommo por enquanto (eventos `lead_status_changed`, sem varrer negócio).

  python3 scripts/retroativos.py --brief clientes/<c>/brief.json --kommo-token ~/.config/sprint-growth/<c>_kommo.key
  python3 scripts/retroativos.py ... --enviar --webhook-url https://<n8n>/webhook/<caminho da devolução>

Janelas: Meta aceita `event_time` de até 7 dias; Google com gclid/gbraid/wbraid até 90 dias; Google só com dados do
usuário (`google.sem_clique`) até 63 dias. Sem `--enviar`, só lista (números e ids de lead, nunca nome/telefone).

Com `--enviar`, cada mudança vai à devolução que já está no ar como o webhook do próprio Kommo, com
`last_modified` = hora real da etapa: o núcleo usa essa hora como `event_time`, decide plataforma por plataforma
(evento velho demais para o Meta sai só para o Google), grava a nota no lead e não repete o que já foi enviado
(`event_id` por lead e evento). Mais velho primeiro: é o que sai da janela antes. Envio é gravação em plataforma:
só com ok explícito do usuário; se o modo automático negar, o usuário roda o comando.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request

DIA = 86400
MARGEM = 600  # 10 min: o evento não pode vencer entre a lista e a chegada ao Meta


def plataformas(ts, agora, tem_clique, sem_clique):
    """Quais plataformas ainda aceitam uma etapa que aconteceu em `ts`."""
    idade = agora - ts
    out = []
    if idade <= 7 * DIA - MARGEM:
        out.append("meta")
    if (tem_clique and idade <= 90 * DIA - MARGEM) or (sem_clique and idade <= 63 * DIA - MARGEM):
        out.append("google")
    return out


def corpo_webhook(lead_id, status_id, pipeline_id, ts):
    """O mesmo formulário que o webhook `status_lead` do Kommo manda, com a hora real da etapa."""
    return urllib.parse.urlencode({
        "leads[status][0][id]": str(lead_id), "leads[status][0][status_id]": str(status_id),
        "leads[status][0][pipeline_id]": str(pipeline_id), "leads[status][0][old_status_id]": "0",
        "leads[status][0][last_modified]": str(int(ts))}).encode()


def tem_clique(lead, campos):
    ids = {int(campos[k]) for k in ("gclid", "gbraid", "wbraid") if campos.get(k)}
    for f in lead.get("custom_fields_values") or []:
        if f.get("field_id") in ids and ((f.get("values") or [{}])[0].get("value") or "").strip():
            return True
    return False


def kommo(api, token):
    def get(caminho):
        r = urllib.request.Request(api.rstrip("/") + caminho, headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read() or b"{}") if resp.status != 204 else {}
    return get


def entradas(get, pipeline_id, status_id, desde):
    out, pag = {}, 1
    while True:
        r = get(f"/events?filter[type]=lead_status_changed&filter[created_at][from]={desde}"
                f"&filter[value_after][leads_statuses][0][pipeline_id]={pipeline_id}"
                f"&filter[value_after][leads_statuses][0][status_id]={status_id}&limit=100&page={pag}")
        evs = (r.get("_embedded") or {}).get("events") or []
        for e in evs:
            out[e["entity_id"]] = max(out.get(e["entity_id"], 0), e["created_at"])  # a entrada mais recente
        if len(evs) < 100:
            return out
        pag += 1
        time.sleep(0.4)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--kommo-token", required=True, help="arquivo com o token (nunca o token na linha de comando)")
    ap.add_argument("--json", help="grava a lista (ids de lead, etapa, hora, plataformas)")
    ap.add_argument("--enviar", action="store_true")
    ap.add_argument("--webhook-url")
    a = ap.parse_args()
    d = json.load(open(a.brief))["devolucao"]
    if d.get("crm", "kommo") != "kommo":
        sys.exit("só Kommo por enquanto")
    if not d.get("funis"):
        sys.exit("devolucao.funis vazio: o 142 é 'ganho' em todo funil (reengajamento no pós-venda não é venda)")
    if a.enviar and not a.webhook_url:
        sys.exit("--enviar pede --webhook-url (o webhook da devolução que está no ar)")
    get = kommo(d["kommo_api"], open(os.path.expanduser(a.kommo_token)).read().strip())
    g = d.get("google") or {}
    sem_clique = bool(g.get("sem_clique")) and bool(g.get("acoes"))
    agora = int(time.time())
    desde = agora - (90 if g.get("acoes") else 7) * DIA

    lista = []
    for pipe in d["funis"]:
        for status, evento in d["etapas"].items():
            for lead, ts in entradas(get, pipe, status, desde).items():
                lista.append({"lead_id": lead, "status_id": status, "pipeline_id": pipe, "evento": evento, "ts": ts})
    ids = sorted({str(x["lead_id"]) for x in lista})
    com_clique = set()
    for i in range(0, len(ids), 50):
        q = "&".join(f"filter[id][]={x}" for x in ids[i:i + 50])
        for l in (get(f"/leads?{q}&limit=250").get("_embedded") or {}).get("leads") or []:
            if tem_clique(l, d.get("campos") or {}):
                com_clique.add(str(l["id"]))
    for x in lista:
        x["plataformas"] = plataformas(x["ts"], agora, str(x["lead_id"]) in com_clique and bool(g.get("acoes")), sem_clique)
    fila = sorted((x for x in lista if x["plataformas"]), key=lambda x: x["ts"])

    resumo = {}
    for x in lista:
        r = resumo.setdefault(x["evento"], {"na_busca": 0, "meta": 0, "google": 0})
        r["na_busca"] += 1
        for p in x["plataformas"]:
            r[p] += 1
    print(json.dumps({"por_evento": resumo, "leads_com_clique_google": len(com_clique), "a_enviar": len(fila)},
                     ensure_ascii=False))
    for x in fila:
        horas = (agora - x["ts"]) / 3600
        vence = "" if "meta" not in x["plataformas"] else f" | sai da janela do Meta em {7 * 24 - horas:.1f} h"
        print(f"  lead {x['lead_id']} {x['evento']} há {horas / 24:.1f} dias → {'+'.join(x['plataformas'])}{vence}")
    if a.json:
        json.dump(fila, open(a.json, "w"), ensure_ascii=False, indent=1)
    if not a.enviar:
        return
    for x in fila:
        r = urllib.request.Request(a.webhook_url, data=corpo_webhook(x["lead_id"], x["status_id"], x["pipeline_id"], x["ts"]),
                                   method="POST", headers={"Content-Type": "application/x-www-form-urlencoded",
                                                           "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(r, timeout=30) as resp:
            print(f"  enviado lead {x['lead_id']} {x['evento']}: HTTP {resp.status} (resultado na nota do lead)")
        time.sleep(3)


if __name__ == "__main__":
    main()
