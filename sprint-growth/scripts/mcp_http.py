"""Cliente MCP sobre HTTP (streamable) para os servidores do n8n: Google Ads, GTM, GA4 Admin.

Os endereços e as chaves ficam em ~/.config/sprint-growth/config.json (fora do repositório).
Ferramentas do n8n recebem UM argumento `input`, que é uma string JSON.

    from mcp_http import MCP, escrita_ads
    ads = MCP("googleads_diretas")
    ads.gaql("1234567890", "SELECT customer.descriptive_name FROM customer")
    gtm = MCP("gtm")
    gtm.call("gtm_list_tags", {"accountId": "...", "containerId": "...", "workspaceId": "..."})
"""
import http.client, json, os, time, urllib.request, urllib.error

CONFIG = os.path.expanduser(os.environ.get("SPRINT_GROWTH_CONFIG", "~/.config/sprint-growth/config.json"))


def config():
    if not os.path.exists(CONFIG):
        raise SystemExit(f"Configuração não encontrada: {CONFIG}. Veja referencias/ferramentas.md.")
    return json.load(open(CONFIG))


def _ler(caminho):
    return open(os.path.expanduser(caminho)).read().strip()


class MCP:
    def __init__(self, nome):
        c = config()["mcp"][nome]
        self.url = c["url"]
        self.bearer = _ler(c["bearer_arquivo"]) if c.get("bearer_arquivo") else None
        self.sid, self.n = None, 0
        self._post({"jsonrpc": "2.0", "id": self._id(), "method": "initialize",
                    "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                               "clientInfo": {"name": "sprint-growth", "version": "1"}}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _id(self):
        self.n += 1
        return self.n

    def _post(self, corpo):
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.bearer:
            h["Authorization"] = "Bearer " + self.bearer
        if self.sid:
            h["mcp-session-id"] = self.sid
        req = urllib.request.Request(self.url, data=json.dumps(corpo).encode(), headers=h, method="POST")
        for tentativa in range(4):  # o n8n às vezes corta resposta grande (IncompleteRead) ou devolve 502/503/504
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    self.sid = r.headers.get("mcp-session-id") or self.sid
                    t = r.read().decode()
                break
            except (http.client.IncompleteRead, urllib.error.HTTPError) as e:
                if isinstance(e, urllib.error.HTTPError) and e.code < 500:
                    raise
                if tentativa == 3:
                    raise RuntimeError(f"servidor MCP falhou 4 vezes ({e}); reduza o período ou a consulta")
                time.sleep(5 * (tentativa + 1))
        for linha in t.splitlines():
            if linha.startswith("data:"):
                t = linha[5:].strip()
        return json.loads(t) if t.strip() else None

    def call(self, ferramenta, args, _tentativa=0):
        r = self._post({"jsonrpc": "2.0", "id": self._id(), "method": "tools/call",
                        "params": {"name": ferramenta, "arguments": {"input": json.dumps(args)}}})
        texto = (r or {}).get("result", {}).get("content", [{}])[0].get("text", "")
        # cota por minuto da API (o GTM estoura fácil ao varrer várias contas): espera e tenta de novo
        if texto.startswith("There was an error") and ("429" in texto or "rateLimitExceeded" in texto) and _tentativa < 3:
            time.sleep(65)
            return self.call(ferramenta, args, _tentativa + 1)
        try:
            return json.loads(texto)
        except Exception:
            return texto

    def gaql(self, conta, consulta):
        """Devolve a lista de linhas; erro da API vira exceção com a mensagem do Google."""
        r = self.call("ads_search", {"customerId": str(conta), "gaql": consulta})
        if isinstance(r, str):
            raise RuntimeError(r[:800])
        return r.get("results", [])


def escrita_ads(conta, operacoes, aplicar=False, mcc="diretas", acao="mutate", payload=None):
    """Webhook de escrita do Google Ads. Padrão = validateOnly. acao: mutate | upload | historico | ideias."""
    c = config()["escrita_ads"][mcc]
    corpo = {"customerId": str(conta), "acao": acao}
    if acao == "mutate":
        corpo.update({"operations": operacoes, "validateOnly": not aplicar})
    else:
        corpo["payload"] = payload
    req = urllib.request.Request(_ler(c["url_arquivo"]), data=json.dumps(corpo).encode(), method="POST",
                                 headers={"X-Api-Key": _ler(c["chave_arquivo"]), "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_corpo": e.read().decode()[:3000]}


def ok(resposta):
    """validateOnly devolve {} quando passa; aplicado devolve mutateOperationResponses."""
    return resposta == {} or "mutateOperationResponses" in (resposta or {})
