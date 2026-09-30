#!/usr/bin/env python3
"""Pré-voo da sprint: testa cada acesso do cliente antes dos agentes e diz o que falta e como resolver.

  python3 scripts/preflight.py --cliente <c> [--sprint clientes/<c>/sprints/<AAAA-MM-DD>] [--sem-rede]

Lê `clientes/<c>/config.json`, `clientes/<c>/briefing.md` e `~/.config/sprint-growth/config.json`. Somente leitura:
nenhuma chamada escreve em conta, fluxo ou CRM. Escreve `<SPRINT>/preflight.md` + `.json` (ou `clientes/<c>/`).

Status: ok · falta (sem isso a frente não roda) · atencao (roda, mas com risco para a análise) · manual (só dá para
conferir na conversa, como o conector do Meta).

Regras que vieram de sprint real:
- execução "success" do n8n não prova integração: o pré-voo testa a credencial do CRM com um GET direto;
- conta do Google Ads encontrada não basta: campanhas com veiculação SUSPENDED ou gasto zero viram atenção;
- o GA4 do site pode ser de outra conta: ID de medição do HTML diferente do config vira atenção;
- o Clarity não é chamado (10 chamadas por dia por projeto): só confere se a chave existe.
"""
import argparse, json, os, re, subprocess, sys, threading, time, urllib.error, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

UA = {"User-Agent": "curl/8.4.0"}
BRIEF_BLOCO = re.compile(r"^## (\d+\. .+)$")


def r(area, item, status, detalhe, resolver=""):
    return {"area": area, "item": item, "status": status, "detalhe": detalhe, "resolver": resolver}


# ------------------------------------------------------------------ lógica pura (testada na regressão, sem rede)

def briefing_pendentes(texto):
    """{bloco: (respondidas, total)} contando as linhas de tabela com a coluna Resposta em branco."""
    blocos, atual = {}, None
    for linha in texto.splitlines():
        m = BRIEF_BLOCO.match(linha)
        if m:
            atual = m.group(1); blocos[atual] = [0, 0]; continue
        if atual and linha.startswith("|") and not linha.startswith("| ---") and not linha.startswith("| Pergunta") \
                and not linha.startswith("| Item"):
            cols = [c.strip() for c in linha.strip().strip("|").split("|")]
            if len(cols) >= 2:
                blocos[atual][1] += 1
                blocos[atual][0] += bool(cols[1])
    return {b: tuple(v) for b, v in blocos.items()}


def status_ads(conta, cliente, campanhas, custo_30d):
    """cliente = linha GAQL de customer; campanhas = [(nome, status, serving_status)]; custo em R$."""
    if not cliente:
        return r("Google Ads", conta, "falta", "conta não encontrada pelo MCP", "conferir o ID e a MCC em config.json (google_ads.mcp)")
    nome = cliente.get("descriptiveName", "")
    ativas = [c for c in campanhas if c[1] == "ENABLED"]
    suspensas = [c for c in ativas if c[2] == "SUSPENDED"]
    if suspensas:
        return r("Google Ads", f"{conta} {nome}", "atencao", f"{len(suspensas)} de {len(ativas)} campanhas ativas com veiculação SUSPENDED; R$ {custo_30d:.0f} em 30 dias",
                 "ver o motivo na interface (política, pagamento ou associação com conta suspensa)")
    if not ativas:
        return r("Google Ads", f"{conta} {nome}", "atencao", f"nenhuma campanha ativa; R$ {custo_30d:.0f} em 30 dias", "confirmar se a conta está pausada de propósito")
    if custo_30d == 0:
        return r("Google Ads", f"{conta} {nome}", "atencao", f"{len(ativas)} campanhas ativas e R$ 0 em 30 dias", "conferir pagamento e status das campanhas")
    return r("Google Ads", f"{conta} {nome}", "ok", f"{len(ativas)} campanhas ativas; R$ {custo_30d:.0f} em 30 dias")


def ids_pagina(html):
    return {"gtm": sorted(set(re.findall(r"GTM-[A-Z0-9]{5,}", html))),
            "ga4": sorted(set(re.findall(r"\bG-[A-Z0-9]{8,12}\b", html))),
            "aw": sorted(set(re.findall(r"AW-\d{6,}", html))),
            "pixel": sorted(set(re.findall(r"fbq\(['\"]init['\"],\s*['\"](\d+)", html)))}


