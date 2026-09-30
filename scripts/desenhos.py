#!/usr/bin/env python3
"""Gera os desenhos animados do README da raiz e os do claude-seo no mesmo visual (SVG com animação nativa).

  python3 scripts/desenhos.py      # grava assets/{capa,loop,disciplinas}.svg e claude-seo/assets/{cover,signal-flow,sub-skills,framework}.svg

Estética do claude-seo (fundo escuro, brilho, partícula que corre pelas linhas) com o vermelho da V4, igual aos
READMEs das skills. Os desenhos do claude-seo mantêm o conteúdo e o texto em inglês do original (licença MIT,
AgriciDaniel) e os mesmos nomes de arquivo, para o README dele não mudar.
"""
import math, os

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = "'JetBrains Mono','Cascadia Mono','Menlo','Consolas',monospace"
FUNDO, VERM, VERM2 = "#161212", "#E50914", "#FF5A5F"
TXT, TXT2, APAGADO, CAIXA, CAIXA_HI, LINHA = "#F7EDEC", "#E6D6D4", "#9B8583", "#211919", "#2A1B1B", "#4A3535"
CINZA, AMBAR, VERDE, AZUL = "#A08F8D", "#F2A33A", "#3CB371", "#5B8DEF"

SKILLS = [  # letra, pasta, o que faz, saída na seta para a próxima
    ("P", "projecao-breakeven", "em que mês o projeto se paga", "meta mês a mês|e CAC permitido"),
    ("T", "tracking-e-integracoes", "mede e integra até a venda", "lead e venda|com origem"),
    ("S", "sprint-growth", "acha a restrição e corrige", "plano em R$|e Executado"),
    ("C", "checkin-ropre", "realizado × projetado", ""),
]
MISSOES = [("Estratégia de tráfego|alinhada ao go-to-market", "P"), ("Atribuição da jornada|nas plataformas", "T"),
           ("Auditoria|recorrente", "S"), ("Execução de|mídia paga", "S"), ("Operação direta em|grandes clientes", "C")]
DOMINIOS = [  # domínio, [(disciplina, letras, profundidade)]  max | sol | con | lac
    ("Geração de demanda", [("Tráfego|Pago", "S", "sol"), ("Tráfego|Orgânico", "S", "sol"), ("Oferta", "S", "sol"),
                            ("Narrativa", "", "lac"), ("Direção|Visual", "", "lac")]),
    ("Jornada", [("Orquestração|de Jornada", "S", "max"), ("Inteligência|de Funil", "SP", "sol"),
                 ("Processo|Comercial", "S", "sol"), ("CRM|Marketing", "ST", "sol")]),
    ("Dados", [("Tracking", "TS", "max"), ("Mensuração e|Atribuição", "TSPC", "max"), ("Arquitetura|de Dados", "TC", "max"),
               ("Análise", "SPC", "max")]),
    ("Sistemas", [("Automação e|Orquestração", "STC", "max"), ("IA", "SPC", "max")]),
    ("Negócios", [("Economics", "PS", "sol"), ("Repertório e|Referência", "SP", "sol"), ("Produto", "", "lac"),
                  ("Comunicação|com Cliente", "C", "con"), ("Gestão de Tarefas|e Projetos", "S", "con"),
                  ("Gestão de|Pessoas", "", "lac")]),
]
PROF = {"max": (VERM, "Maximizar"), "sol": (AZUL, "Sólido"), "con": (CINZA, "Conhecer"), "lac": ("#6E5654", "lacuna")}

SEO_CLUSTERS = [  # sentido horário a partir do topo, como no original
    ("AUDIT", ["seo-audit", "seo-page", "seo-flow"]),
    ("CONTENT", ["seo-content", "seo-content-brief", "seo-cluster"]),
    ("COMMERCE·INTL", ["seo-ecommerce", "seo-hreflang", "seo-plan", "seo-programmatic", "seo-competitor-pages"]),
    ("SCHEMA", ["seo-schema", "seo-sitemap", "seo-images"]),
    ("EXTENSIONS", ["seo-dataforseo", "seo-image-gen"]),
    ("TECHNICAL", ["seo-technical", "seo-google", "seo-backlinks"]),
    ("AI·SEARCH", ["seo-geo", "seo-sxo", "seo-drift", "seo-agentic"]),
    ("LOCAL·MAPS", ["seo-local", "seo-maps"]),
]
SEO_FASES = [("PERCEIVE", "gather signals", ["observe·ext", "observe·int", "listen"]),
             ("ANALYZE", "first principles", ["think", "connect·lat", "connect·sys"]),
             ("VALIDATE", "pressure-test", ["feel", "accept"]),
             ("ACT", "ship + loop", ["create", "grow"])]


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


