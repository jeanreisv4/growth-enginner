#!/usr/bin/env python3
"""Devolução do RD Station CRM ao Google Ads (Data Manager API): SQL (entrada numa etapa) e venda (negócio ganho).

  python3 scripts/devolucao_rd.py --brief clientes/<c>/brief.json --gerar saida/<c>/n8n-devolucao-rd.json [--desde <unix>]
  python3 scripts/devolucao_rd.py --brief ... --n8n <url> --n8n-key <arquivo> --teste
  python3 scripts/devolucao_rd.py --brief ... --n8n ... --n8n-key ... --retroativo [--validar | --enviar]
  python3 scripts/devolucao_rd.py --brief ... --n8n ... --n8n-key ... --criar --desde <unix>
  python3 scripts/devolucao_rd.py --brief ... --n8n ... --n8n-key ... --atualizar <id> --desde <unix>

Fluxo (de hora em hora, sem webhook): lista os negócios cujo nome começa com o prefixo da mídia (ex.: "Lead V4") na
etapa de SQL e os ganhos → descarta o já enviado (staticData) → lê o detalhe de cada um (`deal_stage_histories` dá a
hora REAL de entrada na etapa) → monta os eventos → `events:ingest` → nota no negócio (`POST /activities`) → erro na
execução se o Google recusar. O detalhe do negócio vem SEM contato: e-mail e telefone saem da listagem.
- gclid/gbraid/wbraid até 90 dias; sem clique, e-mail/telefone com hash até 63 dias (precisa das conversões
  otimizadas para leads ligadas na conta). transactionId = rd-<negócio>-sql|purchase: retroativo e contínuo não somam.
- `--desde`: o contínuo só manda o que aconteceu a partir dali; o que veio antes vai pelo `--retroativo`
  (workflow temporário com TODOS os negócios do prefixo, não só os que estão hoje na etapa; nota no negócio só no
  `--enviar`). `--teste`: temporário, `validateOnly`, sem nota. Temporários são apagados no fim.
- Conversões novas: a Data Manager recusa com `destination_references NOT_FOUND` por 10 a 35 min (propagação).
Brief, bloco `devolucao_rd`: prefixo_nome, etapa_sql, usuario_nota, valores.SQL, valor_venda_padrao,
campos {gclid, gbraid, wbraid}, google {customer_id, login_customer_id, acoes {SQL, Purchase}},
n8n {credencial_rd (query auth com o token do RD), credencial_google (OAuth Data Manager)}. Nenhum segredo no brief.
"""
import argparse, json, os, re, sys, time, urllib.request, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
NUCLEO = os.path.join(AQUI, "..", "templates", "devolucao", "nucleo.js")
RD = "https://crm.rdstation.com/api/v1"


def validar(b):
    """Lista de mensagens BLOQUEANTE do bloco devolucao_rd (vazia = ok)."""
    d = b.get("devolucao_rd") or {}
    g, n = d.get("google") or {}, d.get("n8n") or {}
    r = []
    if not str(d.get("prefixo_nome") or "").strip():
        r.append("prefixo_nome vazio: sem ele o fluxo manda negócio que não veio da mídia")
    if not re.fullmatch(r"[0-9a-f]{24}", str(d.get("etapa_sql") or "")):
        r.append("etapa_sql não parece id de etapa do RD (24 hex)")
    if not re.fullmatch(r"[0-9a-f]{24}", str(d.get("usuario_nota") or "")):
        r.append("usuario_nota não parece id de usuário do RD (24 hex)")
    if not re.fullmatch(r"\d{10}", re.sub(r"\D", "", str(g.get("customer_id") or ""))):
        r.append("google.customer_id sem 10 dígitos")
    for ev in ("SQL", "Purchase"):
        if not re.fullmatch(r"\d+", str((g.get("acoes") or {}).get(ev) or "")):
            r.append(f"google.acoes.{ev} vazio (conversion action UPLOAD_CLICKS)")
    for k in ("credencial_rd", "credencial_google"):
        if not n.get(k):
            r.append(f"n8n.{k} vazio")
    texto = json.dumps(b)
    if re.search(r"token=|EAA[A-Za-z0-9]{20}|ya29\.", texto):
        r.append("segredo no brief: token vai na credencial do n8n, nunca no brief")
    return r


def funcoes():
    src = open(NUCLEO, encoding="utf-8").read()
    return "\n".join(re.search(r"^function " + n + r"\(.*?^}\n", src, re.S | re.M).group(0)
                     for n in ("sha256", "telefoneE164", "emailNormalizado", "dataGoogle"))


