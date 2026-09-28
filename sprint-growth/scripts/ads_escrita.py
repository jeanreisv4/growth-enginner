#!/usr/bin/env python3
"""Aplica operações no Google Ads pelo webhook de escrita. SEMPRE valida antes; aplica só com --aplicar.

  python3 scripts/ads_escrita.py --conta 1234567890 --ops clientes/<c>/ads/ops_negativas.json [--mcc diretas]
  python3 scripts/ads_escrita.py --conta 1234567890 --ops ... --aplicar

--ops = JSON com a lista de mutateOperations do googleAds:mutate (camelCase, resourceName com id temporário
negativo quando cria e referencia no mesmo pacote). Helpers para montar pacotes comuns:

  python3 scripts/ads_escrita.py --conta X --negativas clientes/<c>/ads/negativas.json --nome "Negativas gerais" \
      --campanhas 111111111,222222222 [--aplicar]

Regras (vieram de execução real):
- Aplicar só com ok explícito do usuário para AQUELA mudança; validar antes e mostrar o que muda.
- Conversões hospedadas pelo YouTube não mudam pela API (MUTATE_NOT_ALLOWED) — interface.
- Upload de conversão por clique em conta nova é recusado (CUSTOMER_NOT_ALLOWLISTED): gerar CSV para upload manual
  ou usar a Data Manager API (outro escopo OAuth).
- Depois de aplicar, reler pela API e registrar na aba Executado.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_http import escrita_ads, ok


def pacote_negativas(conta, arquivo, nome, campanhas):
    neg = json.load(open(arquivo))["negativas"]
    lista = f"customers/{conta}/sharedSets/-1"
    ops = [{"sharedSetOperation": {"create": {"resourceName": lista, "name": nome, "type": "NEGATIVE_KEYWORDS"}}}]
    ops += [{"sharedCriterionOperation": {"create": {"sharedSet": lista, "keyword": {"text": n["texto"], "matchType": n.get("tipo", "PHRASE")}}}} for n in neg]
    ops += [{"campaignSharedSetOperation": {"create": {"campaign": f"customers/{conta}/campaigns/{c}", "sharedSet": lista}}} for c in campanhas]
    return ops


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conta", required=True)
    ap.add_argument("--mcc", default="diretas", help="diretas | squad | nayara")
    ap.add_argument("--ops")
    ap.add_argument("--negativas")
    ap.add_argument("--nome", default="Negativas gerais")
    ap.add_argument("--campanhas", default="")
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    if a.negativas:
        ops = pacote_negativas(a.conta, a.negativas, a.nome, [c for c in a.campanhas.split(",") if c])
    elif a.ops:
        ops = json.load(open(a.ops))
    else:
        sys.exit("--ops ou --negativas")
    r = escrita_ads(a.conta, ops, aplicar=False, mcc=a.mcc)
    print(f"validação de {len(ops)} operações:", "OK" if ok(r) else json.dumps(r, ensure_ascii=False)[:2000])
    if a.aplicar and ok(r):
        r = escrita_ads(a.conta, ops, aplicar=True, mcc=a.mcc)
        print("APLICADO:" if ok(r) else "FALHOU:", json.dumps(r, ensure_ascii=False)[:2000])


if __name__ == "__main__":
    main()
