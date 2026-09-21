# -*- coding: utf-8 -*-
"""Resumo mensal do GA4 para o piloto (--ga4): sessões por grupo pago (Google, Meta), não pagas e total do site,
carrinho e checkout do tráfego pago, e custo, cliques e impressões do Google Ads vinculado.

Consulta o servidor MCP oficial do Google Analytics (analytics-mcp) direto pelo stdio, com a credencial ADC da máquina.
Uso:
  python3 ga4_resumo.py --propriedade 548387588 --meses agosto/2026,setembro/2026 --ate 2026-09-17 --out ga4.json

Regras de agrupamento (sessionDefaultChannelGroup + sessionSource):
  Meta      canal pago com origem meta, facebook, instagram, fb ou ig (a V4 marca meta_ads / paid, que o GA4 joga em "Paid Other")
  Google    demais canais pagos com origem google, e Cross-network (PMax), que chega sem origem às vezes
  Outros    canal pago de outra origem (TikTok, Bing...): entra como pago e gera alerta
  Não pago  todo o resto (orgânico, direto, referência, não atribuído, assistentes de IA)
Custo, cliques e impressões do Google Ads vêm por campanha, somados no mês (cruzar com yearMonth duplica valores no GA4).
"""
import argparse, calendar, json, os, re, subprocess, sys, threading, time, unicodedata
from datetime import date

MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
PAGOS = {"Paid Search", "Cross-network", "Paid Other", "Display", "Paid Shopping", "Paid Social", "Paid Video"}
RE_META = re.compile(r"(meta|facebook|instagram|^fb|^ig)", re.I)
RE_GOOGLE = re.compile(r"google", re.I)


def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


class MCP:
    """Cliente stdio mínimo (JSON-RPC) para o analytics-mcp."""
    def __init__(self, binario):
        self.p = subprocess.Popen([binario], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.out, self.i = {}, 1
        threading.Thread(target=self._ler, daemon=True).start()
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "ga4_resumo", "version": "1"}})
        self._enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _ler(self):
        for linha in self.p.stdout:
            try:
                d = json.loads(linha); self.out[d.get("id")] = d
            except ValueError:
                pass

    def _enviar(self, o):
        self.p.stdin.write(json.dumps(o) + "\n"); self.p.stdin.flush()

    def _rpc(self, metodo, params, espera=120):
        self.i += 1; i = self.i
        self._enviar({"jsonrpc": "2.0", "id": i, "method": metodo, "params": params})
        for _ in range(espera * 10):
            if i in self.out:
                return self.out.pop(i)
            time.sleep(0.1)
        sys.exit(f"analytics-mcp não respondeu a {metodo} em {espera}s")

    def relatorio(self, **args):
        r = self._rpc("tools/call", {"name": "run_report", "arguments": args})
        if "error" in r:
            sys.exit(f"run_report falhou: {r['error']}")
        txt = "".join(c.get("text", "") for c in r["result"].get("content", []) if c.get("type") == "text")
        try:
            d = json.loads(txt)
        except ValueError:
            sys.exit(f"run_report devolveu erro: {txt[:500]}")
        if isinstance(d, dict) and "error" in d:
            sys.exit(f"run_report devolveu erro: {d['error']}")
        return d.get("rows", [])

    def fechar(self):
        self.p.kill()


def periodo(rotulo, ate):
    nome, ano = rotulo.split("/")
    m, a = MESES.index(norm(nome)) + 1, int(ano)
    ini = date(a, m, 1)
    fim = date(a, m, calendar.monthrange(a, m)[1])
    if ate and ate < fim:
        fim = ate
    return ini, fim


def grupo(canal, origem):
    if canal not in PAGOS:
        return "nao_pago"
    if RE_META.search(origem or ""):
        return "meta"
    if RE_GOOGLE.search(origem or "") or canal in ("Cross-network", "Paid Search", "Display", "Paid Shopping", "Paid Video"):
        return "google"
    return "outros_pagos"


def resumo_mes(mcp, prop, ini, fim):
    dr = [{"start_date": ini.isoformat(), "end_date": fim.isoformat()}]
    s = {g: 0 for g in ("google", "meta", "outros_pagos", "nao_pago")}
    fun = {"carrinho_pago": 0, "checkout_pago": 0, "compras_pagas_ga4": 0, "receita_paga_ga4": 0.0}
    origens_outros = set()
    for r in mcp.relatorio(property_id=prop, date_ranges=dr, dimensions=["sessionDefaultChannelGroup", "sessionSource"],
                           metrics=["sessions", "addToCarts", "checkouts", "ecommercePurchases", "purchaseRevenue"], limit=10000):
        canal, origem = [x["value"] for x in r["dimension_values"]]
        ses, cart, chk, comp, rec = [float(x["value"]) for x in r["metric_values"]]
        g = grupo(canal, origem)
        s[g] += ses
        if g != "nao_pago":
            fun["carrinho_pago"] += cart; fun["checkout_pago"] += chk
            fun["compras_pagas_ga4"] += comp; fun["receita_paga_ga4"] += rec
        if g == "outros_pagos":
            origens_outros.add(f"{canal} / {origem}")
    ads = {"google_investimento": 0.0, "google_cliques": 0, "google_impressoes": 0}
    for r in mcp.relatorio(property_id=prop, date_ranges=dr, dimensions=["sessionCampaignName"],
                           metrics=["advertiserAdCost", "advertiserAdClicks", "advertiserAdImpressions"], limit=10000):
        c, cl, im = [float(x["value"]) for x in r["metric_values"]]
        ads["google_investimento"] += c; ads["google_cliques"] += cl; ads["google_impressoes"] += im
    total = sum(s.values())
    out = {"inicio": ini.isoformat(), "fim": fim.isoformat(),
           "google_investimento": round(ads["google_investimento"], 2), "google_cliques": int(ads["google_cliques"]),
           "google_impressoes": int(ads["google_impressoes"]),
           "sessoes_google": int(s["google"]), "sessoes_meta": int(s["meta"]), "sessoes_outros_pagos": int(s["outros_pagos"]),
           "sessoes_nao_pagas": int(s["nao_pago"]), "sessoes_total": int(total),
           "carrinho_pago": int(fun["carrinho_pago"]), "checkout_pago": int(fun["checkout_pago"]),
           "compras_pagas_ga4": int(fun["compras_pagas_ga4"]), "receita_paga_ga4": round(fun["receita_paga_ga4"], 2)}
    if origens_outros:
        out["alerta"] = "tráfego pago fora de Google e Meta: " + ", ".join(sorted(origens_outros))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--propriedade", required=True, help="id numérico da propriedade GA4 (ex.: 548387588)")
    ap.add_argument("--meses", required=True, help="meses separados por vírgula, no formato da fonte (ex.: agosto/2026,setembro/2026)")
    ap.add_argument("--ate", help="último dia considerado (AAAA-MM-DD); use o mesmo corte da planilha de indicadores no mês corrente")
    ap.add_argument("--binario", default=os.path.expanduser("~/.local/bin/analytics-mcp"))
    ap.add_argument("--out", default="ga4.json")
    a = ap.parse_args()
    ate = date.fromisoformat(a.ate) if a.ate else None
    mcp = MCP(a.binario)
    try:
        meses = {}
        for rot in [x.strip() for x in a.meses.split(",") if x.strip()]:
            ini, fim = periodo(rot, ate)
            meses[rot] = resumo_mes(mcp, str(a.propriedade), ini, fim)
    finally:
        mcp.fechar()
    saida = {"propriedade": f"properties/{a.propriedade}", "extraido_em": date.today().isoformat(), "meses": meses}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(json.dumps(saida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
