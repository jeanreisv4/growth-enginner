#!/usr/bin/env python3
"""Gera os desenhos animados do README (SVG com animação nativa, roda no GitHub sem JavaScript).

  python3 scripts/desenhos.py            # grava assets/capa.svg, assets/fluxo.svg e assets/cadeia.svg

Estética do claude-seo (fundo escuro, brilho, partícula que corre pelas linhas) com o vermelho da V4 e as cores
dos blocos da aba de projeção (investimento cinza, marketing vermelho, vendas âmbar, financeiro verde).
Mudou etapa, veredito ou linha da cadeia? Edite as listas abaixo e rode de novo.
"""
import math, os

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = "'JetBrains Mono','Cascadia Mono','Menlo','Consolas',monospace"
FUNDO, VERM, VERM2 = "#161212", "#E50914", "#FF5A5F"
TXT, TXT2, APAGADO, CAIXA, CAIXA_HI, LINHA = "#F7EDEC", "#E6D6D4", "#9B8583", "#211919", "#2A1B1B", "#4A3535"
CINZA, AMBAR, VERDE = "#A08F8D", "#F2A33A", "#3CB371"

# cadeia da aba de projeção (inside sales): (bloco, nome, alavanca que o cliente edita)
CADEIA = [
    ("investimento", "verba", "fee + verba"),
    ("marketing", "impressões", "CPM"),
    ("marketing", "cliques", "CTR"),
    ("marketing", "leads", "conversão"),
    ("marketing", "MQLs", "lead → MQL"),
    ("vendas", "conexões", "sobre o lead"),
    ("vendas", "SQLs", "conexão → SQL"),
    ("vendas", "vendas", "SQL → venda"),
    ("vendas", "receita", "ticket"),
    ("financeiro", "margem", "MC1 em R$"),
    ("financeiro", "resultado", "− fee − verba"),
    ("financeiro", "acumulado", "caixa e LTV"),
    ("financeiro", "payback", "duas datas"),
]
COR_BLOCO = {"investimento": CINZA, "marketing": VERM, "vendas": AMBAR, "financeiro": VERDE}
VEREDITOS = [("REALISTA", "paga no mês-alvo", VERDE), ("COM RAMPA", "fração do caminho", AMBAR),
             ("IRREALISTA", "+ o caminho", VERM)]


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

MENSAL = [-6, -5, -3.5, -2, -0.5, 1, 2.5, 4, 5, 6, 7, 7.5]          # resultado do mês (caixa)
LTV = [-5, -8.5, -10, -10, -8.5, -5.5, -1.5, 3, 7.5, 12.5, 17.5, 22]  # acumulado por LTV


def acumulado(m):
    s, out = 0, []
    for v in m:
        s += v
        out.append(s)
    return out


