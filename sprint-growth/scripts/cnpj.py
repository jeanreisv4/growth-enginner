#!/usr/bin/env python3
"""Qualificação de leads B2B pelo CNPJ informado no formulário (base pública da Receita via BrasilAPI).

  python3 scripts/cnpj.py --entrada leads.json --campo cnpj --out clientes/<c>/cnpj \
      [--cnae-alvo 41,42,43,7111,7112] [--agrupar anuncio,obras]

Entrada: lista JSON de leads (uma pessoa por item, já sem teste e sem duplicado — ver leads.pessoas).
Saída: <out>/cnpj_qualificacao.json e <out>/cnpj_tabela.md (tabela pronta para o documento).

Classes:
  Qualificado    CNPJ ativo, CNAE principal no setor-alvo, não MEI
  Parcial        MEI do setor, ou setor só em CNAE secundário
  Fora do perfil CPF no lugar do CNPJ, campo com outra coisa, CNPJ inválido/baixado/inexistente, fora do setor

Lições (SaaS de diário de obra, 28/09/2026): 12 de 57 leads do form do Meta não tinham CNPJ de verdade; o anúncio
mudou a taxa de qualificação de 27% para 62%; "mais de 10 obras" foi a resposta menos qualificada. A Receita põe o
CPF do titular no nome do MEI: `limpa_nome` tira antes de publicar.
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.request
from collections import Counter, defaultdict

ALVO_PADRAO = ("41", "42", "43", "7111", "7112")


def digitos(bruto):
    return re.sub(r"\D", "", str(bruto or ""))


def valida(cnpj):
    c = digitos(cnpj)
    if len(c) != 14 or len(set(c)) == 1:
        return False
    def dv(base, pesos):
        r = sum(int(a) * b for a, b in zip(base, pesos)) % 11
        return "0" if r < 2 else str(11 - r)
    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    return c[12] == dv(c[:12], p1) and c[13] == dv(c[:13], [6] + p1)


def tipo(bruto):
    d = digitos(bruto)
    return "CNPJ" if len(d) == 14 else "CPF" if len(d) == 11 else "outro"


def consulta(cnpj, tentativas=4):
    """Dados da Receita (BrasilAPI). None se não existe. Exige User-Agent (urllib padrão é recusado em algumas APIs)."""
    c = digitos(cnpj)
    for t in range(tentativas):
        try:
            r = urllib.request.Request(f"https://brasilapi.com.br/api/cnpj/v1/{c}", headers={"User-Agent": "curl/8.7.1"})
            return json.load(urllib.request.urlopen(r, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(5 * (t + 1))
        except Exception:
            time.sleep(5 * (t + 1))
    raise RuntimeError(f"BrasilAPI não respondeu para {c}")


def no_setor(cnae, alvo=ALVO_PADRAO):
    s = str(cnae or "").zfill(7)
    return any(s.startswith(a) for a in alvo)


def classifica(bruto, dados, alvo=ALVO_PADRAO):
    """-> (classe, motivo). `dados` = resposta da BrasilAPI, {} se não consultado, None se não encontrado."""
    t = tipo(bruto)
    if t == "CPF":
        return "Fora do perfil", "CPF no lugar do CNPJ"
    if t != "CNPJ":
        return "Fora do perfil", "sem CNPJ válido"
    if not valida(bruto):
        return "Fora do perfil", "CNPJ com dígito verificador inválido"
    if dados is None:
        return "Fora do perfil", "CNPJ não encontrado na Receita"
    sit = str(dados.get("descricao_situacao_cadastral") or "").upper()
    if sit != "ATIVA":
        return "Fora do perfil", f"CNPJ {sit.lower() or 'sem situação'}"
    mei = bool(dados.get("opcao_pelo_mei"))
    if no_setor(dados.get("cnae_fiscal"), alvo):
        return ("Parcial", "setor, MEI") if mei else ("Qualificado", "setor-alvo")
    sec = [s.get("codigo") if isinstance(s, dict) else s for s in dados.get("cnaes_secundarios") or []]
    if any(no_setor(s, alvo) for s in sec):
        return "Parcial", "setor só em CNAE secundário" + (" (MEI)" if mei else "")
    return "Fora do perfil", "fora do setor"


def limpa_nome(razao):
    """Tira o CPF que a Receita acrescenta ao nome do MEI (no fim ou no começo)."""
    r = re.sub(r"\s*\d{8,}\s*$", "", str(razao or ""))
    return re.sub(r"^\d{2}\.\d{3}\.\d{3}\s+", "", r).strip()


def fmt(cnpj):
    c = digitos(cnpj)
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}" if len(c) == 14 else c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", required=True)
    ap.add_argument("--campo", default="cnpj")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cnae-alvo", default=",".join(ALVO_PADRAO))
    ap.add_argument("--agrupar", default="", help="campos para cruzar com a classe (ex.: anuncio,obras)")
    a = ap.parse_args()
    alvo = tuple(x.strip() for x in a.cnae_alvo.split(",") if x.strip())
    leads = json.load(open(a.entrada))
    os.makedirs(a.out, exist_ok=True)
    cache = {}
    for x in leads:
        b = x.get(a.campo)
        d = {}
        if tipo(b) == "CNPJ" and valida(b):
            c = digitos(b)
            if c not in cache:
                cache[c] = consulta(c)
                time.sleep(1.2)
            d = cache[c]
        x["classe"], x["motivo"] = classifica(b, d, alvo)
        if d:
            x["receita"] = {"razao_social": limpa_nome(d.get("razao_social")), "cnae": f"{d.get('cnae_fiscal')} {d.get('cnae_fiscal_descricao') or ''}".strip(),
                            "porte": "MEI" if d.get("opcao_pelo_mei") else d.get("descricao_porte"), "uf": d.get("uf"),
                            "abertura": d.get("data_inicio_atividade"), "situacao": d.get("descricao_situacao_cadastral")}
    json.dump(leads, open(os.path.join(a.out, "cnpj_qualificacao.json"), "w"), ensure_ascii=False, indent=1)
    tot = Counter(x["classe"] for x in leads)
    linhas = ["| Classe | Leads | Parcela |", "| --- | --- | --- |"] + [f"| {k} | {tot[k]} | {tot[k]/len(leads):.0%} |" for k in ("Qualificado", "Parcial", "Fora do perfil")]
    for campo in [c for c in a.agrupar.split(",") if c]:
        g = defaultdict(Counter)
        for x in leads:
            g[str(x.get(campo))][x["classe"]] += 1
        linhas += ["", f"| {campo} | Leads | Qualificados | % |", "| --- | --- | --- | --- |"]
        for k, c in sorted(g.items(), key=lambda t: -sum(t[1].values())):
            n = sum(c.values()); linhas.append(f"| {k} | {n} | {c['Qualificado']} | {c['Qualificado']/n:.0%} |")
    open(os.path.join(a.out, "cnpj_tabela.md"), "w").write("\n".join(linhas) + "\n")
    print(dict(tot), "·", os.path.join(a.out, "cnpj_tabela.md"))


if __name__ == "__main__":
    main()
