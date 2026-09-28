# -*- coding: utf-8 -*-
"""Formatação brasileira, num lugar só — para deck e documento dizerem o mesmo número igual."""

NAO_MEDIDO = "não medido"


def moeda(v, casas=2):
    if v is None:
        return NAO_MEDIDO
    sinal = "− " if v < 0 else ""
    s = f"{abs(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {s}"


def moeda_curta(v):
    """Para cartão de KPI: R$ 115,4 mil / R$ 1,2 mi."""
    if v is None:
        return NAO_MEDIDO
    if abs(v) >= 1_000_000:
        return f"R$ {v/1_000_000:.1f} mi".replace(".", ",")
    if abs(v) >= 1_000:
        return f"R$ {v/1_000:.1f} mil".replace(".", ",")
    return moeda(v, 0)


def numero(v, casas=0):
    if v is None:
        return NAO_MEDIDO
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def percentual(v, casas=0):
    if v is None:
        return NAO_MEDIDO
    return f"{v*100:.{casas}f}%".replace(".", ",")


def variacao(v, casas=0):
    """Variação com sinal. None quando não há base de comparação."""
    if v is None:
        return "—"
    return f"{'+' if v >= 0 else '−'}{abs(v)*100:.{casas}f}%".replace(".", ",")


def valor(v, formato):
    return {"moeda": moeda, "percentual": percentual, "numero": lambda x: numero(x, 1)}.get(formato, numero)(v)


def mes_curto(iso_mes):
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    ano, mes = iso_mes.split("-")[:2]
    return f"{meses[int(mes)-1]}/{ano[2:]}"
