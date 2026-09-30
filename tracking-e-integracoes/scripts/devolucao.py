#!/usr/bin/env python3
"""Devolução CRM → plataformas: gera o workflow do n8n e as peças do GTM Server a partir do bloco "devolucao" do brief.

  python3 scripts/devolucao.py --brief clientes/<c>/brief.json --out saida/<c> [--producao]

Desenho (implementacoes/crm-kommo.md): o Kommo avisa a mudança de etapa por webhook → o n8n responde na hora, lê o
lead e o contato na API, monta o evento (núcleo em templates/devolucao/nucleo.js) e manda:
  - ao Meta pelo sGTM: POST no Data Client (/data) → tag CAPI de CRM (system_generated, lead_id, event_time da etapa);
  - ao Google Ads pela Data Manager API (events:ingest), com gclid/gbraid/wbraid e e-mail/telefone com hash.
Cada envio vira nota no lead do Kommo. O token da CAPI continua só no sGTM; a chave entre n8n e sGTM é gerada aqui,
fica em <out>/.chave_devolucao (600) e é reaproveitada nas próximas gerações.

Saída: n8n-devolucao-<c>.json (importar no n8n), sgtm-devolucao-<c>.json (peças para aplicar no sGTM que já existe,
pela MCP do GTM) e resumo-devolucao.md. Container novo: gerar_containers.py já inclui as peças quando o brief tem o bloco.
"""
import argparse, copy, json, os, re, secrets, sys, uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
NUCLEO = os.path.join(RAIZ, "templates", "devolucao", "nucleo.js")
DATA_CLIENT_TPL = os.path.join(RAIZ, "templates", "gtm", "data-client.tpl")
DATA_CLIENT_REF = {"host": "github.com", "owner": "stape-io", "repository": "data-client",
                   "version": "d0eaccc5f2b52c25ed3712daf4176509dc9e95de"}
NOME_CLIENTE = "Data Client | CRM"
PADRAO_META = {"Purchase", "Lead", "CompleteRegistration", "Contact", "Schedule", "SubmitApplication"}
ORDEM = ["Lead", "MQL", "SQL", "Purchase"]  # numeração das tags: 00.5 em diante, nesta ordem
FECHADO = {"142": "ganho", "143": "perdido"}
TOKEN_DEV = "COLE_NO_N8N"


# ----------------------------------------------------------------------------------------------- validação

def via_sgtm(b):
    """Meta pelo sGTM (padrão) ou "direto" (n8n → API de Conversões, sem Stape)."""
    return ((b.get("devolucao") or {}).get("meta_via") or "sgtm") == "sgtm"