def status_pagina(nome, url, codigo, html, ga4_conhecidos=(), tem_acesso_site=True):
    """ga4_conhecidos = IDs de medição que a V4 lê; tem_acesso_site = há propriedade do site no config."""
    if codigo != 200:
        return r("Páginas", f"{nome} {url}", "falta", f"HTTP {codigo}", "conferir a URL em config.json")
    ids = ids_pagina(html)
    marcas = ", ".join(f"{k}: {' '.join(v)}" for k, v in ids.items() if v) or "nenhuma tag no HTML inicial"
    if not ids["gtm"] and not ids["ga4"]:
        return r("Páginas", f"{nome} {url}", "atencao", f"sem GTM nem GA4 no HTML inicial ({marcas})",
                 "construtor pode carregar o GTM só depois do aceite de cookies: `teste_formulario.py`; site sem medição: pedir GTM")
    estranhos = [g for g in ids["ga4"] if g not in ga4_conhecidos]
    if estranhos and not (nome == "site" and tem_acesso_site):
        return r("Páginas", f"{nome} {url}", "atencao", f"GA4 {' '.join(estranhos)} fora do config ({marcas})",
                 "GA4 de outra conta: pedir acesso de leitura e gravar a propriedade no config")
    if not ids["gtm"]:
        return r("Páginas", f"{nome} {url}", "atencao", f"sem GTM ({marcas}): cliques e WhatsApp sem medição",
                 "instalar o GTM antes de mandar mídia para a página")
    return r("Páginas", f"{nome} {url}", "ok", marcas)


def status_http(area, item, codigo, erro_texto="", resolver=""):
    if codigo == 200:
        return r(area, item, "ok", "respondeu 200")
    if codigo in (401, 403):
        return r(area, item, "falta", f"HTTP {codigo}: credencial recusada", resolver)
    return r(area, item, "falta", f"HTTP {codigo} {erro_texto[:120]}".strip(), resolver)


def render(cliente, resultados, briefing):
    ordem = {"falta": 0, "atencao": 1, "manual": 2, "ok": 3}
    md = [f"# Pré-voo · {cliente}", "", f"Gerado em {time.strftime('%d/%m/%Y %H:%M')}. Somente leitura.", ""]
    cont = {s: sum(1 for x in resultados if x["status"] == s) for s in ordem}
    md += [f"**{cont['ok']} ok · {cont['falta']} falta · {cont['atencao']} atenção · {cont['manual']} manual**", ""]
    md += ["| Status | Área | Item | Detalhe | Como resolver |", "| --- | --- | --- | --- | --- |"]
    for x in sorted(resultados, key=lambda x: (ordem[x["status"]], x["area"])):
        md.append(f"| {x['status']} | {x['area']} | {x['item']} | {x['detalhe']} | {x['resolver']} |")
    if briefing:
        md += ["", "## Briefing", "", "| Bloco | Respondidas | Em branco |", "| --- | --- | --- |"]
        for b, (resp, tot) in briefing.items():
            md.append(f"| {b} | {resp} de {tot} | {tot - resp} |")
    md += ["", "## Pedir hoje (expira)", "",
           "- Leads do formulário nativo do Meta: 90 dias na Central de Leads (CSV por formulário, período inteiro).",
           "- Clarity: só as últimas 24–72 h; coletar no dia 1 (`clarity.py`).",
           "- Histórico de alterações do Google Ads: 30 dias; ler antes de qualquer mudança.",
           "", "Formato de cada export: `referencias/entrevista.md`."]
    return "\n".join(md) + "\n"


# ------------------------------------------------------------------------------------------------ rede

def _get(url, headers=None, timeout=40):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:300]
    except Exception as e:  # DNS, tempo esgotado
        return 0, str(e)[:200]


def _ler(caminho):
    return open(os.path.expanduser(caminho)).read().strip()


