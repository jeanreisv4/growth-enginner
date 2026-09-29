#!/usr/bin/env python3
"""Gera os desenhos animados do README (SVG com animação nativa, roda no GitHub sem JavaScript).

  python3 scripts/desenhos.py            # grava assets/capa.svg, assets/fluxo.svg e assets/agentes.svg

Estética do claude-seo (fundo escuro, brilho, partícula que corre pelas linhas) com o vermelho da V4.
Mudou frente, agente ou etapa? Edite as listas abaixo e rode de novo.
"""
import base64, math, os, re

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = "'JetBrains Mono','Cascadia Mono','Menlo','Consolas',monospace"
FUNDO, VERM, VERM2 = "#161212", "#E50914", "#FF5A5F"
TXT, TXT2, APAGADO, CAIXA, CAIXA_HI, LINHA = "#F7EDEC", "#E6D6D4", "#9B8583", "#211919", "#2A1B1B", "#4A3535"

AGENTES = [  # (título, onda, itens, ferramenta) — em sentido horário a partir do topo
    ("FONTES", "onda 1", ["pessoas únicas", "canal e teste", "CNPJ na Receita"], "leads.py · cnpj.py"),
    ("GOOGLE ADS", "onda 2", ["alertas A1–A10", "termos e negativas", "CPL real"], "ads_auditoria.py"),
    ("META ADS", "onda 2", ["criativo × qualidade", "segunda conta", "anomalias"], "conector Meta Ads"),
    ("MEDIÇÃO", "onda 2", ["GTM G1–G5", "disparo e formulário", "GA4 · Pixel/CAPI"], "gtm_auditoria.py"),
    ("CLARITY", "onda 2", ["robôs e raiva", "clique morto", "volta rápida · rolagem"], "clarity.py"),
    ("JORNADA", "onda 2", ["custo por destino", "oferta × página", "on-page · velocidade"], "render do claude-seo"),
    ("COMERCIAL", "onda 2", ["novo × antigo", "perdas e tempos", "receita (piso)"], "datacrazy.py"),
    ("MERCADO", "onda 2", ["concorrentes", "preço com unidade", "anúncios ativos"], "WebSearch · Ads Library"),
]
FRENTES_ONDA2 = ["google-ads", "meta-ads", "medicao", "clarity", "jornada", "comercial", "mercado"]
LOGOS = {  # frente → logos da ferramenta (assets/logos/FONTES.md tem a origem de cada um)
    "FONTES": ["googlesheets"], "GOOGLE ADS": ["googleads"], "META ADS": ["meta"],
    "MEDIÇÃO": ["googletagmanager", "googleanalytics"], "CLARITY": ["clarity"], "JORNADA": ["pagespeedinsights"],
    "google-ads": ["googleads"], "meta-ads": ["meta"], "medicao": ["googletagmanager"], "clarity": ["clarity"],
    "jornada": ["pagespeedinsights"],
}
COR_LOGO = {"googletagmanager": "#246FDB", "googlesheets": "#34A853", "pagespeedinsights": "#4285F4", "meta": "url(#metaGrad)"}


def logo(nome, x, y, t):
    """Logo da ferramenta num quadrado de t px com canto em (x, y)."""
    g = f'<g transform="translate({x:.1f},{y:.1f}) scale({t / 24:.4f})">'
    if nome == "googleads":  # geometria oficial do ícone: barra amarela, barra azul, círculo verde
        return (g + '<line x1="12" y1="5" x2="4" y2="18.93" stroke="#FBBC04" stroke-width="8" stroke-linecap="round"/>'
                '<line x1="12" y1="5" x2="20" y2="18.93" stroke="#4285F4" stroke-width="8" stroke-linecap="round"/>'
                '<circle cx="4" cy="18.93" r="4" fill="#34A853"/></g>')
    if nome == "googleanalytics":
        return (g + '<rect x="16.6" y="1" width="6.4" height="22" rx="3.2" fill="#F9AB00"/>'
                '<rect x="8.8" y="9" width="6.4" height="14" rx="3.2" fill="#E37400"/>'
                '<circle cx="4.2" cy="19.8" r="3.2" fill="#E37400"/></g>')
    arq = os.path.join(AQUI, "assets", "logos", nome)
    if nome == "clarity":
        b64 = base64.b64encode(open(arq + ".png", "rb").read()).decode()
        return f'<image x="{x:.1f}" y="{y:.1f}" width="{t}" height="{t}" href="data:image/png;base64,{b64}"/>'
    d = re.search(r' d="([^"]+)"', open(arq + ".svg", encoding="utf-8").read()).group(1)
    return g + f'<path d="{d}" fill="{COR_LOGO[nome]}"/></g>'