def validar(b):
    """Lista de (nível, mensagem) do bloco devolucao."""
    r = []
    bloq = lambda m: r.append(("BLOQUEANTE", m))
    aten = lambda m: r.append(("ATENÇÃO", m))
    d = b.get("devolucao") or {}
    if not d:
        return r
    api = d.get("kommo_api", "")
    if not re.fullmatch(r"https://[a-z0-9-]+\.(kommo|amocrm)\.com/api/v4", api):
        bloq(f"kommo_api '{api}' fora do formato https://<subdominio>.kommo.com/api/v4")
    etapas = d.get("etapas") or {}
    if not etapas:
        bloq("devolucao.etapas vazio: nenhuma etapa do Kommo vira evento")
    for st, ev in etapas.items():
        if not str(st).isdigit():
            bloq(f"etapa '{st}' não é id numérico do Kommo (use o status_id, não o nome)")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", str(ev)):
            bloq(f"evento '{ev}' com caractere inválido para o Meta")
        if str(st) == "143":
            bloq("etapa 143 (perdido) mapeada como evento: venda perdida não volta como conversão")
    if len(set(etapas.values())) < len(etapas):
        aten("duas etapas viram o mesmo evento: o event_id é por lead e evento, só a primeira conta")
    nomes = set(etapas.values())
    for ev in nomes & {"PageView", "Lead", "Contact", "MQL"}:
        aten(f"evento {ev} também sai do site: em sGTM que já existe, pôr Client Name = <cliente do site> no acionador "
             f"do site (container novo já sai assim), senão a tag do site dispara com o evento do CRM")
    if "Purchase" in nomes and "142" not in etapas:
        aten("Purchase mapeado numa etapa que não é a 142 (ganho): confira se é mesmo a venda")
    if not d.get("funis"):
        aten("sem devolucao.funis: mudança de etapa em qualquer funil conta (o 142 é igual em todos)")
    for nome in nomes - {"Purchase"}:
        if not (d.get("valores") or {}).get(nome):
            aten(f"evento {nome} sem valor proxy em devolucao.valores (vai com valor 0)")
    campos = d.get("campos") or {}
    if not any(campos.get(k) for k in ("meta_lead_id", "fbc", "fbclid")):
        aten("nenhum campo de clique do Meta (meta_lead_id, fbc ou fbclid): o Meta só casa por telefone/e-mail, "
             "e sem lead_id o evento não entra na otimização por lead de conversão (Conversion Leads)")
    for k, v in campos.items():
        if v and not str(v).isdigit():
            bloq(f"campos.{k} = '{v}' não é id numérico de campo do Kommo")
    g = d.get("google") or {}
    if g:
        if not re.fullmatch(r"\d{10}", re.sub(r"\D", "", str(g.get("customer_id", "")))):
            bloq(f"google.customer_id '{g.get('customer_id')}' não tem 10 dígitos")
        for ev, acao in (g.get("acoes") or {}).items():
            if not str(acao).isdigit():
                bloq(f"google.acoes.{ev} = '{acao}' não é id numérico de conversion action")
            if ev not in nomes:
                aten(f"google.acoes.{ev} não corresponde a nenhuma etapa mapeada")
        if not any(campos.get(k) for k in ("gclid", "gbraid", "wbraid")) and not g.get("sem_clique"):
            bloq("Google ligado sem campo de gclid/gbraid/wbraid no Kommo: nenhum evento sai (ou ligue google.sem_clique)")
        if not re.fullmatch(r"[+-]\d{2}:\d{2}", g.get("fuso", "-03:00")):
            bloq(f"google.fuso '{g.get('fuso')}' fora do formato -03:00")
    if d.get("meta_via") not in (None, "sgtm", "direto"):
        bloq(f"meta_via '{d.get('meta_via')}' inválido (sgtm ou direto)")
    if d.get("meta_via") == "direto":
        if not re.fullmatch(r"\d{15,16}", str(b.get("meta_pixel_id", ""))):
            bloq("meta_via direto sem meta_pixel_id válido no brief")
        if not (d.get("n8n") or {}).get("credencial_capi"):
            aten("n8n.credencial_capi vazio: credencial Query Auth (access_token = token da CAPI), restrita a graph.facebook.com")
        if d.get("meta_test_event_code"):
            aten("meta_test_event_code ativo: tire do brief e gere de novo antes de ligar, senão todo evento vira teste")
    lg = d.get("meta_leadgen") or {}
    if lg and not re.fullmatch(r"\d{10,20}", str(lg.get("pagina", ""))):
        bloq(f"meta_leadgen.pagina '{lg.get('pagina')}' não é id de página do Facebook")
    if lg and not lg.get("credencial"):
        aten("meta_leadgen.credencial vazio: credencial Facebook Lead Ads (OAuth) conectada à página")
    n = d.get("n8n") or {}
    if not n.get("credencial_kommo"):
        aten("n8n.credencial_kommo vazio: escolha a credencial (Header Auth: Authorization = Bearer <token>) no n8n depois de importar")
    if g and not n.get("credencial_google"):
        aten("n8n.credencial_google vazio: crie uma OAuth2 com o escopo https://www.googleapis.com/auth/datamanager")
    if any(k in json.dumps(d).lower() for k in ("eyj0", "bearer ", "access_token", '"eaa')):
        bloq("o bloco devolucao tem token: tokens vão nas credenciais do n8n, nunca no brief")
    return r


# ----------------------------------------------------------------------------------------------- sGTM

def eventos(b):
    """Eventos que viram tag no sGTM (nenhum no modo direto)."""
    if not via_sgtm(b):
        return []
    nomes = list(dict.fromkeys((b.get("devolucao") or {}).get("etapas", {}).values()))
    return sorted(nomes, key=lambda n: (ORDEM.index(n) if n in ORDEM else len(ORDEM), nomes.index(n)))


def _p(tipo, key, value):
    return {"type": tipo, "key": key, "value": value}


def _mapa(pares):
    return {"type": "LIST", "key": None, "list": [{"type": "MAP", "map": [_p("TEMPLATE", "name", n), _p("TEMPLATE", "value", v)]}
                                                  for n, v in pares]}


def _lista(key, pares):
    lst = _mapa(pares)
    lst["key"] = key
    return lst


