"""Funções de leads que toda sprint usa: telefone BR, filtro de teste, canal e contagem por pessoa.

Lições embutidas:
- Telefone BR: comparar só os últimos dígitos casa pouco; tire o +55 e compare DDD + 8 dígitos finais,
  assim o 9 de celular (ausente em cadastro antigo) não separa a mesma pessoa.
- Lead de teste distorce funil pequeno: equipe da agência, e-mails de teste, empresa "teste" e os telefones
  da própria equipe do cliente. Os padrões ficam em clientes/<cliente>/config.json (lista `testes`).
- Canal vem de gclid/gbraid/wbraid (Google), fbclid ou utm_source numérico 1202... (Meta), referrer e utm_source.
"""
import re, unicodedata

TESTE_PADRAO = {
    "email": [r"@v4company\.", r"example\.com", r"teste\d*@", r"@teste"],
    "nome": [r"^teste\b", r"\bteste$", r"^test\b"],
    "empresa": [r"^teste", r"^v4( company)?$", r"^empresa( teste)?$", r"^xx+$", r"^aa+$", r"^asd"],
}


def telefone(bruto):
    """Chave canônica DDD + 8 dígitos finais, ou None."""
    d = re.sub(r"\D", "", str(bruto or ""))
    if d.startswith("55") and len(d) > 11:
        d = d[2:]
    return d[:2] + d[-8:] if len(d) >= 10 else None


def email(bruto):
    e = str(bruto or "").strip().lower()
    if "@" not in e:
        return None
    u, dom = e.split("@", 1)
    u = u.split("+")[0]
    if dom in ("gmail.com", "googlemail.com"):
        u = u.replace(".", "")
    return f"{u}@{dom}"


def _sem_acento(t):
    return unicodedata.normalize("NFD", str(t or "").lower()).encode("ascii", "ignore").decode()


def e_teste(nome="", email_="", empresa="", tel="", extra=None):
    """extra = {"telefones": ["98717742", ...], "nomes": [...], "emails": [...]} do config do cliente."""
    extra = extra or {}
    campos = {"nome": _sem_acento(nome), "email": _sem_acento(email_), "empresa": _sem_acento(empresa).strip()}
    for campo, padroes in TESTE_PADRAO.items():
        if any(re.search(p, campos[campo]) for p in padroes):
            return True
    t = re.sub(r"\D", "", str(tel or ""))
    if t and (len(set(t[-8:])) == 1 or any(t.endswith(x) for x in extra.get("telefones", []))):
        return True
    if any(n.lower() in campos["nome"] for n in extra.get("nomes", [])):
        return True
    if any(e.lower() in campos["email"] for e in extra.get("emails", [])):
        return True
    return False


def canal(meta):
    """meta: dict com page_url, referrer, utm_source, gclid, gbraid, wbraid, fbclid."""
    m = {k: str(v or "") for k, v in (meta or {}).items()}
    url, src, ref = m.get("page_url", ""), m.get("utm_source", "").lower(), m.get("referrer", "").lower()
    if m.get("gclid") or m.get("gbraid") or m.get("wbraid") or "utm_source=google" in url or src in ("google", "adwords"):
        return "Google Ads"
    if src.startswith("1202") or "utm_source=1202" in url or src in ("facebook", "fb", "meta", "paid_social"):
        return "Meta Ads"
    if m.get("fbclid") or any(x in ref for x in ("instagram", "facebook")) or src in ("ig", "instagram"):
        return "Meta orgânico"
    if "chatgpt" in url or "chatgpt" in src or "chatgpt" in ref:
        return "ChatGPT"
    if "google." in ref:
        return "Google orgânico"
    return "Direto ou sem origem"


def pessoas(registros, chave_tel="whatsapp", chave_email="email"):
    """Agrupa registros da mesma pessoa (telefone OU e-mail canônico). Devolve lista de grupos."""
    grupos, por_tel, por_mail = [], {}, {}
    for r in registros:
        t, e = telefone(r.get(chave_tel)), email(r.get(chave_email))
        g = por_tel.get(t) if t else None
        g = g if g is not None else (por_mail.get(e) if e else None)
        if g is None:
            g = len(grupos)
            grupos.append([])
        grupos[g].append(r)
        if t:
            por_tel[t] = g
        if e:
            por_mail[e] = g
    return grupos
