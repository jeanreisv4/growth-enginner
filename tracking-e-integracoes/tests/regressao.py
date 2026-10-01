#!/usr/bin/env python3
"""Regressão da skill tracking-e-integracoes com dados fictícios (sem rede). Rodar: python3 tests/regressao.py"""
import copy, glob as glob_mod, json, os, re, shutil, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import gerar_containers as g

BRIEF = json.load(open(os.path.join(RAIZ, "templates", "brief_exemplo.json")))
DEVOLUCAO = BRIEF.pop("devolucao")  # os casos de container sem devolução usam o brief sem o bloco
falhas = []


def confere(nome, cond):
    print(("OK   " if cond else "FALHA ") + nome)
    if not cond:
        falhas.append(nome)


def roda(brief, producao=True):
    c = g.montar(brief, producao)
    return c, g.validar(brief, c, producao)


def bloqueios(achados):
    return [m for n, m in achados if n == "BLOQUEANTE"]


def com(**mud):
    b = copy.deepcopy(BRIEF)
    for k, v in mud.items():
        if k.startswith("label_"):
            b["labels"][k[6:]] = v
        elif k.startswith("sel_"):
            b["seletores"][k[4:]] = v
        else:
            b[k] = v
    return b


def cv(c, tipo):
    return c[tipo]["containerVersion"]


# templates: anônimos e estruturados
for tipo in ("web", "server"):
    d = json.load(open(os.path.join(RAIZ, "templates", "gtm", tipo + ".json")))
    for t in d["containerVersion"].get("customTemplate", []):
        t.pop("templateData", None)  # código dos templates da galeria (imagens em base64, links de ajuda)
    txt = json.dumps(d, ensure_ascii=False)
    confere(f"template {tipo} sem Pixel real (15-16 dígitos)", not re.search(r"(?<!\d)\d{15,16}(?!\d)", txt))
    confere(f"template {tipo} sem GA4 real", not re.search(r"\bG-[A-Z0-9]{8,12}\b", txt))
    confere(f"template {tipo} sem host do Stape", ".stape.io" not in txt)
    confere(f"template {tipo} sem GTM real", not re.search(r"GTM-(?!WEB0000|SRV0000)[A-Z0-9]{6,}", txt))
    confere(f"template {tipo} sem token da CAPI", not re.search(r"EAA[A-Za-z0-9]{20,}", txt))

# brief do exemplo: passa
c, a = roda(BRIEF)
confere("brief do exemplo sem bloqueante", not bloqueios(a))
confere("web com 18 tags (sem Clarity)", len(cv(c, "web")["tag"]) == 18)
confere("server com 4 tags CAPI", len(cv(c, "server")["tag"]) == 4)
confere("nenhum marcador sobra", not any(k in json.dumps(c) for k in g.marcadores({}, True)))
confere("produção zera o Test Event Code", all(p.get("value") == "" for v in cv(c, "server")["variable"]
        if "Test Event Code" in v["name"] for p in v["parameter"] if p.get("key") == "value"))
confere("ID do Ads entra sem AW-", '"987654321"' in json.dumps(c["web"]))
confere("seletor vazio vira seletor inerte", g.SEM_CAMPO in json.dumps(c["web"]) and "querySelector('')" not in json.dumps(c["web"]))
confere("CAPI com inheritEventName override", all(p["value"] == "override" for t in cv(c, "server")["tag"]
        for p in t["parameter"] if p["key"] == "inheritEventName"))
confere("token do template vira aviso, não valor", any("token da CAPI" in m for _, m in a))

# armadilhas: cada uma vira bloqueio ou atenção
confere("ID e rótulo trocados bloqueiam", any("ID e rótulo trocados" in m for m in bloqueios(roda(com(label_lead="987654321"))[1])))
confere("rótulo com um caractere a menos gera atenção", any("20" in m for n, m in roda(com(label_lead="AbCdEfGhIjKlMnOpQrS"))[1] if n == "ATENÇÃO"))
confere("rótulo repetido bloqueia", any("repetido" in m for m in bloqueios(roda(com(label_mql=BRIEF["labels"]["lead"]))[1])))
confere("URL de exemplo no servidor bloqueia", any("GTM Server" in m for m in bloqueios(roda(com(ssgtm_url="https://gtm.dominio.com.br"))[1])))
confere("URL sem https bloqueia", any("GTM Server" in m for m in bloqueios(roda(com(ssgtm_url="http://sgtm.exemplo-pisos.com.br"))[1])))
confere("Pixel curto bloqueia", any("Pixel" in m for m in bloqueios(roda(com(meta_pixel_id="12345"))[1])))
confere("GA4 errado bloqueia", any("GA4" in m for m in bloqueios(roda(com(ga4_id="UA-12345-1"))[1])))
c2, a2 = roda(BRIEF, producao=False)
confere("fora de produção o Test Event Code fica e avisa", "TEST00000" in json.dumps(c2["server"])
        and any("--producao" in m for _, m in a2))