def defs(extra=""):
    return f'''<defs>
    <filter id="brilho" x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="3.6"/></filter>
    <filter id="aurora" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="75"/></filter>
    <radialGradient id="auA" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{VERM}" stop-opacity="0.34"/><stop offset="100%" stop-color="{VERM}" stop-opacity="0"/></radialGradient>
    <radialGradient id="auB" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#8E1016" stop-opacity="0.30"/><stop offset="100%" stop-color="#8E1016" stop-opacity="0"/></radialGradient>
    <radialGradient id="auC" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="{VERM2}" stop-opacity="0.16"/><stop offset="100%" stop-color="{VERM2}" stop-opacity="0"/></radialGradient>
    <linearGradient id="metaGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#0064E0"/><stop offset="100%" stop-color="#0082FB"/></linearGradient>
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


def acende(x, y, w, h, t0, dur, rx=12):
    """Contorno com brilho que acende quando o sinal chega (t0 em fração do ciclo)."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" stroke="{VERM}" stroke-width="2.6" '
            f'filter="url(#brilho)" opacity="0"><animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="0;{kt(t0, t0 + .05, min(t0 + .16, .999))};1" values="0;0;0.95;0;0"/></rect>')


def caixa(x, y, w, h, t1, t2, t0, dur, destaque=False, tam=18):
    borda, larg, fundo = (VERM, 1.7, CAIXA_HI) if destaque else ("#6E4A48", 1.1, CAIXA)
    s = [f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fundo}" stroke="{borda}" stroke-width="{larg}"/>',
         acende(x, y, w, h, t0, dur)]
    if t2:
        s += [texto(x + w / 2, y + h / 2 - 3, t1, tam, TXT if destaque else TXT2, "600"),
              texto(x + w / 2, y + h / 2 + 17, t2, 11, APAGADO, esp="0.4")]
    else:
        s.append(texto(x + w / 2, y + h / 2 + 5, t1, tam, TXT2, "600"))
    return "".join(s) + "</g>"


def particula(caminho, t0, t1, dur, cor=VERM):
    """Rastro + ponto que percorre o caminho entre t0 e t1 (frações do ciclo)."""
    a, b = kt(t0, t1), kt(t0 - .01, t0 + .02, t1 - .02, t1)
    return (f'<circle r="10" fill="{cor}" filter="url(#brilho)" opacity="0"><animateMotion dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="0;{a};1" keyPoints="0;0;1;1" path="{caminho}"/><animate attributeName="opacity" '
            f'dur="{dur}s" repeatCount="indefinite" keyTimes="0;{b};1" values="0;0;0.28;0.28;0;0"/></circle>'
            f'<circle r="5.5" fill="{cor}" filter="url(#brilho)" opacity="0"><animateMotion dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="linear" keyTimes="0;{a};1" keyPoints="0;0;1;1" path="{caminho}"/><animate attributeName="opacity" '
            f'dur="{dur}s" repeatCount="indefinite" keyTimes="0;{b};1" values="0;0;1;1;0;0"/>'
            f'<animate attributeName="r" values="5;6.5;5" dur="1.4s" repeatCount="indefinite"/></circle>')


# ---------------------------------------------------------------- fluxo

def fluxo():
    W, H, D, cy = 1700, 520, 9.0, 250
    nos = [  # x, largura, título, subtítulo, destaque, t0
        (40, 170, "/sprint-growth", "cliente", True, 0.00),
        (260, 150, "memória", "+ entrevista", False, 0.09),
        (460, 150, "SKILL.md", "orquestrador", True, 0.21),
        (660, 170, "sprint-fontes", "onda 1 · pessoas", False, 0.33),
        (1115, 175, "consolidar.py", "ranking · divergências", False, 0.65),
        (1340, 120, "TOC", "restrição", False, 0.74),
        (1500, 160, "5W1H", "plano em R$", True, 0.83),
    ]
    ag_x, ag_w, ag_h = 885, 175, 38
    ys = [cy + (i - 3) * 50 for i in range(7)]
    L = [texto(40, 44, "SPRINT-GROWTH · FLUXO DO SINAL", 13, "#8A6F6D", ancora="start", esp="1.6"),
         texto(ag_x + ag_w / 2, 70, "onda 2 · em paralelo", 11, APAGADO, esp="0.8"),
         texto(ag_x + ag_w / 2, 448, "somente leitura", 11, APAGADO, esp="0.8")]
    arestas = [("M210,250 L260,250", .02, .10), ("M410,250 L460,250", .14, .22), ("M610,250 L660,250", .26, .34)]
    arestas += [(f"M830,250 C857,250 857,{y} {ag_x},{y}", .38, .48) for y in ys]
    arestas += [(f"M{ag_x + ag_w},{y} C1087,{y} 1087,250 1115,250", .55, .65) for y in ys]
    arestas += [("M1290,250 L1340,250", .69, .75), ("M1460,250 L1500,250", .78, .84)]
    laco = "M1580,281 Q1580,470 1400,470 L515,470 Q335,470 335,281"
    L += [f'<path d="{c}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>' for c, _, _ in arestas]
    L.append(f'<path d="{laco}" fill="none" stroke="{VERM}" stroke-opacity="0.45" stroke-width="1.3" stroke-dasharray="5 6">'
             f'<animate attributeName="stroke-dashoffset" values="0;-22" dur="1.2s" repeatCount="indefinite"/></path>')
    L.append(texto(958, 496, "↺ Executado registrado · a próxima sprint começa pela memória", 12, VERM2, esp="0.4"))
    for x, w, t1, t2, hi, t0 in nos:
        L.append(caixa(x, cy - 31, w, 62, t1, t2, t0, D, hi))
    for i, (y, nome) in enumerate(zip(ys, FRENTES_ONDA2)):
        L.append(caixa(ag_x, y - ag_h / 2, ag_w, ag_h, nome, "", .48 + i * .012, D, tam=14))
        L += [logo(n, ag_x + 12, y - 8, 16) for n in LOGOS.get(nome, [])]
    L += [particula(c, a, b, D) for c, a, b in arestas]
    L.append(particula(laco, .86, .99, D, VERM2))
    return svg(W, H, "Fluxo da sprint-growth: o comando entra, a memória e a entrevista preparam o orquestrador, o agente de "
               "fontes roda na onda 1, sete agentes rodam em paralelo na onda 2, consolidar.py junta os achados, a Teoria "
               "das Restrições decide e sai o plano 5W1H em R$; o Executado volta para a memória da próxima sprint.",
               "Fluxo da sprint-growth", "  " + "\n  ".join(L))


# ---------------------------------------------------------------- agentes

def agentes():
    W, H, D = 1400, 900, 8.0
    cx, cy, rx, ry, bw, bh = 700, 470, 450, 330, 250, 128
    L = [texto(48, 56, "SPRINT-GROWTH · 8 AGENTES · SOMENTE LEITURA", 13, "#8A6F6D", ancora="start", esp="1.6"),
         f'<circle cx="{cx}" cy="{cy}" r="300" fill="none" stroke="{LINHA}" stroke-width="1"/>',
         f'<circle cx="{cx}" cy="{cy}" r="160" fill="none" stroke="{VERM}" stroke-opacity="0.35" stroke-width="1.2" '
         f'stroke-dasharray="3 9"><animateTransform attributeName="transform" type="rotate" values="0 {cx} {cy};360 {cx} {cy}" '
         f'dur="60s" repeatCount="indefinite"/></circle>']
    pos = []
    for i in range(8):
        a = math.radians(-90 + 45 * i)
        pos.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    for x, y in pos:
        L.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="{LINHA}" stroke-width="1"/>')
    passo = 1 / 8
    for i, ((x, y), (tit, onda, itens, ferr)) in enumerate(zip(pos, AGENTES)):
        t0 = i * passo
        L.append(particula(f"M{cx},{cy} L{x:.0f},{y:.0f}", t0, t0 + passo * .8, D))
        bx, by = x - bw / 2, y - bh / 2
        hi = i == 0
        L.append(f'<g><rect x="{bx:.0f}" y="{by:.0f}" width="{bw}" height="{bh}" rx="10" fill="{CAIXA_HI if hi else CAIXA}" '
                 f'stroke="{VERM if hi else "#6E4A48"}" stroke-width="{1.6 if hi else 1.1}"/>'
                 + acende(round(bx), round(by), bw, bh, t0 + passo * .8, D, 10)
                 + "".join(logo(n, bx + 16 + 26 * k, by + 12, 18) for k, n in enumerate(LOGOS.get(tit, [])))
                 + texto(bx + 16 + 26 * len(LOGOS.get(tit, [])), by + 26, tit, 14, VERM2, "700", "start", "1.2")
                 + texto(bx + bw - 16, by + 26, onda, 11, APAGADO, ancora="end")
                 + "".join(texto(bx + 16, by + 50 + 20 * k, it, 13, TXT2, ancora="start") for k, it in enumerate(itens))
                 + texto(bx + 16, by + bh - 12, ferr, 11, APAGADO, ancora="start", esp="0.3") + "</g>")
    L.append(f'<circle cx="{cx}" cy="{cy}" r="72" fill="none" stroke="{VERM}" stroke-width="2" opacity="0">'
             f'<animate attributeName="r" values="72;120" dur="{D / 8}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0.6;0" dur="{D / 8}s" repeatCount="indefinite"/></circle>')
    L.append(f'<circle cx="{cx}" cy="{cy}" r="72" fill="{CAIXA_HI}" stroke="{VERM}" stroke-width="2"/>')
    L.append(texto(cx, cy - 4, "sprint-growth/", 15, TXT, "700"))
    L.append(texto(cx, cy + 16, "orquestrador", 12, APAGADO, esp="0.4"))
    return svg(W, H, "Os 8 agentes da sprint-growth em volta do orquestrador: fontes (onda 1), Google Ads, Meta Ads, medição, "
               "Clarity, jornada, comercial e mercado (onda 2), todos somente leitura.", "Agentes da sprint-growth",
               "  " + "\n  ".join(L))


# ---------------------------------------------------------------- capa

def capa():
    W, H = 1460, 460
    fases = ["/sprint-growth &lt;cliente&gt;", "sprint ads &lt;cliente&gt;", "audita só o GTM do cliente",
             "sprint clarity &lt;cliente&gt;"]
    reais = ["/sprint-growth <cliente>", "sprint ads <cliente>", "audita só o GTM do cliente", "sprint clarity <cliente>"]
    ciclo, n = 4.0, len(fases)
    D = ciclo * n
    x0, yb = 150, 318
    L = [f'<text x="120" y="210" font-family="{FONTE}" font-size="78" font-weight="700" fill="url(#titulo)">sprint growth</text>',
         texto(124, 250, "do clique à venda · 8 agentes · plano em R$", 17, APAGADO, ancora="start", esp="0.6"),
         f'<rect x="120" y="{yb - 36}" width="640" height="56" rx="12" fill="#1C1616" stroke="#3A2A2A"/>']
    for k, (f, r) in enumerate(zip(fases, reais)):
        ini, fim = k / n, (k + 1) / n
        larg = len(r) * 12.05
        dig = ini + (fim - ini) * .45
        vis = f"0;{kt(ini, ini + .001, fim - .01, fim)};1" if k else f"0;{kt(fim - .01, fim)};1"
        vals = "0;0;1;1;0;0" if k else "1;1;0;0"
        L.append(f'<clipPath id="dig{k}"><rect x="{x0}" y="{yb - 30}" height="44" width="0"><animate attributeName="width" '
                 f'dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(ini, dig)};1" values="0;0;{larg:.0f};{larg:.0f}"/></rect></clipPath>')
        L.append(f'<g opacity="{1 if k == 0 else 0}"><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" '
                 f'keyTimes="{vis}" values="{vals}"/>'
                 f'<text x="{x0}" y="{yb}" clip-path="url(#dig{k})" font-family="{FONTE}" font-size="20" fill="{TXT}">'
                 + (f'<tspan fill="{VERM2}">/</tspan>{f[1:]}' if f.startswith("/") else f) + '</text>'
                 f'<rect y="{yb - 18}" width="2" height="24" fill="{VERM}" x="{x0}"><animate attributeName="x" dur="{D}s" '
                 f'repeatCount="indefinite" keyTimes="0;{kt(ini, dig)};1" values="{x0};{x0};{x0 + larg:.0f};{x0 + larg:.0f}"/>'
                 f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g>')
    # funil
    fx, topo, alt, vao = 1090, 64, 56, 10
    largs = [420, 340, 260, 190, 130, 90]
    nomes = ["tráfego", "lead", "oportunidade", "venda", "receita"]
    for i, nome in enumerate(nomes):
        y = topo + i * (alt + vao)
        a, b = largs[i] / 2, largs[i + 1] / 2
        rest = i == 2
        L.append(f'<path d="M{fx - a},{y} L{fx + a},{y} L{fx + b},{y + alt} L{fx - b},{y + alt} Z" fill="{CAIXA_HI if rest else CAIXA}" '
                 f'stroke="{VERM if rest else "#6E4A48"}" stroke-width="{1.8 if rest else 1.1}"/>')
        if rest:
            L.append(f'<path d="M{fx - a},{y} L{fx + a},{y} L{fx + b},{y + alt} L{fx - b},{y + alt} Z" fill="none" stroke="{VERM}" '
                     f'stroke-width="3" filter="url(#brilho)"><animate attributeName="opacity" values="0.2;0.95;0.2" dur="2.4s" '
                     f'repeatCount="indefinite"/></path>')
            L.append(texto(fx + a + 18, y + alt / 2 - 2, "restrição", 13, VERM2, "600", "start"))
            L.append(texto(fx + a + 18, y + alt / 2 + 16, "(TOC)", 11, APAGADO, ancora="start"))
        L.append(texto(fx, y + alt / 2 + 5, nome, 15, TXT if rest else TXT2, "600"))
    # leads caindo: alguns param no lead, alguns vazam na restrição, um chega à receita
    y_rest = topo + 2 * (alt + vao) + alt / 2
    quedas = [(-120, topo + alt + 20, 0.0), (90, topo + alt + 25, 0.6), (-40, topo + alt + 30, 1.9), (150, topo + alt + 18, 2.7),
              (-150, None, 0.3), (130, None, 1.2), (-60, None, 2.2), (60, None, 3.1),
              (-20, topo + 3 * (alt + vao) + 30, 1.5), (0, topo + 4 * (alt + vao) + 40, 0.9)]
    for dx, fim_y, atraso in quedas:
        if fim_y is None:  # vaza pela lateral na restrição
            lado = 1 if dx > 0 else -1
            cam = f"M{fx + dx},{topo - 16} L{fx + dx * .55:.0f},{y_rest:.0f} Q{fx + lado * 170},{y_rest:.0f} {fx + lado * 230},{y_rest + 120:.0f}"
            cor = VERM
        else:
            alvo = dx * max(0.15, 1 - (fim_y - topo) / 330)
            cam = f"M{fx + dx},{topo - 16} L{fx + alvo:.0f},{fim_y:.0f}"
            cor = VERM2 if fim_y > topo + 4 * (alt + vao) else "#C9A9A6"
        L.append(f'<circle r="4.5" fill="{cor}" filter="url(#brilho)" opacity="0"><animateMotion dur="4s" begin="{atraso}s" '
                 f'repeatCount="indefinite" path="{cam}"/><animate attributeName="opacity" dur="4s" begin="{atraso}s" '
                 f'repeatCount="indefinite" keyTimes="0;0.08;0.85;1" values="0;1;1;0"/></circle>'
                 f'<circle r="2.6" fill="#FFFFFF" opacity="0"><animateMotion dur="4s" begin="{atraso}s" repeatCount="indefinite" '
                 f'path="{cam}"/><animate attributeName="opacity" dur="4s" begin="{atraso}s" repeatCount="indefinite" '
                 f'keyTimes="0;0.08;0.85;1" values="0;0.9;0.9;0"/></circle>')
    L.append(texto(fx - 232, y_rest + 142, "vaza aqui", 12, VERM2, ancora="middle", esp="0.6"))
    L.append(texto(fx + 232, y_rest + 142, "vaza aqui", 12, VERM2, ancora="middle", esp="0.6"))
    grad = (f'<linearGradient id="titulo" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{VERM2}"/>'
            f'<stop offset="100%" stop-color="{VERM}"/></linearGradient>')
    return svg(W, H, "Capa da sprint-growth: comandos sendo digitados (/sprint-growth, sprint ads, audita só o GTM, sprint "
               "clarity) e um funil do tráfego à receita em que os leads vazam na restrição e poucos chegam à venda.",
               "sprint growth", "  " + "\n  ".join(L), grad)


def main():
    os.makedirs(os.path.join(AQUI, "assets"), exist_ok=True)
    for nome, fn in (("capa.svg", capa), ("fluxo.svg", fluxo), ("agentes.svg", agentes)):
        open(os.path.join(AQUI, "assets", nome), "w", encoding="utf-8").write(fn())
        print("assets/" + nome)


if __name__ == "__main__":
    main()