def digitacao(fases, x0, yb, dur_fase=4.0, tam=20, pref="dig"):
    """Comandos digitados um de cada vez, com cursor que acompanha o texto."""
    n = len(fases)
    D = dur_fase * n
    L = []
    for k, f in enumerate(fases):
        ini, fim = k / n, (k + 1) / n
        larg = len(f) * tam * 0.6025
        dig = ini + (fim - ini) * .45
        vis = f"0;{kt(ini, ini + .001, fim - .01, fim)};1" if k else f"0;{kt(fim - .01, fim)};1"
        vals = "0;0;1;1;0;0" if k else "1;1;0;0"
        conteudo = f.replace("<", "&lt;").replace(">", "&gt;")
        if conteudo.startswith("/"):
            conteudo = f'<tspan fill="{VERM2}">/</tspan>' + conteudo[1:]
        L.append(f'<clipPath id="{pref}{k}"><rect x="{x0}" y="{yb - tam * 1.5:.0f}" height="{tam * 2.2:.0f}" width="0"><animate attributeName="width" '
                 f'dur="{D}s" repeatCount="indefinite" keyTimes="0;{kt(ini, dig)};1" values="0;0;{larg:.0f};{larg:.0f}"/></rect></clipPath>')
        L.append(f'<g opacity="{1 if k == 0 else 0}"><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" '
                 f'keyTimes="{vis}" values="{vals}"/>'
                 f'<text x="{x0}" y="{yb}" clip-path="url(#{pref}{k})" font-family="{FONTE}" font-size="{tam}" fill="{TXT}">{conteudo}</text>'
                 f'<rect y="{yb - tam * 0.9:.0f}" width="2" height="{tam * 1.2:.0f}" fill="{VERM}" x="{x0}"><animate attributeName="x" dur="{D}s" '
                 f'repeatCount="indefinite" keyTimes="0;{kt(ini, dig)};1" values="{x0};{x0};{x0 + larg:.0f};{x0 + larg:.0f}"/>'
                 f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g>')
    return L


# ---------------------------------------------------------------- comuns

def gradiente():
    return (f'<linearGradient id="titulo" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{VERM2}"/>'
            f'<stop offset="100%" stop-color="{VERM}"/></linearGradient>')


def janela(conteudo, t0, t1, dur, base=0):
    """Mostra o conteúdo só entre t0 e t1 do ciclo."""
    return (f'<g opacity="{base}"><animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="0;{kt(t0, t0 + .02, t1 - .02, t1)};1" values="{base};{base};1;1;{base};{base}"/>{conteudo}</g>')


def brilho_janela(x, y, w, h, t0, t1, dur, cor, rx=10):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" stroke="{cor}" stroke-width="2.4" '
            f'filter="url(#brilho)" opacity="0"><animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="0;{kt(t0, t0 + .03, t1 - .03, t1)};1" values="0;0;0.9;0.9;0;0"/></rect>')


def linhas(x, y, s, tam, cor, peso="400", ancora="middle", passo=None):
    passo = passo or tam * 1.35
    partes = s.split("|")
    y0 = y - passo * (len(partes) - 1) / 2
    return "".join(texto(x, y0 + i * passo, p, tam, cor, peso, ancora) for i, p in enumerate(partes))


# ---------------------------------------------------------------- raiz: capa

