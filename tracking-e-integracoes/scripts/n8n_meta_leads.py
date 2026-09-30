#!/usr/bin/env python3
"""Extrai os leads dos formulários instantâneos de uma página (últimos N dias) pela credencial Facebook Lead Ads
conectada no n8n, sem trazer nome, e-mail ou telefone completo: cria um workflow temporário, chama, salva e APAGA.

  python3 scripts/n8n_meta_leads.py --n8n https://<n8n> --chave-n8n ~/.config/<pasta>/n8n.key \\
      --credencial <id da credencial facebookLeadAdsOAuth2Api> --pagina <page_id> --out meta_leads.json [--dias 90]

Saída: [{id, t, form, k (DDD|8 dígitos), ad, adset, camp, plat, org}] — entrada do scripts/auditar_entrada.py e da
recuperação. Por que pelo n8n: o token OAuth fica na credencial (a API do n8n nunca devolve o segredo). Arquivo 600.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request, uuid

CODIGO = r"""
const chave = t => { let d = String(t || '').replace(/\D/g, ''); if (d.length < 10) return ''; if (d.length >= 12 && d.startsWith('55')) d = d.slice(2); return d.slice(0, 2) + '|' + d.slice(-8); };
const tok = $input.first().json.access_token;
if (!tok) throw new Error('sem token da página: a credencial não está conectada (Connect) ou sem acesso à página');
const base = 'https://graph.facebook.com/__GV__/';
const forms = await this.helpers.httpRequest({ url: base + '__PAGINA__/leadgen_forms', qs: { fields: 'id,status', limit: 100, access_token: tok }, json: true });
const out = [];
const desde = Math.floor(Date.now() / 1000) - __DIAS__ * 86400;
for (const f of forms.data || []) {
  let url = base + f.id + '/leads', qs = { fields: 'id,created_time,field_data,ad_name,adset_name,campaign_name,platform,is_organic', limit: 500, access_token: tok, filtering: JSON.stringify([{ field: 'time_created', operator: 'GREATER_THAN', value: desde }]) };
  for (let p = 0; url && p < 40; p++) {
    const r = await this.helpers.httpRequest({ url, qs, json: true });
    for (const l of r.data || []) {
      let tel = '';
      for (const fd of l.field_data || []) if (/phone|telefone|whats|celular/i.test(fd.name)) tel = (fd.values || [])[0];
      out.push({ id: String(l.id), t: l.created_time, form: f.id, k: chave(tel), ad: l.ad_name || '', adset: l.adset_name || '', camp: l.campaign_name || '', plat: l.platform || '', org: !!l.is_organic });
    }
    url = r.paging && r.paging.next; qs = undefined;
  }
}
return [{ json: { leads: out } }];
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n8n", required=True)
    ap.add_argument("--chave-n8n", required=True)
    ap.add_argument("--credencial", required=True)
    ap.add_argument("--pagina", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dias", type=int, default=90)
    ap.add_argument("--graph", default="v24.0")
    a = ap.parse_args()
    base = a.n8n.rstrip("/")
    chave = open(os.path.expanduser(a.chave_n8n)).read().strip()
    H = {"X-N8N-API-KEY": chave, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

    def api(m, c, corpo=None):
        r = urllib.request.Request(base + "/api/v1" + c, method=m, headers=H, data=json.dumps(corpo).encode() if corpo is not None else None)
        t = urllib.request.urlopen(r, timeout=60).read()
        return json.loads(t) if t else {}

    path = "tmp-meta-leads-" + uuid.uuid4().hex[:10]
    codigo = CODIGO.replace("__GV__", a.graph).replace("__PAGINA__", a.pagina).replace("__DIAS__", str(a.dias))
    nos = [{"id": str(uuid.uuid4()), "name": "Chamada", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 0],
            "webhookId": str(uuid.uuid4()), "parameters": {"httpMethod": "GET", "path": path, "responseMode": "lastNode", "options": {}}},
           {"id": str(uuid.uuid4()), "name": "Token", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [220, 0],
            "parameters": {"url": f"https://graph.facebook.com/{a.graph}/{a.pagina}?fields=access_token",
                           "authentication": "predefinedCredentialType", "nodeCredentialType": "facebookLeadAdsOAuth2Api", "options": {}},
            "credentials": {"facebookLeadAdsOAuth2Api": {"id": a.credencial, "name": "Lead Ads"}}},
           {"id": str(uuid.uuid4()), "name": "Extrair", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 0],
            "parameters": {"jsCode": codigo}}]
    con = {"Chamada": {"main": [[{"node": "Token", "type": "main", "index": 0}]]},
           "Token": {"main": [[{"node": "Extrair", "type": "main", "index": 0}]]}}
    wid = api("POST", "/workflows", {"name": "[TEMPORÁRIO] extração de leads do formulário", "nodes": nos, "connections": con,
                                     "settings": {"executionOrder": "v1"}})["id"]
    try:
        api("POST", f"/workflows/{wid}/activate")
        time.sleep(2)
        try:
            dados = json.loads(urllib.request.urlopen(urllib.request.Request(f"{base}/webhook/{path}", headers={"User-Agent": "Mozilla/5.0"}),
                                                      timeout=300).read())
        except urllib.error.HTTPError as e:
            time.sleep(2)
            ex = api("GET", f"/executions?workflowId={wid}&limit=1")["data"]
            erro = api("GET", f"/executions/{ex[0]['id']}?includeData=true")["data"]["resultData"].get("error", {}) if ex else {}
            sys.exit(f"falhou (HTTP {e.code}): {erro.get('message')}")
        json.dump(dados["leads"], open(a.out, "w"), ensure_ascii=False)
        os.chmod(a.out, 0o600)
        print(f"{len(dados['leads'])} leads salvos em {a.out}")
    finally:
        try:
            api("POST", f"/workflows/{wid}/deactivate")
        finally:
            api("DELETE", f"/workflows/{wid}")
            print("workflow temporário apagado")


if __name__ == "__main__":
    main()
