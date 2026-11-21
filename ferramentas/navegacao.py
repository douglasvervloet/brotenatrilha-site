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
  .ns-menu a[aria-current="page"] { color: #fff; background: #2d7046; }
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
</style>"""


def barra(atual):
    itens = "".join(f'<a href="{href}"' + (' aria-current="page"' if pagina == atual else "") + f">{rotulo}</a>" for pagina, href, rotulo in MENU)
    return ('<!--ns:menu--><nav class="ns-barra" aria-label="Site"><div class="ns-miolo"><a class="ns-marca" href="/" aria-label="Brote na Trilha, início">'
            '<img src="/favicon.png" width="26" height="26" alt=""><span>Brote na Trilha</span></a>'
            f'<div class="ns-menu">{itens}</div></div></nav>'
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
    doc = doc.replace("</head>", ESTILO + "\n</head>", 1)
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
