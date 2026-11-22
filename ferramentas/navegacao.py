"""Navegação igual em todas as páginas do site: o menu no topo (o mesmo da inicial, com a página atual marcada), a trilha de navegação
(Início › Pedais › 2026 › pedal) nas páginas de pedal, cidade, mapa, lista do ano e ferramenta, e o mesmo rodapé.

Roda na publicação (workflow cloudflare.yml), sobre a cópia que vai para o ar: os geradores e os robôs não precisam saber dele, e
uma página refeita por um robô ganha a navegação de novo na publicação seguinte. Rodar de novo não duplica nada (os blocos têm marcas).
Uso: python ferramentas/navegacao.py PASTA_DO_SITE
"""
import datetime
import html
import json
import os
import re
import sys

SITE = "https://brotenatrilha.com.br"
ANO = datetime.date.today().year
# o menu: (página, endereço, rótulo); "pedais" vale para tudo debaixo de /pedais/ (pedais, cidades, mapa, anos)
MENU = [("videos", "/#videos", "Vídeos"), ("pedais", "/pedais/", "Pedais"),       # Subidas fica dentro de Pedais (decisão do usuário)
        ("planejar-pedal", "/planejar-pedal/", "Planejar pedal"), ("analises", "/analises/", "Análises"),
        ("ferramentas", "/ferramentas/", "Ferramentas"), ("sobre", "/sobre/", "Sobre")]
RODAPE_LINKS = [("/pedais/", "Pedais"), ("/subidas/", "Subidas"), ("/planejar-pedal/", "Planejar pedal"), ("/analises/", "Análises"),
                ("/ferramentas/", "Ferramentas"), ("/sobre/", "Sobre"), ("/bnteditor/", "BNT Editor"), ("/privacidade/", "Privacidade"),
                ("https://www.youtube.com/@BroteNaTrilha", "Canal no YouTube")]

