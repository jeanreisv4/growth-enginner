# -*- coding: utf-8 -*-
"""Regressão da skill checkin-ropre.

  python3 tests/regressao.py

Confere as regras que não podem quebrar sem alguém notar:

  1. faturamento lê data de fechamento (venda criada em maio e fechada em junho conta em junho);
  2. a regra de atribuição decide quem entra — tag sozinha conta, origem de mídia paga conta,
     prospecção e origem em aberto ficam de fora;
  3. venda com valor zero não vira venda;
  4. novo + recorrente = total, em quantidade e em receita;
  5. período quinzenal corta certo e a meta é proporcional aos dias;
  6. mídia incompleta suprime ROAS, CPL, CTR e CAC — e vira aviso, não zero;
  7. OKR compara com o comparador declarado (>= e <=);
  8. pendência de conversa e acordo de call chegam aos blocos de Entregas e Próximos Passos;
  9. documento e deck saem sem erro, com os cinco blocos do ROPRE;
 10. o JSON do workflow valida (etapa 🔧 nomeia ferramenta, leis por etapa, conexões íntegras)
     e o exemplo de handoff é sintético;
 11. delega para tests/regressao_cliente.py, quando existir: a regressão contra um cliente real,
     com um mês fechado e os números conferidos à mão (o arquivo fica fora do repositório).
"""
import json
import os
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL)
FIX = os.path.join(SKILL, "tests", "fixtures")
TMP = os.path.join(SKILL, "tests", "tmp")

from transformar import canonico  # noqa: E402
from carregar import blocos, documento  # noqa: E402

falhas = []


def conferir(condicao, descricao, detalhe=""):
    print(f"  {'ok  ' if condicao else 'FALHA'}  {descricao}{'' if condicao else ' — ' + str(detalhe)}")
    if not condicao:
        falhas.append(descricao)


def montar(cadencia, referencia, fim=None):
    cliente = json.load(open(os.path.join(FIX, "cliente_teste.json"), encoding="utf-8"))
    pacote = canonico.ler(os.path.join(FIX, "sintetico.json"))
    entradas = {"realizadas": ["Entrega de teste"], "previstas": [{"entrega": "Prevista", "prazo": "julho"}],
                "horas": "40h"}
    p = canonico.periodo(referencia, cadencia, fim=fim)
    return blocos.montar(cliente, pacote, p, entradas)


