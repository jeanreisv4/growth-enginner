#!/usr/bin/env python3
"""Junta os achados das frentes da sprint (um JSON por agente) num ranking único. Sem rede.

  python3 scripts/consolidar.py --sprint clientes/<c>/sprints/<AAAA-MM-DD> [--frentes google-ads,meta-ads,...]

Lê <sprint>/achados/*.json (formato em referencias/contrato_achados.md) e grava:
  <sprint>/consolidado.md    frentes entregues e faltando, cobertura do catálogo (itens não verificados),
                             divergências entre frentes, não medido, perguntas ao usuário e o ranking de achados
  <sprint>/consolidado.json  o mesmo em JSON, para a conversa principal montar o plano 5W1H

Ordem do ranking (referencias/priorizacao.md): segurança e medição primeiro; depois impacto máximo em R$/mês;
empate por confiança. A restrição pela Teoria das Restrições é decidida pela conversa principal, não aqui.
"""
import argparse, glob, json, os, sys

import catalogo

FRENTES = ["fontes", "google-ads", "meta-ads", "medicao", "clarity", "jornada", "comercial", "mercado"]
ETAPAS = {"trafego", "conversao", "medicao", "integracao", "comercial", "margem", "seguranca", "mercado"}
TIPOS = ["seguranca", "medicao", "vazamento", "otimizacao"]
CONFIANCA = ["alta", "media", "baixa"]
ESFORCOS = {"5 min", "15 min", "1 h", "1–2 dias", "processo comercial"}
OBRIGATORIOS = ["id", "titulo", "evidencia", "etapa", "tipo", "confianca", "correcao", "esforco", "verificacao"]
DIVERGENCIA = 0.10
STATUS = {"ok", "achado", "nao_medido", "nao_se_aplica"}
CATALOGO = catalogo.carregar()


def valida(d, arq):
    """Lista de problemas do JSON de uma frente (vazia = ok)."""
    p = []
    if d.get("frente") not in FRENTES:
        p.append(f"{arq}: frente '{d.get('frente')}' fora da lista {FRENTES}")
    for f in d.get("fontes", []):
        if f.get("confiabilidade") not in CONFIANCA:
            p.append(f"{arq}: fonte '{f.get('nome')}' com confiabilidade '{f.get('confiabilidade')}'")
    for k, n in (d.get("numeros") or {}).items():
        if not isinstance(n, dict) or not isinstance(n.get("valor"), (int, float)) or not n.get("unidade") or not n.get("fonte"):
            p.append(f"{arq}: número '{k}' precisa de valor numérico, unidade e fonte")
    aud, cor = CATALOGO["auditoria"], CATALOGO["correcao"]
    for item, st in (d.get("cobertura") or {}).items():
        if item not in aud:
            p.append(f"{arq}: cobertura cita {item}, que não está no catálogo")
        elif aud[item]["Frente"] != d.get("frente"):
            p.append(f"{arq}: {item} é da frente {aud[item]['Frente']}, não de {d.get('frente')}")
        if st not in STATUS:
            p.append(f"{arq}: cobertura de {item} = '{st}' (use {sorted(STATUS)})")
    for a in d.get("achados", []):
        ident = a.get("id", "?")
        if a.get("item") and a["item"] not in aud:
            p.append(f"{arq}: achado {ident} aponta o item {a['item']}, que não está no catálogo")
        if a.get("correcao_id") and a["correcao_id"] not in cor:
            p.append(f"{arq}: achado {ident} aponta a correção {a['correcao_id']}, que não está no catálogo")
        for c in OBRIGATORIOS:
            if not a.get(c):
                p.append(f"{arq}: achado {ident} sem '{c}'")
        if a.get("etapa") and a["etapa"] not in ETAPAS:
            p.append(f"{arq}: achado {ident} com etapa '{a['etapa']}'")
        if a.get("tipo") and a["tipo"] not in TIPOS:
            p.append(f"{arq}: achado {ident} com tipo '{a['tipo']}'")
        if a.get("confianca") and a["confianca"] not in CONFIANCA:
            p.append(f"{arq}: achado {ident} com confiança '{a['confianca']}'")
        if a.get("esforco") and a["esforco"] not in ESFORCOS:
            p.append(f"{arq}: achado {ident} com esforço '{a['esforco']}' (use {sorted(ESFORCOS)})")
        imp = a.get("impacto")
        if imp is not None:
            faltam = [c for c in ("volume", "ganho_min", "ganho_max", "taxas_seguintes", "ticket")
                      if not isinstance(imp.get(c), (int, float))]
            if faltam:
                p.append(f"{arq}: achado {ident} com impacto sem {faltam} (use null quando não houver base)")
            elif imp["ganho_min"] > imp["ganho_max"]:
                p.append(f"{arq}: achado {ident} com ganho_min maior que ganho_max")
    return p


def faixa(imp):
    """Impacto em R$/mês (mínimo, máximo) = volume × ganho × taxas seguintes × ticket; None sem base."""
    if not imp:
        return None
    base = imp["volume"] * imp["taxas_seguintes"] * imp["ticket"]
    return round(base * imp["ganho_min"], 2), round(base * imp["ganho_max"], 2)


def divergencias(por_frente):
    """Mesma chave em `numeros` vinda de frentes diferentes com diferença acima de 10%."""
    chaves = {}
    for frente, d in por_frente.items():
        for k, n in (d.get("numeros") or {}).items():
            chaves.setdefault(k, []).append((frente, n))
    out = []
    for k, lst in sorted(chaves.items()):
        if len(lst) < 2:
            continue
        vals = [n["valor"] for _, n in lst]
        maior, menor = max(vals), min(vals)
        if maior and (maior - menor) / maior > DIVERGENCIA:
            out.append({"numero": k, "valores": [{"frente": f, "valor": n["valor"], "unidade": n["unidade"],
                                                    "fonte": n["fonte"]} for f, n in lst]})
    return out