# A serra no pé da faixa verde de cada página (montanhas, morros e pinheiros em branco translúcido) e o "easter egg":
# um ciclista que atravessa a serra de vez em quando. Desenhos em SVG, sem arquivo a mais.
def _svg(conteudo, largura, altura):
    import urllib.parse
    return "url(\"data:image/svg+xml," + urllib.parse.quote(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{largura}' height='{altura}' viewBox='0 0 {largura} {altura}'>{conteudo}</svg>", safe=" ='/:") + "\")"


def _morro(x):
    """A altura da linha dos morros (em px, de cima da faixa de 48) no ponto x; repete a cada 600 px, como o desenho."""
    import math
    return 37 - 4 * math.sin(2 * math.pi * x / 300) - 2.5 * math.sin(2 * math.pi * x / 120 + 1)


def _pinheiro(x, base, alto):
    """Um pinheiro de três andares (triângulos que se sobrepõem) e o tronco, com o pé em (x, base)."""
    partes = [f"<rect x='{x - .8:.1f}' y='{base - alto * .15:.1f}' width='1.6' height='{alto * .15:.1f}'/>"]
    for andar in range(3):
        topo = base - alto + andar * alto * .24
        pe = topo + alto * .42
        meio = alto * (.16 + .07 * andar)
        partes.append(f"<path d='M{x} {topo:.1f} L{x + meio:.1f} {pe:.1f} L{x - meio:.1f} {pe:.1f} Z'/>")
    return "".join(partes)


SERRA = _svg(
    "<path fill='white' fill-opacity='.07' d='M0 48 L0 30 L40 18 L85 26 L130 8 L175 22 L215 14 L260 27 L310 6 L355 20 L400 12 L450 25 L500 10 L550 21 L600 30 L600 48 Z'/>"
    "<path fill='white' fill-opacity='.10' d='M0 48 " + " ".join(f"L{x} {_morro(x):.1f}" for x in range(0, 601, 6)) + " L600 48 Z'/>"
    "<g fill='white' fill-opacity='.14'>" + "".join(_pinheiro(x, 46, a) for x, a in
                                                  ((34, 18), (46, 13), (150, 15), (290, 20), (303, 14), (316, 17), (430, 14), (522, 19), (536, 13))) + "</g>",
    600, 48)
def _roda(cx, cy, volta):
    """Uma roda do ícone (pneu cheio) com raios e cubo que giram."""
    raios = "".join(f"<rect x='{cx - .28}' y='{cy - 3.4}' width='.56' height='6.8' transform='rotate({g} {cx} {cy})'/>" for g in (0, 60, 120))
    return (f"<path fill-rule='evenodd' d='M{cx - 5} {cy}a5 5 0 1 0 10 0a5 5 0 1 0-10 0zM{cx - 3.5} {cy}a3.5 3.5 0 1 0 7 0a3.5 3.5 0 1 0-7 0z'/>"
            f"<g>{raios}<circle cx='{cx}' cy='{cy}' r='.9'/>"
            f"<animateTransform attributeName='transform' type='rotate' from='0 {cx} {cy}' to='360 {cx} {cy}' dur='{volta}' repeatCount='indefinite'/></g>")


# O ciclista: a silhueta do ícone "directions_bike" do Material Design (Google, licença Apache 2.0), com as rodas
# trocadas por rodas que giram. Desenho em 24 x 24, mostrado em 36 x 36 px.
_VOLTA = "0.8s"
CICLISTA = _svg(
    "<g fill='white' opacity='.8'>"
    "<path d='M15.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2s-2 .9-2 2s.9 2 2 2'/>"                                    # a cabeça
    "<path d='M10.8 10.5l2.4-2.4l.8.8c1.3 1.3 3 2.1 5.1 2.1V9c-1.5 0-2.7-.6-3.6-1.5l-1.9-1.9c-.5-.4-1-.6-1.6-.6"
    "s-1.1.2-1.4.6L7.8 8.4c-.4.4-.6.9-.6 1.4c0 .6.2 1.1.6 1.4L11 14v5h2v-6.2z'/>"                            # o corpo
    + _roda(5, 17, _VOLTA) + _roda(19, 17, _VOLTA) + "</g>",
    24, 24).replace("width='24' height='24'", "width='36' height='36'")

def _caminho_do_ciclista(distancia=2600, passo=10, fracao=.45):
    """Os quadros da animação: a roda sempre na linha dos morros (translate) e a bike inclinada como o morro (rotate).
    O ciclista anda `distancia` px na `fracao` do ciclo e fica fora da tela no resto (passa de novo no ciclo seguinte)."""
    import math
    quadros = []
    for x in range(-60, distancia + 1, passo):
        tras, frente = _morro(x - 10.5), _morro(x + 10.5)              # as duas rodas na linha dos morros: a bike apoia nas duas
        inclinacao = math.degrees(math.atan2(frente - tras, 21))
        pct = (x + 60) / (distancia + 60) * fracao * 100
        quadros.append(f"{pct:.2f}% {{ transform: translate({x - 18}px, {(tras + frente) / 2 - 45:.1f}px) rotate({inclinacao:.1f}deg); }}")
    quadros.append(f"100% {{ transform: translate({distancia - 22}px, 0); }}")
    return "@keyframes ns-pedala { " + " ".join(quadros) + " }"


PEDALA = _caminho_do_ciclista()
CICLISTAS = '<span class="ns-ciclista" aria-hidden="true"></span>' * 3          # o grupo do pedal: três ciclistas em fila

ESTILO = """<link rel="preload" href="/fontes/inter-latin.woff2" as="font" type="font/woff2" crossorigin id="ns-fonte">
<style id="ns-estilo">
  /* a mesma fonte em todos os aparelhos (Inter, hospedada no site, licença OFL em /fontes/) e os mesmos tamanhos de título em todas as páginas */
  @font-face { font-family: "Inter"; src: url("/fontes/inter-latin.woff2") format("woff2"); font-weight: 400 800; font-display: swap; }
  html body, html body button, html body input, html body select, html body textarea { font-family: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif !important; }
  html body h1 { font-size: clamp(1.6rem, 4.4vw, 2.3rem) !important; line-height: 1.15 !important; letter-spacing: -.02em !important; }
  html body main h2, html body section h2 { font-size: clamp(1.15rem, 2.4vw, 1.4rem) !important; line-height: 1.25 !important; }
  html body main h3 { font-size: 1.05rem !important; line-height: 1.3 !important; }
  .ns-barra { background: #0f1a13; border-bottom: 1px solid rgba(255,255,255,.08); font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .ns-barra .ns-miolo { max-width: 1100px; margin: 0 auto; padding: 0 16px; display: flex; align-items: center; gap: 10px; min-height: 40px; }
  .ns-marca { display: inline-flex; align-items: center; gap: 8px; color: #fff; font-weight: 700; font-size: .98rem; letter-spacing: -.01em; text-decoration: none; white-space: nowrap; flex: none; }
  .ns-marca img { width: 26px; height: 26px; border-radius: 50%; }
  .ns-menu { display: flex; gap: 2px; overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
  .ns-menu::-webkit-scrollbar { display: none; }
  @media (max-width: 760px) { .ns-menu { -webkit-mask-image: linear-gradient(to right, #000 85%, transparent); mask-image: linear-gradient(to right, #000 85%, transparent); padding-right: 24px; } }
  .ns-menu a { color: #cfdcd3; text-decoration: none; font-size: .84rem; font-weight: 600; padding: 4px 9px; border-radius: 999px; white-space: nowrap; }
  .ns-menu a:hover { color: #fff; background: rgba(255,255,255,.07); }
  .ns-menu a[aria-current="page"] { color: #fff; background: #1f8448; }
  .ns-trilha { font-size: .8rem; margin-bottom: 4px; }
  .ns-trilha ol { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 2px 6px; }
  .ns-trilha li + li::before { content: "›"; margin-right: 6px; opacity: .7; }
  .ns-trilha a { color: inherit; opacity: .9; }
  .ns-trilha [aria-current] { opacity: .75; }
  /* o vão antes do rodapé: o fim do conteúdo de cada página tinha folga demais (padding do main + margem do último bloco + a do rodapé) */
  body > main { padding-bottom: 24px !important; }
  body > main > :last-child { margin-bottom: 0 !important; }
  body > main:has(> section:last-of-type) { padding-bottom: 0 !important; }      /* página feita de faixas (inicial, Sobre, BNT Editor): a última faixa encosta no rodapé */
  body > main > section:last-of-type { padding-bottom: 24px !important; }
  body > main > section:last-of-type > * > :last-child { margin-bottom: 0 !important; }
  .ns-rodape { background: #0c1510; color: #b9c8bd; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; font-size: .8rem; padding: 14px 0 16px; margin-top: 0; }
  .ns-rodape .ns-miolo { max-width: 1100px; margin: 0 auto; padding: 0 16px; display: flex; flex-wrap: wrap; gap: 8px 20px; align-items: center; justify-content: space-between; }
  .ns-rodape nav { display: flex; flex-wrap: wrap; gap: 4px 12px; }
  .ns-rodape a { color: #dfe9e2; text-decoration: none; }
  .ns-rodape a:hover { text-decoration: underline; }
  .ns-rodape .ns-strava { background: #fff; border-radius: 6px; padding: 5px 9px; line-height: 0; }      /* o selo do Strava pede fundo claro */
  .ns-rodape .ns-strava img { display: block; width: 148px; height: auto; }
  @media (max-width: 640px) { .ns-marca span { display: none; } }
  @media (min-width: 900px) { .ns-barra .ns-miolo { justify-content: center; } }      /* tela larga: o logo e o menu juntos, no meio */
  /* o cabeçalho verde de cada página fica mais baixo: o menu já está em cima (a inicial tem o cabeçalho dela e fica como está) */
  .ns-barra ~ header { padding-top: 12px !important; padding-bottom: 18px !important; }
  .ns-barra ~ header h1 { margin-top: 6px !important; }
  .ns-barra ~ header h1 + p, .ns-barra ~ header .data, .ns-barra ~ header .cidades { margin-top: 5px !important; }
  .ns-barra ~ header .ns-trilha + h1 { margin-top: 2px !important; }
  /* a serra no pé da faixa verde e o ciclista que passa por ela (some para quem pede menos movimento) */
  .ns-barra ~ header { position: relative; overflow: hidden; }
  .ns-barra ~ header > * { position: relative; z-index: 1; }
  .ns-barra ~ header::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 48px; background: """ + SERRA + """ repeat-x left bottom; pointer-events: none; }
  .ns-barra ~ header > .ns-ciclista { position: absolute; z-index: 0; bottom: 0; left: 0; width: 36px; height: 36px; transform: translate(-80px, 0); transform-origin: 18px 33px; background: """ + CICLISTA + """ no-repeat; pointer-events: none; animation: ns-pedala 60s linear 4s infinite; }
  .ns-barra ~ header > .ns-ciclista + .ns-ciclista { animation-delay: 4.5s; }
  .ns-barra ~ header > .ns-ciclista + .ns-ciclista + .ns-ciclista { animation-delay: 5.1s; }
  """ + PEDALA + """
  @media (prefers-reduced-motion: reduce) { .ns-barra ~ header > .ns-ciclista { display: none; } }
  /* o botão de sol e lua: mostra o sol no modo escuro (vai para o claro) e a lua no claro */
  .ns-tema { flex: none; display: grid; place-items: center; width: 30px; height: 30px; padding: 0; border: 0; border-radius: 999px; background: transparent; color: #cfdcd3; cursor: pointer; }
  .ns-tema:hover { color: #fff; background: rgba(255,255,255,.07); }
  .ns-tema svg { width: 17px; height: 17px; }
  .ns-tema .ns-sol { display: none; }
  html[data-tema="escuro"] .ns-tema .ns-sol { display: block; } html[data-tema="escuro"] .ns-tema .ns-lua { display: none; }
  @media (prefers-color-scheme: dark) { html:not([data-tema="claro"]) .ns-tema .ns-sol { display: block; } html:not([data-tema="claro"]) .ns-tema .ns-lua { display: none; } }
  html[data-tema="escuro"] { color-scheme: dark; } html[data-tema="claro"] { color-scheme: light; }
</style>
<script id="ns-tema">try { var t = localStorage.getItem("tema"); if (t === "claro" || t === "escuro") document.documentElement.setAttribute("data-tema", t); } catch (e) {}</script>"""


SOL = ('<svg class="ns-sol" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
       '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>')
LUA = ('<svg class="ns-lua" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
       '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>')
# troca entre claro e escuro e guarda a escolha no navegador; sem escolha, o site segue o modo do aparelho
BOTAO_TEMA = ('<button class="ns-tema" type="button" aria-label="Modo claro ou escuro" title="Modo claro/escuro" onclick="(function () {'
              " var h = document.documentElement, t = h.getAttribute('data-tema');"
              " var escuro = t === 'escuro' || (t !== 'claro' &amp;&amp; matchMedia('(prefers-color-scheme: dark)').matches);"
              " var novo = escuro ? 'claro' : 'escuro'; h.setAttribute('data-tema', novo); try { localStorage.setItem('tema', novo); } catch (e) {} })()\">"
              + SOL + LUA + '</button>')


def com_escolha(seletores, marca):
    """Os seletores de uma regra do modo escuro presos ao html com a marca ([data-tema=...]): ":root" e "html" levam a marca neles."""
    saida = []
    for sel in re.sub(r"/\*.*?\*/", "", seletores, flags=re.S).split(","):
        sel = sel.strip()
        if sel.startswith(":root"):
            saida.append(":root" + marca + sel[5:])
        elif re.match(r"html(?![\w-])", sel):
            saida.append("html" + marca + sel[4:])
        else:
            saida.append("html" + marca + " " + sel)
    return ", ".join(saida)


def tema_escolhido(doc):
    """Cada bloco "@media (prefers-color-scheme: dark)" da página passa a valer só sem escolha contrária (html sem data-tema="claro"),
    e ganha uma cópia que vale quando a pessoa escolhe o escuro no botão. Rodar de novo não duplica (o bloco feito já tem data-tema)."""
    abre = "@media (prefers-color-scheme: dark)"
    partes, pos = [], 0
    while True:
        i = doc.find(abre, pos)
        if i < 0:
            break
        j = doc.find("{", i)
        nivel, k = 1, j + 1
        while nivel and k < len(doc):
            nivel += {"{": 1, "}": -1}.get(doc[k], 0)
            k += 1
        dentro = doc[j + 1:k - 1]
        regras = re.findall(r"([^{}]+)\{([^{}]*)\}", dentro)
        sobra = re.sub(r"/\*.*?\*/", "", re.sub(r"[^{}]+\{[^{}]*\}", "", dentro), flags=re.S).strip()
        if "data-tema" in dentro or not regras or sobra:          # já feito, ou de um jeito que não sei reescrever: fica como está
            partes.append(doc[pos:k])
        else:
            sem_escolha = " ".join(f'{com_escolha(sel, ":not([data-tema=" + chr(34) + "claro" + chr(34) + "])")} {{{dec}}}' for sel, dec in regras)
            escolhido = " ".join(f'{com_escolha(sel, "[data-tema=" + chr(34) + "escuro" + chr(34) + "]")} {{{dec}}}' for sel, dec in regras)
            partes.append(doc[pos:i] + abre + " { " + sem_escolha + " }\n  " + escolhido)
        pos = k
    return "".join(partes) + doc[pos:]


def barra(atual):
    itens = "".join(f'<a href="{href}"' + (' aria-current="page"' if pagina == atual else "") + f">{rotulo}</a>" for pagina, href, rotulo in MENU)
    return ('<!--ns:menu--><nav class="ns-barra" aria-label="Site"><div class="ns-miolo"><a class="ns-marca" href="/" aria-label="Brote na Trilha, início">'
            '<img src="/favicon.png?v=2" width="26" height="26" alt=""><span>Brote na Trilha</span></a>'
            f'<div class="ns-menu">{itens}</div>' + BOTAO_TEMA + '</div></nav>'
            '<script>(function () { var a = document.querySelector(".ns-menu [aria-current]"); if (a) a.parentNode.scrollLeft = a.offsetLeft - 60; })();</script>'
            '<!--/ns:menu-->')


def rodape():
    links = " ".join(f'<a href="{h}"' + (' target="_blank" rel="noopener"' if h.startswith("http") else "") + f">{t}</a>" for h, t in RODAPE_LINKS)
    return ('<!--ns:rodape--><footer class="ns-rodape"><div class="ns-miolo">'
            f'<span>© <span id="ano">{ANO}</span> Brote na Trilha</span><nav aria-label="Rodapé">{links}</nav>'
            '<a class="ns-strava" href="https://www.strava.com" target="_blank" rel="noopener"><img src="/strava_powered_by.png" width="197" height="20" '
            'alt="Powered by Strava" loading="lazy" decoding="async"></a></div></footer><!--/ns:rodape-->')


def trilha_html(itens):
    partes = [f'<li><a href="{href}">{html.escape(nome)}</a></li>' for nome, href in itens[:-1]]      # sem o último: é o título logo abaixo
    return f'<nav class="ns-trilha" aria-label="Você está em"><ol>{"".join(partes)}</ol></nav>'


def trilha_ld(itens):
    lista = [{"@type": "ListItem", "position": i + 1, "name": nome, **({"item": SITE + href} if href else {})} for i, (nome, href) in enumerate(itens)]
    return ('<script type="application/ld+json" id="ns-trilha-ld">'
            + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": lista}, ensure_ascii=False) + "</script>")


def titulo(doc):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def pagina_e_trilha(rel, doc, ano_mais_novo):
    """A página do menu (para marcar) e a trilha de navegação (ou None) pelo caminho do arquivo."""
    partes = rel.replace("\\", "/").split("/")[:-1]                  # sem o "index.html"
    if not partes:
        return "inicio", None
    topo = partes[0]
    inicio = ("Início", "/")
    if topo == "pedais" and len(partes) >= 2:
        if re.fullmatch(r"\d{4}", partes[1]):
            return "pedais", [inicio, ("Pedais", "/pedais/"), (partes[1], None)]
        if partes[1] in ("cidade", "mapa"):
            return "pedais", [inicio, ("Pedais", "/pedais/"), (titulo(doc) or partes[-1], None)]
        m = re.match(r"(\d{4})-", partes[1])
        if m:
            ano = m.group(1)
            return "pedais", [inicio, ("Pedais", "/pedais/"), (ano, "/pedais/" if ano == ano_mais_novo else f"/pedais/{ano}/"), (titulo(doc), None)]
    if topo == "subidas":                                                # Subidas fica dentro de Pedais
        return "pedais", [inicio, ("Pedais", "/pedais/"), ("Subidas", None)]
    if topo == "ferramentas" and len(partes) >= 2:
        return "ferramentas", [inicio, ("Ferramentas", "/ferramentas/"), (titulo(doc) or partes[1], None)]
    return topo, None


def aplicar(doc, atual, trilha):
    # o estilo, uma vez
    doc = re.sub(r'<link [^>]*id="ns-fonte">\n?', "", doc)
    doc = re.sub(r'<style id="ns-estilo">.*?</style>\n?', "", doc, flags=re.S)      # com a quebra de linha: rodar de novo não acumula linhas
    doc = re.sub(r'<script id="ns-tema">.*?</script>\n?', "", doc, flags=re.S)
    doc = doc.replace("</head>", ESTILO + "\n</head>", 1)
    doc = tema_escolhido(doc)                                  # o modo escuro segue o botão de sol e lua (ou o aparelho, sem escolha)
    # a trilha para o Google
    doc = re.sub(r'<script type="application/ld\+json" id="ns-trilha-ld">.*?</script>\n?', "", doc, flags=re.S)
    if trilha:
        doc = doc.replace("</head>", trilha_ld([(n, h) for n, h in trilha]) + "\n</head>", 1)
    # o menu: a barra logo depois do <body>, em todas as páginas; a inicial perde a barra própria dela (pedido do usuário, 2026-11-21)
    doc = re.sub(r"\n?<!--ns:menu-->.*?<!--/ns:menu-->", "", doc, flags=re.S)
    doc = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + barra(atual), doc, count=1)
    doc = re.sub(r'\n?<header class="topo">.*?</header>', "", doc, count=1, flags=re.S)      # a barra própria da inicial, do Sobre e do BNT Editor sai
    if atual != "inicio":
        # o "← ..." do cabeçalho da página vira a trilha (ou sai: o menu já leva a qualquer lugar)
        cab = re.search(r"<header[^>]*>.*?</header>", doc, re.S)
        if cab:
            bloco = cab.group(0)
            if '<nav class="ns-trilha"' in bloco:                         # já tem a trilha (rodou antes): troca no mesmo lugar
                novo = re.sub(r'<nav class="ns-trilha".*?</nav>', lambda m: trilha_html(trilha) if trilha else "", bloco, count=1, flags=re.S)
            else:
                novo = re.sub(r'<a [^>]*href="[^"]*"[^>]*>\s*(?:&larr;|←)[^<]*</a>', lambda m: trilha_html(trilha) if trilha else "", bloco, count=1)
                if trilha and novo == bloco:                              # sem o "←": a trilha entra no começo do miolo do cabeçalho
                    novo = re.sub(r'(<header[^>]*>\s*(?:<div class="miolo">)?)', lambda m: m.group(1) + trilha_html(trilha), bloco, count=1)
            novo = re.sub(r'<span class="ns-ciclista" aria-hidden="true"></span>', "", novo)
            novo = re.sub(r"(<header[^>]*>)", lambda m: m.group(1) + CICLISTAS, novo, count=1)
            doc = doc.replace(cab.group(0), novo, 1)
    # o rodapé
    if "<!--ns:rodape-->" in doc:
        doc = re.sub(r"<!--ns:rodape-->.*?<!--/ns:rodape-->", lambda m: rodape(), doc, count=1, flags=re.S)
    elif re.search(r"<footer[^>]*>.*?</footer>", doc, re.S):
        doc = re.sub(r"<footer[^>]*>.*?</footer>", lambda m: rodape(), doc, count=1, flags=re.S)
    else:
        doc = doc.replace("</body>", rodape() + "\n</body>", 1)
    return doc


def main(raiz):
    anos = sorted({m.group(1) for d in os.listdir(os.path.join(raiz, "pedais")) for m in [re.match(r"(\d{4})-\d{2}-\d{2}-", d)] if m}, reverse=True)
    ano_mais_novo = anos[0] if anos else str(ANO)
    feitas = 0
    for pasta, dirs, arqs in os.walk(raiz):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("functions", "node_modules")]
        for a in arqs:
            if not a.endswith(".html"):
                continue
            caminho = os.path.join(pasta, a)
            rel = os.path.relpath(caminho, raiz)
            if rel == "404.html" or a != "index.html":
                continue                                                 # a 404 tem os atalhos dela; só as páginas index.html
            doc = open(caminho, encoding="utf-8").read()
            if 'http-equiv="refresh"' in doc or "<body" not in doc:
                continue                                                 # páginas de redirecionamento
            atual, trilha = pagina_e_trilha(rel, doc, ano_mais_novo)
            novo = aplicar(doc, atual, trilha)
            if novo != doc:
                open(caminho, "w", encoding="utf-8", newline="\n").write(novo)
                feitas += 1
    print(f"navegação em {feitas} páginas")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
