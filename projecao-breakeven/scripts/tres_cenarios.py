#!/usr/bin/env python3
"""
tres_cenarios.py — roda o piloto nos três cenários e monta uma planilha só, com uma aba por cenário.

  Pessimista  taxas atuais, sem rampa (nada melhora)
  Desejado    rampa até a mediana do período comparável (o plano; é o compromisso)
  Otimista    rampa até o melhor mês fechado do período, ou o benchmark de --alvo quando ele é maior

Os três usam o mesmo histórico e as mesmas premissas confirmadas (fee, verba, margem, fixadas, ciclo, sazonalidade);
só o alvo da rampa muda. Depois escreve o texto da thread de aprovação (aprovacao.py) e põe a restrição mapeada
no topo da aba Premissas de cada cenário.

Uso (os argumentos do piloto e do gerador vão como string, iguais aos de sempre, sem --out/--cenario/--premissas):
  python3 tres_cenarios.py --cliente "indústria química B2B" --out indústria química B2B.xlsx \
      --piloto "--fonte indicadores.csv --modelo inside_sales --fee 2250 --midia 2500 --margem 0.30 --mes-alvo 8 ..." \
      --gerador "--modelo inside_sales --inicio-contrato maio/2026 --legado legado.json --obs '...'" \
      --restricao "recompra não é medida"
"""
import argparse, json, os, shlex, subprocess, sys, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
PILOTO = os.path.join(AQUI, "breakeven_pilot.py")
GERADOR = os.path.join(AQUI, "..", "gerador", "build_workbook.py")
APROV = os.path.join(AQUI, "aprovacao.py")
BREAKEVEN = os.path.join(AQUI, "cenario_breakeven.py")
CENARIOS = ["pessimista", "desejado", "otimista"]


def rodar(cmd):
    r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"falhou: {' '.join(cmd[:2])}\n{r.stderr[-2000:]}")
    return r.stdout


