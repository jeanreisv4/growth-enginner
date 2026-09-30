#!/usr/bin/env python3
"""Devolução ao Google Ads a partir da PLANILHA de leads (sem CRM): as linhas que batem com o filtro (ex.: MQL =
resposta do formulário) viram conversão de importação de cliques pela Data Manager API.

  python3 scripts/devolucao_planilha.py --csv <url de export CSV ou arquivo> \\
      --filtro "utm_source=google" --filtro "Com qual linha você trabalha?=Alto padrão" \\
      --data-col Data [--hora-col Hora] --tel-col WhatsApp --email-col E-mail \\
      --customer <conta> --acao <id da conversion action> [--mcc <conta gerente>] \\
      --credencial <id da credencial Data Manager no n8n> --prefixo <cliente>-mql \\
      --n8n <url base do n8n> --n8n-key <arquivo com a chave da API>  [--validar | --enviar]

Sem --validar/--enviar só lista (data, tipo de clique, quantos identificadores; nunca nome/telefone/e-mail).
- Só linha com gclid/gbraid/wbraid e clique dentro de 90 dias (margem de 1 h). Telefone e e-mail vão com hash
  (SHA-256, e-mail normalizado como o Google pede) quando o evento tem até 63 dias.
- Sem coluna de hora, o evento fica às 23:59 do dia do lead: nunca antes do clique. Lead de hoje espera amanhã
  (evento no futuro é recusado).
- transactionId = <prefixo>-<aaaammdd>-<hash do telefone|e-mail|clique>: reenviar a planilha inteira não duplica.
- --mcc: a conta só é acessível pela gerente → loginAccount. Sem ele, o Google responde 403 em destinations[0].
- O envio passa por um workflow temporário do n8n com a credencial (o token não sai do n8n), apagado no fim.
"""
import argparse, csv, datetime as dt, hashlib, io, json, os, re, sys, time, urllib.error, urllib.request, uuid

MARGEM = 3600
JANELA_CLIQUE, JANELA_DADOS = 90 * 86400, 63 * 86400


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def email_google(e):
    e = (e or "").strip().lower()
    if "@" not in e or "." not in e.split("@")[-1]:
        return ""
    u, d = e.split("@", 1)
    if d in ("gmail.com", "googlemail.com"):
        u = u.replace(".", "")
    return u + "@" + d


def tel_e164(t):
    d = re.sub(r"\D", "", str(t or ""))
    if d.startswith("00"):
        d = d[2:]
    if len(d) >= 12 and d.startswith("55"):
        return "+" + d
    if len(d) in (10, 11):
        return "+55" + d
    return ""


def quando(data, hora, fuso):
    """dd/mm/aaaa ou aaaa-mm-dd [hh:mm[:ss]]; sem hora → 23:59 do dia."""
    data = (data or "").strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", data) or None
    if m:
        d, mes, a = map(int, m.groups())
    else:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", data)
        if not m:
            return None
        a, mes, d = map(int, m.groups())
    h = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", (hora or "") or data[10:])
    hh, mm, ss = (int(h.group(1)), int(h.group(2)), int(h.group(3) or 0)) if h else (23, 59, 0)
    return dt.datetime(a, mes, d, hh, mm, ss, tzinfo=dt.timezone(dt.timedelta(hours=fuso)))


def eventos(linhas, filtros, data_col, hora_col=None, tel_col=None, email_col=None, prefixo="lead", fuso=-3, agora=None):
    """(eventos, contagem) — contagem: sem_clique, fora_janela, hoje (espera), sem_data."""
    agora = agora or time.time()
    evs, n = [], {"sem_clique": 0, "fora_janela": 0, "hoje": 0, "sem_data": 0}
    for x in linhas:
        if any((x.get(c) or "").strip() != v for c, v in filtros):
            continue
        g, gb, wb = ((x.get(c) or "").strip() for c in ("gclid", "gbraid", "wbraid"))
        if not (g or gb or wb):
            n["sem_clique"] += 1
            continue
        q = quando(x.get(data_col), x.get(hora_col) if hora_col else None, fuso)
        if not q:
            n["sem_data"] += 1
            continue
        idade = agora - q.timestamp()
        if idade <= 0:
            n["hoje"] += 1
            continue
        if idade > JANELA_CLIQUE - MARGEM:
            n["fora_janela"] += 1
            continue
        tel = tel_e164(x.get(tel_col)) if tel_col else ""
        em = email_google(x.get(email_col)) if email_col else ""
        ev = {"eventTimestamp": q.isoformat(timespec="seconds"), "eventSource": "WEB",
              "adIdentifiers": {"gclid": g} if g else ({"gbraid": gb} if gb else {"wbraid": wb}),
              "transactionId": f"{prefixo}-{q:%Y%m%d}-" + sha(tel or em or g or gb or wb)[:10]}
        ids = ([{"phoneNumber": sha(tel)}] if tel else []) + ([{"emailAddress": sha(em)}] if em else [])
        if ids and idade <= JANELA_DADOS - MARGEM:
            ev["userData"] = {"userIdentifiers": ids}
        evs.append(ev)
    return evs, n


def corpo(evs, customer, acao, validar, mcc=None):
    dest = {"operatingAccount": {"accountType": "GOOGLE_ADS", "accountId": re.sub(r"\D", "", customer)},
            "productDestinationId": str(acao)}
    if mcc:
        dest["loginAccount"] = {"accountType": "GOOGLE_ADS", "accountId": re.sub(r"\D", "", mcc)}
    return {"destinations": [dest], "encoding": "HEX", "validateOnly": validar, "events": evs}