def _cond(a, b_):
    return {"type": "EQUALS", "parameter": [_p("TEMPLATE", "arg0", a), _p("TEMPLATE", "arg1", b_)]}


def pecas_sgtm(b, chave, tipo_capi, tipo_data_client, base_ids=None):
    """Peças do sGTM no formato da API do GTM (sem accountId/containerId/fingerprint).

    tipo_capi: tipo da tag CAPI da Stape no container (ex.: cvt_300000000_4); tipo_data_client: idem do Data Client.
    base_ids: {"variable": n, "trigger": n, "tag": n} para numerar a partir de ids livres (import de container).
    """
    base = base_ids or {"variable": 100, "trigger": 100, "tag": 100}
    d = b["devolucao"]
    crm = d.get("lead_event_source") or "Kommo"
    ids = {k: iter(range(v, v + 1000)) for k, v in base.items()}
    nid = lambda k: str(next(ids[k]))
    variaveis = [
        {"name": "00 - Devolução - Chave", "type": "c", "parameter": [_p("TEMPLATE", "value", chave)]},
        {"name": "00 - Devolução - CRM", "type": "c", "parameter": [_p("TEMPLATE", "value", crm)]},
    ] + [{"name": f"ED - {k}", "type": "ed", "parameter": [_p("TEMPLATE", "keyPath", k)]}
         for k in ("chave", "event_time", "lead_ip", "lead_user_agent")]
    for v in variaveis:
        v["variableId"] = nid("variable")
        v["_pasta"] = "⚙️ | Configurações"
    cliente = {"name": NOME_CLIENTE, "type": tipo_data_client, "priority": 0, "parameter": [
        _p("BOOLEAN", "exposeFPIDCookie", "false"), _p("BOOLEAN", "generateClientId", "false"),
        _p("BOOLEAN", "prolongCookies", "false"), _p("BOOLEAN", "acceptMultipleEvents", "false"),
        _p("TEMPLATE", "responseStatusCode", "200"), _p("TEMPLATE", "responseBody", "empty"),
        _p("TEMPLATE", "cookieStorageMode", "always")]}
    acionadores, tags = [], []
    for i, ev in enumerate(eventos(b)):
        tid = nid("trigger")
        acionadores.append({"triggerId": tid, "name": f"CRM - Event Name = {ev}", "type": "CUSTOM_EVENT",
                            "customEventFilter": [_cond("{{_event}}", ev)],
                            "filter": [_cond("{{Client Name}}", NOME_CLIENTE),
                                       _cond("{{ED - chave}}", "{{00 - Devolução - Chave}}")],
                            "_pasta": "🔵 | Meta CAPI"})
        padrao = ev in PADRAO_META
        par = [
            _p("TEMPLATE", "pixelId", "{{00 - Meta CAPI - Pixel Id}}"),
            _p("TEMPLATE", "accessToken", "{{00 - Meta CAPI - Access Token}}"),
            # CRM: system_generated (o que o Meta pede para lead de formulário instantâneo e etapa de CRM).
            _p("TEMPLATE", "actionSource", "system_generated"),
            _p("TEMPLATE", "inheritEventName", "override"),
            _p("TEMPLATE", "eventName", "standard" if padrao else "custom"),
            _p("TEMPLATE", "eventNameStandard" if padrao else "eventNameCustom", ev),
            _p("BOOLEAN", "useOptimisticScenario", "false"), _p("BOOLEAN", "enableEventEnhancement", "false"),
            _p("BOOLEAN", "enableMultipixelSetup", "false"), _p("BOOLEAN", "useAppSecretProof", "false"),
            _p("BOOLEAN", "useHttpOnlyCookie", "false"), _p("BOOLEAN", "overrideCookieDomain", "false"),
            # Sem cookie no pedido do n8n: gerar fbp inventaria um navegador por evento.
            _p("BOOLEAN", "generateFbp", "false"),
            _p("TEMPLATE", "logType", "no"), _p("TEMPLATE", "bigQueryLogType", "no"),
            _p("TEMPLATE", "testId", "{{00 - Meta CAPI - Test Event Code}}"),
            # O Data Client põe o IP e o navegador de quem chama (o n8n). Sobrescreve com os do lead; vazio = não manda.
            _lista("userDataList", [("client_ip_address", "{{ED - lead_ip}}"),
                                    ("client_user_agent", "{{ED - lead_user_agent}}"), ("country", "br")]),
            # Hora da mudança de etapa, não a hora do disparo.
            _lista("serverEventDataList", [("event_time", "{{ED - event_time}}")]),
            _lista("customDataList", [("event_source", "crm"), ("lead_event_source", "{{00 - Devolução - CRM}}")]),
        ]
        tags.append({"tagId": nid("tag"), "name": f"00.{5 + i} | Meta CAPI - {ev}", "type": tipo_capi,
                     "parameter": par, "firingTriggerId": [tid], "tagFiringOption": "ONCE_PER_EVENT",
                     "_pasta": "🔵 | Meta CAPI"})
    return {"variable": variaveis, "client": [cliente], "trigger": acionadores, "tag": tags}


