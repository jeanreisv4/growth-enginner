#!/usr/bin/env python3
"""Mostra o que um formulário enviaria (campos, UTM, gclid) SEM enviar: o POST é interceptado e abortado.

  uvx --with playwright python scripts/teste_formulario.py \
      --url "https://lp.exemplo.com.br/?utm_source=teste_claude&gclid=TESTE" \
      --form "#form-trial" --enviar "#botao-enviar" --interceptar n8n \
      --campo nome="TESTE TECNICO - IGNORAR" --campo whatsapp=11000000000 --campo email=teste@example.com \
      --selecao obras_simultaneas=2

Responde três perguntas: o GTM carregou? que campos ocultos existem? o POST leva UTM e gclid?
Na SaaS de diário de obra revelou que a GreatPages só carrega o GTM (e o script de atribuição) depois do aceite de cookies de
marketing: sem aceite, o formulário sai sem origem. Nenhum lead ou trial é criado.
"""
import argparse, re
from urllib.parse import parse_qs
from playwright.sync_api import sync_playwright

BLOQUEAR = re.compile(r"facebook|fbevents|stape\.io|google-analytics\.com|analytics\.google\.com|/g/collect|clarity|googleadservices|doubleclick")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--form", required=True, help="seletor do formulário")
    ap.add_argument("--enviar", required=True, help="seletor do botão de envio")
    ap.add_argument("--interceptar", required=True, help="trecho da URL do POST a interceptar (ex.: n8n, hooks)")
    ap.add_argument("--campo", action="append", default=[], help="nome=valor (repetível)")
    ap.add_argument("--selecao", action="append", default=[], help="nome=índice da opção (repetível)")
    a = ap.parse_args()
    capturado = {}
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = nav.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        pg = ctx.new_page()

        def rota(route):
            req = route.request
            if a.interceptar in req.url and req.method == "POST":
                capturado["url"], capturado["corpo"] = req.url, req.post_data or ""
                return route.abort()
            if BLOQUEAR.search(req.url):
                return route.abort()
            return route.continue_()

        pg.route("**/*", rota)
        pg.goto(a.url, wait_until="load", timeout=60000)
        pg.mouse.move(200, 300)
        pg.mouse.wheel(0, 1500)
        pg.wait_for_timeout(5000)
        estado = pg.evaluate("""(f) => ({
          gtm: window.google_tag_manager ? Object.keys(window.google_tag_manager).filter(k => k.startsWith('GTM-')) : [],
          consentimento: (window.GModalApproval && window.GModalApproval.preferencias) ? JSON.stringify(window.GModalApproval.preferencias()) : 'n/a',
          ocultos: Array.from(document.querySelectorAll(f + ' input[type=hidden]')).map(i => i.name + '=' + i.value)
        })""", a.form)
        for c in a.campo:
            n, v = c.split("=", 1)
            pg.fill(f"{a.form} [name={n}]", v)
        for s in a.selecao:
            n, i = s.split("=", 1)
            pg.select_option(f"{a.form} [name={n}]", index=int(i))
        pg.click(a.enviar)
        pg.wait_for_timeout(3000)
        nav.close()
    print("GTM carregado:", estado["gtm"] or "NÃO")
    print("consentimento (construtor de página):", estado["consentimento"])
    print("campos ocultos:", estado["ocultos"])
    if not capturado:
        print("POST NÃO interceptado: confira --interceptar e --enviar (ou a validação do formulário barrou).")
        return
    corpo = parse_qs(capturado["corpo"])
    print("POST para:", capturado["url"][:90])
    for k, v in sorted(corpo.items()):
        print(f"  {k} = {v[0][:80]}")
    faltam = [k for k in ("utm_source", "gclid") if k not in corpo]
    print("ORIGEM:", "OK" if not faltam else f"FALTAM {', '.join(faltam)} (o lead chega sem origem)")


if __name__ == "__main__":
    main()
