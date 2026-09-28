#!/usr/bin/env python3
"""CRM DataCrazy: download (somente leitura) e o resumo que desmonta "entrada estável, venda caindo".

  python3 scripts/datacrazy.py baixar    --chave ~/.config/sprint-growth/<c>_crm.key --out clientes/<c>/crm
  python3 scripts/datacrazy.py historico --chave ... --out clientes/<c>/crm --desde 2026-07-01 [--perdidos 150 --abertos 60]
  python3 scripts/datacrazy.py resumo    --out clientes/<c>/crm --pipelines "Vendas X,Gestão de vendas"

Pegadinhas da API (aprendidas na sprint de uma distribuidora de peças automotivas, 28/09/2026):
- Exige User-Agent de curl; o urllib padrão leva 403.
- /businesses, /leads, /conversations: take ≤ 500 + skip.
- /leads/{id}/history: SEM take/skip (com eles volta vazio) e limite de 30 req/min → amostra estratificada.
- /conversations traz o token do WhatsApp do cliente em instance.config: este script remove antes de gravar.
- Origem de anúncio de clique para WhatsApp fica em conversation.sourceReferral (vazio se o tracking não foi ligado).
"""
import argparse, json, os, random, sys, time, urllib.error, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta

BASE = "https://api.g1.datacrazy.io/api/v1"


def _dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) - timedelta(hours=3)


def mes(s):
    return _dt(s).strftime("%Y-%m")


class Cliente:
    def __init__(self, arquivo_chave):
        self.t = open(os.path.expanduser(arquivo_chave)).read().strip()

    def get(self, caminho, tentativas=6):
        for t in range(tentativas):
            try:
                r = urllib.request.Request(BASE + caminho, headers={"Authorization": "Bearer " + self.t, "User-Agent": "curl/8.7.1"})
                return json.load(urllib.request.urlopen(r, timeout=120))
            except urllib.error.HTTPError as e:
                time.sleep(65 if e.code == 429 else 3 + 5 * t)
            except Exception:
                time.sleep(5 + 5 * t)
        raise RuntimeError("falhou " + caminho)

    def tudo(self, recurso, limpar=None):
        itens, skip = [], 0
        while True:
            lote = self.get(f"/{recurso}?take=500&skip={skip}").get("data", [])
            itens += [limpar(x) if limpar else x for x in lote]
            if len(lote) < 500:
                return itens
            skip += 500


def sem_credencial(conversa):
    """Remove o token da instância e dados internos do contato antes de gravar."""
    inst = conversa.get("instance") or {}
    conversa["instance"] = {"id": inst.get("id"), "name": inst.get("name"), "provider": inst.get("provider")}
    (conversa.get("contact") or {}).pop("externalInfo", None)
    return conversa


def novo_ou_antigo(negocio, lead, dias=1):
    """'novo' = negócio aberto até `dias` depois do cadastro do lead; 'antigo' = cliente/lead que já existia."""
    lc = (lead or {}).get("createdAt")
    if not lc:
        return "antigo"
    return "novo" if (_dt(negocio["createdAt"]) - _dt(lc)).days <= dias else "antigo"


def resumo(negocios, leads, pipelines):
    """Por mês: negócios e ganhos por safra, separando lead novo de cliente antigo; ganhos por mês de fechamento."""
    L = {x["id"]: x for x in leads}
    M = [x for x in negocios if not pipelines or x["stage"]["pipeline"]["name"] in pipelines]
    safra = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    fech = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
    for x in M:
        tipo = novo_ou_antigo(x, L.get(x["leadId"]))
        s = safra[mes(x["createdAt"])][tipo]; s[0] += 1; s[1] += x["status"] == "won"
        if x["status"] == "won":
            f = fech[mes(x.get("statusChangedAt") or x["lastMovedAt"])][tipo]; f[0] += 1; f[1] += x.get("total") or 0
    return safra, fech


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["baixar", "historico", "resumo"])
    ap.add_argument("--chave")
    ap.add_argument("--out", required=True)
    ap.add_argument("--desde", default="")
    ap.add_argument("--perdidos", type=int, default=150)
    ap.add_argument("--abertos", type=int, default=60)
    ap.add_argument("--pipelines", default="")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    arq = lambda n: os.path.join(a.out, n)
    if a.acao == "baixar":
        c = Cliente(a.chave)
        for rec, lim in (("businesses", None), ("leads", None), ("conversations", sem_credencial)):
            dados = c.tudo(rec, lim); json.dump(dados, open(arq(rec + ".json"), "w"), ensure_ascii=False); print(rec, len(dados))
        json.dump(c.get("/business-loss-reasons"), open(arq("motivos.json"), "w"), ensure_ascii=False)
        json.dump(c.get("/pipelines"), open(arq("pipelines.json"), "w"), ensure_ascii=False)
    elif a.acao == "historico":
        c = Cliente(a.chave); b = json.load(open(arq("businesses.json")))
        pipes = [p for p in a.pipelines.split(",") if p]
        random.seed(42); alvo = []
        for m in sorted({mes(x["createdAt"]) for x in b if x["createdAt"] >= a.desde}):
            xs = [x for x in b if mes(x["createdAt"]) == m and (not pipes or x["stage"]["pipeline"]["name"] in pipes)]
            alvo += [x["leadId"] for x in xs if x["status"] == "won"]
            for st, n in (("lost", a.perdidos), ("in_process", a.abertos)):
                pool = [x["leadId"] for x in xs if x["status"] == st]; alvo += random.sample(pool, min(n, len(pool)))
        feito = json.load(open(arq("historico.json"))) if os.path.exists(arq("historico.json")) else {}
        alvo = [l for l in dict.fromkeys(alvo) if l not in feito]
        print("a baixar", len(alvo), "(30 por minuto)")
        for i, lid in enumerate(alvo):
            d = c.get(f"/leads/{lid}/history")
            feito[lid] = [{"createdAt": h.get("createdAt"), "historyCode": h.get("historyCode"), "parameters": h.get("parameters"),
                           "at": (h.get("attendant") or {}).get("name")} for h in d.get("data", [])]
            time.sleep(2.05)
            if i % 100 == 0:
                json.dump(feito, open(arq("historico.json"), "w"))
        json.dump(feito, open(arq("historico.json"), "w")); print("leads com histórico", len(feito))
    else:
        safra, fech = resumo(json.load(open(arq("businesses.json"))), json.load(open(arq("leads.json"))),
                             [p for p in a.pipelines.split(",") if p])
        print("mês | novo: negócios · ganhos (%) | antigo: negócios · ganhos (%) | valor ganho novo | valor ganho antigo")
        for m in sorted(safra):
            n, o = safra[m]["novo"], safra[m]["antigo"]
            print(m, f"{n[0]} · {n[1]} ({n[1]/max(1,n[0]):.0%})", f"{o[0]} · {o[1]} ({o[1]/max(1,o[0]):.0%})",
                  round(fech[m]["novo"][1]), round(fech[m]["antigo"][1]))


if __name__ == "__main__":
    main()