def capa():
    W, H, D = 1460, 460, 9.0
    L = [f'<text x="110" y="150" font-family="{FONTE}" font-size="70" font-weight="700" fill="url(#titulo)">projeção</text>',
         f'<text x="110" y="222" font-family="{FONTE}" font-size="70" font-weight="700" fill="url(#titulo)">breakeven</text>',
         texto(114, 262, "em que mês o projeto se paga", 17, APAGADO, ancora="start", esp="0.6"),
         f'<rect x="110" y="{330 - 36}" width="640" height="56" rx="12" fill="#1C1616" stroke="#3A2A2A"/>']
    L += digitacao(["em que mês o projeto se paga?", "/projecao-breakeven <cliente>", "a meta de breakeven é realista?",
                    "quanto de verba cobre o fee?"], 140, 330)
    # gráfico: barras do resultado do mês + linhas do acumulado (caixa e LTV)
    x0, y0, esc, passo, bw = 880, 235, 7, 44, 26
    cx = lambda i: x0 + i * passo + bw / 2
    L.append(f'<line x1="{x0 - 12}" y1="{y0}" x2="{x0 + 12 * passo}" y2="{y0}" stroke="#6E4A48" stroke-width="1"/>')
    L.append(texto(x0 - 18, y0 + 4, "0", 11, APAGADO, ancora="end"))
    for i, v in enumerate(MENSAL):
        h, t0 = abs(v) * esc, .02 + i * .03
        cor = VERDE if v > 0 else VERM
        yb = y0 - h if v > 0 else y0
        anim_y = (f'<animate attributeName="y" dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(t0, t0 + .05, .93, .98)};1" '
                  f'values="{y0};{y0};{yb:.0f};{yb:.0f};{y0};{y0}"/>') if v > 0 else ""
        L.append(f'<rect x="{x0 + i * passo}" y="{y0}" width="{bw}" height="0" rx="3" fill="{cor}" fill-opacity="0.55">'
                 f'<animate attributeName="height" dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(t0, t0 + .05, .93, .98)};1" '
                 f'values="0;0;{h:.0f};{h:.0f};0;0"/>{anim_y}</rect>')
        L.append(texto(cx(i), 392, f"M{i + 1}", 10, APAGADO))
    pos = next(i for i, v in enumerate(MENSAL) if v > 0)
    L.append(texto(cx(pos), 410, "no azul a partir daqui", 11, VERDE, esp="0.3"))
    L.append(f'<line x1="{cx(pos)}" y1="{y0 + 8}" x2="{cx(pos)}" y2="378" stroke="{VERDE}" stroke-opacity="0.5" stroke-dasharray="3 4"/>')
    for serie, cor, nome, tracejado in ((acumulado(MENSAL), VERM2, "caixa", ""), (LTV, AMBAR, "LTV", ' stroke-dasharray="7 5"')):
        pts = [(cx(i), y0 - v * esc) for i, v in enumerate(serie)]
        comp = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        if tracejado:
            L.append(f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="2"{tracejado} opacity="0">'
                     f'<animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(.42, .5, .93, .98)};1" '
                     f'values="0;0;0.9;0.9;0;0"/></path>')
        else:
            L.append(f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="2.6" stroke-dasharray="{comp:.0f}" '
                     f'stroke-dashoffset="{comp:.0f}"><animate attributeName="stroke-dashoffset" dur="{D}s" repeatCount="indefinite" '
                     f'keyTimes="0;{kt(.38, .78, .93, .98)};1" values="{comp:.0f};{comp:.0f};0;0;{comp:.0f};{comp:.0f}"/></path>')
            L.append(f'<circle r="5" fill="{cor}" filter="url(#brilho)" opacity="0"><animateMotion dur="{D}s" repeatCount="indefinite" '
                     f'calcMode="linear" keyTimes="0;{kt(.38, .78)};1" keyPoints="0;0;1;1" path="{d}"/><animate attributeName="opacity" '
                     f'dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(.37, .39, .92, .98)};1" values="0;0;1;1;0;0"/></circle>')
        L.append(texto(pts[-1][0] + 12, pts[-1][1] + 4, nome, 12, cor, "600", "start"))
        # onde o acumulado cruza o zero
        k = next(i for i in range(1, len(serie)) if serie[i - 1] < 0 <= serie[i])
        fr = -serie[k - 1] / (serie[k] - serie[k - 1])
        zx = pts[k - 1][0] + fr * (pts[k][0] - pts[k - 1][0])
        t_z = .38 + .40 * (k - 1 + fr) / (len(serie) - 1) if not tracejado else .5
        L.append(f'<circle cx="{zx:.1f}" cy="{y0}" r="6" fill="{cor}" filter="url(#brilho)" opacity="0">'
                 f'<animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(t_z, t_z + .02, .93, .98)};1" '
                 f'values="0;0;1;1;0;0"/><animate attributeName="r" values="5;9;5" dur="1.2s" repeatCount="indefinite"/></circle>')
        ly = y0 + 46 if not tracejado else y0 + 26
        L.append(f'<g opacity="0"><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" '
                 f'keyTimes="0;{kt(t_z, t_z + .03, .93, .98)};1" values="0;0;1;1;0;0"/>'
                 + texto(zx, ly, f"{nome} zera em M{k + 1}", 12, cor, "600") + "</g>")
    # veredito que alterna
    Dv = 12.0
    for k, (v, sub, cor) in enumerate(VEREDITOS):
        ini, fim = k / 3, (k + 1) / 3
        vis = f"0;{kt(ini, ini + .02, fim - .02, fim)};1" if k else f"0;{kt(fim - .02, fim)};1"
        vals = "0;0;1;1;0;0" if k else "1;1;0;0"
        L.append(f'<g opacity="{1 if k == 0 else 0}"><animate attributeName="opacity" dur="{Dv}s" repeatCount="indefinite" '
                 f'keyTimes="{vis}" values="{vals}"/><rect x="880" y="48" width="330" height="34" rx="17" fill="#1C1616" '
                 f'stroke="{cor}" stroke-width="1.4"/>' + texto(900, 70, "veredito", 11, APAGADO, ancora="start", esp="0.6")
                 + texto(972, 70, f"{v} · {sub}", 12, cor, "700", "start") + "</g>")
    grad = (f'<linearGradient id="titulo" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{VERM2}"/>'
            f'<stop offset="100%" stop-color="{VERM}"/></linearGradient>')
    return svg(W, H, "Capa da projeção-breakeven: perguntas sendo digitadas e um gráfico em que o resultado do mês sai do "
               "vermelho para o verde e o acumulado de caixa e o de LTV cruzam o zero, com o veredito alternando entre "
               "realista, com rampa e irrealista com o caminho.", "projeção breakeven", "  " + "\n  ".join(L), grad)