def data_client_template(template_id, account_id, container_id):
    return {"accountId": account_id, "containerId": container_id, "templateId": template_id, "name": "Data Client",
            "fingerprint": "1790000000000", "templateData": open(DATA_CLIENT_TPL, encoding="utf-8").read(),
            "galleryReference": dict(DATA_CLIENT_REF)}


def incluir_no_container(cv, b, chave):
    """Acrescenta as peças da devolução a um containerVersion de servidor gerado dos templates."""
    conta, cont = cv["container"]["accountId"], cv["container"]["containerId"]
    tpl_capi = [t for t in cv["customTemplate"] if t.get("galleryReference", {}).get("repository") == "facebook-tag"][0]
    prox = lambda k, campo: max([int(x[campo]) for x in cv.get(k, [])] + [0]) + 1
    tid_dc = str(prox("customTemplate", "templateId"))
    cv["customTemplate"].append(data_client_template(tid_dc, conta, cont))
    p = pecas_sgtm(b, chave, f"cvt_{cont}_{tpl_capi['templateId']}", f"cvt_{cont}_{tid_dc}",
                   {"variable": prox("variable", "variableId"), "trigger": prox("trigger", "triggerId"), "tag": prox("tag", "tagId")})
    pastas = {f["name"]: f["folderId"] for f in cv.get("folder", [])}
    # Evento do CRM com o mesmo nome de um evento do site (ex.: "Lead" como etapa inicial do Conversion Leads)
    # dispararia também a tag do site, como website e com o IP do n8n. Os acionadores do site passam a exigir o
    # cliente do site.
    cliente_site = cv["client"][0]["name"]
    for g in cv.get("trigger", []):
        ev = [x["value"] for c in g.get("customEventFilter", []) for x in c["parameter"] if x["key"] == "arg1"]
        if ev and ev[0] in eventos(b) and not any("{{Client Name}}" in json.dumps(f) for f in g.get("filter", [])):
            g.setdefault("filter", []).append(_cond("{{Client Name}}", cliente_site))
    p["client"][0]["clientId"] = str(prox("client", "clientId"))
    for k in ("variable", "client", "trigger", "tag"):
        for x in p[k]:
            pasta = x.pop("_pasta", None)
            if pasta in pastas:
                x["parentFolderId"] = pastas[pasta]
            x.update({"accountId": conta, "containerId": cont, "fingerprint": "1790000000000"})
            cv.setdefault(k, []).append(x)
    return cv


# ----------------------------------------------------------------------------------------------- n8n

def _cfg_js(b):
    d = b["devolucao"]
    cfg = {"crm": d.get("lead_event_source") or "Kommo", "etapas": {str(k): v for k, v in d["etapas"].items()},
           "funis": [str(f) for f in d.get("funis") or []], "valores": d.get("valores") or {},
           "valor_venda_padrao": d.get("valor_venda_padrao") or 0, "moeda": d.get("moeda") or "BRL",
           "ddi": d.get("ddi") or "55", "pais": d.get("pais") or "br", "max_dias_meta": 7,
           "campos": {k: str(v) for k, v in (d.get("campos") or {}).items() if v},
           "google": d.get("google") or {}, "meta_via": d.get("meta_via") or "sgtm",
           "meta_test_event_code": d.get("meta_test_event_code") or "",
           "meta_leadgen": {"pagina": str((d.get("meta_leadgen") or {}).get("pagina") or ""),
                            "versao": d.get("graph_versao") or "v24.0",
                            "dias": (d.get("meta_leadgen") or {}).get("dias") or 90}}
    return json.dumps(cfg, ensure_ascii=False, indent=2)


def _no(nome, tipo, versao, pos, params, **extra):
    n = {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "devolucao/" + nome)), "name": nome, "type": tipo,
         "typeVersion": versao, "position": pos, "parameters": params}
    n.update(extra)
    return n


