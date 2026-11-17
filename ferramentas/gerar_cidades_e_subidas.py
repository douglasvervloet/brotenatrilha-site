"""Gera as páginas por cidade (pedais/cidade/<cidade>/) e o catálogo de subidas (subidas/), a partir do que o gerar_pedais.py já escreveu.

Roda depois do gerar_pedais.py, na raiz do site:  python ferramentas/gerar_cidades_e_subidas.py

- Lê pedais/index.html (os cartões: endereço, título, data, números, capa e mapa) e ferramentas/cache_pedais.json (as cidades por onde cada pedal passa).
- Uma página para cada cidade com 2 pedais ou mais (com menos, a página ficaria sem conteúdo): texto, totais, os cartões dos pedais e as outras cidades.
- /subidas/: todas as subidas dos pedais (do GPX), da mais dura à mais leve, com filtro por categoria.
- Põe os links no pedais/index.html e na inicial (entre as marcas <!--CIDADES--> e <!--/CIDADES-->) e as páginas novas no sitemap.xml.
"""
import glob
import html
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_pedais as g                                           # slug_texto, as subidas e a leitura do GPX são as mesmas do site

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MINIMO_DE_PEDAIS = 2
SITE_URL = "https://brotenatrilha.com.br"
DATA_DAS_PAGINAS = "2026-11-17"


def ler(c):
    with open(os.path.join(RAIZ, c), encoding="utf-8") as f:
        return f.read()


def gravar(c, t):
    caminho = os.path.join(RAIZ, c)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)


