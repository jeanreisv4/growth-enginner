# -*- coding: utf-8 -*-
"""O modelo canônico do check-in — o contrato entre extrair e carregar.

Todo adaptador de `extrair/` devolve ESTE formato, venha o dado do Flow, de um
CRM direto, de uma planilha ou de um MCP de conversa. O `carregar/` só conhece
este formato. É isso que permite trocar RD Station por HubSpot, ou uma planilha
pelo Flow, sem reescrever o check-in.

Regras que valem para qualquer fonte:

1. **Data é sempre local do cliente (America/Sao_Paulo), em ISO `YYYY-MM-DD`.**
   Quem converte é o adaptador. O check-in nunca recebe UTC.
2. **Dinheiro é float em reais**, sem símbolo e sem string.
3. **Atribuição é explícita.** Todo negócio e todo contato carrega
   `atribuicao = {"agencia": bool, "marca": "<como foi identificado>"}`.
   Número sem regra declarada não entra em check-in.
4. **Nada é inventado.** Campo que a fonte não tem vem `None` — e o bloco que
   dependia dele diz "não medido", em vez de estimar.
"""
import datetime
import json

ESQUEMA = "checkin-ropre/canonico/1.0"

# Cada entidade e os campos que o carregar/ sabe ler.
CAMPOS = {
    # Negócio/oportunidade/deal — a unidade de venda em qualquer CRM.
    "negocios": {
        "id": "identificador na fonte",
        "criado_em": "YYYY-MM-DD",
        "fechado_em": "YYYY-MM-DD ou None enquanto aberto",
        "status": "ganho | perdido | aberto",
        "valor": "float em reais",
        "funil": "nome do pipeline/funil na fonte",
        "etapa": "etapa atual",
        "tipo": "novo | recorrente",
        "motivo_perda": "texto da fonte ou None",
        "canal": "meta | google | linkedin | tiktok | organico | indicacao | outbound | None",
        "contato_id": "chave para juntar com contatos",
        "atribuicao": '{"agencia": bool, "marca": str}',
    },
    # Contato/lead.
    "contatos": {
        "id": "identificador na fonte",
        "criado_em": "YYYY-MM-DD",
        "origem": "texto cru da fonte, sem normalizar",
        "canal": "canal normalizado ou None",
        "uf": "sigla ou None",
        "atribuicao": '{"agencia": bool, "marca": str}',
    },
    # Mídia paga, um registro por dia e canal (Google, Meta, LinkedIn, TikTok...).
    "midia": {
        "dia": "YYYY-MM-DD",
        "canal": "meta | google | linkedin | tiktok | ...",
        "campanha": "nome ou None",
        "investimento": "float em reais, valor bruto pago à plataforma",
        "impressoes": "int ou None",
        "cliques": "int ou None",
        "leads": "int ou None",
    },
    # Conversas (Chatwoot, WhatsApp) — viram pendências no bloco de Entregas.
    "conversas": {
        "dia": "YYYY-MM-DD",
        "canal": "whatsapp | chat | ...",
        "status": "aberta | resolvida | ...",
        "assunto": "resumo curto",
        "pendencia": "texto da pendência aberta, ou None",
    },
    # Calls com o cliente (transcrição via MCP) — viram acordos e próximos passos.
    "calls": {
        "dia": "YYYY-MM-DD",
        "titulo": "nome da reunião",
        "acordos": "lista de textos: o que ficou combinado",
        "pendencias": "lista de textos: o que ficou pendente e de quem",
        "riscos": "lista de textos: risco levantado na call",
    },
}

ENTIDADES = list(CAMPOS)


def vazio(fonte, cliente, periodo_bruto=None):
    """Esqueleto do modelo canônico. `fonte` identifica o adaptador que produziu."""
    return {
        "esquema": ESQUEMA,
        "fonte": fonte,
        "cliente": cliente,
        "extraido_em": datetime.date.today().isoformat(),
        "periodo_bruto": periodo_bruto,   # janela que a extração cobre, para o check-in não pedir o que não veio
        "negocios": [],
        "contatos": [],
        "midia": [],
        "conversas": [],
        "calls": [],
        "avisos": [],                      # o que a fonte não entregou; sai impresso no check-in
    }


def juntar(*pacotes):
    """Une pacotes canônicos de fontes diferentes (CRM + mídia + conversas + calls)."""
    if not pacotes:
        raise ValueError("nada para juntar")
    base = vazio(fonte=" + ".join(sorted({p.get("fonte", "?") for p in pacotes})),
                 cliente=pacotes[0].get("cliente"))
    janelas = []
    for p in pacotes:
        conferir(p)
        for ent in ENTIDADES:
            base[ent].extend(p.get(ent) or [])
        base["avisos"].extend(p.get("avisos") or [])
        if p.get("periodo_bruto"):
            janelas.append(p["periodo_bruto"])
    if janelas:
        base["periodo_bruto"] = {"de": min(j["de"] for j in janelas), "ate": max(j["ate"] for j in janelas)}
    return base


