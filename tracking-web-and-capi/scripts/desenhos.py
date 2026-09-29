#!/usr/bin/env python3
"""Gera os desenhos animados do README (SVG com animação nativa, roda no GitHub sem JavaScript).

  python3 scripts/desenhos.py            # grava assets/capa.svg, assets/fluxo.svg e assets/eventos.svg

Estética do claude-seo (fundo escuro, brilho, partícula que corre pelas linhas) com o vermelho da V4.
Mudou evento, destino ou modo? Edite as listas abaixo e rode de novo.
"""
import math, os

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = "'JetBrains Mono','Cascadia Mono','Menlo','Consolas',monospace"
FUNDO, VERM, VERM2 = "#161212", "#E50914", "#FF5A5F"
TXT, TXT2, APAGADO, CAIXA, CAIXA_HI, LINHA = "#F7EDEC", "#E6D6D4", "#9B8583", "#211919", "#2A1B1B", "#4A3535"
CINZA, AMBAR, VERDE = "#A08F8D", "#F2A33A", "#3CB371"

# contrato de eventos (canonico/padrao-tracking.md): evento, quando, de onde sai, destinos (Meta, Ads, GA4), valor proxy
EVENTOS = [
    ("PageView", "toda página", "web", (1, 0, 1), 0.0),
    ("Contact", "clique no WhatsApp", "web", (1, 1, 1), 0.08),
    ("Lead", "envio do formulário", "web", (1, 1, 1), 0.16),
    ("MQL", "qualificou na LP", "web", (1, 1, 1), 0.32),
    ("SQL", "qualificou no comercial", "volta", (1, 1, 0), 0.58),
    ("Purchase", "venda fechada", "volta", (1, 1, 0), 1.0),
]
DESTINOS = ["Meta · Pixel + CAPI", "Google Ads", "GA4"]
MODOS = [("planejar", "brief → gerar_containers"), ("auditar", "G1–G5 · checklist 13"), ("troubleshoot", "erro conhecido?")]


def defs(extra=""):
    return f'''<defs>
    <filter id="brilho" x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="3.6"/></filter>
    <filter id="aurora" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="75"/></filter>
    <radialGradient id="auA" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{VERM}" stop-opacity="0.34"/><stop offset="100%" stop-color="{VERM}" stop-opacity="0"/></radialGradient>
    <radialGradient id="auB" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#8E1016" stop-opacity="0.30"/><stop offset="100%" stop-color="#8E1016" stop-opacity="0"/></radialGradient>
    <radialGradient id="auC" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{VERM2}" stop-opacity="0.16"/><stop offset="100%" stop-color="{VERM2}" stop-opacity="0"/></radialGradient>
    {extra}
  </defs>'''


def aurora(w, h):
    return f'''<rect width="{w}" height="{h}" rx="16" fill="{FUNDO}"/>
  <g filter="url(#aurora)" opacity="0.95">
    <ellipse cx="{w*0.18:.0f}" cy="{h*0.35:.0f}" rx="{w*0.29:.0f}" ry="{h*0.62:.0f}" fill="url(#auA)"><animateTransform attributeName="transform" type="translate" values="0 0;58 26;0 0" dur="24s" repeatCount="indefinite"/></ellipse>
    <ellipse cx="{w*0.80:.0f}" cy="{h*0.78:.0f}" rx="{w*0.30:.0f}" ry="{h*0.64:.0f}" fill="url(#auB)"><animateTransform attributeName="transform" type="translate" values="0 0;-48 -20;0 0" dur="30s" repeatCount="indefinite"/></ellipse>
    <ellipse cx="{w*0.50:.0f}" cy="{h*0.18:.0f}" rx="{w*0.23:.0f}" ry="{h*0.46:.0f}" fill="url(#auC)"><animateTransform attributeName="transform" type="translate" values="0 0;30 34;0 0" dur="27s" repeatCount="indefinite"/></ellipse>
  </g>'''


