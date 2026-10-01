#!/usr/bin/env python3
"""
ciclo_crm.py — mede a curva do ciclo de vendas no export do CRM.

Para cada venda ganha, compara o mês de criação do negócio (ou de entrada do lead) com o mês de fechamento e conta
quantos fecharam no próprio mês (M+0), no seguinte (M+1) e assim por diante. A cauda depois de --max-meses é somada
no último mês, para a curva somar 1. A saída é o argumento --ciclo do piloto.

Uso:
  python3 ciclo_crm.py --csv negocios.csv --criacao "Data de criação" --fechamento "Data de fechamento" \
      [--filtro-coluna Status --filtro-valor Ganho] [--max-meses 3]
"""
import argparse, sys

import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--criacao", required=True, help="coluna da data de criação do negócio (ou de entrada do lead)")
    ap.add_argument("--fechamento", required=True, help="coluna da data de fechamento (venda ganha)")
    ap.add_argument("--filtro-coluna", help="coluna que separa as vendas ganhas (ex.: Status)")
    ap.add_argument("--filtro-valor", help="valor dessa coluna para venda ganha (ex.: Ganho)")
    ap.add_argument("--max-meses", type=int, default=3, help="último mês da curva (a cauda soma nele); padrão M+3")
    ap.add_argument("--sep", default=None, help="separador do CSV (padrão: detecta)")
    a = ap.parse_args()
    d = pd.read_csv(a.csv, sep=a.sep, engine="python", dtype=str)
    if a.filtro_coluna:
        d = d[d[a.filtro_coluna].astype(str).str.strip().str.lower() == str(a.filtro_valor).strip().lower()]
    cri = pd.to_datetime(d[a.criacao], dayfirst=True, errors="coerce")
    fec = pd.to_datetime(d[a.fechamento], dayfirst=True, errors="coerce")
    ok = cri.notna() & fec.notna() & (fec >= cri)
    if ok.sum() < 10:
        sys.exit(f"Só {int(ok.sum())} vendas com as duas datas: amostra pequena demais para medir a curva. "
                 "Use --ciclo-dias no piloto como premissa e diga isso ao usuário.")
    meses = ((fec[ok].dt.year - cri[ok].dt.year) * 12 + (fec[ok].dt.month - cri[ok].dt.month)).clip(upper=a.max_meses)
    curva = [float((meses == k).mean()) for k in range(a.max_meses + 1)]
    while len(curva) > 1 and curva[-1] == 0:
        curva.pop()
    dias = (fec[ok] - cri[ok]).dt.days
    print(f"Vendas com as duas datas: {int(ok.sum())} (descartadas: {int((~ok).sum())})")
    print(f"Ciclo em dias: mediana {dias.median():.0f}, média {dias.mean():.0f}, p75 {dias.quantile(0.75):.0f}")
    for k, c in enumerate(curva):
        print(f"  M+{k}{'+' if k == a.max_meses else ''}: {c:.1%}")
    print("--ciclo " + ",".join(f"{c:.4f}" for c in curva))


if __name__ == "__main__":
    main()
