# -*- coding: utf-8 -*-
"""Gera a documentação do workflow a partir do JSON, para as duas nunca divergirem.

  python3 workflow/render_spec.py

Fonte da verdade: `workflow/checkin-ropre.workflow.json` — é dele que o V4OS constrói.
Saídas: `referencias/workflow_v4os.md` (a especificação com os briefings), o diagrama mermaid,
os blocos marcados do README e `referencias/checkin.exemplo.json` (o contrato de handoff,
gerado da fixture sintética para nunca carregar dado de cliente).

Também valida o JSON (`validar`): a regressão chama isso.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "workflow", "checkin-ropre.workflow.json")
SPEC = os.path.join(RAIZ, "referencias", "workflow_v4os.md")
DIAGRAMA = os.path.join(RAIZ, "workflow", "diagrama.mmd")
EXEMPLO = os.path.join(RAIZ, "referencias", "checkin.exemplo.json")
README = os.path.join(RAIZ, "README.md")

CORES = {
    "Briefing": "briefing", "Dados": "dados", "Pesquisa": "pesquisa",
    "Análise": "analise", "Revisão": "revisao", "Entrega": "entrega",
}


def dono(e):
    return e.get("executado_por", "este workflow")


def servidores(wf):
    return {s["chave"]: s for s in wf.get("servidores", [])}


def rotulo_servidor(wf, chave):
    """`Dados Flow (dados-flow)`: o nome do painel do V4OS e a chave usada aqui."""
    s = servidores(wf).get(chave)
    return f'**{s["no_v4os"]}** (`{chave}`)' if s else f'`{chave}`'


def curto(titulo, largura=22):
    """Quebra o título em duas linhas para o nó do diagrama não ficar comprido."""
    palavras, linhas, atual = titulo.split(), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 > largura and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    linhas.append(atual)
    return "<br/>".join(linhas)


# ------------------------------------------------------------------ validação

def etapas_por_id(wf):
    return {e["id"]: e for e in wf["etapas"]}


def validar(wf):
    """Devolve a lista de problemas do JSON. Vazia = pode importar."""
    problemas = []
    ids = [e["id"] for e in wf["etapas"]]
    if len(ids) != len(set(ids)):
        problemas.append("id de etapa repetido")
    conhecidos = set(ids)
    n_leis = len(wf["leis"])
    for e in wf["etapas"]:
        i = e["id"]
        if e["categoria"] not in CORES:
            problemas.append(f"{i}: categoria desconhecida {e['categoria']!r}")
        if e["chama_ferramenta"] and not e.get("ferramentas"):
            problemas.append(f"{i}: chama ferramenta mas não diz qual")
        for f in e.get("ferramentas", []):
            for campo in ("servidor", "ferramenta", "para_que", "parametros", "cuidados"):
                if campo not in f:
                    problemas.append(f"{i}: ferramenta sem `{campo}`")
        if "leis_aplicaveis" not in e:
            problemas.append(f"{i}: sem `leis_aplicaveis` (use [] quando nenhuma)")
        elif any(not (1 <= n <= n_leis) for n in e["leis_aplicaveis"]):
            problemas.append(f"{i}: lei fora do intervalo 1..{n_leis}")
        if e["origem"] == "catalogo" and not e.get("etapa_do_catalogo"):
            problemas.append(f"{i}: origem catálogo sem `etapa_do_catalogo`")
        if e["origem"] == "outra_skill" and dono(e) == "este workflow":
            problemas.append(f"{i}: origem outra_skill mas executada por este workflow")
        if not e.get("briefing", "").strip():
            problemas.append(f"{i}: briefing vazio")
        if not e.get("entradas") or not e.get("saidas"):
            problemas.append(f"{i}: sem entradas ou sem saídas")
    chaves = set(servidores(wf)) | {dono(e) for e in wf["etapas"] if e["origem"] == "outra_skill"}
    for e in wf["etapas"]:
        for f in e.get("ferramentas", []):
            if f["servidor"] not in chaves:
                problemas.append(f'{e["id"]}: servidor {f["servidor"]!r} não está em `servidores`')
    for s in wf.get("servidores", []):
        for i in s.get("etapas", []):
            if i not in conhecidos:
                problemas.append(f'servidor {s["chave"]}: etapa {i} não existe')
            elif s["chave"] not in {f["servidor"] for f in etapas_por_id(wf)[i].get("ferramentas", [])}:
                problemas.append(f'servidor {s["chave"]}: diz que entra na etapa {i}, mas a etapa não o chama')
    for c in wf["conexoes"]:
        if c["de"] not in conhecidos or c["para"] not in conhecidos:
            problemas.append(f"conexão {c['de']}→{c['para']} aponta para etapa inexistente")
    ligadas = {c["de"] for c in wf["conexoes"]} | {c["para"] for c in wf["conexoes"]}
    for i in ids:
        if i not in ligadas:
            problemas.append(f"{i}: etapa sem conexão")
    for campo in ("entradas_do_workflow", "saidas_do_workflow", "instrucoes_de_import"):
        if not wf.get(campo):
            problemas.append(f"workflow sem `{campo}`")
    return problemas


# ------------------------------------------------------------------ diagrama

def mermaid(wf):
    """Um subgrafo por dono: o que este workflow executa e o que roda em outra skill."""
    def no(e):
        marca = " 🔧" if e["chama_ferramenta"] else ""
        rotulo = f'<b>{e["id"]}</b> {curto(e["titulo"])}{marca}'
        if dono(e) != "este workflow":
            rotulo += f'<br/><i>{dono(e)}</i>'
        return f'    E{e["id"]}["{rotulo}"]'

    proprias = [e for e in wf["etapas"] if dono(e) == "este workflow"]
    outras = [e for e in wf["etapas"] if dono(e) != "este workflow"]

    linhas = ["flowchart TD"]
    linhas.append('    subgraph CHECKIN["Check-in ROPRE · este workflow"]')
    linhas += ["    " + no(e) for e in proprias]
    linhas.append("    end")
    if outras:
        linhas.append("")
        linhas.append('    subgraph DECK["Deck · design system da companhia"]')
        linhas += ["    " + no(e) for e in outras]
        linhas.append("    end")
    linhas.append("")
    for c in wf["conexoes"]:
        linhas.append(f'    E{c["de"]} --> E{c["para"]}')
    linhas.append("")
    for cat, classe in CORES.items():
        ids = [f'E{e["id"]}' for e in wf["etapas"] if e["categoria"] == cat and dono(e) == "este workflow"]
        if ids:
            linhas.append(f'    class {",".join(ids)} {classe};')
    fora = [f'E{e["id"]}' for e in wf["etapas"] if dono(e) != "este workflow"]
    if fora:
        linhas.append(f'    class {",".join(fora)} outra;')
    linhas += [
        "",
        "    classDef briefing fill:#1f2937,stroke:#60a5fa,color:#e5e7eb;",
        "    classDef dados fill:#1f2937,stroke:#34d399,color:#e5e7eb;",
        "    classDef pesquisa fill:#1f2937,stroke:#fbbf24,color:#e5e7eb;",
        "    classDef analise fill:#1f2937,stroke:#f87171,color:#e5e7eb;",
        "    classDef revisao fill:#1f2937,stroke:#a78bfa,color:#e5e7eb;",
        "    classDef entrega fill:#1f2937,stroke:#e5e7eb,color:#e5e7eb;",
        "    classDef outra fill:#111827,stroke:#9ca3af,color:#9ca3af,stroke-dasharray:4 3;",
    ]
    return "\n".join(linhas)


# ------------------------------------------------------------------ tabelas

def tabela_etapas(wf):
    linhas = ["| # | Etapa | Categoria | Executada por | Leis | Chama ferramenta |",
              "| --- | --- | --- | --- | --- | --- |"]
    for e in wf["etapas"]:
        quem = "este workflow" if dono(e) == "este workflow" else f"`{dono(e)}`"
        if e["origem"] == "catalogo":
            quem += f' · catálogo `{e["etapa_do_catalogo"]}`'
        leis = ", ".join(str(n) for n in e.get("leis_aplicaveis", [])) or "—"
        linhas.append(f'| {e["id"]} | {e["titulo"]} | {e["categoria"]} | {quem} | {leis} | '
                      f'{"sim" if e["chama_ferramenta"] else "—"} |')
    return "\n".join(linhas)


def tabela_entradas(wf):
    linhas = ["| Entrada | Tipo | Obrigatória | O que é |", "| --- | --- | --- | --- |"]
    for x in wf["entradas_do_workflow"]:
        linhas.append(f'| `{x["campo"]}` | {x["tipo"]} | {"sim" if x["obrigatorio"] else "não"} | {x["descricao"]} |')
    return "\n".join(linhas)


def tabela_saidas(wf):
    linhas = ["| Saída | Sai da etapa | Formato |", "| --- | --- | --- |"]
    for x in wf["saidas_do_workflow"]:
        linhas.append(f'| **{x["saida"]}** | {x["de"]} | {x["formato"]} |')
    return "\n".join(linhas)


def tabela_ferramentas(wf):
    """Uma linha por ferramenta, só das etapas deste workflow (as da outra skill são dela)."""
    linhas = ["| Etapa | Servidor | Ferramenta | Para quê |", "| --- | --- | --- | --- |"]
    for e in wf["etapas"]:
        if dono(e) != "este workflow":
            continue
        for f in e.get("ferramentas", []):
            nome = f["ferramenta"] if f["ferramenta"] == "a confirmar" else f'`{f["ferramenta"]}`'
            linhas.append(f'| {e["id"]} | {rotulo_servidor(wf, f["servidor"])} | {nome} | {f["para_que"]} |')
    return "\n".join(linhas)


def tabela_servidores(wf):
    linhas = ["| No V4OS | Chave aqui | O que responde | Entra em | Acesso | Etapas |",
              "| --- | --- | --- | --- | --- | --- |"]
    for s in wf["servidores"]:
        linhas.append(f'| **{s["no_v4os"]}** | `{s["chave"]}` | {s["responde"]} | {s["entra_em"]} | '
                      f'{s["acesso"]} | {", ".join(s["etapas"]) or "—"} |')
    return "\n".join(linhas)


def tabela_pendencias(wf):
    linhas = ["| O que falta | Por quê | Quem responde |", "| --- | --- | --- |"]
    for p in wf["instrucoes_de_import"]["pendencias"]:
        linhas.append(f'| {p["o_que"]} | {p["por_que"]} | {p["quem"]} |')
    return "\n".join(linhas)


def passos_import(wf):
    return "\n".join(f"{i}. {p}" for i, p in enumerate(wf["instrucoes_de_import"]["passos"], 1))


# ------------------------------------------------------------------ spec

def spec(dados):
    wf = dados["workflow"]
    com_ferramenta = [e["id"] for e in wf["etapas"] if e["chama_ferramenta"] and dono(e) == "este workflow"]
    p = [
        "<!-- Gerado por workflow/render_spec.py a partir de workflow/checkin-ropre.workflow.json.",
        "     Edite o JSON, não este arquivo. -->",
        "",
        "# Check-in ROPRE — especificação do workflow para o V4OS",
        "",
        "Especificação da versão que roda **dentro do V4OS**: os dados chegam pelo Nekt e as etapas",
        "executam lá. Nenhum passo depende de script externo. O arquivo de import é",
        "[`workflow/checkin-ropre.workflow.json`](../workflow/checkin-ropre.workflow.json).",
        "",
        "O ETL em Python deste repositório deixa de ser motor e passa a ser **implementação de",
        "referência**: serve para conferir se o workflow chegou aos mesmos números num período já",
        "fechado.",
        "",
        "**Cabeçalho**",
        "",
        "| Campo | Valor |",
        "| --- | --- |",
        f'| Nome | {wf["nome"]} |',
        f'| Produto | {wf["produto"]} *(confirmar)* |',
        f'| Promessa | {wf["promessa"]} |',
        f'| Escopo | {wf["escopo"]} no primeiro ciclo; solicitar canonização depois de rodar em dois clientes |',
        f'| Cadências | {", ".join(wf["cadencias"])} |',
        f'| Etapas | {len(wf["etapas"])} |',
        f'| Conexões | {len(wf["conexoes"])} |',
        "",
        "## Entradas do workflow",
        "",
        "O formulário que se preenche para rodar. A etapa 01 consome tudo isso; nada é perguntado depois.",
        "",
        tabela_entradas(wf),
        "",
        "## Saídas do workflow",
        "",
        tabela_saidas(wf),
        "",
        "## Os servidores",
        "",
        "Com o nome que têm no painel *Ferramentas* do V4OS e a chave usada neste arquivo. O que se liga",
        "no chat não altera workflows: cada etapa liga os seus.",
        "",
        tabela_servidores(wf),
        "",
        "## O desenho",
        "",
        "```mermaid",
        mermaid(wf),
        "```",
        "",
        "🔧 = etapa que chama ferramenta (MCP) durante a execução.",
        "",
        "## Como levar para o V4OS",
        "",
        wf["instrucoes_de_import"]["formato"],
        "",
        passos_import(wf),
        "",
        "---",
        "",
        "## As leis do workflow",
        "",
        "Entram no briefing de **toda** etapa que toca número — a coluna *Leis* de cada etapa diz quais.",
        "Com o cálculo acontecendo em etapa de modelo, a regra precisa viajar junto com a tarefa — o",
        "agente não pode depender de lembrar.",
        "",
    ]
    for i, lei in enumerate(wf["leis"], 1):
        p.append(f"{i}. {lei}")
    p += ["", "---", "", "## As ferramentas, por etapa", "",
          f"As etapas {', '.join(com_ferramenta)} chamam ferramenta. Servidor, nome e parâmetros de cada uma,",
          "com os cuidados que já custaram número errado — eles entram no briefing da etapa.", "",
          tabela_ferramentas(wf), "", "---", ""]

    for e in wf["etapas"]:
        origem = (f'**do catálogo** (`{e["etapa_do_catalogo"]}`)' if e["origem"] == "catalogo"
                  else ("do zero" if e["origem"] != "outra_skill" else "**outra skill**"))
        ferramenta = " · *chama ferramenta*" if e["chama_ferramenta"] else ""
        marca_dono = "" if dono(e) == "este workflow" else f' · executada por `{dono(e)}`'
        leis = ", ".join(str(n) for n in e.get("leis_aplicaveis", []))
        p += [
            f'## {e["id"]} · {e["titulo"]}',
            "",
            f'**Categoria:** {e["categoria"]} · {origem}{ferramenta}{marca_dono}',
            f'**Entradas:** {", ".join(e["entradas"])}',
            f'**Saídas:** {", ".join(e["saidas"])}',
            f'**Leis que entram neste briefing:** {leis or "nenhuma"}',
            "",
        ]
        p += ["> " + l if l.strip() else ">" for l in e["briefing"].splitlines()]
        p.append("")
        if e.get("ferramentas"):
            p.append("**Ferramentas**")
            p.append("")
            for f in e["ferramentas"]:
                nome = f["ferramenta"] if f["ferramenta"] in ("a confirmar", "internas da skill") else f'`{f["ferramenta"]}`'
                p.append(f'- {rotulo_servidor(wf, f["servidor"])} · {nome} — {f["para_que"]}')
                p.append(f'  Parâmetros: `{f["parametros"]}`')
                if f.get("sql"):
                    p.append("  ```sql")
                    p.append("  " + f["sql"])
                    p.append("  ```")
                for c in f["cuidados"]:
                    p.append(f"  - {c}")
            p.append("")

    if wf.get("integracoes_da_plataforma"):
        p += [
            "---",
            "",
            "## Onde este workflow encosta em outras skills",
            "",
            "O check-in produz **conteúdo com número defensável**. Diagramação, identidade visual e QA",
            "visual são de quem cuida do design system. A fronteira:",
            "",
            "| Skill | Papel | Relação com este workflow | Contrato de entrada |",
            "| --- | --- | --- | --- |",
        ]
        for i in wf["integracoes_da_plataforma"]:
            p.append(f'| `{i["skill"]}` | {i["papel"]} | {i["relacao"]} | {i["contrato_de_entrada"]} |')
        p += [
            "",
            "Os contratos de entrada marcados como *a confirmar* são o que falta para o encaixe ser",
            "automático em vez de manual. Até lá, o check-in entrega no formato de",
            "[`referencias/checkin.exemplo.json`](checkin.exemplo.json).",
            "",
        ]

    p += [
        "---",
        "",
        "## Conexões",
        "",
        "```",
        "  " + "  ".join(f'{c["de"]}→{c["para"]}' for c in wf["conexoes"]),
        "```",
        "",
        "## Como validar antes de publicar",
        "",
        "Rode o workflow num **período já fechado** e compare com a implementação de referência deste",
        "repositório, número a número: vendas, receita, novos, recorrentes, ganhos da safra e taxa de",
        "ganho. Se o workflow chegar sozinho aos mesmos valores, as definições estão corretamente",
        "escritas nos briefings. Se não chegar, a diferença aponta exatamente qual definição ficou",
        "ambígua.",
        "",
        "## O que ainda depende de quem está dentro da plataforma",
        "",
        tabela_pendencias(wf),
        "",
    ]
    return "\n".join(p)


# ------------------------------------------------------------------ exemplo de handoff

def exemplo_checkin():
    """O contrato de saída da etapa 15, gerado da fixture sintética (sem dado de cliente)."""
    sys.path.insert(0, RAIZ)
    from transformar import canonico  # noqa: E402
    from carregar import blocos  # noqa: E402
    fix = os.path.join(RAIZ, "tests", "fixtures")
    cliente = json.load(open(os.path.join(fix, "cliente_teste.json"), encoding="utf-8"))
    pacote = canonico.ler(os.path.join(fix, "sintetico.json"))
    entradas = {"realizadas": [{"entrega": "Auditoria de medição publicada", "evidencia": "documento da auditoria"}],
                "previstas": [{"entrega": "Padronizar a tag da agência na criação da oportunidade",
                               "prazo": "próximo mês", "dono": "a_confirmar"}],
                "horas": "40h"}
    c = blocos.montar(cliente, pacote, canonico.periodo("2026-06-15", "mensal"), entradas)
    c["gerado_em"] = "2026-06-30"
    c["extraido_em"] = "2026-06-30"
    c["_o_que_e"] = ("Exemplo do check-in aprovado que a etapa 15 entrega à etapa 16. Gerado por "
                     "workflow/render_spec.py a partir de tests/fixtures (dado sintético). Os cinco blocos "
                     "do ROPRE são resultados, objetivos, premissas_riscos, entregas e proximos_passos; "
                     "regra_atribuicao é o que vai escrito no deck; avisos é a lista do que não foi medido. "
                     "null significa 'não medido', nunca zero.")
    c = {"_o_que_e": c.pop("_o_que_e"), **c}
    with open(EXEMPLO, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ------------------------------------------------------------------ README

def preencher(texto, marca, conteudo):
    """Troca o miolo entre <!-- marca:inicio --> e <!-- marca:fim -->."""
    padrao = re.compile(rf"(<!-- {marca}:inicio -->)(.*?)(<!-- {marca}:fim -->)", re.S)
    if not padrao.search(texto):
        raise SystemExit(f"README sem os marcadores de {marca}")
    return padrao.sub(lambda m: f"{m.group(1)}\n{conteudo}\n{m.group(3)}", texto)


def atualizar_readme(wf):
    texto = open(README, encoding="utf-8").read()
    texto = preencher(texto, "diagrama", "```mermaid\n" + mermaid(wf) + "\n```")
    texto = preencher(texto, "etapas", tabela_etapas(wf))
    leis = "\n".join(f"{i}. {lei}" for i, lei in enumerate(wf["leis"], 1))
    texto = preencher(texto, "leis", leis)
    texto = preencher(texto, "entradas", tabela_entradas(wf))
    texto = preencher(texto, "import", passos_import(wf))
    texto = preencher(texto, "ferramentas", tabela_ferramentas(wf))
    texto = preencher(texto, "pendencias", tabela_pendencias(wf))
    texto = preencher(texto, "servidores", tabela_servidores(wf))
    open(README, "w", encoding="utf-8").write(texto)


def main():
    dados = json.load(open(FONTE, encoding="utf-8"))
    wf = dados["workflow"]
    problemas = validar(wf)
    if problemas:
        print("JSON do workflow com problemas:\n  - " + "\n  - ".join(problemas))
        sys.exit(1)
    open(SPEC, "w", encoding="utf-8").write(spec(dados))
    open(DIAGRAMA, "w", encoding="utf-8").write(mermaid(wf) + "\n")
    exemplo_checkin()
    atualizar_readme(wf)
    print(f'{os.path.relpath(SPEC, RAIZ)}: {len(wf["etapas"])} etapas, {len(wf["conexoes"])} conexões, validação ok')
    print(f'{os.path.relpath(DIAGRAMA, RAIZ)}: diagrama mermaid')
    print(f'{os.path.relpath(EXEMPLO, RAIZ)}: contrato de handoff gerado da fixture')
    print(f'{os.path.relpath(README, RAIZ)}: blocos gerados atualizados')


if __name__ == "__main__":
    main()