def capa():
    W, H, D = 1460, 460, 8.0
    L = [f'<text x="110" y="150" font-family="{FONTE}" font-size="70" font-weight="700" fill="url(#titulo)">growth</text>',
         f'<text x="110" y="222" font-family="{FONTE}" font-size="70" font-weight="700" fill="url(#titulo)">engineer</text>',
         texto(114, 262, "do clique à venda · 4 skills · 1 loop por mês", 17, APAGADO, ancora="start", esp="0.6"),
         f'<rect x="110" y="{330 - 36}" width="640" height="56" rx="12" fill="#1C1616" stroke="#3A2A2A"/>']
    L += digitacao(["/projecao-breakeven <cliente>", "/tracking-e-integracoes integrar", "/sprint-growth <cliente>",
                    "/checkin-ropre <cliente>", "/seo audit <site>"], 140, 330)
    cx, cy, r = 1150, 230, 170
    circ = f"M{cx},{cy - r} A{r},{r} 0 1,1 {cx - .01},{cy - r}"
    L.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINHA}" stroke-width="1.2"/>')
    L.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 26}" fill="none" stroke="{VERM}" stroke-opacity="0.3" stroke-dasharray="3 9">'
             f'<animateTransform attributeName="transform" type="rotate" values="0 {cx} {cy};360 {cx} {cy}" dur="50s" '
             f'repeatCount="indefinite"/></circle>')
    L.append(texto(cx, cy - 4, "receita do cliente", 14, TXT, "600"))
    L.append(texto(cx, cy + 16, "do clique à venda", 11, APAGADO, esp="0.4"))
    pos = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    nomes = ["projeção", "tracking", "sprint", "check-in"]
    for i, ((x, y), n) in enumerate(zip(pos, nomes)):
        bw, bh = 140, 42
        L.append(f'<g><rect x="{x - bw / 2}" y="{y - bh / 2}" width="{bw}" height="{bh}" rx="21" fill="{CAIXA_HI}" stroke="{VERM}" '
                 f'stroke-width="1.4"/>' + acende(x - bw / 2, y - bh / 2, bw, bh, i / 4, D, 21)
                 + texto(x, y + 5, n, 15, TXT, "600") + "</g>")
    L.append(f'<circle r="10" fill="{VERM}" filter="url(#brilho)" opacity="0.3"><animateMotion dur="{D}s" repeatCount="indefinite" '
             f'path="{circ}"/></circle><circle r="5.5" fill="{VERM2}" filter="url(#brilho)"><animateMotion dur="{D}s" '
             f'repeatCount="indefinite" path="{circ}"/><animate attributeName="r" values="5;6.5;5" dur="1.4s" repeatCount="indefinite"/></circle>')
    return svg(W, H, "Capa do growth engineer: os comandos das skills sendo digitados e o loop do cliente girando entre "
               "projeção, tracking, sprint e check-in em volta da receita do cliente.", "growth engineer",
               "  " + "\n  ".join(L), gradiente())


# ---------------------------------------------------------------- raiz: loop