def svg(w, h, rotulo, titulo, corpo, extra_defs=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="{rotulo}">
  <title>{titulo}</title>
  {defs(extra_defs)}
  {aurora(w, h)}
{corpo}
</svg>
'''


def texto(x, y, s, tam=13, cor=TXT2, peso="400", ancora="middle", esp="0", extra=""):
    return (f'<text x="{x}" y="{y}" text-anchor="{ancora}" font-family="{FONTE}" font-size="{tam}" font-weight="{peso}" '
            f'fill="{cor}" letter-spacing="{esp}"{extra}>{s}</text>')


def kt(*t):
    return ";".join(f"{min(max(v, 0), 1):.3f}" for v in t)


def acende(x, y, w, h, t0, dur, rx=12, cor=VERM):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" stroke="{cor}" stroke-width="2.6" '
            f'filter="url(#brilho)" opacity="0"><animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="0;{kt(t0, t0 + .05, min(t0 + .16, .999))};1" values="0;0;0.95;0;0"/></rect>')


def caixa(x, y, w, h, t1, t2, t0, dur, destaque=False, tam=18, cor=None):
    borda = cor or (VERM if destaque else "#6E4A48")
    larg = 1.7 if (destaque or cor) else 1.1
    s = [f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{CAIXA_HI if destaque else CAIXA}" '
         f'stroke="{borda}" stroke-width="{larg}"/>', acende(x, y, w, h, t0, dur, cor=cor or VERM)]
    s += [texto(x + w / 2, y + h / 2 - 3, t1, tam, cor or (TXT if destaque else TXT2), "600"),
          texto(x + w / 2, y + h / 2 + 17, t2, 11, APAGADO, esp="0.4")]
    return "".join(s) + "</g>"


def particula(caminho, t0, t1, dur, cor=VERM):
    a, b = kt(t0, t1), kt(t0 - .01, t0 + .02, t1 - .02, t1)
    return (f'<circle r="10" fill="{cor}" filter="url(#brilho)" opacity="0"><animateMotion dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="0;{a};1" keyPoints="0;0;1;1" path="{caminho}"/><animate attributeName="opacity" '
            f'dur="{dur}s" repeatCount="indefinite" keyTimes="0;{b};1" values="0;0;0.28;0.28;0;0"/></circle>'
            f'<circle r="5.5" fill="{cor}" filter="url(#brilho)" opacity="0"><animateMotion dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="0;{a};1" keyPoints="0;0;1;1" path="{caminho}"/><animate attributeName="opacity" '
            f'dur="{dur}s" repeatCount="indefinite" keyTimes="0;{b};1" values="0;0;1;1;0;0"/>'
            f'<animate attributeName="r" values="5;6.5;5" dur="1.4s" repeatCount="indefinite"/></circle>')


def digitacao(fases, x0, yb, dur_fase=4.0):
    """Comandos digitados um de cada vez, com cursor que acompanha o texto."""
    n = len(fases)
    D = dur_fase * n
    L = []
    for k, f in enumerate(fases):
        ini, fim = k / n, (k + 1) / n
        larg = len(f) * 12.05
        dig = ini + (fim - ini) * .45
        vis = f"0;{kt(ini, ini + .001, fim - .01, fim)};1" if k else f"0;{kt(fim - .01, fim)};1"
        vals = "0;0;1;1;0;0" if k else "1;1;0;0"
        conteudo = f.replace("<", "&lt;").replace(">", "&gt;")
        if conteudo.startswith("/"):
            conteudo = f'<tspan fill="{VERM2}">/</tspan>' + conteudo[1:]
        L.append(f'<clipPath id="dig{k}"><rect x="{x0}" y="{yb - 30}" height="44" width="0"><animate attributeName="width" '
                 f'dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(ini, dig)};1" values="0;0;{larg:.0f};{larg:.0f}"/></rect></clipPath>')
        L.append(f'<g opacity="{1 if k == 0 else 0}"><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" '
                 f'keyTimes="{vis}" values="{vals}"/>'
                 f'<text x="{x0}" y="{yb}" clip-path="url(#dig{k})" font-family="{FONTE}" font-size="20" fill="{TXT}">{conteudo}</text>'
                 f'<rect y="{yb - 18}" width="2" height="24" fill="{VERM}" x="{x0}"><animate attributeName="x" dur="{D}s" '
                 f'repeatCount="indefinite" keyTimes="0;{kt(ini, dig)};1" values="{x0};{x0};{x0 + larg:.0f};{x0 + larg:.0f}"/>'
                 f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g>')
    return L


# ---------------------------------------------------------------- capa

def no(x, y, w, h, t1, t0, dur, cor="#6E4A48", destaque=False):
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{CAIXA_HI if destaque else CAIXA}" stroke="{cor}" '
            f'stroke-width="{1.6 if destaque else 1.1}"/>' + (acende(x, y, w, h, t0, dur, 10) if t0 is not None else "")
            + texto(x + w / 2, y + h / 2 + 5, t1, 14, TXT if destaque else TXT2, "600") + "</g>")


def aparece(conteudo, t0, t1, dur):
    return (f'<g opacity="0"><animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="0;{kt(t0, t0 + .02, t1 - .02, t1)};1" values="0;0;1;1;0;0"/>{conteudo}</g>')


def capa():
    W, H, D = 1460, 460, 8.0
    L = [f'<text x="110" y="150" font-family="{FONTE}" font-size="70" font-weight="700" fill="url(#titulo)">tracking</text>',
         f'<text x="110" y="222" font-family="{FONTE}" font-size="70" font-weight="700" fill="url(#titulo)">web &amp; capi</text>',
         texto(114, 262, "tracking só está pronto quando a venda volta", 17, APAGADO, ancora="start", esp="0.6"),
         f'<rect x="110" y="{330 - 36}" width="640" height="56" rx="12" fill="#1C1616" stroke="#3A2A2A"/>']
    L += digitacao(["/tracking-web-and-capi planejar", "auditar antes do go-live", "o lead chega sem gclid. por quê?",
                    "a venda voltou para o Meta?"], 140, 330)
    # a página manda o evento pelos dois caminhos; o Meta deduplica; a venda volta do CRM
    bw, bh = 130, 44
    pag, gtm, pix, srv, meta, crm = (830, 188), (990, 188), (1160, 98), (1160, 278), (1300, 188), (990, 358)
    arestas = [
        ("M960,210 L990,210", .02, .12, VERM),
        ("M1120,210 C1140,210 1140,120 1160,120", .14, .30, VERM),
        ("M1120,210 C1140,210 1140,300 1160,300", .14, .30, VERM),
        ("M1290,120 C1330,120 1340,150 1365,188", .32, .46, VERM),
        ("M1290,300 C1330,300 1340,270 1365,232", .32, .46, VERM),
        ("M895,232 C895,380 950,380 990,380", .50, .64, AMBAR),
        ("M1120,380 C1300,380 1400,330 1400,232", .68, .86, VERDE),
    ]
    L += [f'<path d="{c}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>' for c, *_ in arestas]
    L.append(texto(1335, 290, "CAPI", 11, APAGADO, ancora="start", esp="0.6"))
    L.append(texto(1335, 146, "Pixel", 11, APAGADO, ancora="start", esp="0.6"))
    L.append(texto(908, 306, "lead + gclid / fbclid", 11, AMBAR, ancora="start"))
    L.append(texto(1180, 404, "Purchase volta pela CAPI e pelo offline", 11, VERDE, ancora="start"))
    L.append(no(*pag, bw, bh, "página", .0, D))
    L.append(no(*gtm, bw, bh, "GTM web", .12, D))
    L.append(no(*pix, bw, bh, "navegador", .30, D))
    L.append(no(*srv, bw, bh, "GTM server", .30, D))
    L.append(no(*crm, bw, bh, "CRM · venda", .64, D, AMBAR))
    mx, my = meta
    L.append(f'<g><rect x="{mx}" y="{my}" width="{bw}" height="{bh}" rx="10" fill="{CAIXA_HI}" stroke="{VERM}" stroke-width="1.6"/>'
             + acende(mx, my, bw, bh, .46, D, 10) + acende(mx, my, bw, bh, .86, D, 10)
             + texto(mx + bw / 2, my + 19, "Meta", 14, TXT, "600") + "</g>")
    L.append(aparece(texto(mx + bw / 2, my + 35, "evento", 10, APAGADO), 0, .46, D))
    L.append(aparece(texto(mx + bw / 2, my + 35, "event_id · 1, não 2", 10, VERM2, "600"), .46, .86, D))
    L.append(aparece(texto(mx + bw / 2, my + 35, "Purchase ✓", 10, VERDE, "600"), .86, .999, D))
    L += [particula(c, a, b, D, cor) for c, a, b, cor in arestas]
    grad = (f'<linearGradient id="titulo" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{VERM2}"/>'
            f'<stop offset="100%" stop-color="{VERM}"/></linearGradient>')
    return svg(W, H, "Capa da tracking-web-and-capi: comandos sendo digitados e o evento saindo da página pelo GTM web, indo "
               "ao Meta pelo navegador e pelo servidor com o mesmo event_id (um evento, não dois), o lead gravado no CRM com "
               "gclid e fbclid e a venda voltando ao Meta.", "tracking web e capi", "  " + "\n  ".join(L), grad)


# ---------------------------------------------------------------- fluxo

def fluxo():
    W, H, D, cy = 1460, 520, 9.0, 250
    nos = [(40, 235, "/tracking-web-and-capi", "cliente", True, .00, 16),
           (315, 170, "armadilhas", "lidas antes", False, .09, 18),
           (525, 150, "modo", "qual dos três?", False, .21, 18),
           (985, 200, "go-live", "ok explícito · lead teste", False, .65, 18),
           (1225, 195, "venda volta", "CAPI · Ads offline", True, .78, 18)]
    mx, mw, mys = 715, 220, [140, 250, 360]
    L = [texto(40, 44, "TRACKING-WEB-AND-CAPI · FLUXO DO SINAL", 13, "#8A6F6D", ancora="start", esp="1.6"),
         texto(mx + mw / 2, 92, "três modos", 11, APAGADO, esp="0.8")]
    arestas = [("M275,250 L315,250", .02, .10), ("M485,250 L525,250", .14, .22)]
    arestas += [(f"M675,250 C695,250 695,{y} {mx},{y}", .27, .37) for y in mys]
    arestas += [(f"M{mx + mw},{y} C960,{y} 960,250 985,250", .52, .64) for y in mys]
    arestas += [("M1185,250 L1225,250", .69, .77)]
    laco = "M1322,281 Q1322,470 1142,470 L580,470 Q400,470 400,281"
    L += [f'<path d="{c}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>' for c, _, _ in arestas]
    L.append(f'<path d="{laco}" fill="none" stroke="{VERM}" stroke-opacity="0.45" stroke-width="1.3" stroke-dasharray="5 6">'
             f'<animate attributeName="stroke-dashoffset" values="0;-22" dur="1.2s" repeatCount="indefinite"/></path>')
    L.append(texto(861, 496, "↺ erro novo vira armadilha, item do checklist e caso de teste", 12, VERM2, esp="0.4"))
    for x, w, t1, t2, hi, t0, tam in nos:
        L.append(caixa(x, cy - 31, w, 62, t1, t2, t0, D, hi, tam))
    for (m, sub), y in zip(MODOS, mys):
        L.append(caixa(mx, y - 31, mw, 62, m, sub, .37, D, False, 18))
    L += [particula(c, a, b, D) for c, a, b in arestas]
    L.append(particula(laco, .86, .99, D, VERM2))
    return svg(W, H, "Fluxo da tracking-web-and-capi: o comando entra, as armadilhas são lidas, o modo abre em planejar, "
               "auditar ou troubleshoot, tudo converge no go-live com ok explícito e na venda voltando às plataformas, e o "
               "erro novo vira armadilha e teste.", "Fluxo da tracking-web-and-capi", "  " + "\n  ".join(L))


# ---------------------------------------------------------------- eventos

def eventos():
    W, H, D = 1400, 720, 12.0
    ys = [160 + 76 * i for i in range(len(EVENTOS))]
    ex, ew = 48, 230          # evento
    ox, ow = 318, 170         # origem
    sx, sw = 530, 150         # servidor (barramento)
    dxs = [790, 950, 1080]    # destinos
    vx, vw = 1150, 200        # valor proxy
    L = [texto(48, 56, "TRACKING-WEB-AND-CAPI · O CONTRATO DE EVENTOS", 13, "#8A6F6D", ancora="start", esp="1.6")]
    for x, t in ((ex, "evento"), (ox, "sai de"), (sx, "servidor"), (vx, "valor proxy (Modelo A)")):
        L.append(texto(x, 108, t, 11, APAGADO, ancora="start", esp="0.8"))
    for x, t in zip(dxs, DESTINOS):
        L.append(texto(x, 108, t, 11, APAGADO, esp="0.4"))
    L.append(f'<rect x="{sx}" y="126" width="{sw}" height="{ys[-1] - 126 + 34}" rx="12" fill="{CAIXA_HI}" stroke="{VERM}" '
             f'stroke-width="1.4" stroke-opacity="0.7"/>')
    L.append(texto(sx + sw / 2, 148, "GTM server", 13, TXT, "600"))
    L.append(texto(sx + sw / 2, 164, "Stape", 11, APAGADO))
    passo = .8 / len(EVENTOS)
    for i, ((ev, quando, origem, dest, valor), y) in enumerate(zip(EVENTOS, ys)):
        t0 = .04 + i * passo
        volta = origem == "volta"
        cor_o = AMBAR if volta else "#6E4A48"
        L.append(f'<path d="M{ex + ew},{y} L{dxs[-1]},{y}" fill="none" stroke="{LINHA}" stroke-width="1.1"/>')
        L.append(f'<g><rect x="{ex}" y="{y - 26}" width="{ew}" height="52" rx="10" fill="{CAIXA}" stroke="#6E4A48"/>'
                 + acende(ex, y - 26, ew, 52, t0, D, 10) + texto(ex + 16, y - 3, ev, 16, TXT, "700", "start")
                 + texto(ex + 16, y + 15, quando, 11, APAGADO, ancora="start") + "</g>")
        rotulo = "planilha · CRM" if volta else "GTM web"
        tracejado = ' stroke-dasharray="5 4"' if volta else ""
        L.append(f'<g><rect x="{ox}" y="{y - 20}" width="{ow}" height="40" rx="10" fill="{CAIXA}" stroke="{cor_o}"{tracejado}/>'
                 + acende(ox, y - 20, ow, 40, t0 + passo * .25, D, 10, AMBAR if volta else VERM)
                 + texto(ox + ow / 2, y + 5, rotulo, 13, AMBAR if volta else TXT2, "600") + "</g>")
        ultimo = max(k for k, f in enumerate(dest) if f)
        cor_p = AMBAR if volta else VERM
        L.append(particula(f"M{ex + ew},{y} L{dxs[ultimo]},{y}", t0, t0 + passo * .9, D, cor_p))
        for k, (x, f) in enumerate(zip(dxs, dest)):
            if not f:
                L.append(texto(x, y + 4, "—", 12, "#5E4A48"))
                continue
            chega = t0 + passo * .9 * (x - ex - ew) / (dxs[ultimo] - ex - ew)
            L.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{CAIXA}" stroke="{VERDE}" stroke-width="1.4"/>'
                     f'<circle cx="{x}" cy="{y}" r="7" fill="{VERDE}" opacity="0"><animate attributeName="opacity" dur="{D}s" '
                     f'repeatCount="indefinite" keyTimes="0;{kt(chega, chega + .01, .95, .99)};1" values="0;0;1;1;0;0"/></circle>')
        if valor:
            larg = vw * valor
            L.append(f'<rect x="{vx}" y="{y - 9}" width="{vw}" height="18" rx="4" fill="#1C1616" stroke="#3A2A2A"/>'
                     f'<rect x="{vx}" y="{y - 9}" width="0" height="18" rx="4" fill="{VERDE}" fill-opacity="0.7">'
                     f'<animate attributeName="width" dur="{D}s" repeatCount="indefinite" keyTimes="0;'
                     f'{kt(t0 + passo * .8, t0 + passo, .95, .99)};1" values="0;0;{larg:.0f};{larg:.0f};0;0"/></rect>')
        else:
            L.append(texto(vx, y + 4, "sem valor", 11, "#5E4A48", ancora="start"))
    yl = ys[-1] + 70
    L.append(f'<rect x="{ox}" y="{yl - 12}" width="18" height="12" rx="3" fill="none" stroke="{AMBAR}" stroke-dasharray="4 3"/>'
             + texto(ox + 26, yl - 2, "volta da venda: o status muda na planilha ou no CRM e sobe pelo servidor", 12, APAGADO, ancora="start"))
    L.append(texto(48, yl + 26, "Modelo A: lucro = ticket × margem · valor SQL = lucro × SQL→venda · valor MQL = SQL × MQL→SQL "
                   "· valor Lead = MQL × Lead→MQL", 12, APAGADO, ancora="start"))
    L.append(texto(48, yl + 50, "Meta sempre com Pixel + CAPI e o mesmo event_id · token da CAPI só no GTM server, nunca em "
                   "arquivo", 12, APAGADO, ancora="start"))
    return svg(W, H, "O contrato de eventos da tracking-web-and-capi: PageView, Contact, Lead e MQL saem do GTM web; SQL e "
               "Purchase voltam da planilha ou do CRM; todos passam pelo GTM server e chegam ao Meta (Pixel + CAPI), ao Google "
               "Ads e ao GA4, com o valor proxy do Modelo A crescendo até a venda.", "Contrato de eventos",
               "  " + "\n  ".join(L))


def main():
    os.makedirs(os.path.join(AQUI, "assets"), exist_ok=True)
    for nome, fn in (("capa.svg", capa), ("fluxo.svg", fluxo), ("eventos.svg", eventos)):
        open(os.path.join(AQUI, "assets", nome), "w", encoding="utf-8").write(fn())
        print("assets/" + nome)


if __name__ == "__main__":
    main()
