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



# Dois formatos de arquivo de benchmark convivem: o antigo, com "linhas" como listas de 6 campos na ordem das
# colunas, e o novo, com "linhas" como dicionários (premissa, faixa_mercado, veredito, verificacao, fontes,
# descartados por premissa). Este conversor põe os dois na mesma forma em vez de obrigar a reescrever arquivo.
COLUNAS_PADRAO = ["PREMISSA", "FONTE", "BENCHMARK ENCONTRADO", "PERÍODO ANALISADO", "TAXA UTILIZADA", "JUSTIFICATIVA"]
SPANS_PADRAO = [["B", "B"], ["C", "D"], ["E", "G"], ["H", "H"], ["I", "I"], ["J", "N"]]


def normalizar(bm):
    if not bm.get("linhas") or not isinstance(bm["linhas"][0], dict):
        return bm
    linhas, fontes, descartados = [], [], list(bm.get("descartados") or [])
    for l in bm["linhas"]:
        fs = l.get("fontes") or []
        nomes = [f if isinstance(f, str) else f.get("texto", "") for f in fs]
        bench = l.get("faixa_mercado", "")
        if l.get("veredito"):
            bench = f"{bench}  ·  veredito: {l['veredito']}"
        if l.get("atual_do_cliente"):
            bench = f"cliente hoje: {l['atual_do_cliente']}  ·  {bench}"
        linhas.append([l.get("premissa", ""), "; ".join(nomes), bench,
                       l.get("verificacao", ""), l.get("taxa_utilizada", ""), l.get("justificativa", "")])
        for f in fs:
            if isinstance(f, dict) and f.get("link"):
                fontes.append(f)
        for d in (l.get("descartados") or []):
            descartados.append(d if isinstance(d, str) else json.dumps(d, ensure_ascii=False))
    return {**bm, "linhas": linhas, "fontes": bm.get("fontes") or fontes,
            "descartados": descartados, "colunas": bm.get("colunas") or COLUNAS_PADRAO,
            "spans": bm.get("spans") or SPANS_PADRAO,
            "nota_tabela": bm.get("nota_tabela", "")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--benchmarks", required=True)
    ap.add_argument("--analise", required=True)
    ap.add_argument("--out", default="metodologia_mercado.json")
    a = ap.parse_args()
    bm = normalizar(json.load(open(a.benchmarks, encoding="utf-8")))
    an = json.load(open(a.analise, encoding="utf-8"))
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
