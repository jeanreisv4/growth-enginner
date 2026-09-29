#!/usr/bin/env python3
"""Gera os containers GTM Web e Server do cliente a partir dos templates canônicos e valida antes de entregar.

  python3 scripts/gerar_containers.py --brief clientes/<c>/brief.json --out saida/<c> [--producao]

O brief (modelo em templates/brief_exemplo.json) NUNCA leva o token da CAPI: ele é colado direto na variável
"00 - Meta CAPI - Access Token" do GTM Server. Saída: gtm-web-<cliente>.json, gtm-server-<cliente>.json e resumo.md.
Sai com código 1 se houver item bloqueante.

As validações vêm de erros reais: rótulo de conversão incompleto ou trocado com o ID, rótulo repetido (duas tags
contando a mesma conversão), URL de exemplo esquecida no transporte do servidor, Test Event Code em produção,
seletor vazio que derruba o script de captura e inheritEventName booleano no template da CAPI.
"""
import argparse, copy, json, os, re, sys, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(AQUI, "..", "templates", "gtm")
SEM_CAMPO = "[data-v4-sem-campo]"  # seletor que não casa com nada: querySelector('') derrubaria a captura
TOKEN_TEMPLATE = "COLE_O_TOKEN_AQUI"
PASTAS = {"web": 8, "server": 2}
TAGS = {"web": 19, "server": 4}
URL_DE_EXEMPLO = ("dominio.com.br", "exemplo.com", "seudominio", "xyz.sac.stape.io", "__")


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def marcadores(b, producao):
    s = b.get("seletores", {})
    sel = lambda k: s.get(k) or SEM_CAMPO
    lab = b.get("labels", {})
    ads = re.sub(r"^AW-", "", str(b.get("google_ads_id", "")))
    return {
        "__DOMINIO_LP__": b.get("dominio_lp") or b.get("dominio", ""),
        "__DOMINIO__": b.get("dominio", ""),
        "__SSGTM_URL__": b.get("ssgtm_url", "").rstrip("/"),
        "__META_PIXEL_ID__": str(b.get("meta_pixel_id", "")),
        "__GOOGLE_ADS_ID__": ads,
        "__GA4_ID__": b.get("ga4_id", ""),
        "__LABEL_LEAD__": lab.get("lead") or "",
        "__LABEL_MQL__": lab.get("mql") or "",
        "__LABEL_CONTACT__": lab.get("contact") or "",
        "__CLARITY_ID__": b.get("clarity_id") or "",
        "__TEST_EVENT_CODE__": "" if producao else (b.get("test_event_code") or ""),
        "__PATH_OBRIGADO__": b.get("path_obrigado", "/obrigado"),
        "__SEL_FORM__": sel("form"), "__SEL_BOTAO__": sel("botao"), "__SEL_NOME__": sel("nome"),
        "__SEL_EMAIL__": sel("email"), "__SEL_TELEFONE__": sel("telefone"),
        "__SEL_QUALIF_1__": sel("qualif_1"), "__SEL_QUALIF_2__": sel("qualif_2"),
        "__REGRA_MQL__": b.get("regra_mql") or "false",
    }


def preencher(no, mapa):
    if isinstance(no, dict):
        return {k: preencher(v, mapa) for k, v in no.items()}
    if isinstance(no, list):
        return [preencher(v, mapa) for v in no]
    if isinstance(no, str):
        for de, para in mapa.items():
            no = no.replace(de, para)
    return no


def tirar(cv, cond_tag):
    """Remove as tags que casam e os acionadores que ficaram sem tag."""
    cv["tag"] = [t for t in cv.get("tag", []) if not cond_tag(t)]
    usados = {i for t in cv["tag"] for i in t.get("firingTriggerId", []) + t.get("blockingTriggerId", [])}
    cv["trigger"] = [g for g in cv.get("trigger", []) if g["triggerId"] in usados or "MQL" not in g["name"] and "is_mql" not in g["name"]]