def ranking(por_frente):
    achados = []
    for frente, d in por_frente.items():
        for a in d.get("achados", []):
            achados.append(dict(a, frente=frente, impacto_rs=faixa(a.get("impacto"))))
    return sorted(achados, key=lambda a: (TIPOS.index(a["tipo"]) if a["tipo"] in ("seguranca", "medicao") else 2,
                                          -(a["impacto_rs"][1] if a["impacto_rs"] else -1),
                                          CONFIANCA.index(a["confianca"])))


def cobertura(por_frente):
    """Por frente entregue: itens do catálogo verificados e os que ficaram sem status."""
    out = {}
    for frente, d in por_frente.items():
        itens = catalogo.por_frente(CATALOGO, frente)
        cob = d.get("cobertura") or {}
        faltam = [i for i in itens if i not in cob]
        out[frente] = {"itens": len(itens), "verificados": len(itens) - len(faltam), "nao_verificados": faltam,
                       "criticos_sem_status": [i for i in faltam if itens[i]["Gravidade"] in ("crítica", "alta")],
                       "nao_medidos": [i for i, st in cob.items() if st == "nao_medido"]}
    return out


def brl(v):
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def consolidar(pasta, esperadas=None):
    por_frente, problemas = {}, []
    for arq in sorted(glob.glob(os.path.join(pasta, "achados", "*.json"))):
        nome = os.path.basename(arq)
        try:
            d = json.load(open(arq, encoding="utf-8"))
        except json.JSONDecodeError as e:
            problemas.append(f"{nome}: JSON inválido ({e})")
            continue
        p = valida(d, nome)
        problemas += p
        if not p:
            por_frente[d["frente"]] = d
    esperadas = esperadas or FRENTES
    faltando = [f for f in esperadas if f not in por_frente]
    res = {
        "entregues": sorted(por_frente), "faltando": faltando, "problemas": problemas,
        "cobertura": cobertura(por_frente),
        "divergencias": divergencias(por_frente),
        "nao_medido": [{"frente": f, "item": i} for f, d in por_frente.items() for i in d.get("nao_medido", [])],
        "perguntas": [{"frente": f, "pergunta": q} for f, d in por_frente.items() for q in d.get("perguntas", [])],
        "achados": ranking(por_frente),
    }
    return res


def markdown(res):
    L = ["# Consolidado da sprint", ""]
    L.append(f"Frentes entregues: {', '.join(res['entregues']) or 'nenhuma'}. "
             f"Faltando: {', '.join(res['faltando']) or 'nenhuma'}.")
    if res["problemas"]:
        L += ["", "## Arquivos recusados (corrigir e rodar de novo)", ""] + [f"- {p}" for p in res["problemas"]]
    if res["cobertura"]:
        L += ["", "## Cobertura do catálogo (referencias/plataformas/)", "",
              "| Frente | Itens | Verificados | Sem status | Críticos ou altos sem status |", "| --- | --- | --- | --- | --- |"]
        for f, c in sorted(res["cobertura"].items()):
            L.append(f"| {f} | {c['itens']} | {c['verificados']} | {', '.join(c['nao_verificados']) or '—'} | "
                     f"{', '.join(c['criticos_sem_status']) or '—'} |")
    if res["divergencias"]:
        L += ["", "## Divergências entre frentes (decidir qual fonte manda)", "",
              "| Número | Frente | Valor | Fonte |", "| --- | --- | --- | --- |"]
        for dv in res["divergencias"]:
            for v in dv["valores"]:
                L.append(f"| {dv['numero']} | {v['frente']} | {v['valor']} {v['unidade']} | {v['fonte']} |")
    L += ["", "## Achados em ordem", "",
          "| # | Id | Item | Frente | Tipo | Achado | Evidência | Impacto R$/mês | Confiança | Esforço | Correção |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i, a in enumerate(res["achados"], 1):
        imp = f"{brl(a['impacto_rs'][0])}–{brl(a['impacto_rs'][1])}" if a["impacto_rs"] else "sem base"
        L.append(f"| {i} | {a['id']} | {a.get('item') or '—'} | {a['frente']} | {a['tipo']} | {a['titulo']} | "
                 f"{a['evidencia']} | {imp} | {a['confianca']} | {a['esforco']} | {a.get('correcao_id') or '—'} |")
    if res["nao_medido"]:
        L += ["", "## Não medido", ""] + [f"- **{n['frente']}**: {n['item']}" for n in res["nao_medido"]]
    if res["perguntas"]:
        L += ["", "## Perguntas ao usuário", ""] + [f"- **{q['frente']}**: {q['pergunta']}" for q in res["perguntas"]]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sprint", required=True, help="pasta da sprint (contém achados/)")
    ap.add_argument("--frentes", default="", help="frentes esperadas, separadas por vírgula (padrão: todas)")
    a = ap.parse_args()
    res = consolidar(a.sprint, [f for f in a.frentes.split(",") if f] or None)
    json.dump(res, open(os.path.join(a.sprint, "consolidado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(os.path.join(a.sprint, "consolidado.md"), "w", encoding="utf-8").write(markdown(res))
    lacunas = sum(len(c["criticos_sem_status"]) for c in res["cobertura"].values())
    print(f"{len(res['achados'])} achados de {len(res['entregues'])} frentes; faltando: {res['faltando'] or 'nenhuma'}; "
          f"divergências: {len(res['divergencias'])}; críticos ou altos sem status: {lacunas}; "
          f"arquivos recusados: {len(res['problemas'])}")
    sys.exit(1 if res["problemas"] else 0)


if __name__ == "__main__":
    main()