GENERICAS = ("httpHeaderAuth", "httpQueryAuth", "oAuth2Api")


def _http(nome, pos, metodo, url, cred=None, corpo=None, cred_tipo="httpHeaderAuth", nunca_erro=False):
    p = {"method": metodo, "url": url, "options": {"timeout": 20000}}
    if cred is not None and cred_tipo in GENERICAS:
        p.update({"authentication": "genericCredentialType", "genericAuthType": cred_tipo})
    elif cred is not None:  # credencial de um serviço (ex.: facebookLeadAdsOAuth2Api)
        p.update({"authentication": "predefinedCredentialType", "nodeCredentialType": cred_tipo})
    if corpo is not None:
        p.update({"sendBody": True, "specifyBody": "json", "jsonBody": corpo})
    # O Kommo responde application/hal+json e o n8n trata como texto (o lead vira uma string em "data"):
    # força JSON em todo nó HTTP.
    p["options"]["response"] = {"response": {"responseFormat": "json"}}
    if nunca_erro:
        p["options"]["response"]["response"].update({"fullResponse": True, "neverError": True})
    extra = {}
    if cred is not None:
        extra["credentials"] = {cred_tipo: {"id": cred or "", "name": {"httpHeaderAuth": "Kommo (Bearer)", "httpQueryAuth": "Meta CAPI (access_token)",
                                                       "facebookLeadAdsOAuth2Api": "Meta Lead Ads"}.get(cred_tipo, "Google Data Manager")}}
    return _no(nome, "n8n-nodes-base.httpRequest", 4.2, pos, p, **extra)