# ---------------------------------------------------------------- fluxo

def fluxo():
    W, H, D, cy = 1690, 520, 9.0, 250
    nos = [(40, 210, "/projecao-breakeven", "cliente", True, .00, 16),
           (290, 185, "entrevista", "fonte · fee · margem R$", False, .09, 18),
           (515, 175, "taxas efetivas", "último trimestre", False, .21, 18),
           (730, 200, "economia unitária", "CAC permitido · 3 camadas", True, .33, 17),
           (1210, 190, "planilha .xlsx", "projetado | realizado", True, .65, 18),
           (1440, 200, "validação", "pycel · receita = piloto", False, .76, 18)]
    vx, vw, vys = 975, 190, [140, 250, 360]
    L = [texto(40, 44, "PROJEÇÃO-BREAKEVEN · FLUXO DO SINAL", 13, "#8A6F6D", ancora="start", esp="1.6"),
         texto(vx + vw / 2, 92, "veredito · sempre com duas datas", 11, APAGADO, esp="0.8")]
    arestas = [("M250,250 L290,250", .02, .10), ("M475,250 L515,250", .14, .22), ("M690,250 L730,250", .26, .34)]
    arestas += [(f"M930,250 C952,250 952,{y} {vx},{y}", .38, .48) for y in vys]
    arestas += [(f"M{vx + vw},{y} C1188,{y} 1188,250 1210,250", .55, .65) for y in vys]
    arestas += [("M1400,250 L1440,250", .69, .77)]
    laco = "M1540,281 Q1540,470 1360,470 L562,470 Q382,470 382,281"
    L += [f'<path d="{c}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>' for c, _, _ in arestas]
    L.append(f'<path d="{laco}" fill="none" stroke="{VERM}" stroke-opacity="0.45" stroke-width="1.3" stroke-dasharray="5 6">'
             f'<animate attributeName="stroke-dashoffset" values="0;-22" dur="1.2s" repeatCount="indefinite"/></path>')
    L.append(texto(961, 496, "↺ o realizado de cada mês entra na planilha e recalibra as taxas", 12, VERM2, esp="0.4"))
    for x, w, t1, t2, hi, t0, tam in nos:
        L.append(caixa(x, cy - 31, w, 62, t1, t2, t0, D, hi, tam))
    for (v, sub, cor), y in zip(VEREDITOS, vys):
        L.append(caixa(vx, y - 31, vw, 62, v, sub, .48, D, False, 17, cor))
    L += [particula(c, a, b, D) for c, a, b in arestas]
    L.append(particula(laco, .84, .99, D, VERM2))
    return svg(W, H, "Fluxo da projeção-breakeven: o comando entra, a entrevista fixa fonte, fee e margem em reais, o piloto "
               "calcula as taxas do último trimestre e a economia unitária, o veredito sai realista, com rampa ou irrealista "
               "com o caminho, a planilha é gerada e validada, e o realizado de cada mês recalibra as taxas.",
               "Fluxo da projeção-breakeven", "  " + "\n  ".join(L))


# ---------------------------------------------------------------- cadeia