# sem MQL: some tag, acionador e variável de MQL
c3, a3 = roda(com(regra_mql=None, label_mql=None))
confere("sem MQL: sem bloqueante", not bloqueios(a3))
confere("sem MQL: web com 14 tags", len(cv(c3, "web")["tag"]) == 14)
confere("sem MQL: server com 3 tags", len(cv(c3, "server")["tag"]) == 3)
confere("sem MQL: sem is_mql nem acionador de MQL", "is_mql" not in json.dumps(c3["web"]) and
        not any("MQL" in t["name"] for t in cv(c3, "server")["trigger"]))
ids = {t["triggerId"] for t in cv(c3, "web")["trigger"]}
confere("sem MQL: nenhuma tag aponta para acionador removido", all(i in ids or int(i) >= 2147479000  # nativos do GTM
        for t in cv(c3, "web")["tag"] for i in t.get("firingTriggerId", [])))

# Clarity só quando pedido
confere("com Clarity: web com 19 tags", len(cv(roda(com(clarity_id="abcd1234ef"))[0], "web")["tag"]) == 19)

# regra de MQL roda de verdade (JavaScript do macOS, quando existir)
if shutil.which("osascript"):
    fn = [v for v in cv(c, "web")["variable"] if v["name"] == "cJS - is_mql"][0]["parameter"][0]["value"]
    js = ("var sessionStorage={getItem:function(){return JSON.stringify({qualif_1:'Corporativo',qualif_2:'Acima de 100 m²'})}};"
          f"var f=({fn}); String(f());")
    out = subprocess.run(["osascript", "-l", "JavaScript", "-e", js], capture_output=True, text=True).stdout.strip()
    confere("is_mql gerado roda e qualifica o lead do exemplo", out == "true")