def checar_ads(cfg):
    ga = cfg.get("google_ads") or {}
    contas = [ga.get("conta")] + [c.get("conta") for c in ga.get("outras_contas", []) if isinstance(c, dict)]
    if isinstance(ga.get("conta_antiga"), dict):
        contas.append(ga["conta_antiga"].get("conta"))
    contas = [c for c in contas if c]
    if not contas:
        return [r("Google Ads", "conta", "falta", "sem conta no config", "preencher google_ads.conta")]
    from mcp_http import MCP
    out = []
    for conta in contas:
        mcp_nome = ga.get("mcp", "googleads_diretas")
        if isinstance(ga.get("conta_antiga"), dict) and conta == ga["conta_antiga"].get("conta"):
            mcp_nome = ga["conta_antiga"].get("mcp", mcp_nome)
        try:
            m = MCP(mcp_nome)
            cli = (m.gaql(conta, "SELECT customer.descriptive_name, customer.status FROM customer") or [{}])[0].get("customer")
            camp = [(x["campaign"]["name"], x["campaign"]["status"], x["campaign"].get("servingStatus"))
                    for x in m.gaql(conta, "SELECT campaign.name, campaign.status, campaign.serving_status FROM campaign WHERE campaign.status != 'REMOVED'")]
            custo = sum(int(x["metrics"].get("costMicros", 0)) for x in m.gaql(conta, "SELECT metrics.cost_micros FROM customer WHERE segments.date DURING LAST_30_DAYS")) / 1e6
            out.append(status_ads(conta, cli, camp, custo))
        except Exception as e:
            out.append(r("Google Ads", conta, "falta", str(e)[:150], f"conferir acesso da MCC ({mcp_nome}) à conta"))
    return out


def checar_gtm(cfg):
    g = cfg.get("gtm") or {}
    if not g.get("conta") or not (g.get("web_container") or g.get("web", "").isdigit()):
        return [r("GTM", "container", "falta" if not g.get("web") else "atencao", "sem conta ou ID interno do container no config",
                  "preencher gtm.conta e gtm.web_container (ID interno, não o GTM-XXXX)")]
    from mcp_http import MCP
    try:
        ws = MCP("gtm").call("gtm_list_workspaces", {"accountId": g["conta"], "containerId": g.get("web_container") or g["web"]})
        n = len((ws or {}).get("workspace", [])) if isinstance(ws, dict) else 0
        return [r("GTM", g.get("web", ""), "ok" if n else "falta", f"{n} workspace(s)" if n else str(ws)[:120], "" if n else "dar acesso à conta de serviço do MCP")]
    except Exception as e:
        return [r("GTM", g.get("web", ""), "falta", str(e)[:150], "MCP gtm fora do ar ou sem acesso")]


class _GA4:
    def __init__(self, binario):
        self.p = subprocess.Popen([binario], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.out, self.i = {}, 1
        threading.Thread(target=self._ler, daemon=True).start()
        self.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "preflight", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); self.p.stdin.flush()

    def _ler(self):
        for linha in self.p.stdout:
            try:
                d = json.loads(linha); self.out[d.get("id")] = d
            except ValueError:
                pass

    def rpc(self, metodo, params, espera=60):
        self.i += 1; i = self.i
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": metodo, "params": params}) + "\n"); self.p.stdin.flush()
        for _ in range(espera * 10):
            if i in self.out:
                return self.out.pop(i)
            time.sleep(0.1)
        return {"error": {"message": f"sem resposta em {espera}s"}}


def checar_ga4(cfg):
    ga = cfg.get("ga4") or {}
    props = [("LP", ga.get("propriedade")), ("site", ga.get("propriedade_site"))]
    binario = os.path.expanduser("~/.local/bin/analytics-mcp")
    out = []
    if not os.path.exists(binario):
        return [r("GA4", "analytics-mcp", "falta", "binário não instalado", "ver referencias/ferramentas.md")]
    cli = None
    for nome, prop in props:
        if not prop or not str(prop).split()[0].isdigit():
            out.append(r("GA4", nome, "atencao" if nome == "site" else "falta", "propriedade não informada",
                         "pedir acesso de leitura e gravar ga4.propriedade" + ("_site" if nome == "site" else "")))
            continue
        cli = cli or _GA4(binario)
        resp = cli.rpc("tools/call", {"name": "run_report", "arguments": {"property_id": int(str(prop).split()[0]),
                       "date_ranges": [{"start_date": "7daysAgo", "end_date": "yesterday"}], "dimensions": [], "metrics": ["sessions"]}})
        txt = json.dumps(resp)
        if "invalid_grant" in txt:
            out.append(r("GA4", f"{nome} {prop}", "falta", "token vencido (invalid_grant)",
                         "gcloud auth application-default login (comando na memória ga4-mcp-setup); depois conversa nova"))
        elif "PERMISSION_DENIED" in txt or "403" in txt:
            out.append(r("GA4", f"{nome} {prop}", "falta", "sem permissão na propriedade", "pedir acesso de leitura"))
        elif "error" in resp or '"isError": true' in txt:
            out.append(r("GA4", f"{nome} {prop}", "falta", txt[:150], ""))
        else:
            out.append(r("GA4", f"{nome} {prop}", "ok", "relatório respondeu"))
    if cli:
        cli.p.kill()
    return out


