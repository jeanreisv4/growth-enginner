#!/usr/bin/env python3
"""Microsoft Clarity pela Data Export API: coleta econômica (10 chamadas/projeto/dia) e resumo com alertas.

  python3 scripts/clarity.py coletar --chave ~/.config/sprint-growth/<c>_clarity.key --out clientes/<c>/clarity [--dias 3]
  python3 scripts/clarity.py resumo  --out clientes/<c>/clarity [--min-sessoes 30]

Limites da API (learn.microsoft.com/clarity/setup-and-installation/clarity-data-export-api):
- 10 chamadas por projeto por dia; só os últimos 1, 2 ou 3 dias (numOfDays); até 3 dimensões; até 1.000 linhas,
  sem paginação; horário em UTC. Token: Configurações → Exportação de dados → Gerar token (só admin do projeto).
- Por isso a coleta roda UMA vez por dia durante a sprint (primeira com --dias 3, depois --dias 1) e acumula em
  <out>/raw/. O plano padrão gasta 6 chamadas e deixa 4 de folga; chamada já feita hoje não se repete.
- A documentação só mostra os campos da métrica Traffic (totalSessionCount, totalBotSessionCount,
  distantUserCount, PagesPerSessionPercentage). Os campos das métricas de fricção são lidos pelo padrão do nome
  (…Percentage) e todo campo não reconhecido aparece no resumo: confira na primeira coleta real.

Alertas:
  C1 sessões de robô acima de 30% do total (tráfego pago comprando robô ou filtro de bot desligado)
  C2 página com clique de raiva em 5%+ das sessões
  C3 página com clique morto em 10%+ das sessões (elemento que parece botão e não é)
  C4 página com volta rápida em 10%+ das sessões (promessa do anúncio × página)
  C5 página com erro de script em 5%+ das sessões (formulário pode estar quebrado)
  C6 rolagem no celular abaixo de 70% da rolagem no computador (conteúdo e formulário abaixo da dobra)
"""
import argparse, glob, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
LIMITE_DIA = 10
PLANO = [("total", []), ("url", ["URL"]), ("dispositivo", ["Device"]), ("canal", ["Channel"]),
         ("url_dispositivo", ["URL", "Device"]), ("origem", ["Source", "Medium", "Campaign"])]
DIMENSOES = {"Browser", "Device", "Country/Region", "Country", "OS", "Source", "Medium", "Campaign", "Channel", "URL"}
FRICCAO = {"deadclickcount": "clique_morto", "rageclickcount": "clique_raiva", "quickbackclick": "volta_rapida",
           "excessivescroll": "rolagem_excessiva", "scripterrorcount": "erro_script", "errorclickcount": "clique_erro"}
TRAFEGO = {"totalsessioncount": "sessoes", "totalbotsessioncount": "sessoes_robo", "distantusercount": "usuarios",
           "pagespersessionpercentage": "paginas_por_sessao"}


def norm(nome):
    return re.sub(r"[^a-z]", "", str(nome).lower())


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def hoje():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------- coleta ----------

def chamar(token, dias, dims):
    q = {"numOfDays": str(dias)}
    for i, d in enumerate(dims, 1):
        q[f"dimension{i}"] = d
    r = urllib.request.Request(API + "?" + urllib.parse.urlencode(q),
                               headers={"Authorization": "Bearer " + token, "Content-Type": "application/json",
                                        "User-Agent": "curl/8.7.1"})
    return json.load(urllib.request.urlopen(r, timeout=120))