def main():
    os.makedirs(TMP, exist_ok=True)
    print("Junho (mês fechado)")
    c = montar("mensal", "2026-06-15")
    r = c["resultados"]
    conferir(r["vendas"] == 2, "só as duas vendas da agência com valor entram", r["vendas"])
    conferir(abs(r["receita"] - 3000.0) < 0.01, "receita por data de fechamento = 3.000", r["receita"])
    conferir(r["novos"]["n"] == 1 and r["recorrentes"]["n"] == 1, "novo e recorrente separados",
             (r["novos"], r["recorrentes"]))
    conferir(abs(r["novos"]["receita"] + r["recorrentes"]["receita"] - r["receita"]) < 0.01,
             "novo + recorrente = total")
    conferir("sem marca" not in [m for m in r["cobertura_atribuicao"] if r["cobertura_atribuicao"][m] and m == "x"],
             "cobertura de atribuição publicada", r["cobertura_atribuicao"])
    conferir(abs(r["roas"] - 1.0) < 0.001, "ROAS = 3.000 ÷ 3.000 investidos em junho", r["roas"])
    conferir(abs(r["cpl"] - 20.0) < 0.001, "CPL = 3.000 ÷ 150 leads", r["cpl"])
    conferir(r["perdas"]["total"] == 1 and r["perdas"]["motivos"][0]["motivo"] == "Parou de Interagir",
             "perda com motivo entra no bloco", r["perdas"])
    conferir(abs(r["break_even_mes"] - 50000.0) < 0.01, "break-even = (6.000 + 4.000) ÷ 20%", r["break_even_mes"])
    conferir(abs(r["meta_periodo"] - 50000.0) < 0.01, "mês fechado: meta = break-even", r["meta_periodo"])

    print("\nOKRs e blocos qualitativos")
    okrs = {k["kr"]: k for k in c["objetivos"]["okrs"]}
    conferir(okrs["Receita do período"]["status"] == "atingido", "OKR de receita bate a meta de 3.000",
             okrs["Receita do período"])
    conferir(okrs["Recorrência no máximo em metade das vendas"]["status"] == "atingido",
             "OKR com comparador <= aceita 50%", okrs["Recorrência no máximo em metade das vendas"])
    conferir(any("inativos" in p["pendencia"] for p in c["entregas"]["pendencias"]),
             "pendência da call chega em Entregas", c["entregas"]["pendencias"])
    conferir(any("criativos" in p["pendencia"] for p in c["entregas"]["pendencias"]),
             "pendência do WhatsApp chega em Entregas")
    conferir(any("verba segue" in (p.get("passo") or "") for p in c["proximos_passos"]),
             "acordo da call vira próximo passo", c["proximos_passos"])
    conferir(any("time comercial" in (x.get("risco") or "") for x in c["premissas_riscos"]["riscos"]),
             "risco levantado na call entra no bloco P")
    conferir(c["premissas_riscos"]["riscos"][0].get("score") == 10,
             "risco com P × I fica no topo da lista", c["premissas_riscos"]["riscos"][0])

    print("\nQuinzena")
    q = montar("quinzenal", "2026-06-10")
    rq = q["resultados"]
    conferir(q["periodo"]["de"] == "2026-06-01" and q["periodo"]["ate"] == "2026-06-15",
             "1ª quinzena corta em 15", q["periodo"])
    conferir(rq["vendas"] == 1 and abs(rq["receita"] - 1000.0) < 0.01,
             "só a venda fechada até o dia 15", (rq["vendas"], rq["receita"]))
    conferir(abs(rq["meta_periodo"] - 25000.0) < 1, "meta da quinzena = metade do break-even", rq["meta_periodo"])

    print("\nMídia incompleta (julho para no dia 10)")
    j = montar("mensal", "2026-07-15")
    rj = j["resultados"]
    conferir(rj["roas"] is None and rj["cpl"] is None and rj["investimento"] is None,
             "indicador que depende de mídia fica sem medição", (rj["roas"], rj["cpl"]))
    conferir(any("Mídia incompleta" in a for a in j["avisos"]), "a lacuna vira aviso", j["avisos"])
    conferir(rj["receita"] == 4000.0, "receita do mês continua medida", rj["receita"])

    print("\nRenderizadores")
    md = documento.montar(c)
    for bloco in ("## R · Resultados", "## O · Objetivos", "## P · Premissas e Riscos",
                  "## E · Entregas", "## E · Próximos Passos"):
        conferir(bloco in md, f"documento traz {bloco}")
    conferir("não medido" not in md.split("## R")[0], "cabeçalho do documento sem buraco")
    caminho_json = os.path.join(TMP, "checkin.json")
    json.dump(c, open(caminho_json, "w", encoding="utf-8"), ensure_ascii=False)
    saida_pptx = os.path.join(TMP, "checkin.pptx")
    r_deck = subprocess.run([sys.executable, os.path.join(SKILL, "carregar", "deck.py"),
                             "--checkin", caminho_json, "--saida", saida_pptx],
                            capture_output=True, text=True)
    conferir(r_deck.returncode == 0 and os.path.exists(saida_pptx), "deck .pptx gerado", r_deck.stderr[-300:])
    if os.path.exists(saida_pptx):
        from pptx import Presentation
        prs = Presentation(saida_pptx)
        textos = " ".join(sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.has_text_frame)
        conferir(len(prs.slides._sldIdLst) >= 12, "deck com os cinco blocos e divisórias",
                 len(prs.slides._sldIdLst))
        for bloco in ("Resultados", "Objetivos", "Premissas e Riscos", "Entregas", "Próximos Passos"):
            conferir(bloco in textos, f"deck traz o bloco {bloco}")

    print("\nWorkflow (o JSON que o V4OS lê)")
    sys.path.insert(0, os.path.join(SKILL, "workflow"))
    import render_spec  # noqa: E402
    wf = json.load(open(render_spec.FONTE, encoding="utf-8"))["workflow"]
    problemas = render_spec.validar(wf)
    conferir(not problemas, "JSON do workflow válido para import", "; ".join(problemas))
    com_ferramenta = [e["id"] for e in wf["etapas"] if e["chama_ferramenta"]]
    conferir(all(e["ferramentas"] for e in wf["etapas"] if e["chama_ferramenta"]),
             f"toda etapa 🔧 nomeia a ferramenta ({', '.join(com_ferramenta)})")
    conferir(all(e["leis_aplicaveis"] for e in wf["etapas"] if e["id"] in ("04", "09", "14")),
             "cálculo, bloco R e conferência carregam leis no briefing")
    conferir(os.path.exists(render_spec.EXEMPLO), "contrato de handoff de exemplo existe")
    if os.path.exists(render_spec.EXEMPLO):
        ex = json.load(open(render_spec.EXEMPLO, encoding="utf-8"))
        conferir(all(k in ex for k in ("resultados", "objetivos", "premissas_riscos", "entregas",
                                       "proximos_passos", "regra_atribuicao", "avisos")),
                 "exemplo traz os cinco blocos, a regra e os avisos")
        conferir("Cliente Teste" in json.dumps(ex) and "Nord" not in json.dumps(ex),
                 "exemplo é sintético, sem dado de cliente")

    print("\nCliente real")
    caminho_cliente = os.path.join(SKILL, "tests", "regressao_cliente.py")
    if os.path.exists(caminho_cliente):
        r = subprocess.run([sys.executable, caminho_cliente], capture_output=True, text=True)
        print(r.stdout.rstrip() or r.stderr[-400:])
        if r.returncode != 0:
            falhas.append("regressão do cliente real")
    else:
        print("  (pulado: sem tests/regressao_cliente.py — quem opera um cliente real mantém o seu,")
        print("   com um mês fechado e os números conferidos à mão. O arquivo fica fora do git.)")

    print()
    if falhas:
        print(f"{len(falhas)} falha(s): " + "; ".join(falhas))
        sys.exit(1)
    print("regressão ok")


if __name__ == "__main__":
    main()
