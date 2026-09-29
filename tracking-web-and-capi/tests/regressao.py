#!/usr/bin/env python3
"""Regressão da skill tracking-web-and-capi com dados fictícios (sem rede). Rodar: python3 tests/regressao.py"""
import copy, json, os, re, shutil, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import gerar_containers as g

BRIEF = json.load(open(os.path.join(RAIZ, "templates", "brief_exemplo.json")))
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