def cadeia():
    W, H, D = 1400, 760, 11.0
    bw, bh = 200, 72
    xs = [60, 330, 600, 870, 1140]
    ys = [200, 400, 600]
    pos = [(xs[0], ys[0])] + [(x, ys[0]) for x in xs[1:]] + [(x, ys[1]) for x in xs[:0:-1]] + [(x, ys[2]) for x in xs[1:]]
    centros = [(x + bw / 2, y) for x, y in pos]
    comp = [0.0]
    for a, b in zip(centros, centros[1:]):
        comp.append(comp[-1] + math.dist(a, b))
    fr = [c / comp[-1] for c in comp]
    t_ini, t_fim = .03, .85
    L = [texto(48, 56, "PROJEÇÃO-BREAKEVEN · A CADEIA QUE A PLANILHA CALCULA", 13, "#8A6F6D", ancora="start", esp="1.6"),
         texto(xs[1], ys[0] - 58, "MARKETING · DA VERBA AO MQL", 12, VERM2, "700", "start", "1.2"),
         texto(xs[0], ys[0] - 58, "INVESTIMENTO", 12, CINZA, "700", "start", "1.2"),
         texto(xs[1], ys[1] - 58, "VENDAS · DO ATENDIMENTO À RECEITA", 12, AMBAR, "700", "start", "1.2"),
         texto(xs[1], ys[2] - 58, "FINANCEIRO · O RESULTADO", 12, VERDE, "700", "start", "1.2")]
    caminho = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in centros)
    L.append(f'<path d="{caminho}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>')
    for i, ((x, y), (bloco, nome, alav)) in enumerate(zip(pos, CADEIA)):
        cor = COR_BLOCO[bloco]
        t0 = t_ini + (t_fim - t_ini) * fr[i]
        fim = i == len(CADEIA) - 1
        L.append(f'<g><rect x="{x}" y="{y - bh / 2}" width="{bw}" height="{bh}" rx="12" fill="{CAIXA_HI if fim else CAIXA}" '
                 f'stroke="{cor}" stroke-width="{1.8 if fim else 1.2}"/>' + acende(x, y - bh / 2, bw, bh, t0, D, cor=cor)
                 + texto(x + bw / 2, y - 4, nome, 18, TXT if fim else TXT2, "600")
                 + f'<circle cx="{x + 18}" cy="{y + 18}" r="3.5" fill="{AMBAR}"/>'
                 + texto(x + 28, y + 22, alav, 11, APAGADO, ancora="start", esp="0.3") + "</g>")
    L.append(f'<circle r="10" fill="{VERM}" filter="url(#brilho)" opacity="0"><animateMotion dur="{D}s" repeatCount="indefinite" '
             f'calcMode="linear" keyTimes="0;{kt(t_ini, t_fim)};1" keyPoints="0;0;1;1" path="{caminho}"/><animate attributeName="opacity" '
             f'dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(t_ini - .01, t_ini + .01, t_fim - .01, t_fim + .02)};1" '
             f'values="0;0;0.3;0.3;0;0"/></circle>'
             f'<circle r="5.5" fill="{VERM2}" filter="url(#brilho)" opacity="0"><animateMotion dur="{D}s" repeatCount="indefinite" '
             f'calcMode="linear" keyTimes="0;{kt(t_ini, t_fim)};1" keyPoints="0;0;1;1" path="{caminho}"/><animate attributeName="opacity" '
             f'dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(t_ini - .01, t_ini + .01, t_fim - .01, t_fim + .02)};1" '
             f'values="0;0;1;1;0;0"/></circle>')
    px, py = pos[-1]
    L.append(f'<g opacity="0"><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" '
             f'keyTimes="0;{kt(t_fim, t_fim + .03, .97, .99)};1" values="0;0;1;1;0;0"/>'
             + texto(px + bw / 2, py + 62, "no azul a partir de · acumulado zera em", 12, VERDE, "600") + "</g>")
    L.append(f'<circle cx="{48}" cy="{700}" r="3.5" fill="{AMBAR}"/>'
             + texto(60, 704, "alavanca: célula amarela que o cliente edita mês a mês", 12, APAGADO, ancora="start"))
    L.append(texto(48, 732, "3 camadas de breakeven: transação ROAS = 1 / MC1 · contrato (fee + verba) / MC1 / verba "
                   "← a projeção usa · empresa + custos fixos", 12, APAGADO, ancora="start"))
    return svg(W, H, "A cadeia que a planilha da projeção-breakeven calcula: verba, impressões, cliques, leads e MQLs no "
               "marketing; conexões, SQLs, vendas e receita em vendas; margem, resultado, acumulado e payback no financeiro, "
               "com a alavanca de cada etapa.", "Cadeia da projeção-breakeven", "  " + "\n  ".join(L))


def main():
    os.makedirs(os.path.join(AQUI, "assets"), exist_ok=True)
    for nome, fn in (("capa.svg", capa), ("fluxo.svg", fluxo), ("cadeia.svg", cadeia)):
        open(os.path.join(AQUI, "assets", nome), "w", encoding="utf-8").write(fn())
        print("assets/" + nome)


if __name__ == "__main__":
    main()
