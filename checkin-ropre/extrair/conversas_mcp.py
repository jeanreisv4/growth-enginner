# -*- coding: utf-8 -*-
"""Adaptador do lado qualitativo: calls e conversas que chegam por MCP.

Transcrição de call e conversa de WhatsApp não vêm por HTTP daqui — quem as puxa
é o Claude, pelas conexões MCP do Flow, durante a execução da skill. Este
adaptador fecha o circuito: o Claude grava o que leu em dois arquivos de entrada
com formato fixo, e aqui eles viram modelo canônico, com as mesmas regras de
data e de fonte do resto do ETL.

  python3 extrair/conversas_mcp.py --cliente clientes/<c>/cliente.json \\
      --calls entradas/calls.json --conversas entradas/conversas.json --saida bruto_conversas.json

`entradas/calls.json` (o Claude preenche a partir das transcrições):

```json
[{"dia": "2026-09-18", "titulo": "Alinhamento semanal",
  "acordos": ["Verba segue em R$ 6.000", "Cliente aprova trocar o critério de MQL"],
  "pendencias": ["Cliente vai mandar a base de clientes inativos"],
  "riscos": ["Time comercial sem SDR dedicada até outubro"]}]
```

`entradas/conversas.json` (WhatsApp/chat, só o que virou pendência):

```json
[{"dia": "2026-09-19", "canal": "whatsapp", "status": "aberta",
  "assunto": "Aprovação de criativo", "pendencia": "Cliente não aprovou os 3 criativos novos"}]
```

Por que arquivo e não chamada direta: o que entra num check-in de cliente
precisa ser lido por uma pessoa antes de virar slide. O arquivo é esse ponto de
conferência — e deixa o check-in reproduzível depois, sem depender de a call
ainda estar acessível.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extrair.base import Adaptador, registrar  # noqa: E402
from transformar import canonico  # noqa: E402


def _ler_lista(caminho, rotulo, avisos):
    if not caminho:
        return []
    if not os.path.exists(caminho):
        avisos.append(f"{rotulo}: arquivo {os.path.basename(caminho)} não existe — o bloco sai sem essa fonte.")
        return []
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    if not isinstance(dados, list):
        raise SystemExit(f"{rotulo}: o arquivo precisa ser uma lista de objetos.")
    return dados


@registrar("conversas_mcp")
class ConversasMCP(Adaptador):

    def extrair(self, cliente, janela=None):
        pacote = self.pacote(cliente, janela)

        for c in _ler_lista(self.config.get("calls"), "Calls", pacote["avisos"]):
            if janela and not canonico.dentro(c.get("dia"), janela):
                continue
            pacote["calls"].append({
                "dia": c.get("dia"),
                "titulo": c.get("titulo") or "Call com o cliente",
                "acordos": list(c.get("acordos") or []),
                "pendencias": list(c.get("pendencias") or []),
                "riscos": list(c.get("riscos") or []),
            })

        for c in _ler_lista(self.config.get("conversas"), "Conversas", pacote["avisos"]):
            if janela and not canonico.dentro(c.get("dia"), janela):
                continue
            pacote["conversas"].append({
                "dia": c.get("dia"),
                "canal": c.get("canal") or "whatsapp",
                "status": c.get("status") or "aberta",
                "assunto": c.get("assunto"),
                "pendencia": c.get("pendencia"),
            })

        if not pacote["calls"]:
            pacote["avisos"].append("Nenhuma call no período: o bloco de Objetivos fica sem o que foi acordado "
                                    "com o cliente, e Próximos Passos sai só do que a equipe planejou.")
        return pacote


def main():
    p = argparse.ArgumentParser(description="Converte calls e conversas (MCP) no modelo canônico")
    p.add_argument("--cliente", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--calls")
    p.add_argument("--conversas")
    p.add_argument("--de")
    p.add_argument("--ate")
    a = p.parse_args()
    with open(a.cliente, encoding="utf-8") as f:
        cliente = json.load(f)
    janela = {"de": a.de, "ate": a.ate} if a.de and a.ate else None
    pacote = ConversasMCP({"calls": a.calls, "conversas": a.conversas}).extrair(cliente, janela)
    canonico.gravar(pacote, a.saida)
    print(f"{a.saida}: {len(pacote['calls'])} calls, {len(pacote['conversas'])} conversas.")
    for aviso in pacote["avisos"]:
        print(f"  aviso: {aviso}")


if __name__ == "__main__":
    main()
