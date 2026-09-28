#!/usr/bin/env python3
"""Confere se as tags de conversão disparam com o rótulo certo, sem criar lead e sem sujar dados.

  uvx --with playwright python scripts/teste_disparo.py --url https://site.com.br/ \
      --evento '{"event":"generate_lead","mql_eligible":"true"}' --evento '{"event":"mql"}' \
      --rotulo AbCdEfGhIjKlMnOpQr-="00.2 Lead" --rotulo ZyXwVuTsRqPoNmLkJi-="00.4 MQL"

Abre a página num Chrome sem janela, bloqueia GA4, Meta, Stape e Clarity (para não gerar evento falso),
empurra os eventos no dataLayer e lista os hits do Google Ads com o rótulo de cada um. O hit sai sem gclid,
então o Google não atribui a nenhuma campanha. Nenhum formulário é enviado.
"""
import argparse, json, re
from playwright.sync_api import sync_playwright

BLOQUEAR = re.compile(r"facebook|fbevents|stape\.io|google-analytics\.com|analytics\.google\.com|/g/collect|clarity")
ADS = re.compile(r"googleadservices|/pagead/|doubleclick|google\.com/ccm")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--evento", action="append", default=[], help="JSON do push no dataLayer (repetível)")
    ap.add_argument("--rotulo", action="append", default=[], help="rotulo=nome (repetível)")
    a = ap.parse_args()
    rotulos = dict(r.split("=", 1) for r in a.rotulo)
    hits, bloqueados = [], [0]
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True)
        pg = nav.new_page()

        def rota(route):
            if BLOQUEAR.search(route.request.url):
                bloqueados[0] += 1
                return route.abort()
            return route.continue_()

        pg.route("**/*", rota)
        pg.on("request", lambda r: hits.append(r.url) if ADS.search(r.url) else None)
        pg.goto(a.url, wait_until="load", timeout=60000)
        pg.wait_for_timeout(6000)
        gtm = pg.evaluate("() => window.google_tag_manager ? Object.keys(window.google_tag_manager).filter(k => k.startsWith('GTM-')) : []")
        antes = len(hits)
        for ev in a.evento:
            pg.evaluate("(e) => { window.dataLayer = window.dataLayer || []; window.dataLayer.push(e); }", json.loads(ev))
        pg.wait_for_timeout(5000)
        nav.close()
    print(f"GTM carregado: {gtm or 'NÃO (ver banner de cookies / construtor de página)'}")
    print(f"hits do Google Ads antes dos eventos: {antes} · depois: {len(hits) - antes} · bloqueados: {bloqueados[0]}")
    achados = set()
    for u in hits[antes:]:
        nome = next((n for k, n in rotulos.items() if k in u), None)
        rot = re.search(r"label=([A-Za-z0-9_\-]+)", u)
        achados.add(nome or (rot.group(1) if rot else "?"))
        print(f"  [{nome or (rot.group(1) if rot else '?')}] {u[:120]}")
    for k, n in rotulos.items():
        print(f"{'OK ' if n in achados else 'FALTOU'} {n} ({k})")


if __name__ == "__main__":
    main()
