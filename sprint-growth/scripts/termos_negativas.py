#!/usr/bin/env python3
"""Classifica os termos de pesquisa por intenção e propõe negativas que NÃO bloqueiam nada que converteu.

  python3 scripts/termos_negativas.py --raw clientes/<c>/ads/ads_raw.json \
      --negativas referencias/negativas_base.json [--extra clientes/<c>/negativas.json] --out clientes/<c>/ads

Saída: termos.md (gasto por intenção, termos sem conversão, quanto cada negativa bloqueia) e negativas.json
(lista pronta para o webhook de escrita). A trava: se uma negativa pegar termo com conversão, ela sai da
lista e aparece no relatório como "recusada".

Regras que vieram de cliente real:
- "grátis" NÃO é negativa quando o produto tem teste grátis (na SaaS de diário de obra, "diário de obra gratuito" converteu).
- Termo central do produto sem conversão não vira negativa: vira monitoramento (exata ou lance menor).
- Nome de concorrente colado ("diariodeobra") é marca; a expressão separada ("diario de obra") é o produto.
"""
import argparse, json, os, re
from collections import defaultdict

M = lambda v: int(v or 0) / 1e6


def casa(neg, termo):
    return re.search(r"(^|\s)" + re.escape(neg) + r"(\s|$)", termo) is not None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--negativas", required=True, help="JSON {grupo: [termos]} base")
    ap.add_argument("--extra", help="JSON {grupo: [termos]} do cliente (concorrentes, fora do produto)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = json.load(open(a.raw))
    termos = defaultdict(lambda: [0.0, 0, 0.0])
    for x in raw.get("termos", []):
        t = x["searchTermView"]["searchTerm"].lower()
        m = x["metrics"]
        termos[t][0] += M(m.get("costMicros"))
        termos[t][1] += int(m.get("clicks", 0))
        termos[t][2] += float(m.get("conversions", 0))
    neg = json.load(open(a.negativas))
    if a.extra:
        for g, lst in json.load(open(a.extra)).items():
            if g.startswith("_") or not isinstance(lst, list):  # "_nota" e afins são comentário, não grupo
                continue
            neg.setdefault(g, [])
            neg[g] += [t for t in lst if t not in neg[g]]
    neg = {g: [t for t in lst if not t.startswith("_")] for g, lst in neg.items() if not g.startswith("_")}
    total = sum(v[0] for v in termos.values()) or 1
    aceitas, recusadas, por_neg = [], [], {}
    for g, lst in neg.items():
        for n in lst:
            pegos = {t: v for t, v in termos.items() if casa(n, t)}
            conv = sum(v[2] for v in pegos.values())
            por_neg[n] = (g, sum(v[0] for v in pegos.values()), len(pegos), conv)
            (recusadas if conv > 0 else aceitas).append((g, n))
    bloqueados = {t: v for t, v in termos.items() if any(casa(n, t) for _, n in aceitas)}
    gasto_bloq = sum(v[0] for v in bloqueados.values())
    L = ["# Termos de pesquisa e negativas", "",
         f"Gasto com termo visível: R$ {total:,.2f}. As negativas aceitas bloqueiam {len(bloqueados)} termos que custaram "
         f"R$ {gasto_bloq:,.2f} ({gasto_bloq/total:.0%}), sem nenhuma conversão.", "",
         "| Negativa | Grupo | Termos | Gasto bloqueado | Conversões | Situação |", "| --- | --- | --- | --- | --- | --- |"]
    for n, (g, custo, qtd, conv) in sorted(por_neg.items(), key=lambda z: -z[1][1]):
        L.append(f"| {n} | {g} | {qtd} | R$ {custo:,.2f} | {conv:g} | {'RECUSADA: pega termo que converteu' if conv else 'aceita'} |")
    L += ["", "## Maiores termos sem conversão que NÃO foram bloqueados (revisar à mão)", "",
          "| Termo | Gasto | Cliques |", "| --- | --- | --- |"]
    livres = sorted(((t, v) for t, v in termos.items() if v[2] == 0 and t not in bloqueados), key=lambda z: -z[1][0])[:40]
    L += [f"| {t} | R$ {v[0]:,.2f} | {v[1]} |" for t, v in livres]
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, "termos.md"), "w").write("\n".join(L) + "\n")
    json.dump({"negativas": [{"grupo": g, "texto": n, "tipo": "PHRASE"} for g, n in aceitas],
               "recusadas": [{"grupo": g, "texto": n} for g, n in recusadas],
               "gasto_bloqueado": round(gasto_bloq, 2), "termos_bloqueados": len(bloqueados)},
              open(os.path.join(a.out, "negativas.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(aceitas)} negativas aceitas, {len(recusadas)} recusadas · bloqueia R$ {gasto_bloq:,.2f} ({gasto_bloq/total:.0%}) em {len(bloqueados)} termos")


if __name__ == "__main__":
    main()