def loop():
    W, H, D = 1460, 640, 10.0
    bw, bh, by = 240, 92, 330
    xs = [50, 410, 770, 1130]
    L = [texto(40, 44, "GROWTH ENGINEER · O LOOP DO CLIENTE", 13, "#8A6F6D", ancora="start", esp="1.6"),
         texto(40, 84, "canais lineares · as 5 missões do cargo", 11, APAGADO, ancora="start", esp="0.8"),
         texto(40, by - bh / 2 - 22, "loop do cliente · uma volta por mês", 11, APAGADO, ancora="start", esp="0.8")]
    centro = {s[0]: xs[i] + bw / 2 for i, s in enumerate(SKILLS)}
    mw, mh, my = 250, 58, 104
    mxs = [40 + i * 280 for i in range(5)]
    for i, ((m, alvo), x) in enumerate(zip(MISSOES, mxs)):
        tx = centro[alvo] + (-30 if (alvo == "S" and i == 2) else 30 if alvo == "S" else 0)
        cam = f"M{x + mw / 2},{my + mh} C{x + mw / 2},{my + mh + 60} {tx},{by - bh / 2 - 60} {tx},{by - bh / 2}"
        L.append(f'<path d="{cam}" fill="none" stroke="{CINZA}" stroke-opacity="0.45" stroke-width="1.1" stroke-dasharray="4 5"/>')
        t0 = .05 + i * .12
        L.append(particula(cam, t0, t0 + .1, D, CINZA))
        L.append(f'<g><rect x="{x}" y="{my}" width="{mw}" height="{mh}" rx="10" fill="{CAIXA}" stroke="#6E5E5C"/>'
                 + linhas(x + mw / 2, my + mh / 2 + 4, m, 13, TXT2, "600") + "</g>")
    ts = [.10, .30, .50, .70]
    for i, ((letra, nome, faz, saida), x) in enumerate(zip(SKILLS, xs)):
        L.append(f'<g><rect x="{x}" y="{by - bh / 2}" width="{bw}" height="{bh}" rx="12" fill="{CAIXA_HI}" stroke="{VERM}" '
                 f'stroke-width="1.6"/>' + acende(x, by - bh / 2, bw, bh, ts[i], D)
                 + texto(x + 18, by - 14, letra, 13, VERM2, "700", "start")
                 + texto(x + bw / 2 + 8, by - 8, nome, 15 if len(nome) > 18 else 17, TXT, "700")
                 + texto(x + bw / 2, by + 18, faz, 12, APAGADO, esp="0.3") + "</g>")
        if saida:
            a, b = x + bw, xs[i + 1]
            cam = f"M{a},{by} L{b},{by}"
            L.append(f'<path d="{cam}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>')
            L.append(linhas((a + b) / 2, by + 34, saida, 11, AMBAR))
            L.append(particula(cam, ts[i] + .05, ts[i + 1], D))
    volta = f"M{xs[3] + bw / 2},{by + bh / 2} Q{xs[3] + bw / 2},{by + 150} {xs[3] + bw / 2 - 180},{by + 150} L{xs[0] + bw / 2 + 180},{by + 150} Q{xs[0] + bw / 2},{by + 150} {xs[0] + bw / 2},{by + bh / 2}"
    L.append(f'<path d="{volta}" fill="none" stroke="{VERM}" stroke-opacity="0.45" stroke-width="1.3" stroke-dasharray="5 6">'
             f'<animate attributeName="stroke-dashoffset" values="0;-22" dur="1.2s" repeatCount="indefinite"/></path>')
    L.append(texto(730, by + 172, "↺ desvio explicado e premissas novas voltam para a projeção", 12, VERM2, esp="0.4"))
    L.append(particula(volta, .78, .99, D, VERM2))
    # complemento: claude-seo alimenta a sprint (tráfego orgânico)
    sx, sy = xs[2] + bw / 2, by + 230
    L.append(f'<path d="M{sx},{sy - 26} L{sx},{by + bh / 2}" fill="none" stroke="{AMBAR}" stroke-opacity="0.5" stroke-dasharray="3 5"/>')
    L.append(f'<g><rect x="{sx - 150}" y="{sy - 26}" width="300" height="52" rx="10" fill="{CAIXA}" stroke="{AMBAR}" '
             f'stroke-dasharray="5 4"/>' + texto(sx, sy - 3, "claude-seo · complemento", 14, AMBAR, "600")
             + texto(sx, sy + 15, "SEO completo (MIT, AgriciDaniel)", 11, APAGADO) + "</g>")
    return svg(W, H, "O loop do growth engineer: as 5 missões do cargo alimentam o loop do cliente, em que a projeção dá a "
               "meta, o tracking mede e integra do clique à venda, a sprint acha a restrição e corrige, o check-in reporta realizado "
               "contra projetado e o desvio volta para a projeção; o claude-seo complementa a sprint.",
               "Loop do growth engineer", "  " + "\n  ".join(L))


# ---------------------------------------------------------------- raiz: disciplinas