def numero_br(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pedais_da_lista():
    """Os pedais da lista em ordem (do mais novo ao mais velho): id, endereço, título, data, números e o cartão pronto para reaproveitar."""
    lista = ler("pedais/index.html")
    pedais = []
    for cartao in re.findall(r'<article class="pedal.*?</article>', lista, re.S):
        slug = re.search(r'class="mapa-link" href="([^"/]+)/"', cartao).group(1)
        pid = re.search(r"/planejar-pedal/\?pedal=(\d+)", cartao).group(1)
        titulo = html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", cartao, re.S).group(1))).strip()
        data = re.search(r'<p class="data">([^<]*)</p>', cartao).group(1)
        km = float(re.search(r'data-km="([\d.]+)"', cartao).group(1))
        rotulos = dict(re.findall(r"<dt>([^<]+)</dt><dd>([^<]+)</dd>", cartao))
        subida = int(re.sub(r"\D", "", rotulos.get("Subida", "0")) or 0)
        absoluto = cartao.replace('href="' + slug + '/"', 'href="/pedais/' + slug + '/"').replace('src="capas/', 'src="/pedais/capas/').replace('src="mapas/', 'src="/pedais/mapas/')
        absoluto = re.sub(r'(<a class="mapa-link" href="/pedais/[^"]+">)', r"\1", absoluto)
        pedais.append({"id": pid, "slug": slug, "titulo": titulo, "data": data, "km": km, "subida": subida, "tempo": rotulos.get("Tempo", ""), "cartao": absoluto})
    return pedais


def cidades_dos_pedais(pedais):
    cache = json.load(open(os.path.join(RAIZ, "ferramentas", "cache_pedais.json"), encoding="utf-8"))
    registros = cache["pedais"] if "pedais" in cache else cache
    por_cidade = {}
    for p in pedais:
        d = (registros.get(p["id"]) or {}).get("d", {})
        cidades = {c for c in (d.get("_passa") or []) + [d.get("_sai"), d.get("_chega")] if c}
        p["cidades"] = sorted(cidades)
        for c in cidades:
            por_cidade.setdefault(c, []).append(p)
    return por_cidade


def cabecalho_html(titulo, descricao, url, ld):
    """O <head> da lista de pedais (o mesmo CSS dos cartões) com título, descrição, endereço e dados estruturados desta página."""
    lista = ler("pedais/index.html")
    topo = lista[:lista.index("</style>") + len("</style>")]
    topo = re.sub(r'(href|src)="\.\./', r'\1="/', topo)
    topo = re.sub(r"<title>.*?</title>", f"<title>{html.escape(titulo)} | Brote na Trilha</title>", topo, flags=re.S)
    topo = re.sub(r'(<meta name="description" content=")[^"]*"', lambda m: m.group(1) + html.escape(descricao) + '"', topo)
    topo = re.sub(r'(<link rel="canonical" href=")[^"]*"', lambda m: m.group(1) + url + '"', topo)
    topo = re.sub(r'(<meta property="og:title" content=")[^"]*"', lambda m: m.group(1) + html.escape(titulo) + ' | Brote na Trilha"', topo)
    topo = re.sub(r'(<meta property="og:description" content=")[^"]*"', lambda m: m.group(1) + html.escape(descricao) + '"', topo)
    topo = re.sub(r'(<meta property="og:url" content=")[^"]*"', lambda m: m.group(1) + url + '"', topo)
    topo = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", topo, flags=re.S)
    return topo.replace("</style>", "</style>\n" + "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + "</script>\n" for x in ld).rstrip("\n"))


def rodape_html():
    return """<footer>
  <div class="miolo">
    <span>© <span id="ano">2026</span> Brote na Trilha</span>
    <span><a href="/privacidade/">Política de privacidade</a> · <a href="/">Voltar ao site</a></span>
    <a class="strava" href="https://www.strava.com" target="_blank" rel="noopener"><img src="/strava_powered_by.png" width="197" height="20" alt="Powered by Strava" loading="lazy" decoding="async"></a>
  </div>
</footer>
<script>
  document.getElementById("ano").textContent = new Date().getFullYear();
  [].forEach.call(document.querySelectorAll(".pedal .alterna"), function (botao) {
    botao.hidden = false;
    botao.addEventListener("click", function () {
      var cartao = botao.closest(".pedal");
      var mapa = cartao.classList.toggle("ver-mapa");
      botao.textContent = mapa ? "Ver capa" : "Ver mapa";
      botao.setAttribute("aria-pressed", String(mapa));
    });
  });
</script>
<script data-goatcounter="https://brotenatrilha.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


def pagina_da_cidade(cidade, pedais, todas):
    slug = g.slug_texto(cidade)
    url = f"{SITE_URL}/pedais/cidade/{slug}/"
    n, km, subida = len(pedais), sum(p["km"] for p in pedais), sum(p["subida"] for p in pedais)
    mais_novo, mais_longo = pedais[0], max(pedais, key=lambda p: p["km"])
    intro = (f"O Brote na Trilha tem {n} pedais que passam por {cidade}, no Espírito Santo: {numero_br(km)} km pedalados e {numero_br(subida)} m de subida no total. "
             f"O mais recente é “{mais_novo['titulo']}”, de {mais_novo['data']}; o mais longo, “{mais_longo['titulo']}”, tem {numero_br(mais_longo['km'], 1)} km.")
    titulo = f"Pedais de bike em {cidade}, ES"
    descricao = f"{n} pedais de bike que passam por {cidade}, no Espírito Santo, com o mapa, a altimetria, as subidas e o vídeo de cada um. {numero_br(km)} km e {numero_br(subida)} m de subida."
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Brote na Trilha", "item": SITE_URL + "/"},
              {"@type": "ListItem", "position": 2, "name": "Pedais", "item": SITE_URL + "/pedais/"},
              {"@type": "ListItem", "position": 3, "name": cidade, "item": url}]},
          {"@context": "https://schema.org", "@type": "CollectionPage", "name": titulo, "url": url, "inLanguage": "pt-BR", "description": descricao,
           "mainEntity": {"@type": "ItemList", "numberOfItems": n, "itemListElement": [
               {"@type": "ListItem", "position": i + 1, "url": f"{SITE_URL}/pedais/{p['slug']}/", "name": p["titulo"]} for i, p in enumerate(pedais)]}}]
    outras = " ".join(f'<a class="botao claro" href="/pedais/cidade/{g.slug_texto(c)}/">{html.escape(c)} ({len(ps)})</a>' for c, ps in todas if c != cidade)
    corpo = f"""<body>
<header>
  <div class="miolo">
    <a href="/pedais/">&larr; Pedais</a>
    <h1>Pedais em {html.escape(cidade)}</h1>
    <p>{html.escape(intro)}</p>
    <p class="resumo">{n} pedais · {numero_br(km)} km · {numero_br(subida)} m de subida</p>
  </div>
</header>

<main class="miolo">
  <div class="grade">
{chr(10).join(p["cartao"] for p in pedais)}
  </div>
  <h2 class="ano" style="margin-top:34px">Pedais por outras cidades</h2>
  <p class="links">{outras}</p>
  <p class="links" style="margin-top:18px"><a class="botao" href="/pedais/">Ver todos os pedais</a> <a class="botao claro" href="/subidas/">Ver as subidas</a></p>
</main>

"""
    return slug, cabecalho_html(titulo, descricao, url, ld) + "\n</head>\n" + corpo + rodape_html()


def pagina_das_subidas(pedais):
    por_id = {p["id"]: p for p in pedais}
    linhas = []
    for pid, p in por_id.items():
        gpx = os.path.join(RAIZ, "pedais", "gpx", pid + ".gpx")
        if not os.path.exists(gpx):
            continue
        for s in g.subidas_do_perfil(g.ler_perfil_do_gpx(gpx)):
            linhas.append((s, p))
    linhas.sort(key=lambda x: -x[0]["pontos"])
    cores = g.CORES_CATEGORIA
    contagem = {}
    for s, _ in linhas:
        contagem[s["categoria"]] = contagem.get(s["categoria"], 0) + 1
    com_categoria = sum(v for k, v in contagem.items() if k != "Sem categoria")
    corpo_tabela = []
    for s, p in linhas:
        cor, txt = cores[s["categoria"]]
        corpo_tabela.append(
            f'<tr data-cat="{html.escape(s["categoria"])}"><td><span class="selo-cat" style="background:{cor};color:{txt}">{html.escape(s["categoria"])}</span></td>'
            f'<td><a href="/pedais/{p["slug"]}/">{html.escape(p["titulo"])}</a><small>subida {s["numero"]}, do km {numero_br(s["inicio"], 1)} ao {numero_br(s["fim"], 1)}</small></td>'
            f'<td class="num" data-rotulo="Extensão">{numero_br(s["comprimento"] / 1000, 2)} km</td><td class="num" data-rotulo="Ganho">{numero_br(s["ganho"])} m</td>'
            f'<td class="num" data-rotulo="Média">{numero_br(s["media"], 1)}%</td><td class="num" data-rotulo="Máxima">{numero_br(s["maxima"], 1)}%</td></tr>')
    chips = ['<button type="button" class="chip" data-cat="com" aria-pressed="true">Com categoria (%d)</button>' % com_categoria]
    for nome in ("HC", "Cat 1", "Cat 2", "Cat 3", "Cat 4", "Sem categoria"):
        if contagem.get(nome):
            chips.append(f'<button type="button" class="chip" data-cat="{nome}" aria-pressed="false">{nome} ({contagem[nome]})</button>')
    chips.append(f'<button type="button" class="chip" data-cat="todas" aria-pressed="false">Todas ({len(linhas)})</button>')
    url = SITE_URL + "/subidas/"
    titulo = "Subidas de bike no Espírito Santo, com categoria"
    descricao = (f"{len(linhas)} subidas dos pedais do Brote na Trilha, da mais dura à mais leve, com a categoria (Cat 4 ao HC), a extensão, o ganho e a inclinação de cada uma. "
                 f"{com_categoria} têm categoria.")
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Brote na Trilha", "item": SITE_URL + "/"},
              {"@type": "ListItem", "position": 2, "name": "Subidas", "item": url}]},
          {"@context": "https://schema.org", "@type": "CollectionPage", "name": titulo, "url": url, "inLanguage": "pt-BR", "description": descricao}]
    extra_css = """<style>
  .tabela-subidas { overflow-x: auto; margin-top: 18px; }
  .tabela-subidas table { width: 100%; border-collapse: collapse; font-size: .95rem; }
  .tabela-subidas th { text-align: left; font-size: .75rem; letter-spacing: .5px; text-transform: uppercase; color: var(--suave); padding: 8px 10px; border-bottom: 2px solid var(--linha); }
  .tabela-subidas td { padding: 10px; border-bottom: 1px solid var(--linha); vertical-align: top; }
  .tabela-subidas td small { display: block; color: var(--suave); margin-top: 2px; }
  .tabela-subidas td.num, .tabela-subidas th.num { text-align: right; white-space: nowrap; }
  .tabela-subidas tr[hidden] { display: none; }
  .selo-cat { display: inline-block; padding: 3px 12px; border-radius: 999px; font-weight: 800; font-size: .8rem; white-space: nowrap; }
  .filtros-subidas { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
  @media (max-width: 640px) {                              /* celular: cada subida vira um bloco, sem rolar para o lado */
    .tabela-subidas thead { display: none; }
    .tabela-subidas table, .tabela-subidas tbody { display: block; }
    .tabela-subidas tr { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px 8px; padding: 12px 0; border-bottom: 1px solid var(--linha); }
    .tabela-subidas tr[hidden] { display: none; }
    .tabela-subidas td { border: 0; padding: 0; }
    .tabela-subidas td:nth-child(1) { grid-column: 1 / -1; }
    .tabela-subidas td:nth-child(2) { grid-column: 1 / -1; margin: 6px 0 4px; }
    .tabela-subidas td.num { text-align: left; font-weight: 700; }
    .tabela-subidas td.num::before { content: attr(data-rotulo); display: block; font-size: .68rem; font-weight: 400; letter-spacing: .4px; text-transform: uppercase; color: var(--suave); }
  }
</style>"""
    corpo = f"""<body>
<header>
  <div class="miolo">
    <a href="/pedais/">&larr; Pedais</a>
    <h1>Subidas dos pedais</h1>
    <p>Todas as subidas dos pedais do canal, da mais dura à mais leve. A categoria vai do Cat 4 ao HC, pelo comprimento e pela inclinação média.</p>
    <p class="resumo">{len(linhas)} subidas · {com_categoria} com categoria · {len(por_id)} pedais</p>
    <p><a href="/ferramentas/categoria-de-subida/">Como a categoria é calculada &rarr;</a></p>
  </div>
</header>

<main class="miolo">
  <div class="filtros-subidas" id="filtros-subidas" role="group" aria-label="Filtrar por categoria" hidden>{" ".join(chips)}</div>
  <div class="tabela-subidas"><table>
    <thead><tr><th>Categoria</th><th>Pedal</th><th class="num">Extensão</th><th class="num">Ganho</th><th class="num">Média</th><th class="num">Máxima</th></tr></thead>
    <tbody>
{chr(10).join(corpo_tabela)}
    </tbody>
  </table></div>
  <p class="nota">O ganho e a inclinação vêm da altitude do relevo do mapa, conferida com o Strava. Subidas de menos de 500 m ou com menos de 3% de média não entram.</p>
  <p class="links" style="margin-top:18px"><a class="botao" href="/pedais/">Ver todos os pedais</a> <a class="botao claro" href="/planejar-pedal/">Planejar um pedal</a></p>
</main>

"""
    script = """<script>
  var barra = document.getElementById("filtros-subidas"), linhas = [].slice.call(document.querySelectorAll(".tabela-subidas tbody tr"));
  function filtrar(cat) {
    linhas.forEach(function (l) { var c = l.dataset.cat; l.hidden = !(cat === "todas" || (cat === "com" && c !== "Sem categoria") || c === cat); });
    [].forEach.call(barra.querySelectorAll(".chip"), function (b) { b.setAttribute("aria-pressed", String(b.dataset.cat === cat)); });
  }
  barra.hidden = false;
  barra.addEventListener("click", function (e) { var b = e.target.closest("button"); if (b) filtrar(b.dataset.cat); });
  filtrar("com");
</script>
"""
    pagina = cabecalho_html(titulo, descricao, url, ld).replace("</style>\n", "</style>\n" + extra_css + "\n", 1) + "\n</head>\n" + corpo + rodape_html()
    pagina = pagina.replace("<script data-goatcounter", script + "<script data-goatcounter", 1)
    return pagina, len(linhas)


def links_das_cidades(cidades, prefixo):
    return " · ".join(f'<a href="{prefixo}pedais/cidade/{g.slug_texto(c)}/">{html.escape(c)}</a>' for c, _ in cidades)


def entre_marcas(texto, miolo):
    novo = re.sub(r"<!--CIDADES-->.*?<!--/CIDADES-->", lambda m: "<!--CIDADES-->" + miolo + "<!--/CIDADES-->", texto, flags=re.S)
    return novo


def main():
    pedais = pedais_da_lista()
    por_cidade = cidades_dos_pedais(pedais)
    com_pagina = sorted(((c, ps) for c, ps in por_cidade.items() if len(ps) >= MINIMO_DE_PEDAIS), key=lambda x: (-len(x[1]), g.sem_acento(x[0])))
    # as páginas das cidades (as que saíram da lista somem)
    pasta = os.path.join(RAIZ, "pedais", "cidade")
    gravadas = set()
    for cidade, ps in com_pagina:
        slug, pagina = pagina_da_cidade(cidade, ps, com_pagina)
        gravar(f"pedais/cidade/{slug}/index.html", pagina)
        gravadas.add(slug)
    if os.path.isdir(pasta):
        for nome in os.listdir(pasta):
            if nome not in gravadas and os.path.isdir(os.path.join(pasta, nome)):
                import shutil
                shutil.rmtree(os.path.join(pasta, nome))
                print("  página de cidade removida:", nome)
    pagina_subidas, n_subidas = pagina_das_subidas(pedais)
    gravar("subidas/index.html", pagina_subidas)
    # os links: na lista de pedais e na inicial (entre as marcas) e na página de cada pedal já vão pelo gerar_pedais (linha das cidades)
    for arq, prefixo, rotulo in (("pedais/index.html", "/", "Pedais por cidade"), ("index.html", "", "Pedais por cidade")):
        caminho = os.path.join(RAIZ, arq)
        t = ler(arq)
        if "<!--CIDADES-->" in t:
            bloco = f'<p class="por-cidade"><b>{rotulo}:</b> {links_das_cidades(com_pagina, prefixo)} · <a href="{prefixo}subidas/"><b>Subidas</b></a></p>'
            gravar(arq, entre_marcas(t, bloco))
    # o sitemap
    sm = ler("sitemap.xml")
    sm = re.sub(r"  <url><loc>https://brotenatrilha\.com\.br/(?:pedais/cidade/[^<]*|subidas/)</loc>.*?</url>\n", "", sm)
    novas = "".join(f"  <url><loc>{SITE_URL}/pedais/cidade/{g.slug_texto(c)}/</loc><lastmod>{DATA_DAS_PAGINAS}</lastmod></url>\n" for c, _ in com_pagina)
    novas += f"  <url><loc>{SITE_URL}/subidas/</loc><lastmod>{DATA_DAS_PAGINAS}</lastmod></url>\n"
    gravar("sitemap.xml", sm.replace("</urlset>", novas + "</urlset>"))
    print(f"  cidades: {len(com_pagina)} páginas ({', '.join(c for c, _ in com_pagina)}); subidas: {n_subidas} no catálogo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