def checar_crm(cfg):
    c = cfg.get("crm") or {}
    tipo = (c.get("tipo") or "").lower()
    if not tipo:
        return [r("CRM", "tipo", "falta", "CRM não informado", "preencher crm.tipo e crm.chave_arquivo, ou pedir export")]
    chave = c.get("chave_arquivo")
    if not chave or not os.path.exists(os.path.expanduser(chave)):
        return [r("CRM", tipo, "falta", "sem arquivo de chave", f"token em ~/.config/sprint-growth/<cliente>_{tipo}.key (chmod 600) ou export")]
    tok = _ler(chave)
    if tipo == "kommo":
        base = c.get("base", "").rstrip("/")
        cod, txt = _get(f"{base}/api/v4/account", {"Authorization": "Bearer " + tok})
        return [status_http("CRM", f"Kommo {base}", cod, txt, "token de longa duração novo na integração do Kommo")]
    if tipo == "datacrazy":
        cod, txt = _get("https://api.g1.datacrazy.io/api/v1/pipelines", {"Authorization": "Bearer " + tok})
        return [status_http("CRM", "DataCrazy", cod, txt, "token novo no DataCrazy")]
    return [r("CRM", tipo, "manual", "sem teste automático para este CRM", "testar um GET na conversa ou usar export")]


def checar_n8n(cfg_local, cfg):
    n = cfg_local.get("n8n") or {}
    if not n.get("base"):
        return [r("n8n", "API", "manual", "sem n8n configurado", "")]
    k = _ler(n["chave_arquivo"])
    fluxos = (cfg.get("n8n") or {}).get("workflows", [])
    out = []
    cod, txt = _get(f"{n['base']}/workflows?limit=1", {"X-N8N-API-KEY": k})
    out.append(status_http("n8n", "API", cod, txt, "chave da API do n8n"))
    for f in fluxos:
        cod, txt = _get(f"{n['base']}/workflows/{f}", {"X-N8N-API-KEY": k})
        if cod == 200:
            ativo = json.loads(txt).get("active")
            out.append(r("n8n", f, "ok" if ativo else "atencao", "ativo" if ativo else "inativo",
                         "" if ativo else "confirmar se o fluxo deveria estar ligado"))
        else:
            out.append(status_http("n8n", f, cod, txt))
    if fluxos:
        out.append(r("n8n", "credencial do CRM nos fluxos", "manual", "execução \"success\" não prova que chega ao CRM",
                     "conferir itens nos nós do CRM das últimas execuções (armadilha: filtro que esconde credencial morta)"))
    return out


def checar_planilhas(cfg):
    b = cfg.get("backup") or {}
    if not b.get("planilha"):
        return [r("Planilhas", "backup de leads", "atencao", "sem planilha de backup no config", "pedir o link e as abas")]
    out = []
    for aba, gid in (b.get("abas") or {"(primeira)": "0"}).items():
        cod, txt = _get(f"https://docs.google.com/spreadsheets/d/{b['planilha']}/export?format=csv&gid={gid}")
        if cod == 200 and not txt.lstrip().startswith("<"):
            linhas = sum(1 for l in txt.splitlines()[1:] if l.strip(", "))
            out.append(r("Planilhas", aba, "ok", f"CSV público, {linhas} linhas com dado"))
        else:
            out.append(r("Planilhas", aba, "falta", f"HTTP {cod}: planilha privada", "compartilhar como leitor com o link"))
    return out