def coletar(chave, out, dias, forcar=False):
    token = open(os.path.expanduser(chave)).read().strip()
    os.makedirs(os.path.join(out, "raw"), exist_ok=True)
    cont_arq = os.path.join(out, "chamadas.json")
    cont = json.load(open(cont_arq)) if os.path.exists(cont_arq) else {}
    dia = hoje()
    for nome, dims in PLANO:
        destino = os.path.join(out, "raw", f"{dia}_{nome}.json")
        if os.path.exists(destino) and not forcar:
            print(f"{nome}: já coletado hoje ({dia}), pulando")
            continue
        if cont.get(dia, 0) >= LIMITE_DIA:
            print(f"Limite de {LIMITE_DIA} chamadas de hoje atingido; o resto fica para amanhã.")
            break
        try:
            resp = chamar(token, dias, dims)
        except urllib.error.HTTPError as e:
            cont[dia] = cont.get(dia, 0) + 1
            json.dump(cont, open(cont_arq, "w"))
            if e.code == 429:
                print("429: a cota diária do projeto acabou (conta também o que outra ferramenta usou hoje).")
                break
            sys.exit(f"{nome}: HTTP {e.code} ({'token inválido ou vencido' if e.code in (401, 403) else 'parâmetro'})")
        cont[dia] = cont.get(dia, 0) + 1
        json.dump(cont, open(cont_arq, "w"))
        json.dump({"coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "dias": dias,
                   "dimensoes": dims, "resposta": resp}, open(destino, "w"), ensure_ascii=False)
        print(f"{nome}: ok ({len(resp)} métricas)")
        time.sleep(1)
    print(f"Chamadas hoje ({dia}, UTC): {cont.get(dia, 0)} de {LIMITE_DIA}")


# ---------- leitura ----------

def linhas(resposta):
    """Resposta da API → {chave_dimensões: {métrica: valor}} + campos não reconhecidos."""
    tab, estranhos = {}, set()
    for m in resposta:
        met = norm(m.get("metricName", ""))
        for row in m.get("information") or []:
            dims = tuple(sorted((k, str(v)) for k, v in row.items() if k in DIMENSOES))
            reg = tab.setdefault(dims, {})
            for campo, v in row.items():
                if campo in DIMENSOES:
                    continue
                c, x = norm(campo), num(v)
                if x is None:
                    continue
                if met == "traffic" and c in TRAFEGO:
                    reg[TRAFEGO[c]] = x
                elif met in FRICCAO and "percentage" in c and "without" not in c:
                    reg[FRICCAO[met]] = x
                elif met in FRICCAO and c in ("sessionscount", "subtotal"):
                    reg.setdefault(FRICCAO[met] + "_sessoes", x)
                elif met == "scrolldepth" and ("scroll" in c or "average" in c):
                    reg["rolagem"] = x
                elif met == "engagementtime" and "active" in c:
                    reg["tempo_ativo"] = x
                elif met == "engagementtime" and "total" in c:
                    reg["tempo_total"] = x
                elif met in ("traffic", "scrolldepth", "engagementtime") or met in FRICCAO:
                    estranhos.add(f"{m.get('metricName')}.{campo}")
    return tab, estranhos


def acumular(out):
    """Soma as coletas diárias por plano: sessões somam; percentuais e médias ponderam pelas sessões."""
    planos, estranhos, datas = {}, set(), []
    for arq in sorted(glob.glob(os.path.join(out, "raw", "*.json"))):
        snap = json.load(open(arq, encoding="utf-8"))
        nome = os.path.basename(arq)[11:-5]
        datas.append((snap["coletado_em"], snap["dias"]))
        tab, e = linhas(snap["resposta"])
        estranhos |= e
        dest = planos.setdefault(nome, {})
        for dims, reg in tab.items():
            acc = dest.setdefault(dims, {"_peso": 0.0})
            peso = reg.get("sessoes") or 1.0
            for k, v in reg.items():
                if k in ("sessoes", "sessoes_robo", "usuarios") or k.endswith("_sessoes"):
                    acc[k] = acc.get(k, 0) + v
                else:
                    acc[k + "_soma"] = acc.get(k + "_soma", 0) + v * peso
                    acc[k + "_peso"] = acc.get(k + "_peso", 0) + peso
    final = {}
    for nome, tab in planos.items():
        final[nome] = {}
        for dims, acc in tab.items():
            reg = {k: v for k, v in acc.items() if not k.endswith(("_soma", "_peso")) and k != "_peso"}
            for k in [k[:-5] for k in acc if k.endswith("_soma")]:
                reg[k] = acc[k + "_soma"] / acc[k + "_peso"] if acc[k + "_peso"] else None
            final[nome][dims] = reg
    return final, sorted(estranhos), datas