def montar(b, producao):
    mapa = marcadores(b, producao)
    saida = {}
    for tipo in ("web", "server"):
        d = json.load(open(os.path.join(TEMPLATES, tipo + ".json")))
        cv = d["containerVersion"]
        if not b.get("regra_mql"):
            tirar(cv, lambda t: "MQL" in t["name"])
            cv["variable"] = [v for v in cv.get("variable", []) if v["name"] not in ("cJS - is_mql", "01 - Google Ads - MQL")]
        if tipo == "web" and not b.get("clarity_id"):
            tirar(cv, lambda t: "Clarity" in t["name"])
        saida[tipo] = preencher(d, mapa)
    return saida


def validar(b, conts, producao):
    """Lista de (nível, mensagem). Nível: BLOQUEANTE ou ATENÇÃO."""
    r = []
    bloq = lambda m: r.append(("BLOQUEANTE", m))
    aten = lambda m: r.append(("ATENÇÃO", m))
    mql = bool(b.get("regra_mql"))
    pixel, ads, ga4 = str(b.get("meta_pixel_id", "")), re.sub(r"^AW-", "", str(b.get("google_ads_id", ""))), b.get("ga4_id", "")
    if not re.fullmatch(r"\d{15,16}", pixel):
        bloq(f"Pixel do Meta '{pixel}' fora do formato (15 ou 16 dígitos)")
    if not re.fullmatch(r"\d{9,11}", ads):
        bloq(f"ID do Google Ads '{ads}' fora do formato (9 a 11 dígitos, sem AW-)")
    if not re.fullmatch(r"G-[A-Z0-9]{6,12}", ga4 or ""):
        bloq(f"ID do GA4 '{ga4}' fora do formato G-XXXXXXXXXX")
    labs = {k: v for k, v in (b.get("labels") or {}).items() if v}
    for k in ("lead", "contact") + (("mql",) if mql else ()):
        v = labs.get(k)
        if not v:
            bloq(f"rótulo de conversão '{k}' vazio")
        elif v.isdigit():
            bloq(f"rótulo '{k}' = '{v}' é só número: parece o ID da conta no lugar do rótulo (ID e rótulo trocados)")
        elif not re.fullmatch(r"[A-Za-z0-9_-]{14,24}", v):
            bloq(f"rótulo '{k}' = '{v}' com caractere inválido")
        elif len(v) != 20:
            aten(f"rótulo '{k}' tem {len(v)} caracteres (os atuais têm 20): confira letra a letra na conta; "
                 "rótulo com um caractere a menos dispara no GTM e a conta não conta nada")
    repetidos = [v for v in set(labs.values()) if list(labs.values()).count(v) > 1]
    if repetidos:
        bloq(f"rótulo repetido em duas conversões ({', '.join(repetidos)}): a mesma ação conta duas vezes")
    url = b.get("ssgtm_url", "")
    if not url.startswith("https://") or any(x in url for x in URL_DE_EXEMPLO):
        bloq(f"URL do GTM Server '{url}' vazia, sem https ou de exemplo: nada chega ao servidor")
    if b.get("whatsapp") and not re.fullmatch(r"55\d{10,11}", str(b["whatsapp"])):
        aten(f"WhatsApp '{b['whatsapp']}' fora do formato 55DDDNÚMERO")
    if not str(b.get("path_obrigado", "/obrigado")).startswith("/"):
        bloq("path da página de obrigado precisa começar com /")
    if b.get("test_event_code"):
        aten("Test Event Code do brief ignorado (--producao): variável vazia no servidor" if producao else
             "Test Event Code ativo: gere de novo com --producao antes de publicar; em produção todo evento vira teste")
    for tipo, d in conts.items():
        if tipo == "server" and producao:
            tec = [p.get("value") for v in d["containerVersion"].get("variable", []) if "Test Event Code" in v["name"]
                   for p in v.get("parameter", []) if p.get("key") == "value"]
            if any(tec):
                bloq(f"server: Test Event Code '{tec[0]}' no container de produção")
        txt = json.dumps(d, ensure_ascii=False)
        sobra = [k for k in marcadores({}, producao) if k in txt]
        if sobra:
            bloq(f"{tipo}: marcador não preenchido {sobra}")
        if "querySelector('')" in txt or 'querySelector(\\"\\")' in txt:
            bloq(f"{tipo}: seletor vazio no script de captura")
        cv = d["containerVersion"]
        np_ = len(cv.get("folder", []))
        if np_ != PASTAS[tipo]:
            bloq(f"{tipo}: {np_} pastas (o canônico tem {PASTAS[tipo]})")
        esperado = TAGS[tipo] - (0 if mql else (4 if tipo == "web" else 1)) - (1 if tipo == "web" and not b.get("clarity_id") else 0)
        if len(cv.get("tag", [])) != esperado:
            bloq(f"{tipo}: {len(cv.get('tag', []))} tags (esperado {esperado})")
        if tipo == "server":
            for t in cv["tag"]:
                inh = [p.get("value") for p in t.get("parameter", []) if p.get("key") == "inheritEventName"]
                if inh and inh[0] != "override":
                    bloq(f"server: '{t['name']}' com inheritEventName={inh[0]!r} (tem de ser \"override\")")
            if TOKEN_TEMPLATE in txt:
                aten("server: token da CAPI ainda é o texto do template; cole o token direto no GTM Server (nunca no brief nem em print)")
    return r