def conferir(pacote):
    """Valida o mínimo. Erra cedo e com o nome do campo, em vez de gerar check-in torto."""
    if pacote.get("esquema") != ESQUEMA:
        raise ValueError(f"esquema desconhecido: {pacote.get('esquema')!r}; esperado {ESQUEMA!r}")
    for ent in ENTIDADES:
        for i, reg in enumerate(pacote.get(ent) or []):
            if not isinstance(reg, dict):
                raise ValueError(f"{ent}[{i}] não é objeto")
            for campo in ("criado_em", "dia"):
                if campo in reg and reg[campo] is not None:
                    _conferir_data(reg[campo], f"{ent}[{i}].{campo}")
            if ent in ("negocios", "contatos"):
                a = reg.get("atribuicao")
                if not isinstance(a, dict) or "agencia" not in a:
                    raise ValueError(f"{ent}[{i}] sem atribuicao.agencia — a regra precisa viajar com o dado")
            if ent == "negocios":
                if reg.get("status") not in ("ganho", "perdido", "aberto"):
                    raise ValueError(f"negocios[{i}].status inválido: {reg.get('status')!r}")
                if reg.get("tipo") not in ("novo", "recorrente"):
                    raise ValueError(f"negocios[{i}].tipo inválido: {reg.get('tipo')!r}")
    return True


def _conferir_data(valor, onde):
    try:
        datetime.date.fromisoformat(str(valor))
    except ValueError:
        raise ValueError(f"{onde}: data fora do formato YYYY-MM-DD: {valor!r}")


def gravar(pacote, caminho):
    conferir(pacote)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(pacote, f, ensure_ascii=False)
    return caminho


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        pacote = json.load(f)
    conferir(pacote)
    return pacote


# ----------------------------------------------------------------- períodos

def periodo(referencia, cadencia, fim=None):
    """Janela do check-in.

    cadencia = 'quinzenal' | 'mensal' | 'quarter'
    referencia = data dentro do período desejado (YYYY-MM-DD)
    fim = corta o período (para check-in parcial, ex.: dia 21 do mês corrente)
    """
    d = datetime.date.fromisoformat(referencia)
    if cadencia == "quinzenal":
        de = d.replace(day=1) if d.day <= 15 else d.replace(day=16)
        ate = d.replace(day=15) if d.day <= 15 else _fim_do_mes(d)
        rotulo = f"{'1ª' if d.day <= 15 else '2ª'} quinzena de {_mes_extenso(d)}"
    elif cadencia == "mensal":
        de, ate = d.replace(day=1), _fim_do_mes(d)
        rotulo = _mes_extenso(d).capitalize()
    elif cadencia == "quarter":
        q = (d.month - 1) // 3
        de = datetime.date(d.year, q * 3 + 1, 1)
        ate = _fim_do_mes(datetime.date(d.year, q * 3 + 3, 1))
        rotulo = f"Q{q + 1} {d.year}"
    else:
        raise ValueError(f"cadência desconhecida: {cadencia!r}")
    if fim:
        limite = datetime.date.fromisoformat(fim)
        if limite < ate:
            ate, parcial = limite, True
        else:
            parcial = False
    else:
        parcial = ate > datetime.date.today()
        if parcial:
            ate = datetime.date.today()
    return {"cadencia": cadencia, "rotulo": rotulo, "de": de.isoformat(), "ate": ate.isoformat(), "parcial": parcial}


def periodo_anterior(p):
    """O período imediatamente anterior, do mesmo tamanho — é contra ele que o check-in compara."""
    de = datetime.date.fromisoformat(p["de"])
    if p["cadencia"] == "quinzenal":
        ref = (de - datetime.timedelta(days=1))
        anterior = periodo(ref.isoformat(), "quinzenal", fim=(de - datetime.timedelta(days=1)).isoformat())
    elif p["cadencia"] == "mensal":
        ref = de - datetime.timedelta(days=1)
        anterior = periodo(ref.isoformat(), "mensal")
    else:
        ref = de - datetime.timedelta(days=1)
        anterior = periodo(ref.isoformat(), "quarter")
    return anterior


def dentro(dia, p):
    return dia is not None and p["de"] <= str(dia) <= p["ate"]


def _fim_do_mes(d):
    if d.month == 12:
        return d.replace(day=31)
    return d.replace(month=d.month + 1, day=1) - datetime.timedelta(days=1)


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _mes_extenso(d):
    return f"{MESES[d.month - 1]} de {d.year}"