# CLI ponta a ponta: recusa brief com token
with tempfile.TemporaryDirectory() as d:
    b = com(); b["access_token"] = "EAAfalso"
    json.dump(b, open(os.path.join(d, "b.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "gerar_containers.py"), "--brief", os.path.join(d, "b.json"),
                        "--out", d], capture_output=True, text=True)
    confere("brief com token é recusado", r.returncode != 0 and "token" in (r.stderr + r.stdout))
    json.dump(BRIEF, open(os.path.join(d, "b.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "gerar_containers.py"), "--brief", os.path.join(d, "b.json"),
                        "--out", d, "--producao"], capture_output=True, text=True)
    confere("CLI gera os dois JSONs e o resumo", r.returncode == 0 and sorted(os.listdir(d)) ==
            ["b.json", "gtm-server-exemplo-pisos-premium.json", "gtm-web-exemplo-pisos-premium.json", "resumo.md"])

# devolução CRM → plataformas (Kommo → n8n → sGTM/Meta e Data Manager/Google)
import devolucao as dv, hashlib
BD = copy.deepcopy(BRIEF); BD["devolucao"] = copy.deepcopy(DEVOLUCAO)
NUC = open(os.path.join(RAIZ, "templates", "devolucao", "nucleo.js"), encoding="utf-8").read()

def js(expr):
    if not shutil.which("osascript"):
        return None
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", NUC + "\nJSON.stringify(" + expr + ")"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else {"_erro": r.stderr}

if shutil.which("osascript"):
    for t in ("", "abc", "joão@exemplo.com", "+5511988887777"):
        confere(f"sha256 do núcleo = hashlib ({t!r})", js(f"sha256({json.dumps(t)})") == hashlib.sha256(t.encode()).hexdigest())
    plano = js("lerWebhookKommo({'leads[status][0][id]':'5','leads[status][0][status_id]':'142','leads[status][0][pipeline_id]':'9'})")
    confere("celular sem o 9 vai com e sem o 9; fixo vai uma vez só",
            js("[variantesCelularBR('+551188887777'), variantesCelularBR('+5511988887777'), variantesCelularBR('+551133334444')]")
            == [["551188887777", "5511988887777"], ["5511988887777", "551188887777"], ["551133334444"]])
    confere("webhook da conta achatado é lido", plano == [{"lead_id": "5", "status_id": "142", "pipeline_id": "9", "old_status_id": "", "quando": None}])
    confere("webhook da conta aninhado é lido", js("lerWebhookKommo({leads:{status:{'0':{id:5,status_id:142,pipeline_id:9}}}})")[0]["status_id"] == "142")
    confere("webhook do Digital Pipeline é lido", js("lerWebhookKommo({lead:{event:{id:5,status_id:77,pipeline_id:9}}})")[0]["status_id"] == "77")
    CFG = json.dumps({"etapas": {"77": "SQL", "142": "Purchase"}, "funis": ["9"], "valores": {"SQL": 900},
                      "campos": {"meta_lead_id": "1", "gclid": "2", "fbclid": "3"},
                      "google": {"customer_id": "123-456-7890", "acoes": {"SQL": "11", "Purchase": "22"}}})
    LEAD = lambda lid="1234567890123456", gclid="Cj0abc", price=0: json.dumps({"id": 5, "price": price, "custom_fields_values": [
        {"field_id": 1, "values": [{"value": lid}]}, {"field_id": 2, "values": [{"value": gclid}]}, {"field_id": 3, "values": [{"value": "IwAR1"}]}]})
    CONT = json.dumps({"id": 7, "name": "Maria da Silva", "custom_fields_values": [
        {"field_code": "PHONE", "values": [{"value": "(11) 98888-7777"}]}, {"field_code": "EMAIL", "values": [{"value": " Ma.Ria@Gmail.com"}]}]})
    ev = lambda st, lead=None, quando=1790000000, agora=1790000100, pipe="9": js(
        f"montarEvento({CFG}, {{lead_id:'5',status_id:'{st}',pipeline_id:'{pipe}',quando:{quando}}}, {lead or LEAD()}, {CONT}, {agora})")
    e = ev("77")
    confere("SQL: event_id por lead e evento", e["event_id"] == "kommo-5-sql")
    confere("SQL: Meta com lead_id em texto, telefone E.164 e fbc do fbclid", e["meta"]["lead_id"] == "1234567890123456" and
            e["meta"]["user_data"]["phone_number"] == "+5511988887777" and e["meta"]["fbc"] == "fb.1.1790000000000.IwAR1")
    confere("SQL: hora da etapa, não a do envio", e["meta"]["event_time"] == 1790000000)
    gg = e["google"]
    confere("Google: formato Data Manager (destino, gclid, ISO com fuso)", gg["destinations"][0]["operatingAccount"]["accountId"] == "1234567890"
            and gg["destinations"][0]["productDestinationId"] == "11" and gg["events"][0]["adIdentifiers"] == {"gclid": "Cj0abc"}
            and gg["events"][0]["eventTimestamp"] == "2026-09-21T11:13:20-03:00" and gg["encoding"] == "HEX")
    confere("Google: e-mail do gmail sem pontos e com hash", gg["events"][0]["userData"]["userIdentifiers"][0]["emailAddress"]
            == hashlib.sha256(b"maria@gmail.com").hexdigest())
    confere("Purchase usa o valor do lead", ev("142", LEAD(price=4500))["meta"]["value"] == 4500)
    confere("etapa fora do mapa é pulada", ev("143").get("pular") is True)
    confere("funil fora da lista é pulado", ev("77", pipe="8").get("pular") is True)
    ruim = ev("77", LEAD(lid="123"))
    confere("lead_id fora de 15-17 dígitos sai do evento e vira aviso", "lead_id" not in ruim["meta"] and any("lead_id" in f for f in ruim["faltando"]))
    confere("evento com mais de 7 dias não vai ao Meta", ev("77", quando=1790000000, agora=1790000000 + 8 * 86400)["meta"] is None)
    sem = ev("77", LEAD(gclid=""))
    confere("sem gclid o Google não recebe (sem_clique desligado)", sem["google"] is None and any("gclid" in f for f in sem["faltando"]))

# validação do bloco
achados = lambda **m: [x for n, x in dv.validar({"devolucao": {**DEVOLUCAO, **m}}) if n == "BLOQUEANTE"]
confere("devolução do exemplo sem bloqueante", not achados())
confere("etapa 143 (perdido) mapeada bloqueia", any("143" in x for x in achados(etapas={"143": "Purchase"})))
confere("nome de etapa no lugar do id bloqueia", any("status_id" in x for x in achados(etapas={"Ganho": "Purchase"})))
confere("token no bloco bloqueia", any("token" in x for x in achados(n8n={"credencial_kommo": "Bearer eyJ0abc"})))
confere("Google sem campo de clique bloqueia", any("gclid" in x for x in achados(campos={"meta_lead_id": 1})))

# container de servidor com a devolução
c5 = g.montar(BD, True, "chave-teste")
a5 = g.validar(BD, c5, True)
sv = cv(c5, "server")
confere("com devolução: sem bloqueante", not bloqueios(a5))
confere("com devolução: server com 6 tags (SQL e Purchase)", len(sv["tag"]) == 6)
confere("com devolução: Data Client e template dele no servidor", any(x["name"] == dv.NOME_CLIENTE for x in sv["client"])
        and any(t.get("galleryReference", {}).get("repository") == "data-client" for t in sv["customTemplate"]))
crm = [t for t in sv["tag"] if t["name"].endswith(("SQL", "Purchase"))]
par = lambda t, k: [p for p in t["parameter"] if p["key"] == k][0]
confere("tags de CRM: system_generated, sem fbp gerado, IP do lead no lugar do IP do n8n", all(
    par(t, "actionSource")["value"] == "system_generated" and par(t, "generateFbp")["value"] == "false" and
    "{{ED - lead_ip}}" in json.dumps(par(t, "userDataList")) and "{{ED - event_time}}" in json.dumps(par(t, "serverEventDataList"))
    for t in crm))
confere("acionadores de CRM exigem o Data Client e a chave", all("{{ED - chave}}" in json.dumps(x.get("filter")) and dv.NOME_CLIENTE in json.dumps(x.get("filter"))
        for x in sv["trigger"] if x["name"].startswith("CRM")))
confere("chave só no servidor, não no web", "chave-teste" in json.dumps(c5["server"]) and "chave-teste" not in json.dumps(c5["web"]))
BL = copy.deepcopy(BD); BL["devolucao"]["etapas"] = {"111": "Lead", "142": "Purchase"}
lead_site = [x for x in cv(g.montar(BL, True, "k"), "server")["trigger"] if x["name"] == "Event Name = Lead"][0]
confere("etapa 'Lead' do CRM não dispara a tag de Lead do site", "{{Client Name}}" in json.dumps(lead_site.get("filter")))

# workflow do n8n: nós Code rodando com o n8n simulado
wf = dv.workflow_n8n(BD, "chave-teste")
confere("workflow sem token e sem marcador", not re.search(r"EAA[A-Za-z0-9]{20,}|eyJ0eXAi|__[A-Z_]+__", json.dumps(wf)))
confere("nós HTTP pedem resposta em JSON (Kommo responde hal+json)", all(n["parameters"]["options"]["response"]["response"].get("responseFormat") == "json"
        for n in wf["nodes"] if n["type"].endswith("httpRequest")))
confere("webhook responde na hora (Kommo exige resposta em até 2 s)", [n for n in wf["nodes"] if n["type"].endswith("webhook")][0]["parameters"]["responseMode"] == "onReceived")
if shutil.which("osascript"):
    codigo = {n["name"]: n["parameters"].get("jsCode") for n in wf["nodes"]}
    def no(nome, entrada, nos=None, estado=None):
        src = ("var __est=%s;var $getWorkflowStaticData=function(){return __est};var __nos=%s;"
               "var __sel=function(n){return {all:function(){return __nos[n]}}};var $input={all:function(){return %s}};"
               "var __r=(function(){%s})();JSON.stringify({r:__r,est:__est});") % (
            json.dumps(estado or {}), json.dumps(nos or {}), json.dumps(entrada), codigo[nome].replace("$('", "__sel('"))
        r = subprocess.run(["osascript", "-l", "JavaScript", "-e", src], capture_output=True, text=True)
        return json.loads(r.stdout) if r.returncode == 0 else {"r": None, "erro": r.stderr}
    corpo = {"leads[status][0][id]": "5", "leads[status][0][status_id]": "7654321", "leads[status][0][pipeline_id]": "1234567",
             "leads[status][1][id]": "6", "leads[status][1][status_id]": "1", "leads[status][1][pipeline_id]": "1234567"}
    l1 = no("Ler mudança de etapa", [{"json": {"body": corpo}}])
    confere("n8n: só a etapa mapeada segue", l1["r"] and len(l1["r"]) == 1 and l1["r"][0]["json"]["evento"] == "SQL")
    lead = {"id": 5, "custom_fields_values": [{"field_id": 900001, "values": [{"value": "1234567890123456"}]},
                                              {"field_id": 900004, "values": [{"value": "Cj0abc"}]}]}
    m = no("Montar eventos", [{"json": {"statusCode": 200, "body": json.loads(CONT) if shutil.which("osascript") else {}}}],
           {"Ler mudança de etapa": l1["r"], "Kommo | Lead e contatos": [{"json": lead}]})
    mt = no("Montar eventos", [{"json": {"statusCode": 200, "data": json.dumps(json.loads(CONT))}}],
            {"Ler mudança de etapa": l1["r"], "Kommo | Lead e contatos": [{"json": {"data": json.dumps(lead)}}]})
    confere("n8n: lead e contato em texto (hal+json) também viram evento", mt["r"] and mt["r"][0]["json"]["meta"]
            and mt["r"][0]["json"]["meta"]["user_data"]["phone_number"] == "+5511988887777")
    confere("n8n: evento do Meta leva a chave do sGTM", m["r"] and m["r"][0]["json"]["meta"]["chave"] == "chave-teste")
    s1 = no("Só com Meta", m["r"])
    r1 = no("Meta | Registrar", [{"json": {"statusCode": 200, "body": ""}}], {"Só com Meta": s1["r"]})
    confere("n8n: envio certo vira nota no lead", r1["r"][0]["json"]["nota"][0]["entity_id"] == 5 and "SQL" in r1["r"][0]["json"]["nota"][0]["params"]["text"])
    r0 = no("Meta | Registrar", [{"json": {"statusCode": 500, "body": "x"}}], {"Só com Meta": s1["r"]})
    confere("n8n: falha não marca como enviado", r0["est"].get("enviados") == {} and "FALHOU" in r0["r"][0]["json"]["nota"][0]["params"]["text"])
    sg = no("Só com Google", m["r"])
    r2 = no("Google | Registrar", [{"json": {"statusCode": 200, "body": {}}}], {"Só com Google": sg["r"]}, r1["est"])
    confere("n8n: o mesmo evento não sai duas vezes", no("Ler mudança de etapa", [{"json": {"body": corpo}}], estado=r2["est"])["r"] == [])

# modo direto: n8n → API de Conversões, sem sGTM (quando a Stape cai ou o cliente não tem)
BDIR = copy.deepcopy(BD); BDIR["devolucao"]["meta_via"] = "direto"; BDIR["devolucao"]["meta_test_event_code"] = "TEST123"
confere("direto: container de servidor sem peças de devolução", len(cv(g.montar(BDIR, True, "k"), "server")["tag"]) == 4)
confere("direto: sem Pixel bloqueia", any("meta_pixel_id" in x for n, x in dv.validar({**BDIR, "meta_pixel_id": ""}) if n == "BLOQUEANTE"))
confere("direto: Test Event Code no bloco gera atenção", any("meta_test_event_code" in x for n, x in dv.validar(BDIR) if n == "ATENÇÃO"))
wfd = dv.workflow_n8n(BDIR, "chave-teste")
nomes_d = {n["name"]: n for n in wfd["nodes"]}
confere("direto: nó da CAPI com a credencial de token e sem sGTM", "Meta | CAPI direta" in nomes_d and "sGTM | Meta CAPI" not in nomes_d
        and "graph.facebook.com/v24.0/123456789012345/events" in nomes_d["Meta | CAPI direta"]["parameters"]["url"]
        and "httpQueryAuth" in nomes_d["Meta | CAPI direta"]["credentials"])
if shutil.which("osascript"):
    codigo = {n["name"]: n["parameters"].get("jsCode") for n in wfd["nodes"]}
    l1 = no("Ler mudança de etapa", [{"json": {"body": corpo}}])
    m = no("Montar eventos", [{"json": {"statusCode": 200, "body": json.loads(CONT)}}],
           {"Ler mudança de etapa": l1["r"], "Kommo | Lead e contatos": [{"json": lead}]})
    gph = m["r"][0]["json"]["meta_graph"]
    ev0 = gph["data"][0]
    confere("direto: evento no formato da CAPI, telefone com hash, lead_id cru, sem chave",
            ev0["action_source"] == "system_generated" and ev0["user_data"]["ph"] == [hashlib.sha256(b"5511988887777").hexdigest(), hashlib.sha256(b"551188887777").hexdigest()]
            and ev0["user_data"]["lead_id"] == "1234567890123456" and ev0["custom_data"]["event_source"] == "crm"
            and "chave" not in json.dumps(gph) and gph.get("test_event_code") == "TEST123")
    sm = no("Só com Meta", m["r"])
    rt = no("Meta | Registrar", [{"json": {"statusCode": 200, "body": {"events_received": 1}}}], {"Só com Meta": sm["r"]})
    confere("direto: teste marca em lista separada (o envio de verdade não fica bloqueado)",
            list(rt["est"]["enviados"]) == ["meta-teste:kommo-5-sql"])

# id do lead do formulário buscado no Meta pelo telefone (meta_leadgen)
BLG = copy.deepcopy(BDIR); BLG["devolucao"]["meta_leadgen"] = {"pagina": "100000000000001", "credencial": "X"}
wlg = dv.workflow_n8n(BLG, "k")
con = {de: [x["node"] for x in v["main"][0]] for de, v in wlg["connections"].items()}
confere("leadgen: Montar → Token da página → Casar id do lead → Só com Meta",
        con["Montar eventos"] == ["Meta | Token da página"] and con["Meta | Token da página"] == ["Casar id do lead"]
        and "Só com Meta" in con["Casar id do lead"])
tokn = [n for n in wlg["nodes"] if n["name"] == "Meta | Token da página"][0]
confere("leadgen: token com a credencial do Lead Ads, uma vez por execução, sem derrubar o fluxo",
        tokn.get("executeOnce") and tokn["parameters"]["nodeCredentialType"] == "facebookLeadAdsOAuth2Api"
        and tokn["parameters"]["options"]["response"]["response"].get("neverError"))
confere("leadgen: página inválida bloqueia", any("meta_leadgen.pagina" in x for n, x in
        dv.validar({**BLG, "devolucao": {**BLG["devolucao"], "meta_leadgen": {"pagina": "abc"}}}) if n == "BLOQUEANTE"))
if shutil.which("osascript"):
    casar = [n for n in wlg["nodes"] if n["name"] == "Casar id do lead"][0]["parameters"]["jsCode"]
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", "var f = (async function(){" + casar.replace("$('", "__sel('") + "}); 'ok'"],
                       capture_output=True, text=True)
    confere("leadgen: código do Casar compila" + (" (" + r.stderr.strip()[:120] + ")" if r.returncode else ""), r.stdout.strip() == "ok")

# auditoria de entrada (formulário × CRM por semana e origem)
import auditar_entrada as ae
META = [{"id": "1", "t": "2026-09-01T12:00:00+0000", "k": "11|88887777"},   # entrou pela automação A
        {"id": "2", "t": "2026-09-02T12:00:00+0000", "tel": "+55 21 99999-0000"},  # contato só com lead antigo
        {"id": "3", "t": "2026-09-03T12:00:00+0000", "k": "31|11112222"},   # fora do CRM
        {"id": "4", "t": "2026-09-15T12:00:00+0000", "k": "41|33334444"}]   # entrou pela automação B
CRM = [{"telefones": ["(11) 98888-7777"], "leads": [{"criado_em": 1788264000, "origem": "A"}]},
       {"telefones": ["21999990000"], "leads": [{"criado_em": 1700000000, "origem": "A"}]},
       {"telefones": ["41 3333-4444"], "leads": [{"criado_em": 1789473600, "origem": "B"}]}]
r = ae.auditar(META, CRM)
tot = {k: sum(v[k] for v in r.values()) for k in ("formulario", "fora", "antigo")}
confere("entrada: acha lead fora, lead só com negociação antiga e a origem de cada semana",
        tot == {"formulario": 4, "fora": 1, "antigo": 1} and any(v["origens"].get("B") for v in r.values())
        and any(v["origens"].get("A") for v in r.values()))
kl = [{"created_at": 1788264000, "_embedded": {"contacts": [{"id": 9}], "source": {"name": "A"}}}]
kc = [{"id": 9, "custom_fields_values": [{"field_code": "PHONE", "values": [{"value": "+5511988887777"}]}]}]
confere("entrada: adaptador do Kommo monta telefones e leads do contato",
        ae.crm_do_kommo(kl, kc) == [{"telefones": ["+5511988887777"], "leads": [{"criado_em": 1788264000, "origem": "A"}]}])

# retroativos: janela de cada plataforma e o webhook com a hora real da etapa
import retroativos as rt
AG = 1790000000
confere("retroativos: 6 dias vai ao Meta; 8 dias com gclid só ao Google; 8 dias sem clique a nenhum",
        rt.plataformas(AG - 6 * 86400, AG, False, False) == ["meta"]
        and rt.plataformas(AG - 8 * 86400, AG, True, False) == ["google"]
        and rt.plataformas(AG - 8 * 86400, AG, False, False) == [])
confere("retroativos: sem clique só até 63 dias; com clique até 90; margem antes de vencer o Meta",
        rt.plataformas(AG - 60 * 86400, AG, False, True) == ["google"]
        and rt.plataformas(AG - 70 * 86400, AG, False, True) == []
        and rt.plataformas(AG - 89 * 86400, AG, True, False) == ["google"]
        and rt.plataformas(AG - 7 * 86400 + 60, AG, False, False) == [])
cw = dict(__import__("urllib.parse").parse.parse_qsl(rt.corpo_webhook(123, 142, 9, AG - 3600).decode()))
confere("retroativos: webhook no formato do Kommo com last_modified = hora da etapa",
        cw == {"leads[status][0][id]": "123", "leads[status][0][status_id]": "142", "leads[status][0][pipeline_id]": "9",
               "leads[status][0][old_status_id]": "0", "leads[status][0][last_modified]": str(AG - 3600)})
if shutil.which("osascript"):
    confere("retroativos: o núcleo lê o last_modified como a hora do evento (não a do envio)",
            js("lerWebhookKommo(" + json.dumps(cw) + ")")[0]["quando"] == AG - 3600)
confere("retroativos: clique conta só com gclid/gbraid/wbraid preenchido",
        rt.tem_clique({"custom_fields_values": [{"field_id": 7, "values": [{"value": "Cj0abc"}]}]}, {"gclid": 7})
        and not rt.tem_clique({"custom_fields_values": [{"field_id": 7, "values": [{"value": " "}]}]}, {"gclid": 7})
        and not rt.tem_clique({"custom_fields_values": [{"field_id": 8, "values": [{"value": "x"}]}]}, {"gclid": 7, "fbclid": 8}))

# devolução do RD Station CRM ao Google (ids fictícios)
import devolucao_rd as drd
BRD = {"sigla": "TESTE", "devolucao_rd": {"prefixo_nome": "Lead Mídia", "etapa_sql": "a" * 24, "usuario_nota": "b" * 24,
       "valores": {"SQL": 500}, "valor_venda_padrao": 5000, "campos": {"gclid": "c" * 24},
       "google": {"customer_id": "123-456-7890", "login_customer_id": "", "acoes": {"SQL": "111", "Purchase": "222"}},
       "n8n": {"credencial_rd": "credRD", "credencial_google": "credG"}}}
confere("devolução RD: brief de exemplo passa na validação", drd.validar(BRD) == [])
ruim = copy.deepcopy(BRD); ruim["devolucao_rd"]["prefixo_nome"] = ""; ruim["devolucao_rd"]["google"]["acoes"]["Purchase"] = ""
ruim["devolucao_rd"]["_x"] = "https://crm.rdstation.com/api/v1/deals?token=abc"
confere("devolução RD: bloqueia sem prefixo, sem ação de venda e com token no brief", len(drd.validar(ruim)) == 3)
wp = drd.workflow(BRD, 1790000000)
qs = lambda w, n: {q["name"]: q["value"] for q in [x for x in w["nodes"] if x["name"] == n][0]["parameters"]["queryParameters"]["parameters"]}
montar = [x for x in wp["nodes"] if x["name"] == "Montar eventos"][0]["parameters"]["jsCode"]
confere("devolução RD: produção agendada, filtra prefixo e etapa, desde e validateOnly falso no código",
        wp["nodes"][0]["type"].endswith("scheduleTrigger") and qs(wp, "RD | Na etapa de SQL") == {"limit": "200", "name": "Lead Mídia", "deal_stage_id": "a" * 24}
        and '"desde": 1790000000' in montar and '"validar_apenas": false' in montar and '"customer_id": "1234567890"' in montar)
confere("devolução RD: contato vem da listagem (o detalhe do negócio não traz) e hora vem do histórico de etapas",
        "porId[c.deal_id]" in montar and "deal_stage_histories" in montar and "function sha256" in montar)
wr = drd.workflow(BRD, 1790000000, "retro_validar")
mjs = lambda w: [x for x in w["nodes"] if x["name"] == "Montar eventos"][0]["parameters"]["jsCode"]
confere("devolução RD: retroativo lê todos os negócios do prefixo, desde 0, só valida e não escreve nota",
        "deal_stage_id" not in qs(wr, "RD | Na etapa de SQL") and '"desde": 0' in [x for x in wr["nodes"] if x["name"] == "Montar eventos"][0]["parameters"]["jsCode"]
        and '"validar_apenas": true' in mjs(wr) and [x for x in wr["nodes"] if x["name"] == "RD | Nota no negócio"][0].get("disabled") is True
        and wr["nodes"][0]["type"].endswith("webhook"))
we = drd.workflow(BRD, 1790000000, "retro_enviar")
confere("devolução RD: retroativo de verdade grava e escreve nota",
        '"validar_apenas": false' in mjs(we) and not [x for x in we["nodes"] if x["name"] == "RD | Nota no negócio"][0].get("disabled"))
bm = copy.deepcopy(BRD); bm["devolucao_rd"]["google"]["login_customer_id"] = "999-888-7777"
confere("devolução RD: conta sob MCC leva loginAccount; credenciais só por id",
        '"login_customer_id": "9998887777"' in mjs(drd.workflow(bm, 1)) and "loginAccount" in montar
        and all(set((n.get("credentials") or {}).keys()) <= {"httpQueryAuth", "oAuth2Api"} for n in wp["nodes"]))

# agentes de integração: fonte coerente e instalados iguais (quando a skill está dentro de um projeto)
ag = sorted(glob_mod.glob(os.path.join(RAIZ, "agentes", "integracao-*.md")))
confere("agentes: 4 frentes (crm, meta, google-ads, conversacional)",
        [os.path.basename(a) for a in ag] == ["integracao-conversacional.md", "integracao-crm.md", "integracao-google-ads.md", "integracao-meta.md"])
for a in ag:
    txt = open(a, encoding="utf-8").read()
    nome = os.path.basename(a)[:-3]
    confere(f"agente {nome}: cabeçalho com name igual ao arquivo, tools e contrato citado",
            txt.startswith("---\n") and f"\nname: {nome}\n" in txt and "\ntools: " in txt and "contrato_integracao.md" in txt)
inst = os.path.join(RAIZ, "..", "..", "agents")
if os.path.isdir(inst):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "instalar_agentes.py"), "--conferir"], capture_output=True, text=True)
    confere("agentes instalados em .claude/agents batem com a fonte", r.returncode == 0)