def resumo(b, conts, achados, producao):
    m = marcadores(b, producao)
    linhas = [f"# Containers gerados: {b.get('cliente', '')}", "",
              f"Modo: {'produção' if producao else 'validação (Test Event Code mantido)'}", "",
              "| Marcador | Valor |", "|---|---|"]
    linhas += [f"| `{k}` | `{v}` |" for k, v in m.items() if k != "__TEST_EVENT_CODE__" or v]
    linhas += ["", "| Container | Tags | Acionadores | Variáveis |", "|---|---|---|---|"]
    for t, d in conts.items():
        cv = d["containerVersion"]
        linhas.append(f"| {t} | {len(cv.get('tag', []))} | {len(cv.get('trigger', []))} | {len(cv.get('variable', []))} |")
    linhas += ["", "## Validação", ""] + ([f"- **{n}**: {msg}" for n, msg in achados] or ["- Nenhum achado."])
    linhas += ["", "Antes de publicar: versão com nome claro (não \"Versão N\"), lead de teste ponta a ponta e o",
               "teste de disparo da sprint-growth (`scripts/teste_disparo.py`) com os rótulos acima."]
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--producao", action="store_true", help="zera o Test Event Code")
    a = ap.parse_args()
    b = json.load(open(a.brief))
    if any(k in json.dumps(b).lower() for k in ("access_token", "token_capi", '"eaa')):
        sys.exit("O brief tem token. Tire o token do arquivo: ele vai direto no GTM Server.")
    conts = montar(b, a.producao)
    achados = validar(b, conts, a.producao)
    os.makedirs(a.out, exist_ok=True)
    s = slug(b.get("cliente", "cliente"))
    for tipo, d in conts.items():
        json.dump(d, open(os.path.join(a.out, f"gtm-{tipo}-{s}.json"), "w"), ensure_ascii=False, indent=2)
    open(os.path.join(a.out, "resumo.md"), "w").write(resumo(b, conts, achados, a.producao))
    for n, msg in achados:
        print(f"{n}: {msg}")
    bl = sum(n == "BLOQUEANTE" for n, _ in achados)
    print(f"\n{'BLOQUEADO: ' + str(bl) + ' item(ns)' if bl else 'OK para importar'} → {a.out}")
    sys.exit(1 if bl else 0)


if __name__ == "__main__":
    main()