def workflow_n8n(b, chave):
    d = b["devolucao"]
    cliente = b.get("cliente", "cliente")
    sigla = (d.get("sigla") or re.sub(r"[^A-Z]", "", cliente.upper())[:4] or "CLI")
    nucleo = open(NUCLEO, encoding="utf-8").read()
    api = d["kommo_api"].rstrip("/")
    ssgtm = b.get("ssgtm_url", "").rstrip("/")
    n8n = d.get("n8n") or {}
    g = d.get("google") or {}
    cab = nucleo + "\n// ---- configuração do cliente (gerada por scripts/devolucao.py; mudar no brief e gerar de novo) ----\n" \
        + "const CFG = " + _cfg_js(b) + ";\n"
    ler = cab + r"""
// Uma mudança de etapa por item; ignora etapa fora do mapa e o que já foi enviado às duas plataformas.
const enviados = $getWorkflowStaticData('global').enviados || {};
const saida = [];
for (const item of $input.all()) {
  for (const m of lerWebhookKommo(item.json.body)) {
    const ev = eventoDaEtapa(CFG, m);
    if (!ev) continue;
    const id = 'kommo-' + m.lead_id + '-' + ev.toLowerCase();
    if (enviados['meta:' + id] && (enviados['google:' + id] || !(CFG.google.acoes || {})[ev])) continue;
    saida.push({ json: { mudanca: m, evento: ev } });
  }
}
return saida;
"""
    montar = cab + r"""
// Junta a mudança, o lead e o contato (mesma ordem dos nós anteriores, 1 item entra e 1 sai em cada um).
const mud = $('Ler mudança de etapa').all();
const leads = $('Kommo | Lead e contatos').all();
const agora = Math.floor(Date.now() / 1000);
// resposta que ainda chegue como texto (hal+json sem Response Format JSON) vira objeto aqui
const obj = (j) => {
  for (const k of ['body', 'data']) if (j && typeof j[k] === 'string') { try { return JSON.parse(j[k]); } catch (e) {} }
  return j && j.body && typeof j.body === 'object' ? j.body : j;
};
return $input.all().map((item, i) => {
  // o nó do contato devolve a resposta inteira (neverError): o contato está em body; 204/404 = lead sem contato
  const c = obj(item.json);
  const contato = c && c.id ? c : null;
  const r = montarEvento(CFG, mud[i].json.mudanca, obj(leads[i].json), contato, agora);
  if (r.meta && CFG.meta_via === 'direto') {
    r.meta_graph = { data: [metaGraph(r.meta, CFG.crm)] };
    if (CFG.meta_test_event_code) r.meta_graph.test_event_code = CFG.meta_test_event_code;
  } else if (r.meta) r.meta.chave = '__CHAVE__';
  return { json: { lead_id: mud[i].json.mudanca.lead_id, ...r } };
});
""".replace("__CHAVE__", chave)
    so = lambda plat: r"""
const enviados = $getWorkflowStaticData('global').enviados || {};
return $input.all().filter(i => i.json.""" + plat + r""" && !enviados['""" + plat + r""":' + i.json.event_id])
  .map(i => ({ json: i.json }));
"""
    teste = bool(d.get("meta_test_event_code"))
    registrar = lambda plat, rotulo, no_envio, ok_txt: r"""
// Marca o envio que deu certo (não manda de novo) e escreve a nota no lead do Kommo.
const est = $getWorkflowStaticData('global');
est.enviados = est.enviados || {};
const corte = Date.now() / 1000 - 120 * 86400;
for (const k of Object.keys(est.enviados)) if (est.enviados[k] < corte) delete est.enviados[k];
const base = $('""" + no_envio + r"""').all();
return $input.all().map((item, i) => {
  const ev = base[i].json;
  const st = item.json.statusCode || 0;
  const corpo = JSON.stringify(item.json.body || item.json).slice(0, 400);
  const ok = st >= 200 && st < 300;
  // modo de teste (Test Event Code) marca em lista separada: o envio de verdade desse lead não fica bloqueado
  if (ok) est.enviados['""" + plat + ("-teste" if teste else "") + r""":' + ev.event_id] = Math.floor(Date.now() / 1000);
  const texto = '[Devolução """ + rotulo + r"""] ' + ev.event_name + ' ' + (ok ? '""" + ok_txt + r"""' : 'FALHOU') + ' (HTTP ' + st + ')' +
    (ok ? '' : ' ' + corpo) + (ev.faltando && ev.faltando.length ? ' | ' + ev.faltando.join('; ') : '');
  return { json: { nota: [{ entity_id: Number(ev.lead_id), note_type: 'common', params: { text: texto } }] } };
});
"""
    if via_sgtm(b):
        no_meta = _http("sGTM | Meta CAPI", [1440, 180], "POST", ssgtm + "/data", corpo="={{ JSON.stringify($json.meta) }}",
                        nunca_erro=True)
    else:
        versao = d.get("graph_versao") or "v24.0"
        no_meta = _http("Meta | CAPI direta", [1440, 180], "POST",
                        f"https://graph.facebook.com/{versao}/{b['meta_pixel_id']}/events", cred=n8n.get("credencial_capi", ""),
                        cred_tipo="httpQueryAuth", corpo="={{ JSON.stringify($json.meta_graph) }}", nunca_erro=True)
    nome_meta = no_meta["name"]
    nos = [
        _no("Kommo | Mudança de etapa", "n8n-nodes-base.webhook", 2, [0, 300],
            {"httpMethod": "POST", "path": f"devolucao-{re.sub(r'[^a-z0-9]+', '-', cliente.lower()).strip('-')}-{chave[:10].lower()}",
             "responseMode": "onReceived", "options": {}},
            webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, "devolucao/" + chave))),
        _no("Ler mudança de etapa", "n8n-nodes-base.code", 2, [240, 300], {"jsCode": ler}),
        _http("Kommo | Lead e contatos", [480, 300], "GET", "=" + api + "/leads/{{ $json.mudanca.lead_id }}?with=contacts",
              cred=n8n.get("credencial_kommo", "")),
        _http("Kommo | Contato principal", [720, 300], "GET",
              "=" + api + "/contacts/{{ ((($json._embedded || {}).contacts || []).filter(c => c.is_main).concat(($json._embedded || {}).contacts || [])[0] || {}).id || 0 }}",
              cred=n8n.get("credencial_kommo", ""), nunca_erro=True),
        _no("Montar eventos", "n8n-nodes-base.code", 2, [960, 300], {"jsCode": montar}),
        _no("Só com Meta", "n8n-nodes-base.code", 2, [1200, 180], {"jsCode": so("meta")}),
        no_meta,
        _no("Meta | Registrar", "n8n-nodes-base.code", 2, [1680, 180], {"jsCode": registrar(
            "meta", "Meta", "Só com Meta", "entregue ao sGTM (conferir no Gerenciador de Eventos)" if via_sgtm(b)
            else "aceito pela API de Conversões")}),
        _http("Kommo | Nota no lead", [1920, 300], "POST", api + "/leads/notes", cred=n8n.get("credencial_kommo", ""),
              corpo="={{ JSON.stringify($json.nota) }}"),
    ]
    lg = d.get("meta_leadgen") or {}
    casar = cab + r"""
// Lead de formulário instantâneo: acha o id do lead no Meta pelo telefone (formulários da página, últimos N dias).
// Com o id o Meta casa o evento com o lead certo; sem ele o evento sai só com telefone e nome. Erro aqui nunca
// derruba o envio: vira aviso na nota do lead.
const evs = $('Montar eventos').all().map(i => i.json);
const tok = ($input.first() || {}).json || {};
const token = (tok.body && tok.body.access_token) || tok.access_token || '';
const LG = CFG.meta_leadgen;
let leads = [], erro = '';
const precisa = evs.some(e => e.meta && !e.meta.lead_id);
if (precisa && token) {
  try {
    const base = 'https://graph.facebook.com/' + LG.versao + '/';
    const forms = await this.helpers.httpRequest({ url: base + LG.pagina + '/leadgen_forms',
      qs: { fields: 'id,status', limit: 100, access_token: token }, json: true });
    const desde = Math.floor(Date.now() / 1000) - LG.dias * 86400;
    for (const f of (forms.data || [])) {
      let url = base + f.id + '/leads';
      let qs = { fields: 'id,created_time,field_data', limit: 500, access_token: token,
                 filtering: JSON.stringify([{ field: 'time_created', operator: 'GREATER_THAN', value: desde }]) };
      for (let pag = 0; url && pag < 20; pag++) {
        const r = await this.helpers.httpRequest({ url, qs, json: true });
        leads = leads.concat(r.data || []);
        url = r.paging && r.paging.next; qs = undefined;   // o "next" já traz a query inteira
      }
    }
  } catch (e) { erro = String((e && e.message) || e).slice(0, 150); }
} else if (precisa) {
  erro = 'sem token da página: ' + JSON.stringify(tok.body && tok.body.error ? tok.body.error.message : tok.error || '').slice(0, 120);
}
return evs.map(e => {
  if (e.meta && !e.meta.lead_id) {
    const id = acharLeadId(leads, e.meta.user_data && e.meta.user_data.phone_number, e.meta.event_time);
    if (id) {
      e.meta.lead_id = id;
      if (e.meta_graph) e.meta_graph.data[0].user_data.lead_id = id;
    } else {
      e.faltando = (e.faltando || []).concat(erro ? ['meta: id do lead não consultado (' + erro + ')']
        : ['meta: telefone sem lead nos formulários dos últimos ' + LG.dias + ' dias (' + leads.length + ' lidos)']);
    }
  }
  return { json: e };
});
"""
    if lg:
        tokn = _http("Meta | Token da página", [1080, 60], "GET",
                     f"https://graph.facebook.com/{d.get('graph_versao') or 'v24.0'}/{lg['pagina']}?fields=access_token",
                     cred=lg.get("credencial", ""), cred_tipo="facebookLeadAdsOAuth2Api", nunca_erro=True)
        tokn["executeOnce"] = True
        nos += [tokn, _no("Casar id do lead", "n8n-nodes-base.code", 2, [1100, 300], {"jsCode": casar})]
    depois_de_montar = "Casar id do lead" if lg else "Montar eventos"
    liga = {"Kommo | Mudança de etapa": ["Ler mudança de etapa"], "Ler mudança de etapa": ["Kommo | Lead e contatos"],
            "Kommo | Lead e contatos": ["Kommo | Contato principal"], "Kommo | Contato principal": ["Montar eventos"],
            depois_de_montar: ["Só com Meta"], "Só com Meta": [nome_meta], nome_meta: ["Meta | Registrar"],
            "Meta | Registrar": ["Kommo | Nota no lead"]}
    if g:
        gh = _http("Google Ads | Data Manager", [1440, 420], "POST", "https://datamanager.googleapis.com/v1/events:ingest",
                   cred=n8n.get("credencial_google", ""), cred_tipo="oAuth2Api", corpo="={{ JSON.stringify($json.google) }}",
                   nunca_erro=True)
        nos += [_no("Só com Google", "n8n-nodes-base.code", 2, [1200, 420], {"jsCode": so("google")}), gh,
                _no("Google | Registrar", "n8n-nodes-base.code", 2, [1680, 420],
                    {"jsCode": registrar("google", "Google Ads", "Só com Google", "aceito pela Data Manager API")})]
        liga[depois_de_montar].append("Só com Google")
        liga.update({"Só com Google": ["Google Ads | Data Manager"], "Google Ads | Data Manager": ["Google | Registrar"],
                     "Google | Registrar": ["Kommo | Nota no lead"]})
    if lg:
        liga["Montar eventos"] = ["Meta | Token da página"]
        liga["Meta | Token da página"] = ["Casar id do lead"]
    conexoes = {de: {"main": [[{"node": para, "type": "main", "index": 0} for para in lista]]} for de, lista in liga.items()}
    destino = "Meta CAPI" + (" (sGTM)" if via_sgtm(b) else " (direta)") + (" + Google Ads" if g else "")
    return {"name": f"[{sigla}] [DEVOLUÇÃO] [KOMMO] | Etapa do CRM → {destino}",
            "nodes": nos, "connections": conexoes, "settings": {"executionOrder": "v1"}}


