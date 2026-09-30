#!/usr/bin/env python3
"""Auditoria de entrada: todo lead do formulário virou lead no CRM? Semana a semana e por origem do lead no CRM.

  python3 scripts/auditar_entrada.py --meta meta_leads.json --kommo-leads leads.json --kommo-contatos contatos.json
  python3 scripts/auditar_entrada.py --meta meta_leads.json --crm crm.json [--desde 2026-08-01] [--json saida.json]

meta_leads.json: lista de {id, t (created_time do Meta, ISO), k (DDD|8 dígitos) ou tel, camp?, plat?}
  (sai de scripts/n8n_meta_leads.py). Fonte da verdade é o Meta, não a planilha.
crm.json (qualquer CRM, já normalizado): lista de {telefones: [...], leads: [{criado_em: unix, origem: "..."}]}.
Kommo: passe os dois exports da API (/leads com with=contacts,source e /contacts) e o adaptador monta o crm.json.

Saída só com números (sem nome/telefone). A semana em que uma origem some é a semana em que a integração quebrou
(caso de referência: a origem da automação antiga zerou em 31/08 e 57 de 66 leads de 16 a 30/09 ficaram fora).
"""
import argparse, collections, json, sys
from datetime import datetime, timedelta, timezone

BR = timezone(timedelta(hours=-3))


def chave(tel):
    d = "".join(c for c in str(tel or "") if c.isdigit())
    if len(d) < 10:
        return ""
    if len(d) >= 12 and d.startswith("55"):
        d = d[2:]
    return d[:2] + "|" + d[-8:]


def crm_do_kommo(leads, contatos):
    por_contato = collections.defaultdict(list)
    for l in leads:
        origem = str(((l.get("_embedded") or {}).get("source") or {}).get("name") or "sem origem")
        for c in (l.get("_embedded") or {}).get("contacts") or []:
            por_contato[c["id"]].append({"criado_em": l["created_at"], "origem": origem})
    out = []
    for c in contatos:
        tels = [v.get("value") for f in c.get("custom_fields_values") or [] if f.get("field_code") == "PHONE"
                for v in f.get("values") or []]
        out.append({"telefones": tels, "leads": por_contato.get(c["id"], [])})
    return out


def situacao(m, indice, folga=86400):
    """('criado', origem) | ('antigo', None) | ('fora', None) para um lead do formulário."""
    t = datetime.fromisoformat(m["t"].replace("Z", "+00:00").replace("+0000", "+00:00")).timestamp()
    ls = [l for c in indice.get(m.get("k") or chave(m.get("tel")), []) for l in c["leads"]]
    novos = [l for l in ls if l["criado_em"] >= t - folga]
    if novos:
        return "criado", min(novos, key=lambda l: l["criado_em"])["origem"]
    return ("antigo", None) if ls else ("fora", None)


def auditar(meta, crm, desde=None):
    indice = collections.defaultdict(list)
    for c in crm:
        for k in {chave(t) for t in c.get("telefones") or [] if chave(t)}:
            indice[k].append(c)
    semanas = collections.defaultdict(lambda: {"formulario": 0, "fora": 0, "antigo": 0, "origens": collections.Counter()})
    for m in meta:
        dt = datetime.fromisoformat(m["t"].replace("Z", "+00:00").replace("+0000", "+00:00")).astimezone(BR)
        if desde and dt.strftime("%Y-%m-%d") < desde:
            continue
        s = semanas[dt.strftime("%G-S%V")]
        s["formulario"] += 1
        est, origem = situacao(m, indice)
        if est == "criado":
            s["origens"][origem] += 1
        else:
            s[est] += 1
    return {k: {**v, "origens": dict(v["origens"])} for k, v in sorted(semanas.items())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--crm")
    ap.add_argument("--kommo-leads")
    ap.add_argument("--kommo-contatos")
    ap.add_argument("--desde")
    ap.add_argument("--json")
    a = ap.parse_args()
    meta = json.load(open(a.meta))
    if a.crm:
        crm = json.load(open(a.crm))
    elif a.kommo_leads and a.kommo_contatos:
        crm = crm_do_kommo(json.load(open(a.kommo_leads)), json.load(open(a.kommo_contatos)))
    else:
        sys.exit("Passe --crm ou --kommo-leads + --kommo-contatos.")
    r = auditar(meta, crm, a.desde)
    tot = collections.Counter()
    print("semana    | formulário | fora do CRM | só lead antigo | criado depois (por origem)")
    for s, v in r.items():
        tot.update({"formulario": v["formulario"], "fora": v["fora"], "antigo": v["antigo"]})
        alerta = "  ⚠" if v["formulario"] and v["fora"] / v["formulario"] > 0.2 else ""
        print(f"{s:9} | {v['formulario']:10} | {v['fora']:11} | {v['antigo']:14} | {v['origens']}{alerta}")
    if tot["formulario"]:
        print(f"TOTAL: {tot['formulario']} do formulário, {tot['fora']} fora do CRM ({100*tot['fora']/tot['formulario']:.1f}%), "
              f"{tot['antigo']} só com lead antigo")
    if a.json:
        json.dump(r, open(a.json, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