def diagnostico(status, resposta):
    """Tradução dos erros que já apareceram no uso real."""
    t = json.dumps(resposta, ensure_ascii=False)
    if status == 200:
        return "ok"
    if status == 403 and "destinations[0]" in t:
        return "conta sob gerente: passar --mcc com o id da MCC (loginAccount)"
    if status == 400 and "destination_references" in t and "NOT_FOUND" in t:
        return "ação de conversão recém-criada ainda não propagou na Data Manager (10 a 35 min): tentar de novo"
    if status == 403:
        return "credencial sem acesso à conta, ou Data Manager API desligada no projeto do Google Cloud"
    return "ver a resposta"


def enviar(b, n8n, chave, credencial):
    H = {"X-N8N-API-KEY": chave, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

    def api(m, c, d=None):
        r = urllib.request.Request(n8n + "/api/v1" + c, method=m, headers=H, data=json.dumps(d).encode() if d is not None else None)
        t = urllib.request.urlopen(r, timeout=60).read()
        return json.loads(t) if t else {}

    path = "tmp-dm-planilha-" + uuid.uuid4().hex[:10]
    nos = [{"id": str(uuid.uuid4()), "name": "Chamada", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 0],
            "webhookId": str(uuid.uuid4()), "parameters": {"httpMethod": "POST", "path": path, "responseMode": "lastNode", "options": {}}},
           {"id": str(uuid.uuid4()), "name": "Data Manager", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
            "position": [220, 0], "credentials": {"oAuth2Api": {"id": credencial, "name": "Data Manager"}},
            "parameters": {"method": "POST", "url": "https://datamanager.googleapis.com/v1/events:ingest",
                           "authentication": "genericCredentialType", "genericAuthType": "oAuth2Api", "sendBody": True,
                           "specifyBody": "json", "jsonBody": "={{ JSON.stringify($json.body) }}",
                           "options": {"response": {"response": {"fullResponse": True, "neverError": True, "responseFormat": "json"}}}}}]
    wid = api("POST", "/workflows", {"name": "[TESTE TEMPORÁRIO] Data Manager planilha", "nodes": nos, "settings": {"executionOrder": "v1"},
                                     "connections": {"Chamada": {"main": [[{"node": "Data Manager", "type": "main", "index": 0}]]}}})["id"]
    try:
        api("POST", f"/workflows/{wid}/activate")
        time.sleep(2)
        r = urllib.request.Request(f"{n8n}/webhook/{path}", data=json.dumps(b).encode(), method="POST",
                                   headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        x = json.loads(urllib.request.urlopen(r, timeout=90).read())
        return x.get("statusCode"), x.get("body")
    finally:
        try:
            api("POST", f"/workflows/{wid}/deactivate")
        finally:
            api("DELETE", f"/workflows/{wid}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--filtro", action="append", default=[], help='"coluna=valor" (repetível; todos têm de bater)')
    ap.add_argument("--data-col", required=True)
    ap.add_argument("--hora-col")
    ap.add_argument("--tel-col")
    ap.add_argument("--email-col")
    ap.add_argument("--fuso", type=int, default=-3)
    ap.add_argument("--prefixo", default="lead")
    ap.add_argument("--customer", required=True)
    ap.add_argument("--acao", required=True)
    ap.add_argument("--mcc")
    ap.add_argument("--credencial")
    ap.add_argument("--n8n")
    ap.add_argument("--n8n-key", help="arquivo com a chave da API do n8n (nunca a chave na linha de comando)")
    ap.add_argument("--validar", action="store_true")
    ap.add_argument("--enviar", action="store_true")
    a = ap.parse_args()
    bruto = urllib.request.urlopen(a.csv, timeout=60).read().decode("utf-8") if a.csv.startswith("http") else open(a.csv, encoding="utf-8").read()
    filtros = [tuple(s.strip() for s in f.split("=", 1)) for f in a.filtro]
    evs, n = eventos(list(csv.DictReader(io.StringIO(bruto))), filtros, a.data_col, a.hora_col, a.tel_col, a.email_col,
                     a.prefixo, a.fuso)
    for e in evs:
        print(e["eventTimestamp"][:10], "clique:", ",".join(e["adIdentifiers"]), "| identificadores:",
              len(e.get("userData", {}).get("userIdentifiers", [])))
    print(f"{len(evs)} na janela | {n['sem_clique']} sem clique | {n['fora_janela']} fora da janela | "
          f"{n['hoje']} de hoje (amanhã) | {n['sem_data']} sem data")
    if evs and (a.validar or a.enviar):
        if not (a.credencial and a.n8n and a.n8n_key):
            sys.exit("--credencial, --n8n e --n8n-key são obrigatórios para validar/enviar")
        chave = open(os.path.expanduser(a.n8n_key)).read().strip()
        st, body = enviar(corpo(evs, a.customer, a.acao, not a.enviar, a.mcc), a.n8n.rstrip("/"), chave, a.credencial)
        print("ENVIADO" if a.enviar else "VALIDADO (nada gravado)", "HTTP", st, "|", diagnostico(st, body))
        print(json.dumps(body, ensure_ascii=False)[:900])
        sys.exit(0 if st == 200 else 1)


if __name__ == "__main__":
    main()
