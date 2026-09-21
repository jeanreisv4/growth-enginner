# -*- coding: utf-8 -*-
"""Monta as seções de dados de mercado da aba Metodologia, para o --metodologia-extra do gerador.

  python3 scripts/metodologia_mercado.py --benchmarks referencias/multimidia_automotiva_benchmarks.json --analise analise.json --out metodologia_mercado.json

Usar quando o histórico do cliente é curto demais e as premissas vêm de benchmark (--alvo no piloto). O benchmarks.json traz a tabela
Premissa | Fonte | Benchmark | Período | Taxa utilizada | Justificativa, os benchmarks descartados e as fontes com link (mesmo formato de
crm_turismo_benchmarks.json). O analise.json do cliente traz {"titulo": ..., "linhas": [...], "taxas": {"<premissa>": "<taxa usada>"}}:
o texto da análise e, se quiser, a taxa utilizada e a justificativa de cada linha da tabela ("taxas" e "justificativas", pelo rótulo
da premissa), para um cenário que usa taxas diferentes das do benchmarks.json.
"""
import argparse, json


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--benchmarks", required=True)
    ap.add_argument("--analise", required=True)
    ap.add_argument("--out", default="metodologia_mercado.json")
    a = ap.parse_args()
    bm = json.load(open(a.benchmarks, encoding="utf-8")); an = json.load(open(a.analise, encoding="utf-8"))
    taxas, just = an.get("taxas") or {}, an.get("justificativas") or {}
    linhas = [[l[0], l[1], l[2], l[3], taxas.get(l[0], l[4]), just.get(l[0], l[5])] for l in bm["linhas"]]
    out = {"secoes": [[an.get("titulo", "DADOS DE MERCADO"), an["linhas"]],
                      [bm.get("titulo_tabela", "PREMISSAS DE MERCADO · FONTE E JUSTIFICATIVA"),
                       {"colunas": bm["colunas"], "spans": bm["spans"], "linhas": linhas, "nota": bm["nota_tabela"]}],
                      ["BENCHMARKS PESQUISADOS E NÃO USADOS", bm["descartados"]]],
           "fim": [[bm.get("titulo_fontes", "FONTES · DADOS DE MERCADO (PUBLICAÇÃO · DADO UTILIZADO · ANO · LINK)"),
                    [{"texto": f["texto"] + " · " + f["link"], "link": f["link"]} for f in bm["fontes"]]]]}
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{a.out}: {len(linhas)} premissas, {len(bm['fontes'])} fontes")


if __name__ == "__main__":
    main()
