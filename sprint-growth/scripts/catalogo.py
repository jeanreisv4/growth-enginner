#!/usr/bin/env python3
"""Catálogo de auditoria e correção por plataforma (referencias/plataformas/*.md). Sem rede.

  python3 scripts/catalogo.py                 # confere o catálogo e imprime a cobertura por plataforma
  python3 scripts/catalogo.py --frente medicao   # itens de auditoria que a frente precisa cobrir

Regras (a regressão roda as mesmas):
- ids únicos em todo o catálogo; auditoria com frente, gravidade e sinal de problema;
- toda correção tem risco R1/R2/R3, "voltar atrás" e "verificar depois", e só corrige ids que existem;
- todo item de auditoria é corrigido por pelo menos uma correção (em qualquer arquivo): cobertura de 100%.
"""
import argparse, glob, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "referencias", "plataformas")
FRENTES = ["fontes", "google-ads", "meta-ads", "medicao", "clarity", "jornada", "comercial", "mercado"]
GRAVIDADES = ["crítica", "alta", "média", "baixa"]
RISCOS = ["R1", "R2", "R3"]
COLS_AUD = ["Id", "Verificação", "Frente", "Como verificar", "Sinal de problema", "Gravidade"]
COLS_COR = ["Id", "Correção", "Corrige", "Como aplicar", "Validar antes", "Risco", "Voltar atrás", "Verificar depois"]


def _tabela(texto, secao):
    """Linhas da primeira tabela depois do título '## <secao>'."""
    m = re.search(rf"^## {secao}\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    if not m:
        return None, []
    linhas = [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(linhas) < 2:
        return None, []
    celulas = lambda l: [c.strip() for c in l.strip("|").split("|")]
    return celulas(linhas[0]), [celulas(l) for l in linhas[2:]]


def carregar(pasta=PASTA):
    """{'auditoria': {id: {...}}, 'correcao': {id: {...}}, 'problemas': [...]}"""
    aud, cor, problemas = {}, {}, []
    for arq in sorted(glob.glob(os.path.join(pasta, "*.md"))):
        nome = os.path.basename(arq)
        texto = open(arq, encoding="utf-8").read()
        for secao, cols, destino in (("Auditoria", COLS_AUD, aud), ("Correção", COLS_COR, cor)):
            cab, linhas = _tabela(texto, secao)
            if cab is None:
                problemas.append(f"{nome}: sem a tabela '## {secao}'")
                continue
            if cab != cols:
                problemas.append(f"{nome}: colunas de {secao} {cab} ≠ {cols}")
                continue
            for l in linhas:
                if len(l) != len(cols):
                    problemas.append(f"{nome}: linha de {secao} com {len(l)} colunas: {l[:2]}")
                    continue
                item = dict(zip(cols, l), arquivo=nome)
                if item["Id"] in aud or item["Id"] in cor:
                    problemas.append(f"{nome}: id repetido {item['Id']}")
                destino[item["Id"]] = item
    return {"auditoria": aud, "correcao": cor, "problemas": problemas}


def ids_de(celula):
    return [x.strip() for x in celula.split(",") if x.strip()]


def conferir(cat):
    p = list(cat["problemas"])
    aud, cor = cat["auditoria"], cat["correcao"]
    for i, a in aud.items():
        if a["Frente"] not in FRENTES:
            p.append(f"{a['arquivo']}: {i} com frente '{a['Frente']}'")
        if a["Gravidade"] not in GRAVIDADES:
            p.append(f"{a['arquivo']}: {i} com gravidade '{a['Gravidade']}'")
        if not a["Sinal de problema"] or not a["Como verificar"]:
            p.append(f"{a['arquivo']}: {i} sem como verificar ou sinal de problema")
        if i.startswith("CX-"):
            p.append(f"{a['arquivo']}: id de auditoria não pode começar com CX- ({i})")
    for i, c in cor.items():
        if not i.startswith("CX-"):
            p.append(f"{c['arquivo']}: correção {i} sem prefixo CX-")
        if c["Risco"] not in RISCOS:
            p.append(f"{c['arquivo']}: {i} com risco '{c['Risco']}'")
        for campo in ("Como aplicar", "Validar antes", "Voltar atrás", "Verificar depois"):
            if not c[campo]:
                p.append(f"{c['arquivo']}: {i} sem '{campo}'")
        for alvo in ids_de(c["Corrige"]):
            if alvo not in aud:
                p.append(f"{c['arquivo']}: {i} corrige {alvo}, que não existe na auditoria")
        for ref in re.findall(r"CX-[A-Z]+\d+", " ".join(c.values())):
            if ref not in cor:
                p.append(f"{c['arquivo']}: {i} cita {ref}, que não existe")
    corrigidos = {a for c in cor.values() for a in ids_de(c["Corrige"])}
    p += [f"{aud[i]['arquivo']}: {i} sem nenhuma correção (cobertura < 100%)" for i in aud if i not in corrigidos]
    return p


def por_frente(cat, frente):
    return {i: a for i, a in cat["auditoria"].items() if a["Frente"] == frente}


def resumo(cat):
    linhas = ["| Plataforma | Itens de auditoria | Correções | Críticos e altos |", "| --- | --- | --- | --- |"]
    arquivos = sorted({a["arquivo"] for a in cat["auditoria"].values()})
    for arq in arquivos:
        aud = [a for a in cat["auditoria"].values() if a["arquivo"] == arq]
        cor = [c for c in cat["correcao"].values() if c["arquivo"] == arq]
        altos = sum(a["Gravidade"] in ("crítica", "alta") for a in aud)
        linhas.append(f"| [`{arq}`](referencias/plataformas/{arq}) | {len(aud)} | {len(cor)} | {altos} |")
    linhas.append(f"| **Total** | **{len(cat['auditoria'])}** | **{len(cat['correcao'])}** | "
                  f"**{sum(a['Gravidade'] in ('crítica', 'alta') for a in cat['auditoria'].values())}** |")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frente", choices=FRENTES)
    a = ap.parse_args()
    cat = carregar()
    if a.frente:
        for i, it in por_frente(cat, a.frente).items():
            print(f"{i:5} [{it['Gravidade']}] {it['Verificação']} · {it['Como verificar']}")
        return
    p = conferir(cat)
    print(resumo(cat))
    print("\n" + ("\n".join(p) if p else "Catálogo íntegro: todo item de auditoria tem correção."))
    sys.exit(1 if p else 0)


if __name__ == "__main__":
    main()