def cfg(b, desde, validar_apenas):
    d = b["devolucao_rd"]
    g = d["google"]
    return {"customer_id": re.sub(r"\D", "", str(g["customer_id"])),
            "login_customer_id": re.sub(r"\D", "", str(g.get("login_customer_id") or "")),
            "acoes": {k: str(v) for k, v in g["acoes"].items()}, "prefixo": d["prefixo_nome"],
            "valor_sql": float((d.get("valores") or {}).get("SQL") or 0), "ticket": float(d.get("valor_venda_padrao") or 0),
            "desde": int(desde), "validar_apenas": bool(validar_apenas), "etapa_sql": d["etapa_sql"],
            "campos": d.get("campos") or {}}


CANDIDATOS = r"""
const CFG = __CFG__;
const st = $getWorkflowStaticData('global'); st.enviados = st.enviados || {}; st.antes = st.antes || {};
const lista = (no) => $(no).all().flatMap(i => (i.json && i.json.deals) || []);
const daMidia = (d) => String(d.name || '').startsWith(CFG.prefixo);
const out = [], visto = {};
const quer = (d, evento) => {
  const tx = 'rd-' + (d._id || d.id) + '-' + evento.toLowerCase();
  if (st.enviados[tx] || st.antes[tx] || visto[tx]) return;
  visto[tx] = 1; out.push({ json: { deal_id: d._id || d.id, evento, tx } });
};
for (const d of lista('RD | Na etapa de SQL')) if (daMidia(d)) quer(d, 'SQL');
for (const d of lista('RD | Ganhos')) {
  if (d.win !== true || !daMidia(d)) continue;
  quer(d, 'Purchase');
  quer(d, 'SQL');  // ganhou entre duas varreduras: a entrada na etapa de SQL vem do histórico
}
return out;
"""

MONTAR = r"""
const CFG = __CFG__;
__FUNCOES__
const st = $getWorkflowStaticData('global'); st.antes = st.antes || {};
const agora = Date.now() / 1000;
const grupos = {};
const itens = $input.all();
// o detalhe do negócio (/deals/{id}) vem sem contato: e-mail e telefone saem da listagem
const porId = {};
for (const no of ['RD | Na etapa de SQL', 'RD | Ganhos'])
  for (const x of $(no).all().flatMap(i => (i.json && i.json.deals) || [])) porId[x._id || x.id] = x;
for (let i = 0; i < itens.length; i++) {
  const d = itens[i].json, c = $('Candidatos').itemMatching(i).json;
  let ts = null;
  if (c.evento === 'SQL') {
    const h = (d.deal_stage_histories || []).filter(x => x.deal_stage_id === CFG.etapa_sql)
      .map(x => Date.parse(x.start_date) / 1000).sort((a, b) => a - b);
    ts = h.length ? h[0] : null;
  } else ts = d.closed_at ? Date.parse(d.closed_at) / 1000 : null;
  if (!ts || ts < CFG.desde) { st.antes[c.tx] = 1; continue; }
  const cf = (id) => { for (const f of d.deal_custom_fields || []) if (id && f.custom_field_id === id && f.value) return String(f.value).trim(); return ''; };
  const gclid = cf(CFG.campos.gclid), gbraid = cf(CFG.campos.gbraid), wbraid = cf(CFG.campos.wbraid);
  const ids = [], ja = {};
  for (const ct of (porId[c.deal_id] || {}).contacts || d.contacts || []) {
    for (const e of ct.emails || []) { const n = emailNormalizado(e.email, true); if (n) { const h = sha256(n); if (!ja[h]) { ja[h] = 1; ids.push({ emailAddress: h }); } } }
    for (const p of ct.phones || []) { const n = telefoneE164(p.phone); if (n) { const h = sha256(n); if (!ja[h]) { ja[h] = 1; ids.push({ phoneNumber: h }); } } }
  }
  const idade = agora - ts, clique = !!(gclid || gbraid || wbraid);
  const okClique = clique && idade <= 90 * 86400 - 3600, okDados = ids.length > 0 && idade <= 63 * 86400 - 3600;
  if (!okClique && !okDados) { st.antes[c.tx] = 1; continue; }
  const valor = c.evento === 'Purchase' ? (Number(d.amount_total) > 0 ? Number(d.amount_total) : CFG.ticket) : CFG.valor_sql;
  const ev = { eventTimestamp: dataGoogle(Math.floor(ts), '-03:00'), transactionId: c.tx, eventSource: 'WEB',
               conversionValue: valor, currency: 'BRL' };
  if (okClique) { const ad = {}; if (gclid) ad.gclid = gclid; if (gbraid) ad.gbraid = gbraid; if (wbraid && !gclid && !gbraid) ad.wbraid = wbraid; ev.adIdentifiers = ad; }
  if (okDados) ev.userData = { userIdentifiers: ids.slice(0, 10) };
  const g = (grupos[c.evento] = grupos[c.evento] || { evs: [], txs: [] });
  g.evs.push(ev); g.txs.push({ tx: c.tx, deal_id: d._id || d.id, clique: okClique });
}
return Object.keys(grupos).map(n => {
  const destino = { operatingAccount: { accountType: 'GOOGLE_ADS', accountId: CFG.customer_id }, productDestinationId: CFG.acoes[n] };
  if (CFG.login_customer_id) destino.loginAccount = { accountType: 'GOOGLE_ADS', accountId: CFG.login_customer_id };
  return { json: { evento: n, txs: grupos[n].txs, body: { destinations: [destino], encoding: 'HEX',
                   validateOnly: !!CFG.validar_apenas, events: grupos[n].evs } } };
});
"""