def alertas(planos, min_sessoes=30):
    out = []
    tot = next(iter(planos.get("total", {}).values()), {})
    if tot.get("sessoes") and tot.get("sessoes_robo") is not None and tot["sessoes_robo"] / tot["sessoes"] > 0.30:
        out.append(("C1", f"{tot['sessoes_robo'] / tot['sessoes']:.0%} das sessões são de robô "
                          f"({tot['sessoes_robo']:.0f} de {tot['sessoes']:.0f})"))
    regras = [("C2", "clique_raiva", 5, "clique de raiva"), ("C3", "clique_morto", 10, "clique morto"),
              ("C4", "volta_rapida", 10, "volta rápida"), ("C5", "erro_script", 5, "erro de script")]
    for dims, reg in sorted(planos.get("url", {}).items()):
        url = dict(dims).get("URL", "?")
        if (reg.get("sessoes") or 0) < min_sessoes:
            continue
        for cod, k, lim, rotulo in regras:
            if reg.get(k) is not None and reg[k] >= lim:
                out.append((cod, f"{url}: {rotulo} em {reg[k]:.1f}% das sessões ({reg['sessoes']:.0f} sessões)"))
    disp = {dict(d).get("Device", "").lower(): r for d, r in planos.get("dispositivo", {}).items()}
    cel = disp.get("mobile", {}).get("rolagem")
    pc = (disp.get("pc") or disp.get("desktop") or {}).get("rolagem")
    if cel is not None and pc and cel < 0.7 * pc:
        out.append(("C6", f"rolagem média no celular {cel:.0f}% × computador {pc:.0f}%"))
    return out


def resumo(out, min_sessoes):
    planos, estranhos, datas = acumular(out)
    if not planos:
        sys.exit("Nenhuma coleta em " + os.path.join(out, "raw") + ": rode `coletar` primeiro.")
    al = alertas(planos, min_sessoes)
    L = ["# Clarity: resumo", "",
         f"Coletas: {len(datas)} arquivos, de {datas[0][0][:10]} a {datas[-1][0][:10]} (UTC). "
         "Cada coleta cobre as últimas 24–72 h; coletas de dias seguidos com --dias 1 não se sobrepõem.", ""]
    L += ["## Alertas", ""] + ([f"- **{c}** {t}" for c, t in al] or ["- nenhum"])
    tot = next(iter(planos.get("total", {}).values()), {})
    if tot:
        L += ["", "## Total", "", "| Métrica | Valor |", "| --- | --- |"]
        L += [f"| {k} | {v:.1f} |" if isinstance(v, float) else f"| {k} | {v} |" for k, v in sorted(tot.items()) if v is not None]
    cols = ["sessoes", "clique_raiva", "clique_morto", "volta_rapida", "erro_script", "rolagem", "tempo_ativo"]
    for nome, titulo in (("url", "Por página"), ("dispositivo", "Por dispositivo"), ("canal", "Por canal")):
        if nome not in planos:
            continue
        L += ["", f"## {titulo}", "", "| " + " | ".join(["Dimensão"] + cols) + " |", "|" + " --- |" * (len(cols) + 1)]
        for dims, reg in sorted(planos[nome].items(), key=lambda x: -(x[1].get("sessoes") or 0))[:40]:
            vals = [f"{reg[c]:.1f}" if isinstance(reg.get(c), float) else "—" for c in cols]
            L.append("| " + " · ".join(v for _, v in dims) + " | " + " | ".join(vals) + " |")
    if estranhos:
        L += ["", "## Campos não reconhecidos (conferir o nome e ajustar `linhas()`)", ""] + [f"- {e}" for e in estranhos]
    open(os.path.join(out, "clarity_resumo.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    json.dump({"alertas": al, "campos_nao_reconhecidos": estranhos, "coletas": datas,
               "planos": {n: [{"dimensoes": dict(d), **r} for d, r in t.items()] for n, t in planos.items()}},
              open(os.path.join(out, "clarity_resumo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(al)} alertas; resumo em {os.path.join(out, 'clarity_resumo.md')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["coletar", "resumo"])
    ap.add_argument("--chave", help="arquivo com o token do projeto (fora do repositório)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dias", type=int, default=1, choices=[1, 2, 3])
    ap.add_argument("--forcar", action="store_true", help="refaz chamada já feita hoje (gasta cota)")
    ap.add_argument("--min-sessoes", type=int, default=30)
    a = ap.parse_args()
    if a.acao == "coletar":
        if not a.chave:
            sys.exit("--chave é obrigatório para coletar")
        coletar(a.chave, a.out, a.dias, a.forcar)
    else:
        resumo(a.out, a.min_sessoes)


if __name__ == "__main__":
    main()
