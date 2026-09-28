# -*- coding: utf-8 -*-
"""Contrato dos adaptadores de extração (o E do ETL).

Um adaptador faz uma coisa: pega o dado cru de UMA fonte e devolve o modelo
canônico de `transformar/canonico.py`. Ele não calcula métrica, não decide
período e não formata nada — isso é do transformar/ e do carregar/.

Para escrever um adaptador novo:

    from extrair.base import Adaptador, registrar

    @registrar("meu_crm")
    class MeuCRM(Adaptador):
        def extrair(self, cliente, janela):
            pacote = self.pacote(cliente)
            pacote["negocios"].append({...})
            return pacote

Regras:
  * data em YYYY-MM-DD no fuso do cliente;
  * `atribuicao` preenchida em todo negócio e contato (ver `Atribuicao`);
  * o que a fonte não entrega vira aviso em `pacote["avisos"]`, não vira zero.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from transformar import canonico  # noqa: E402

REGISTRO = {}


def registrar(nome):
    def dec(classe):
        classe.nome = nome
        REGISTRO[nome] = classe
        return classe
    return dec


def adaptador(nome):
    if nome not in REGISTRO:
        raise KeyError(f"adaptador {nome!r} não existe; disponíveis: {', '.join(sorted(REGISTRO))}")
    return REGISTRO[nome]


class Adaptador:
    nome = "base"

    def __init__(self, config=None):
        self.config = config or {}

    def pacote(self, cliente, janela=None):
        return canonico.vazio(fonte=self.nome, cliente=cliente.get("cliente"), periodo_bruto=janela)

    def extrair(self, cliente, janela=None):  # pragma: no cover - contrato
        raise NotImplementedError


class Atribuicao:
    """Regra de atribuição do cliente — quem é da agência e por quê.

    Sai do `cliente.json` e viaja junto com cada registro, para o check-in poder
    imprimir a regra que produziu o número. Exemplo de regra real: tag da agência
    vale sozinha, e origem de mídia paga conta mesmo quando o texto não nomeia a
    agência.
    """

    def __init__(self, cfg):
        cfg = cfg or {}
        self.tags = set(cfg.get("tags") or [])
        self.origens_agencia = set(cfg.get("origens_agencia") or [])
        self.origens_midia_paga = set(cfg.get("origens_midia_paga") or [])
        self.origens_em_aberto = set(cfg.get("origens_em_aberto") or [])
        self.canal_por_origem = cfg.get("canal_por_origem") or {}
        self.cfg = cfg

    def marcar(self, tags_negocio=(), tags_contato=(), origem=None):
        origem = origem or ""
        tem_tag = bool(self.tags & set(tags_negocio or ())) or bool(self.tags & set(tags_contato or ()))
        if tem_tag and origem in self.origens_agencia:
            return {"agencia": True, "marca": "tag e origem da agência"}
        if tem_tag and origem in self.origens_midia_paga:
            return {"agencia": True, "marca": "tag e origem de mídia paga"}
        if tem_tag:
            return {"agencia": True, "marca": "só tag"}
        if origem in self.origens_agencia:
            return {"agencia": True, "marca": "só origem da agência"}
        if origem in self.origens_midia_paga:
            return {"agencia": True, "marca": "só origem de mídia paga"}
        if origem in self.origens_em_aberto:
            return {"agencia": False, "marca": "origem em aberto"}
        return {"agencia": False, "marca": "sem marca"}

    def canal(self, origem):
        """Canal normalizado a partir do texto livre de origem, quando dá."""
        if not origem:
            return None
        return self.canal_por_origem.get(origem)