REGISTRAR = r"""
const st = $getWorkflowStaticData('global'); st.enviados = st.enviados || {};
const agora = Math.floor(Date.now() / 1000);
const out = [], rs = $input.all();
for (let i = 0; i < rs.length; i++) {
  const r = rs[i].json, src = $('Montar eventos').itemMatching(i).json;
  const ok = r.statusCode === 200, teste = !!src.body.validateOnly;
  const nome = src.evento === 'SQL' ? 'SQL' : 'Venda';
  const msg = ok ? 'aceito pela Data Manager API (HTTP 200' + (teste ? ', só validação' : '') + ')'
                 : 'RECUSADO pela Data Manager API (HTTP ' + r.statusCode + '): ' + JSON.stringify(r.body || {}).slice(0, 400);
  for (const t of src.txs) {
    if (ok && !teste) st.enviados[t.tx] = agora;
    out.push({ json: { deal_id: t.deal_id, ok, teste, evento: src.evento,
      text: '[Devolução Google Ads] ' + nome + ' ' + msg + (t.clique ? ' | com gclid' : ' | por e-mail/telefone') } });
  }
}
const corte = agora - 200 * 86400;
for (const k of Object.keys(st.enviados)) if (st.enviados[k] < corte) delete st.enviados[k];
return out;
"""

FALHOU = r"""
const ruins = $('Registrar').all().filter(i => !i.json.ok);
if (ruins.length) throw new Error(ruins.length + ' conversão(ões) recusada(s) pelo Google: ' + ruins[0].json.text.slice(0, 300));
return [{ json: { enviados: $('Registrar').all().length } }];
"""


def _no(nome, tipo, versao, pos, params, **extra):
    n = {"id": str(uuid.uuid4()), "name": nome, "type": tipo, "typeVersion": versao, "position": pos, "parameters": params}
    n.update(extra)
    return n


def _lista(nome, pos, prefixo, filtros, cred):
    q = [{"name": "limit", "value": "200"}, {"name": "name", "value": prefixo}] + filtros
    return _no(nome, "n8n-nodes-base.httpRequest", 4.2, pos, {
        "url": RD + "/deals", "authentication": "genericCredentialType", "genericAuthType": "httpQueryAuth",
        "sendQuery": True, "queryParameters": {"parameters": q},
        "options": {"pagination": {"pagination": {"paginationMode": "updateAParameterInEachRequest",
                    "parameters": {"parameters": [{"type": "qs", "name": "page", "value": "={{ $pageCount + 1 }}"}]},
                    "paginationCompleteWhen": "other", "completeExpression": "={{ $response.body.has_more !== true }}",
                    "limitPagesFetched": True, "maxRequestCount": 25}},
                    "response": {"response": {"responseFormat": "json"}}}},
        credentials=cred, executeOnce=True)