# devolução a partir da planilha (sem CRM): filtro, janela, 23:59, lead de hoje, id estável, diagnóstico dos erros
import devolucao_planilha as dp
_agora = dp.quando("30/09/2026", "16:00", -3).timestamp()
_linhas = [
    {"Data": "29/09/2026", "fonte": "google", "linha": "A", "gclid": "Gx1", "tel": "(11) 90000-0001", "mail": "a.b@gmail.com"},
    {"Data": "09/09/2026", "fonte": "google", "linha": "A", "gbraid": "Bx2", "wbraid": "Wx2", "tel": "11900000002"},
    {"Data": "30/09/2026", "fonte": "google", "linha": "A", "gclid": "Gx3"},                       # hoje: espera
    {"Data": "01/05/2026", "fonte": "google", "linha": "A", "gclid": "Gx4"},                       # fora dos 90 dias
    {"Data": "28/09/2026", "fonte": "google", "linha": "A"},                                        # sem clique
    {"Data": "28/09/2026", "fonte": "google", "linha": "B", "gclid": "Gx5"},                       # não é MQL
    {"Data": "28/09/2026", "fonte": "ig", "linha": "A", "gclid": "Gx6"},                           # outra origem
    {"Data": "2026-09-27 10:15:00", "fonte": "google", "linha": "A", "wbraid": "Wx7"},              # ISO com hora
]
_evs, _n = dp.eventos(_linhas, [("fonte", "google"), ("linha", "A")], "Data", tel_col="tel", email_col="mail",
                      prefixo="cli-mql", agora=_agora)