def disciplinas():
    W, H, D = 1460, 760, 12.0
    cw, ch, passo, x0 = 182, 70, 194, 250
    ys = [190 + 104 * i for i in range(len(DOMINIOS))]
    L = [texto(40, 44, "GROWTH ENGINEER · AS 21 DISCIPLINAS DO PDI", 13, "#8A6F6D", ancora="start", esp="1.6")]
    nomes = {"P": "projecao-breakeven", "T": "tracking-e-integracoes", "S": "sprint-growth", "C": "checkin-ropre"}
    for k, letra in enumerate("PTSC"):
        x = 40 + k * 260
        t0, t1 = k / 4, (k + 1) / 4
        L.append(f'<rect x="{x}" y="72" width="244" height="40" rx="20" fill="{CAIXA}" stroke="#6E4A48"/>')
        L.append(brilho_janela(x, 72, 244, 40, t0, t1, D, VERM, 20))
        L.append(janela(f'<rect x="{x}" y="72" width="244" height="40" rx="20" fill="{CAIXA_HI}" stroke="{VERM}" stroke-width="1.6"/>',
                        t0, t1, D))
        L.append(texto(x + 22, 97, letra, 14, VERM2, "700", "start"))
        L.append(texto(x + 42, 97, nomes[letra], 13, TXT2, "600", "start"))
    for (dom, itens), y in zip(DOMINIOS, ys):
        L.append(linhas(40, y, dom.replace(" de ", "|de "), 14, TXT, "700", "start"))
        for j, (nome, letras, prof) in enumerate(itens):
            x = x0 + j * passo
            cor, _ = PROF[prof]
            trac = ' stroke-dasharray="5 4"' if prof == "lac" else ""
            L.append(f'<rect x="{x}" y="{y - ch / 2}" width="{cw}" height="{ch}" rx="10" fill="{CAIXA}" stroke="{cor}" '
                     f'stroke-width="{1.5 if prof == "max" else 1.1}"{trac}/>')
            for k, letra in enumerate("PTSC"):
                if letra in letras:
                    L.append(brilho_janela(x, y - ch / 2, cw, ch, k / 4, (k + 1) / 4, D, cor))
            L.append(linhas(x + cw / 2, y - 8, nome, 13, TXT2 if prof != "lac" else APAGADO, "600"))
            if letras:
                bolinhas = []
                for k, letra in enumerate("PTSC"):
                    if letra not in letras:
                        continue
                    bx = x + cw / 2 - (len(letras) - 1) * 11 + letras.index(letra) * 22
                    bolinhas.append(texto(bx, y + 25, letra, 11, APAGADO, "700"))
                    bolinhas.append(janela(texto(bx, y + 25, letra, 11, VERM2, "700"), k / 4, (k + 1) / 4, D))
                L.append("".join(bolinhas))
            else:
                L.append(texto(x + cw / 2, y + 25, "lacuna", 11, "#6E5654"))
    ly = ys[-1] + 80
    for k, prof in enumerate(("max", "sol", "con", "lac")):
        cor, rot = PROF[prof]
        x = 40 + k * 200
        trac = ' stroke-dasharray="4 3"' if prof == "lac" else ""
        L.append(f'<rect x="{x}" y="{ly - 11}" width="22" height="14" rx="4" fill="none" stroke="{cor}"{trac}/>'
                 + texto(x + 32, ly, rot, 12, APAGADO, ancora="start"))
    L.append(texto(840, ly, "a cada 3 s uma skill acende as disciplinas que exercita", 12, APAGADO, ancora="start"))
    return svg(W, H, "As 21 disciplinas do PDI de growth engineer por domínio e profundidade; uma skill por vez acende as "
               "disciplinas que exercita, e as lacunas (Narrativa, Direção Visual, Produto, Gestão de Pessoas) ficam "
               "tracejadas.", "Disciplinas do growth engineer", "  " + "\n  ".join(L))


# ---------------------------------------------------------------- claude-seo: cover