def tirar(args, flag):
    """Remove `flag VALOR` da lista de argumentos e devolve (valor, resto)."""
    if flag not in args:
        return None, args
    i = args.index(flag)
    return args[i + 1], args[:i] + args[i + 2:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--piloto", required=True, help="argumentos do modo projetar do piloto, numa string")
    ap.add_argument("--gerador", required=True, help="argumentos do gerador, numa string (sem --premissas, --out, --extra)")
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--out", required=True, help="xlsx final")
    ap.add_argument("--restricao", action="append", default=[], help="lacuna ou restrição mapeada pelo usuário (vai para a thread e para o topo das Premissas)")
    ap.add_argument("--prefixo", default="premissas", help="prefixo dos JSONs gerados (premissas_<cenario>.json)")
    ap.add_argument("--cenario-extra", action="append", default=[],
                    metavar='"Nome|args do piloto[|metodologia.json[|args sem legado[|metodologia sem legado.json]]]"',
                    help="aba a mais depois do otimista (ex.: cenário-meta com recompra): roda o piloto com os argumentos base + estes "
                         "(os repetidos valem os daqui, ex.: --horizonte 18), no cenário desejado. Com --sem-legado, os campos 4 e 5 "
                         "valem para a leitura sem legado (vazios = os mesmos da leitura com legado)")
    ap.add_argument("--sem-legado", metavar="ARGS",
                    help="monta também a leitura SEM LEGADO, na frente: os mesmos cenários começando no mês seguinte ao último fechado, "
                         "sem --inicio e com acumulado inicial zero, mais estes argumentos (ex.: \"--horizonte 3 --mes-alvo 3\"). "
                         "As abas viram '<Cenário> sem legado' e '<Cenário> com legado'")
    ap.add_argument("--sem-breakeven", action="store_true",
                    help="não monta o cenário Breakeven (padrão: monta sempre — funil de mercado onde o cliente está abaixo + verba em degraus + recompra)")
    ap.add_argument("--mercado", help="arquivo de nível de mercado por alavanca (padrão: referencias/mercado_alavancas.json)")
    ap.add_argument("--setor", help="setor dentro do arquivo de mercado (padrão: o do modelo)")
    a = ap.parse_args()

    pil = shlex.split(a.piloto)
    for proibido in ("--out", "--cenario"):
        if proibido in pil: sys.exit(f"--piloto não leva {proibido}: o script define um por cenário")
    ger = shlex.split(a.gerador)
    for proibido in ("--premissas", "--out", "--extra", "--aba-principal", "--ordem", "--cenario"):
        if proibido in ger: sys.exit(f"--gerador não leva {proibido}: o script define")
    met_user, ger = tirar(ger, "--metodologia-extra")
    precisa_vocab = lambda: any((json.load(open(x[1], encoding="utf-8"))["premissas_confirmadas"].get("recorrencia")) for x in abas)
    ini_cl = None
    if a.sem_legado is not None:   # a principal passa a ser a leitura sem legado: o Mês 1 com legado vai aba por aba
        ini_cl, ger = tirar(ger, "--inicio-contrato")
        _, pil_sl = tirar(pil, "--inicio")
        _, pil_sl = tirar(pil_sl, "--acumulado-inicial")
        pil_sl += ["--acumulado-inicial", "0"] + shlex.split(a.sem_legado)

    def slug(t):
        return ''.join(ch if ch.isalnum() else '_' for ch in unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode())

    # leituras: (sufixo do nome da aba, argumentos do piloto, Mês 1 da aba no gerador, campos do cenário-extra)
    leituras = ([(" sem legado", pil_sl, "-", (3, 4)), (" com legado", pil, ini_cl or "", (1, 2))] if a.sem_legado is not None
                else [("", pil, "", (1, 2))])
    abas = []   # (nome da aba, arquivo, metodologia própria ou "", Mês 1 da aba)
    be_resumos, be_mets = [], []
    for suf, args_p, ini, (ia, im) in leituras:
        for c in CENARIOS:
            arq = f"{a.prefixo}_{c}{slug(suf)}.json"
            rodar([PILOTO, "projetar", *args_p, "--cenario", c, "--out", arq])
            abas.append((c.capitalize() + suf, arq, "", ini))
        if not a.sem_breakeven:   # o cenário que bate, sempre
            arq = f"{a.prefixo}_breakeven{slug(suf)}.json"; met_be = f"metodologia_breakeven{slug(suf)}.json"
            cmd_be = [BREAKEVEN, "--base", f"{a.prefixo}_desejado{slug(suf)}.json", "--piloto", shlex.join(args_p),
                      "--out", arq, "--metodologia", met_be, "--rotulo", suf.strip()]
            if a.mercado: cmd_be += ["--mercado", a.mercado]
            if a.setor: cmd_be += ["--setor", a.setor]
            # cada leitura procura a própria verba: com legado, o déficit herdado pede mais para o acumulado zerar
            res_be = json.loads(rodar(cmd_be).strip().splitlines()[-1])
            be_resumos.append(res_be); be_mets.append(met_be)
            abas.append(("Breakeven" + suf, arq, met_be, ini))
        for ce in a.cenario_extra:
            partes = ce.split("|") + [""] * 5
            nome = partes[0].strip()
            mais = partes[ia] if partes[ia].strip() or ia == 1 else partes[1]
            met_ce = (partes[im] if partes[im].strip() or im == 2 else partes[2]).strip()
            arq = f"{a.prefixo}_{slug(nome + suf)}.json"
            rodar([PILOTO, "projetar", *args_p, *shlex.split(mais), "--out", arq])
            abas.append((nome + suf, arq, met_ce, ini))

    principal = abas[1]   # o Desejado da primeira leitura
    suf0 = leituras[0][0]
    aprov = [APROV, "--desejado", abas[1][1], "--pessimista", abas[0][1], "--otimista", abas[2][1], "--sufixo", suf0,
             "--cliente", a.cliente, "--out-md", "aprovacao.md", "--out-json", "restricao_topo.json"]
    for r in a.restricao:
        aprov += ["--restricao", r]
    for nome, arq, _m, _i in abas[3:]:
        aprov += ["--extra", f"{nome}={arq}"]
    if be_mets:
        aprov += ["--breakeven", be_mets[0]]
    texto = rodar(aprov)

    topo = json.load(open("restricao_topo.json", encoding="utf-8"))
    base = json.load(open(met_user, encoding="utf-8")) if met_user else {}
    met = {**base, "topo": topo["topo"] + list(base.get("topo") or [])}
    json.dump(met, open("metodologia_cenarios.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cmd = [GERADOR, "--premissas", principal[1], *ger, "--cliente", a.cliente, "--out", a.out,
           "--cenario", principal[0], "--aba-principal", principal[0], "--metodologia-extra", "metodologia_cenarios.json",
           "--ordem", ",".join(x[0] for x in abas)]
    for nome, arq, met_ce, ini in [x for x in abas if x is not principal]:
        met_arq = "metodologia_cenarios.json"
        if met_ce:   # a explicação própria do cenário entra depois da restrição e dos cenários
            proprio = json.load(open(met_ce, encoding="utf-8"))
            met_arq = f"metodologia_{slug(nome)}.json"
            json.dump({**met, "topo": met["topo"] + list(proprio.get("topo") or []), "secoes": list(proprio.get("secoes") or []) + list(met.get("secoes") or [])},
                      open(met_arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        cmd += ["--extra", f"{arq}|{nome}|{nome}|{met_arq}|{ini}"]
    if "--vocabulario" not in cmd and precisa_vocab():   # recompra modelada com o motor da assinatura fala de cliente, não de assinante
        cmd += ["--vocabulario", "recompra"]
    saida = rodar(cmd)
    print(texto)
    print(saida.strip())


if __name__ == "__main__":
    main()