# ----------------------------------------------------------------------------------------------- CLI

def chave_do_cliente(out):
    arq = os.path.join(out, ".chave_devolucao")
    if os.path.exists(arq):
        return open(arq).read().strip()
    os.makedirs(out, exist_ok=True)
    ch = secrets.token_urlsafe(24)
    with open(arq, "w") as f:
        f.write(ch)
    os.chmod(arq, 0o600)
    return ch


def resumo(b, achados, wf):
    d = b["devolucao"]
    g = d.get("google") or {}
    webhook = [n for n in wf["nodes"] if n["type"].endswith("webhook")][0]["parameters"]["path"]
    ls = [f"# Devolução CRM → plataformas: {b.get('cliente', '')}", "",
          "| Etapa do Kommo (status_id) | Evento | Meta (sGTM) | Google Ads (conversion action) |", "|---|---|---|---|"]
    for st, ev in d["etapas"].items():
        ls.append(f"| {st}{' (' + FECHADO[st] + ')' if st in FECHADO else ''} | {ev} | 00.x Meta CAPI - {ev} | "
                  f"{(g.get('acoes') or {}).get(ev, '—')} |")
    ls += ["", f"Webhook do n8n: `<n8n>/webhook/{webhook}` (POST). Kommo: Configurações → Integrações → Webhooks → "
           "\"Etapa do lead alterada\", ou a ação \"Send webhook\" do Digital Pipeline em cada etapa mapeada.", "",
           "## Validação", ""] + ([f"- **{n}**: {m}" for n, m in achados] or ["- Nenhum achado."])
    ls += ["", "## Antes de ligar", "",
           "1. Importar o workflow no n8n **inativo**; escolher as credenciais (Kommo Bearer; Google OAuth2 com o escopo "
           "`https://www.googleapis.com/auth/datamanager`).",
           "2. Aplicar as peças do sGTM (`sgtm-devolucao-*.json`) pela MCP do GTM, com ok para a mudança; publicar com nome claro.",
           "3. Test Event Code no sGTM, mover um lead de teste para cada etapa, conferir no Meta (Eventos de teste) e a "
           "nota no lead; no Google, `validar_apenas: true` na primeira rodada.",
           "4. Tirar o Test Event Code, ativar o workflow e ligar o webhook no Kommo."]
    return "\n".join(ls) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    b = json.load(open(a.brief))
    if not b.get("devolucao"):
        sys.exit("O brief não tem o bloco \"devolucao\" (modelo em templates/brief_exemplo.json).")
    achados = validar(b)
    if via_sgtm(b) and not b.get("ssgtm_url", "").startswith("https://"):
        achados.append(("BLOQUEANTE", "ssgtm_url vazia ou sem https: o n8n não tem para onde mandar o evento do Meta"))
    for n, m in achados:
        print(f"{n}: {m}")
    if any(n == "BLOQUEANTE" for n, _ in achados):
        sys.exit(1)
    chave = chave_do_cliente(a.out)
    s = re.sub(r"[^a-z0-9]+", "-", b.get("cliente", "cliente").lower()).strip("-")
    wf = workflow_n8n(b, chave)
    pecas = pecas_sgtm(b, chave, "<tipo da tag CAPI no container>", "<tipo do Data Client depois de importar>")
    json.dump(wf, open(os.path.join(a.out, f"n8n-devolucao-{s}.json"), "w"), ensure_ascii=False, indent=2)
    json.dump(pecas, open(os.path.join(a.out, f"sgtm-devolucao-{s}.json"), "w"), ensure_ascii=False, indent=2)
    open(os.path.join(a.out, "resumo-devolucao.md"), "w").write(resumo(b, achados, wf))
    print(f"\nOK → {a.out}")


if __name__ == "__main__":
    main()