def seo_cover():
    W, H, D = 1680, 768, 12.0
    L = [f'<text x="130" y="330" font-family="{FONTE}" font-size="112" font-weight="700" fill="url(#titulo)">claude seo</text>',
         texto(136, 384, "SEO analysis for any website, inside Claude Code", 20, APAGADO, ancora="start", esp="0.6"),
         f'<rect x="130" y="{470 - 44}" width="760" height="68" rx="14" fill="#1C1616" stroke="#3A2A2A"/>']
    L += digitacao(["/seo audit my website", "/seo schema example.com", "/seo geo my homepage", "/seo content my blog",
                    "/seo backlinks rival.com"], 166, 470, 4.0, 26, "cmd")
    # SERP: a pergunta muda, o AI Overview cita o site e o site sobe do #5 ao #1
    px, py, pw = 1010, 110, 560
    perguntas = ["how to rank #1?", "what is E-E-A-T?", "get cited by AI?", "Core Web Vitals?", "what is GEO?"]
    L.append(f'<rect x="{px}" y="{py}" width="{pw}" height="560" rx="18" fill="#1A1414" stroke="#3A2A2A"/>')
    L.append(f'<rect x="{px + 24}" y="{py + 24}" width="{pw - 48}" height="50" rx="25" fill="{CAIXA}" stroke="#4A3535"/>')
    L.append(f'<circle cx="{px + 54}" cy="{py + 49}" r="9" fill="none" stroke="{APAGADO}" stroke-width="2"/>'
             f'<line x1="{px + 61}" y1="{py + 56}" x2="{px + 68}" y2="{py + 63}" stroke="{APAGADO}" stroke-width="2"/>')
    n = len(perguntas)
    for k, q in enumerate(perguntas):
        L.append(janela(texto(px + 84, py + 55, q, 18, TXT, ancora="start"), k / n, (k + 1) / n, D, 1 if k == 0 else 0)
                 if k else f'<g opacity="1"><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" '
                           f'keyTimes="0;{kt(1 / n - .02, 1 / n)};1" values="1;1;0;0"/>'
                           + texto(px + 84, py + 55, q, 18, TXT, ancora="start") + "</g>")
    ay = py + 100
    L.append(f'<rect x="{px + 24}" y="{ay}" width="{pw - 48}" height="86" rx="12" fill="{CAIXA_HI}" stroke="{VERM}" stroke-width="1.2"/>')
    L.append(brilho_janela(px + 24, ay, pw - 48, 86, .72, .98, D, VERM, 12))
    L.append(texto(px + 44, ay + 28, "AI Overview", 14, VERM2, "700", "start", "0.6"))
    for j, w in enumerate((380, 300)):
        L.append(f'<rect x="{px + 44}" y="{ay + 42 + j * 16}" width="{w}" height="7" rx="3.5" fill="#4A3535"/>')
    L.append(janela(f'<rect x="{px + pw - 190}" y="{ay + 14}" width="150" height="26" rx="13" fill="{VERM}" fill-opacity="0.2" '
                    f'stroke="{VERM}"/>' + texto(px + pw - 115, ay + 32, "cites your site", 12, TXT, "600"), .72, .98, D))
    slot = lambda s: ay + 118 + s * 66
    for s in range(5):
        L.append(texto(px + 44, slot(s) + 32, f"#{s + 1}", 14, APAGADO, "700", "start"))
    # quatro concorrentes descem uma posição quando o site passa por eles
    passos = [.15, .30, .45, .60]   # o site entra na posição 4, 3, 2, 1
    for j in range(4):
        entra = passos[3 - j]
        vals = f"{slot(j):.0f};{slot(j):.0f};{slot(j + 1):.0f};{slot(j + 1):.0f};{slot(j):.0f};{slot(j):.0f}"
        L.append(f'<g><animateTransform attributeName="transform" type="translate" dur="{D}s" repeatCount="indefinite" '
                 f'keyTimes="0;{kt(entra, entra + .04, .95, .99)};1" values="{";".join("0 " + str(float(v) - slot(j)) for v in vals.split(";"))}"/>'
                 f'<rect x="{px + 90}" y="{slot(j)}" width="{pw - 114}" height="54" rx="10" fill="{CAIXA}" stroke="#3A2A2A"/>'
                 f'<circle cx="{px + 114}" cy="{slot(j) + 27}" r="9" fill="#4A3535"/>'
                 + texto(px + 134, slot(j) + 24, f"competitor-{j + 1}.com", 12, APAGADO, ancora="start")
                 + f'<rect x="{px + 134}" y="{slot(j) + 33}" width="{220 - j * 20}" height="7" rx="3.5" fill="#3A2E2E"/></g>')
    ys = [slot(4), slot(4), slot(3), slot(3), slot(2), slot(2), slot(1), slot(1), slot(0), slot(0), slot(4), slot(4)]
    tk = [0, .15, .19, .30, .34, .45, .49, .60, .64, .95, .99, 1]
    L.append(f'<g><animateTransform attributeName="transform" type="translate" dur="{D}s" repeatCount="indefinite" '
             f'keyTimes="{";".join(f"{t:.3f}" for t in tk)}" values="{";".join(f"0 {y - slot(4):.0f}" for y in ys)}"/>'
             f'<rect x="{px + 90}" y="{slot(4)}" width="{pw - 114}" height="54" rx="10" fill="{CAIXA_HI}" stroke="{VERM}" stroke-width="1.6"/>'
             f'<rect x="{px + 90}" y="{slot(4)}" width="{pw - 114}" height="54" rx="10" fill="none" stroke="{VERM}" stroke-width="2.4" '
             f'filter="url(#brilho)" opacity="0.6"/>'
             f'<circle cx="{px + 114}" cy="{slot(4) + 27}" r="9" fill="{VERM}"/>'
             + texto(px + 134, slot(4) + 24, "your-site.com", 13, TXT, "700", "start")
             + f'<rect x="{px + 134}" y="{slot(4) + 33}" width="260" height="7" rx="3.5" fill="{VERM}" fill-opacity="0.5"/></g>')
    return svg(W, H, "Claude SEO cover: /seo commands being typed next to a search results page where your site climbs "
               "from #5 to #1 and the AI Overview cites it.", "claude seo", "  " + "\n  ".join(L), gradiente())


