#!/usr/bin/env python3
"""Instala os agentes da sprint (fonte única: agentes/*.md desta skill) na pasta de agentes do projeto.

  python3 scripts/instalar_agentes.py                       # copia para <projeto>/.claude/agents/
  python3 scripts/instalar_agentes.py --conferir            # só compara; sai com 1 se algo estiver diferente
  python3 scripts/instalar_agentes.py --destino ~/.claude/agents   # instalação global, se preferir

<projeto> é a pasta que contém .claude/skills/sprint-growth. O Claude Code só lê agentes de .claude/agents/
(projeto), ~/.claude/agents/ (global) ou de plugin; atalho (symlink) não é documentado, por isso a cópia.
Edite sempre agentes/*.md aqui e rode de novo; a regressão confere que os instalados batem com a fonte.
Agente sprint-* que não existe mais na fonte é removido do destino.
"""
import argparse, filecmp, glob, os, shutil, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(SKILL, "agentes")


def destino_padrao():
    # <projeto>/.claude/skills/sprint-growth → <projeto>/.claude/agents
    return os.path.join(os.path.dirname(os.path.dirname(SKILL)), "agents")


def diferencas(destino):
    fonte = {os.path.basename(p) for p in glob.glob(os.path.join(FONTE, "sprint-*.md"))}
    inst = {os.path.basename(p) for p in glob.glob(os.path.join(destino, "sprint-*.md"))}
    dif = [f"falta instalar: {n}" for n in sorted(fonte - inst)]
    dif += [f"sobrando no destino: {n}" for n in sorted(inst - fonte)]
    dif += [f"diferente da fonte: {n}" for n in sorted(fonte & inst)
            if not filecmp.cmp(os.path.join(FONTE, n), os.path.join(destino, n), shallow=False)]
    return dif


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--destino", default=destino_padrao())
    ap.add_argument("--conferir", action="store_true")
    a = ap.parse_args()
    destino = os.path.expanduser(a.destino)
    if a.conferir:
        d = diferencas(destino)
        print("\n".join(d) if d else f"Agentes instalados em {destino} batem com a fonte.")
        sys.exit(1 if d else 0)
    os.makedirs(destino, exist_ok=True)
    for n in diferencas(destino):
        if n.startswith("sobrando no destino: "):
            os.remove(os.path.join(destino, n.split(": ", 1)[1]))
    for p in sorted(glob.glob(os.path.join(FONTE, "sprint-*.md"))):
        shutil.copy2(p, destino)
    print(f"{len(glob.glob(os.path.join(FONTE, 'sprint-*.md')))} agentes instalados em {destino}. "
          "Abra uma conversa nova para o Claude Code carregar.")


if __name__ == "__main__":
    main()