confere("planilha: só as linhas do filtro com clique na janela", len(_evs) == 3 and _n == {"sem_clique": 1, "fora_janela": 1, "hoje": 1, "sem_data": 0})
confere("planilha: sem hora vira 23:59 do dia; com hora usa a hora", _evs[0]["eventTimestamp"] == "2026-09-29T23:59:00-03:00"
        and _evs[2]["eventTimestamp"] == "2026-09-27T10:15:00-03:00")
confere("planilha: gclid > gbraid > wbraid, um só identificador de clique",
        [list(e["adIdentifiers"]) for e in _evs] == [["gclid"], ["gbraid"], ["wbraid"]])
_ids = json.dumps(_evs)
confere("planilha: sem telefone/e-mail em claro e e-mail do gmail sem ponto antes do hash",
        "90000" not in _ids and "gmail" not in _ids and dp.sha("ab@gmail.com") in _ids and dp.sha("+5511900000001") in _ids)
_de_novo, _ = dp.eventos(_linhas, [("fonte", "google"), ("linha", "A")], "Data", tel_col="tel", email_col="mail",
                         prefixo="cli-mql", agora=_agora + 3600)
confere("planilha: transactionId estável (reenviar não duplica)",
        [e["transactionId"] for e in _evs] == [e["transactionId"] for e in _de_novo] and _evs[0]["transactionId"].startswith("cli-mql-20260929-"))