# ---------------------------------------------------------------- claude-seo: signal flow

def seo_signal_flow():
    W, H, D, cy = 1460, 420, 6.0, 212
    nos = [(47, 130, "/seo audit", "entry", True, .00), (267, 158, "crawl", "to 500 pages", False, .09),
           (501, 158, "seo/SKILL.md", "orchestrator", True, .25), (1002, 168, "scoring", "weighted dims", False, .61),
           (1241, 158, "report", "score · plan", True, .75)]
    ramos = [(753, 158, 104, "26 sub-skills", "modules"), (742, 180, 212, "17 audit agents", "parallel"),
             (762, 139, 320, "AI search", "GEO + LLMs")]
    L = [texto(40, 50, "CLAUDE-SEO · AUDIT SIGNAL FLOW", 13, "#8A6F6D", ancora="start", esp="1.6")]
    arestas = [("M177,212 L267,212", .02, .14), ("M425,212 L501,212", .14, .30)]
    arestas += [(f"M659,212 C706,212 706,{y} {x},{y}", .32, .46) for x, w, y, *_ in ramos]
    arestas += [(f"M{x + w},{y} C957,{y} 957,212 1002,212", .50, .66) for x, w, y, *_ in ramos]
    arestas += [("M1170,212 L1241,212", .66, .80)]
    L += [f'<path d="{c}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>' for c, _, _ in arestas]
    for x, w, t1, t2, hi, t0 in nos:
        L.append(caixa(x, cy - 31, w, 62, t1, t2, t0, D, hi))
    for x, w, y, t1, t2 in ramos:
        L.append(caixa(x, y - 31, w, 62, t1, t2, .41, D))
    L += [particula(c, a, b, D) for c, a, b in arestas]
    return svg(W, H, "Claude SEO audit signal flow: /seo audit enters, crawls the site, fans out through the orchestrator to "
               "26 sub-skills, up to 17 parallel audit agents, and AI-search analysis, converges through scoring, and ripens "
               "into a prioritized report.", "Claude SEO audit signal flow", "  " + "\n  ".join(L))


# ---------------------------------------------------------------- claude-seo: sub-skills

def seo_sub_skills():
    W, H, D = 1180, 760, 8.0
    cx, cy, rx, ry, bw = 590, 400, 380, 290, 210
    L = [texto(48, 56, "CLAUDE-SEO · 26 SUB-SKILLS · 8 CLUSTERS", 13, "#8A6F6D", ancora="start", esp="1.6"),
         f'<circle cx="{cx}" cy="{cy}" r="250" fill="none" stroke="{LINHA}" stroke-width="1"/>',
         f'<circle cx="{cx}" cy="{cy}" r="150" fill="none" stroke="{VERM}" stroke-opacity="0.35" stroke-width="1.2" '
         f'stroke-dasharray="3 9"><animateTransform attributeName="transform" type="rotate" values="0 {cx} {cy};360 {cx} {cy}" '
         f'dur="60s" repeatCount="indefinite"/></circle>']
    pos = [(cx + rx * math.cos(math.radians(-90 + 45 * i)), cy + ry * math.sin(math.radians(-90 + 45 * i))) for i in range(8)]
    for x, y in pos:
        L.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="{LINHA}" stroke-width="1"/>')
    passo = 1 / 8
    for i, ((x, y), (nome, itens)) in enumerate(zip(pos, SEO_CLUSTERS)):
        t0 = i * passo
        bh = 40 + 20 * len(itens)
        bx, by = x - bw / 2, y - bh / 2
        L.append(particula(f"M{cx},{cy} L{x:.0f},{y:.0f}", t0, t0 + passo * .8, D))
        L.append(f'<g><rect x="{bx:.0f}" y="{by:.0f}" width="{bw}" height="{bh}" rx="10" fill="{CAIXA_HI if i == 0 else CAIXA}" '
                 f'stroke="{VERM if i == 0 else "#6E4A48"}" stroke-width="{1.6 if i == 0 else 1.1}"/>'
                 + acende(round(bx), round(by), bw, bh, t0 + passo * .8, D, 10)
                 + texto(bx + 16, by + 24, nome, 13, VERM2, "700", "start", "1.2")
                 + texto(bx + bw - 16, by + 24, f"{len(itens):02d}", 11, APAGADO, ancora="end")
                 + "".join(texto(bx + 16, by + 46 + 20 * k, it, 13, TXT2, ancora="start") for k, it in enumerate(itens)) + "</g>")
    L.append(f'<circle cx="{cx}" cy="{cy}" r="70" fill="none" stroke="{VERM}" stroke-width="2" opacity="0">'
             f'<animate attributeName="r" values="70;115" dur="{D / 8}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0.6;0" dur="{D / 8}s" repeatCount="indefinite"/></circle>')
    L.append(f'<circle cx="{cx}" cy="{cy}" r="70" fill="{CAIXA_HI}" stroke="{VERM}" stroke-width="2"/>')
    L.append(texto(cx, cy - 4, "seo/", 16, TXT, "700"))
    L.append(texto(cx, cy + 16, "orchestrator", 12, APAGADO, esp="0.4"))
    return svg(W, H, "Claude SEO sub-skill ecosystem: 26 modules grouped into 8 clusters (audit, content, commerce and intl, "
               "schema, extensions, technical, AI search, local and maps) around the central orchestrator.",
               "Claude SEO sub-skills", "  " + "\n  ".join(L))


