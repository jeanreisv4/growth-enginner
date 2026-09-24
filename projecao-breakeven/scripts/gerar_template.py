#!/usr/bin/env python3
"""Atalho da skill: gera o template (xlsx) a partir do premissas.json chamando o gerador em gerador/ dentro da própria skill.
Uso: python3 scripts/gerar_template.py --premissas premissas.json --modelo inside_sales|ecommerce --cliente "Nome" [--cenario Realista] --out arquivo.xlsx
Sem argumentos de premissas, o gerador reconstrói a planilha demo (turismo + varejo de tecidos): python3 gerador/build_workbook.py saida.xlsx
"""
import os, subprocess, sys
GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gerador", "build_workbook.py")
if not os.path.exists(GEN):
    sys.exit(f"Gerador não encontrado em {GEN}.")
sys.exit(subprocess.call([sys.executable, GEN] + sys.argv[1:]))