confere("planilha: dados do usuário só até 63 dias", all("userData" in e for e in _evs[:2])
        and "userData" not in dp.eventos([dict(_linhas[0], Data="10/07/2026")], [], "Data", tel_col="tel", agora=_agora)[0][0])
_c = dp.corpo(_evs, "123-456-7890", "99", True, mcc="111-222-3333")
confere("planilha: --mcc vira loginAccount e validateOnly respeitado",
        _c["destinations"][0]["loginAccount"]["accountId"] == "1112223333" and _c["validateOnly"] is True
        and "loginAccount" not in dp.corpo(_evs, "1", "2", False)["destinations"][0])
confere("planilha: diagnóstico do 403 da MCC e do NOT_FOUND da propagação",
        "mcc" in dp.diagnostico(403, {"error": {"details": [{"metadata": {"field_path": "destinations[0]"}}]}})
        and "propag" in dp.diagnostico(400, {"fieldViolations": [{"field": "events[0].destination_references", "reason": "NOT_FOUND"}]}))

# publicação: cliente novo anonimizado (só no git local; o publicar.py não vai para a cópia pública)
pub = os.path.join(RAIZ, "scripts", "publicar.py")
if os.path.exists(pub):
    import publicar
    t = publicar.limpar("distribuidora de automatizadores e a distribuidora de automatizadores, [CLIENTE]. Mecanismo fica.")
    confere("publicar: troca o cliente só como palavra inteira", "distribuidora de automatizadores" not in t.replace("Mecanismo", "") and "Mecanismo fica" in t)
    with tempfile.TemporaryDirectory() as d:
        # amostra montada da própria lista do publicar.py: nenhum id real escrito neste teste (ele é publicado)
        ids = [r.pattern for r in publicar.PROIBIDO_RX if r.pattern.isdigit()][-2:]
        open(os.path.join(d, "x.md"), "w").write(" ".join(ids) + "\n")
        confere("publicar: conferência barra ids do cliente", len(ids) == 2 and len(publicar.conferir(d)) >= 2)