# ---------------------------------------------------------------- claude-seo: framework

def seo_framework():
    W, H, D = 1020, 640, 8.0
    L = [texto(40, 50, "CLAUDE-SEO · 10-PRINCIPLE METHOD · 4 PHASES", 13, "#8A6F6D", ancora="start", esp="1.6")]
    ys = [140 + 125 * i for i in range(4)]
    lx = 64
    trilho = f"M{lx},{ys[0]} L{lx},{ys[-1]}"
    L.append(f'<path d="{trilho}" fill="none" stroke="{LINHA}" stroke-width="1.4"/>')
    L.append(particula(trilho, .02, .9, D))
    for i, ((fase, sub, chips), y) in enumerate(zip(SEO_FASES, ys)):
        t0 = .02 + .88 * i / 3
        L.append(f'<circle cx="{lx}" cy="{y}" r="8" fill="{FUNDO}" stroke="{VERM2}" stroke-width="2"/>')
        L.append(f'<line x1="{lx + 8}" y1="{y}" x2="100" y2="{y}" stroke="{LINHA}"/>')
        L.append(f'<g><rect x="100" y="{y - 50}" width="880" height="100" rx="14" fill="{CAIXA}" stroke="#4A3535"/>'
                 + acende(100, y - 50, 880, 100, t0, D, 14)
                 + texto(128, y - 20, f"{i + 1:02d}", 12, APAGADO, ancora="start")
                 + texto(128, y + 8, fase, 26, VERM2 if i % 2 == 0 else VERM, "700", "start")
                 + texto(128, y + 32, sub, 13, APAGADO, ancora="start") + "</g>")
        x = 420
        for j, c in enumerate(chips):
            w = len(c) * 10 + 34
            tc = t0 + .03 + j * .025
            L.append(f'<g><rect x="{x}" y="{y - 20}" width="{w}" height="40" rx="10" fill="{CAIXA_HI}" stroke="#6E4A48"/>'
                     + acende(x, y - 20, w, 40, tc, D, 10) + texto(x + w / 2, y + 6, c, 16, TXT2, "600") + "</g>")
            x += w + 18
    return svg(W, H, "Claude SEO 10-principle methodology: PERCEIVE, ANALYZE, VALIDATE, and ACT phases with 10 principles "
               "arranged by phase.", "Claude SEO methodology", "  " + "\n  ".join(L))


def main():
    saidas = [("assets/capa.svg", capa), ("assets/loop.svg", loop), ("assets/disciplinas.svg", disciplinas),
              ("claude-seo/assets/cover.svg", seo_cover), ("claude-seo/assets/signal-flow.svg", seo_signal_flow),
              ("claude-seo/assets/sub-skills.svg", seo_sub_skills), ("claude-seo/assets/framework.svg", seo_framework)]
    for caminho, fn in saidas:
        destino = os.path.join(AQUI, caminho)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        open(destino, "w", encoding="utf-8").write(fn())
        print(caminho)


if __name__ == "__main__":
    main()