def checar_paginas(cfg):
    ga = cfg.get("ga4") or {}
    conhecidos = [x for x in (ga.get("fluxo"), ga.get("fluxo_site")) if x]
    acesso_site = bool(str(ga.get("propriedade_site") or "").strip())
    out = []
    for nome, url in [("LP", cfg.get("site")), ("site", cfg.get("site_institucional"))] + [("LP", u) for u in cfg.get("lps", [])]:
        if not url:
            continue
        cod, html = _get(url, timeout=30)
        out.append(status_pagina(nome, url, cod, html, conhecidos, acesso_site))
    return out or [r("Páginas", "site e LP", "falta", "sem URL no config", "preencher site e site_institucional")]


def checar_clarity(cfg):
    c = cfg.get("clarity") or {}
    if not c.get("projeto"):
        return [r("Clarity", "projeto", "atencao", "sem projeto no config", "frente clarity fica de fora")]
    ok = c.get("chave_arquivo") and os.path.exists(os.path.expanduser(c["chave_arquivo"]))
    return [r("Clarity", c["projeto"], "ok" if ok else "falta", "chave presente (API não chamada: 10 por dia)" if ok else "sem token",
              "" if ok else "Clarity → Configurações → Data Export → gerar token; gravar no arquivo do config")]


def checar_meta(cfg, pasta_sprint):
    m = cfg.get("meta") or {}
    exports = []
    if pasta_sprint and os.path.isdir(os.path.join(pasta_sprint, "base", "meta")):
        exports = [f for f in os.listdir(os.path.join(pasta_sprint, "base", "meta")) if f.endswith(".csv")]
    if exports:
        return [r("Meta", "exports", "ok", f"{len(exports)} arquivo(s) em base/meta")]
    return [r("Meta", m.get("conta") or "conta", "manual", "conector do claude.ai só se testa na conversa",
              "na conversa: ads_get_ad_accounts; sem autorização, claude.ai → Conectores → Meta Ads, ou exports (formato em entrevista.md)")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--sprint")
    ap.add_argument("--sem-rede", action="store_true", help="só confere config e briefing")
    a = ap.parse_args()
    pasta_cli = os.path.join(RAIZ, "clientes", a.cliente)
    cfg_p = os.path.join(pasta_cli, "config.json")
    if not os.path.exists(cfg_p):
        sys.exit(f"sem {cfg_p}: copie templates/cliente/ para clientes/{a.cliente}/")
    cfg = json.load(open(cfg_p))
    from mcp_http import config as cfg_local_f
    try:
        cfg_local = cfg_local_f()
    except SystemExit:
        cfg_local = {}
    pasta_sprint = os.path.join(RAIZ, a.sprint) if a.sprint and not os.path.isabs(a.sprint) else a.sprint
    brief_p = os.path.join(pasta_cli, "briefing.md")
    briefing = briefing_pendentes(open(brief_p).read()) if os.path.exists(brief_p) else {}
    res = [] if briefing else [r("Briefing", "briefing.md", "falta", "sem briefing", "copiar templates/cliente/briefing.md e mandar ao usuário")]
    if not a.sem_rede:
        for f in (lambda: checar_ads(cfg), lambda: checar_gtm(cfg), lambda: checar_ga4(cfg), lambda: checar_crm(cfg),
                  lambda: checar_n8n(cfg_local, cfg), lambda: checar_planilhas(cfg), lambda: checar_paginas(cfg),
                  lambda: checar_clarity(cfg), lambda: checar_meta(cfg, pasta_sprint)):
            try:
                res += f()
            except Exception as e:
                res.append(r("Pré-voo", "erro", "falta", str(e)[:150], "rodar de novo; se persistir, conferir o config"))
    destino = pasta_sprint or pasta_cli
    os.makedirs(destino, exist_ok=True)
    md = render(a.cliente, res, briefing)
    open(os.path.join(destino, "preflight.md"), "w").write(md)
    json.dump({"resultados": res, "briefing": {k: list(v) for k, v in briefing.items()}}, open(os.path.join(destino, "preflight.json"), "w"),
              ensure_ascii=False, indent=1)
    print(md)


if __name__ == "__main__":
    main()