def workflow(b, desde, modo="producao"):
    """modo: producao (agendado), teste (webhook, validateOnly, sem nota), retro_validar, retro_enviar
    (webhook, todos os negócios do prefixo, desde=0)."""
    d = b["devolucao_rd"]
    temporario = modo != "producao"
    validar_apenas = modo in ("teste", "retro_validar")
    c = json.dumps(cfg(b, 0 if modo.startswith("retro") else desde, validar_apenas))
    code = lambda s: s.replace("__CFG__", c).replace("__FUNCOES__", funcoes())
    cred_rd = {"httpQueryAuth": {"id": d["n8n"]["credencial_rd"], "name": "RD CRM"}}
    cred_dm = {"oAuth2Api": {"id": d["n8n"]["credencial_google"], "name": "Google Data Manager"}}
    sigla = b.get("sigla") or "CLIENTE"
    gatilho = (_no("Chamada", "n8n-nodes-base.webhook", 2, [0, 0],
                   {"httpMethod": "GET", "path": "tmp-devolucao-rd-" + uuid.uuid4().hex[:12], "responseMode": "onReceived",
                    "options": {}}, webhookId=str(uuid.uuid4()))
               if temporario else
               _no("De hora em hora", "n8n-nodes-base.scheduleTrigger", 1.2, [0, 0],
                   {"rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}}))
    filtro_sql = [] if modo.startswith("retro") else [{"name": "deal_stage_id", "value": d["etapa_sql"]}]
    nos = [gatilho,
           _lista("RD | Na etapa de SQL", [220, 0], d["prefixo_nome"], filtro_sql, cred_rd),
           _lista("RD | Ganhos", [440, 0], d["prefixo_nome"], [{"name": "win", "value": "true"}], cred_rd),
           _no("Candidatos", "n8n-nodes-base.code", 2, [660, 0], {"jsCode": code(CANDIDATOS)}),
           _no("RD | Negócio (histórico)", "n8n-nodes-base.httpRequest", 4.2, [880, 0], {
               "url": "=" + RD + "/deals/{{ $json.deal_id }}", "authentication": "genericCredentialType",
               "genericAuthType": "httpQueryAuth",
               "options": {"batching": {"batch": {"batchSize": 1, "batchInterval": 500}},
                           "response": {"response": {"responseFormat": "json"}}}}, credentials=cred_rd),
           _no("Montar eventos", "n8n-nodes-base.code", 2, [1100, 0], {"jsCode": code(MONTAR)}),
           _no("Google Ads | Data Manager", "n8n-nodes-base.httpRequest", 4.2, [1320, 0], {
               "method": "POST", "url": "https://datamanager.googleapis.com/v1/events:ingest",
               "authentication": "genericCredentialType", "genericAuthType": "oAuth2Api", "sendBody": True,
               "specifyBody": "json", "jsonBody": "={{ JSON.stringify($json.body) }}",
               "options": {"response": {"response": {"fullResponse": True, "neverError": True, "responseFormat": "json"}}}},
               credentials=cred_dm),
           _no("Registrar", "n8n-nodes-base.code", 2, [1540, 0], {"jsCode": REGISTRAR}),
           _no("RD | Nota no negócio", "n8n-nodes-base.httpRequest", 4.2, [1760, 0], {
               "method": "POST", "url": RD + "/activities", "authentication": "genericCredentialType",
               "genericAuthType": "httpQueryAuth", "sendBody": True, "specifyBody": "json",
               "jsonBody": "={{ JSON.stringify({ activity: { deal_id: $json.deal_id, user_id: '" + d["usuario_nota"]
                           + "', text: $json.text } }) }}",
               "options": {"batching": {"batch": {"batchSize": 1, "batchInterval": 400}}}},
               credentials=cred_rd, onError="continueRegularOutput", disabled=validar_apenas),
           _no("Falhou?", "n8n-nodes-base.code", 2, [1980, 0], {"jsCode": FALHOU})]
    ordem = [n["name"] for n in nos]
    con = {a: {"main": [[{"node": x, "type": "main", "index": 0}]]} for a, x in zip(ordem, ordem[1:])}
    nome = (f"[{sigla}] [TEMPORÁRIO] Devolução RD → Google ({modo})" if temporario
            else f"[{sigla}] [DEVOLUÇÃO] [RD CRM] | SQL e venda → Google Ads (Data Manager)")
    return {"name": nome, "nodes": nos, "connections": con, "settings": {"executionOrder": "v1"}}


# ----------------------------------------------------------------------------------------------- n8n

def _api(base, chave, m, c, corpo=None):
    r = urllib.request.Request(base.rstrip("/") + "/api/v1" + c, method=m, data=json.dumps(corpo).encode() if corpo is not None else None,
                               headers={"X-N8N-API-KEY": chave, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    t = urllib.request.urlopen(r, timeout=60).read()
    return json.loads(t) if t else {}


def resumo_execucao(rd):
    """Uma linha por nó, sem dado pessoal (só contagens, status e o início da resposta do Google)."""
    out = []
    for nome, runs in rd["runData"].items():
        for run in runs:
            itens = [i.get("json") for l in ((run.get("data") or {}).get("main") or [[]]) for i in (l or [])]
            if nome.startswith("RD | Na etapa") or nome.startswith("RD | Ganhos"):
                r = f"{sum(len(x.get('deals', [])) for x in itens)} negócios"
            elif nome == "Candidatos":
                r = json.dumps({e: sum(x["evento"] == e for x in itens) for e in ("SQL", "Purchase")})
            elif nome == "Montar eventos":
                r = json.dumps([{"evento": x["evento"], "eventos": len(x["body"]["events"]),
                                 "com_clique": sum("adIdentifiers" in e for e in x["body"]["events"]),
                                 "validateOnly": x["body"]["validateOnly"]} for x in itens])
            elif nome.startswith("Google"):
                r = json.dumps([{"status": x.get("statusCode"), "body": json.dumps(x.get("body"))[:240]} for x in itens])
            else:
                r = f"{len(itens)} item(ns)"
            out.append(f"- {nome}: {run.get('executionStatus')} {((run.get('error') or {}).get('message') or '')[:200]} {r}")
    return out


def temporario(base, chave, w):
    path = w["nodes"][0]["parameters"]["path"]
    wid = _api(base, chave, "POST", "/workflows", w)["id"]
    try:
        _api(base, chave, "POST", f"/workflows/{wid}/activate")
        time.sleep(2)
        urllib.request.urlopen(urllib.request.Request(f"{base.rstrip('/')}/webhook/{path}", headers={"User-Agent": "Mozilla/5.0"}), timeout=60)
        for _ in range(100):
            time.sleep(3)
            l = _api(base, chave, "GET", f"/executions?workflowId={wid}&limit=1")["data"]
            if l and l[0].get("status") not in ("running", "new", "waiting"):
                d = _api(base, chave, "GET", f"/executions/{l[0]['id']}?includeData=true")["data"]["resultData"]
                print("execução", l[0]["id"], l[0]["status"], ((d.get("error") or {}).get("message") or "")[:300])
                print("\n".join(resumo_execucao(d)))
                return
        print("nenhuma execução terminou em 5 min")
    finally:
        try:
            _api(base, chave, "POST", f"/workflows/{wid}/deactivate")
        finally:
            _api(base, chave, "DELETE", f"/workflows/{wid}")
            print("workflow temporário apagado")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--gerar", help="só grava o JSON do workflow de produção (sem rede)")
    ap.add_argument("--desde", type=int)
    ap.add_argument("--n8n")
    ap.add_argument("--n8n-key", help="arquivo com a chave da API do n8n (nunca a chave na linha de comando)")
    ap.add_argument("--teste", action="store_true")
    ap.add_argument("--retroativo", action="store_true")
    ap.add_argument("--validar", action="store_true")
    ap.add_argument("--enviar", action="store_true")
    ap.add_argument("--criar", action="store_true")
    ap.add_argument("--atualizar")
    a = ap.parse_args()
    b = json.load(open(a.brief))
    erros = validar(b)
    if erros:
        sys.exit("BLOQUEANTE:\n- " + "\n- ".join(erros))
    if a.gerar:
        os.makedirs(os.path.dirname(os.path.abspath(a.gerar)), exist_ok=True)
        json.dump(workflow(b, a.desde or int(time.time())), open(a.gerar, "w"), ensure_ascii=False, indent=1)
        print("gerado:", a.gerar)
        return
    if not (a.n8n and a.n8n_key):
        sys.exit("--n8n e --n8n-key são obrigatórios fora do --gerar")
    chave = open(os.path.expanduser(a.n8n_key)).read().strip()
    if a.teste:
        temporario(a.n8n, chave, workflow(b, 0, "teste"))
    elif a.retroativo:
        if not (a.validar or a.enviar):
            sys.exit("--retroativo pede --validar ou --enviar")
        temporario(a.n8n, chave, workflow(b, 0, "retro_enviar" if a.enviar else "retro_validar"))
    elif a.criar or a.atualizar:
        if not a.desde:
            sys.exit("--desde <unix> é obrigatório: o que vem antes vai pelo --retroativo")
        w = workflow(b, a.desde)
        if a.criar:
            x = _api(a.n8n, chave, "POST", "/workflows", w)
            print("criado DESLIGADO (ligar é outra decisão):", x["id"], x["name"])
        else:
            x = _api(a.n8n, chave, "PUT", f"/workflows/{a.atualizar}", {k: w[k] for k in ("name", "nodes", "connections", "settings")})
            print("atualizado:", x["id"], "ativo" if x.get("active") else "desligado")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