# desenhos: os SVG de assets/ são os que o gerador produz hoje
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import desenhos
for nome, fn in (("capa.svg", desenhos.capa), ("fluxo.svg", desenhos.fluxo), ("eventos.svg", desenhos.eventos)):
    arq = os.path.join(RAIZ, "assets", nome)
    confere(f"assets/{nome} bate com scripts/desenhos.py", os.path.exists(arq) and open(arq, encoding="utf-8").read() == fn())

# README: todo script citado existe (nesta skill ou na irmã sprint-growth, quando ela está ao lado)
readme = open(os.path.join(RAIZ, "README.md")).read()
irma = os.path.join(RAIZ, "..", "sprint-growth")
def existe(nome):
    for base in (RAIZ, irma):
        for pasta in ("scripts", "tests"):
            if os.path.exists(os.path.join(base, pasta, nome)):
                return True
    return not os.path.isdir(irma)  # skill instalada sozinha: não dá para conferir a irmã
faltando = sorted(n for n in set(re.findall(r"\b([a-z_]+\.py)\b", readme)) if not existe(n))
confere("README só cita scripts que existem" + (f" (faltam: {faltando})" if faltando else ""), not faltando)

print(f"\n{'TUDO OK' if not falhas else str(len(falhas)) + ' FALHA(S)'}")
sys.exit(1 if falhas else 0)
