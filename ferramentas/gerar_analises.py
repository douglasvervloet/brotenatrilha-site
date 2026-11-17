"""Monta a página de análises (analises/index.html) com os vídeos da playlist "Análises" do canal.

Com o segredo YOUTUBE_API_KEY lê a playlist inteira pela API do YouTube; sem ele, pelo feed público da playlist (os 15 mais novos).
Sem nenhum vídeo (a API ou o feed falharam), não mexe na página que já existe.

Uso: python ferramentas/gerar_analises.py [--saida analises/index.html]
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request

PLAYLIST = "PLOHdygxxt5OA"                            # "Análises" no canal
AGENTE = "brotenatrilha.com.br (contato@brotenatrilha.com.br)"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
TEXTO_MAX = 260                                       # o começo da descrição no cartão, em caracteres


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def videos_pela_api(chave):
    """Os vídeos da playlist pela API (id, título, descrição, data de publicação)."""
    itens, token = [], ""
    while True:
        r = json.loads(baixar("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=" + PLAYLIST
                              + "&key=" + chave + (("&pageToken=" + token) if token else "")))
        itens += r.get("items", [])
        token = r.get("nextPageToken", "")
        if not token:
            break
    videos = []
    for i in range(0, len(itens), 50):
        ids = ",".join(x["snippet"]["resourceId"]["videoId"] for x in itens[i:i + 50])
        r = json.loads(baixar("https://www.googleapis.com/youtube/v3/videos?part=snippet,status&id=" + ids + "&key=" + chave))
        for v in r.get("items", []):
            if v.get("status", {}).get("privacyStatus") != "public":
                continue
            s = v["snippet"]
            videos.append({"id": v["id"], "titulo": s["title"], "descricao": s.get("description", ""), "publicado": s["publishedAt"]})
    return videos


def videos_pelo_feed():
    """Os vídeos da playlist pelo feed público (os 15 mais novos), sem chave."""
    xml = baixar("https://www.youtube.com/feeds/videos.xml?playlist_id=" + PLAYLIST)
    videos = []
    for e in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        descricao = re.search(r"<media:description>(.*?)</media:description>", e, re.S)
        videos.append({"id": re.search(r"<yt:videoId>([^<]+)", e).group(1), "titulo": html.unescape(re.search(r"<title>([^<]+)", e).group(1)),
                       "descricao": html.unescape(descricao.group(1)) if descricao else "", "publicado": re.search(r"<published>([^<]+)", e).group(1)})
    return videos


def data_longa(iso):
    ano, mes, dia = iso[:10].split("-")
    return f"{int(dia)} de {MESES[int(mes) - 1]} de {ano}"


def resumo_da_descricao(texto):
    """O primeiro parágrafo da descrição, sem links e hashtags, cortado numa palavra."""
    paragrafo = next((p.strip() for p in re.split(r"\n\s*\n", texto or "") if p.strip() and not p.strip().startswith(("http", "#"))), "")
    paragrafo = re.sub(r"https?://\S+|#\S+", "", paragrafo)
    paragrafo = re.sub(r"\s+", " ", paragrafo).strip()
    if len(paragrafo) > TEXTO_MAX:
        paragrafo = paragrafo[:TEXTO_MAX].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return paragrafo


# Domínios de links de afiliado: vão com rel="sponsored" (o pedido do Google para link pago ou de comissão)
AFILIADOS = ("s.click.aliexpress.com", "amzn.to", "shope.ee", "mercadolivre.com/sec", "magalu.lu")
ICONE_TOCAR = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.5v15l13-7.5z"/></svg>'
SELO_AFILIADO = '<span class="selo-afiliado" title="Link de afiliado: se você comprar por ele, o canal recebe uma comissão, sem custo extra para você">afiliado</span>'      # o selo ao lado de cada link pago: o aviso tem de estar à vista
AVISO_AFILIADO = '<aside class="aviso-afiliado" role="note"><strong>Links de afiliado.</strong> Alguns links desta página são de afiliados e vêm marcados com &ldquo;afiliado&rdquo;. Se você comprar por eles, o canal recebe uma comissão, sem custo extra para você.</aside>'


def eh_afiliado(url):
    return any(a in url for a in AFILIADOS)


def partes_da_descricao(texto):
    """Da descrição: os links com o rótulo da linha de cima ("- Link do quadro:" e o endereço embaixo), a configuração da bike (linhas
    "Peça: modelo") e os capítulos da minutagem ("00:44 Preço, peso e pintura", em segundos)."""
    linhas = [l.strip() for l in (texto or "").splitlines()]
    links, pecas, capitulos = [], [], []
    for i, l in enumerate(linhas):
        url = re.match(r"^(https?://\S+)$", l)
        if url:
            anterior = next((x for x in reversed(linhas[:i]) if x), "")
            rotulo = anterior.lstrip("-•– ").rstrip(":").strip() if anterior.endswith(":") else re.sub(r"^www\.", "", url.group(1).split("/")[2])
            links.append((rotulo, url.group(1)))
            continue
        tempo = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s+(.+)$", l)
        if tempo:
            h, m, seg = (0, int(tempo.group(1)), int(tempo.group(2))) if tempo.group(3) is None else (int(tempo.group(1)), int(tempo.group(2)), int(tempo.group(3)))
            capitulos.append((h * 3600 + m * 60 + seg, l.split(None, 1)[0], tempo.group(4).strip()))
            continue
        peca = re.match(r"^([A-ZÀ-Ú][\wÀ-ú ]{1,24}):\s+(\S.*)$", l)
        if peca and not peca.group(1).lower().startswith(("minutagem", "link", "geometria", "análise", "analise")):
            pecas.append((peca.group(1).strip(), peca.group(2).strip()))
    return links, pecas, capitulos


def cartao(v):
    titulo = html.escape(v["titulo"])
    texto = resumo_da_descricao(v["descricao"])
    links, pecas, capitulos = partes_da_descricao(v["descricao"])
    extras = ""
    if links:
        itens = "".join(f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener{" sponsored" if eh_afiliado(u) else ""}">{html.escape(r)}{SELO_AFILIADO if eh_afiliado(u) else ""}</a></li>'
                        for r, u in links)
        extras += f'<ul class="links">{itens}</ul>'
    if capitulos:
        itens = "".join(f'<li><button type="button" class="capitulo" data-id="{v["id"]}" data-inicio="{s}"><span>{m}</span>{html.escape(t)}</button></li>'
                        for s, m, t in capitulos)
        extras += f'<details><summary>Capítulos</summary><ol class="capitulos">{itens}</ol></details>'
    if pecas:
        itens = "".join(f"<div><dt>{html.escape(a)}</dt><dd>{html.escape(b)}</dd></div>" for a, b in pecas)
        extras += f'<details><summary>Configuração da bike</summary><dl class="pecas">{itens}</dl></details>' 
    return f"""  <article class="analise">
    <div class="video">
      <button type="button" class="tocar" data-id="{v["id"]}" data-titulo="{titulo}" aria-label="Assistir: {titulo}">
        <img src="https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg" width="480" height="360" loading="lazy" decoding="async" alt="">
        <span class="play" aria-hidden="true"><svg width="26" height="26" viewBox="0 0 24 24"><polygon points="7,4 20,12 7,20" fill="#1c2a22"/></svg></span>
      </button>
    </div>
    <div class="corpo">
      <h2>{titulo}</h2>
      <p class="data">{data_longa(v["publicado"])}</p>
      {f'<p class="texto">{html.escape(texto)}</p>' if texto else ""}
      {extras}
      <a class="abrir" href="https://www.youtube.com/watch?v={v["id"]}" target="_blank" rel="noopener">{ICONE_TOCAR}Assistir no YouTube</a>
    </div>
  </article>"""


def montar(videos, modelo):
    videos = sorted(videos, key=lambda v: v["publicado"], reverse=True)
    n = len(videos)
    resumo = f"{n} {'análise' if n == 1 else 'análises'} em vídeo"
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Análises do Brote na Trilha",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {
              "@type": "VideoObject", "name": v["titulo"], "description": resumo_da_descricao(v["descricao"]) or v["titulo"],
              "thumbnailUrl": [f"https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg"], "uploadDate": v["publicado"],
              "embedUrl": f"https://www.youtube.com/embed/{v['id']}", "contentUrl": f"https://www.youtube.com/watch?v={v['id']}"}}
              for i, v in enumerate(videos)]}
    tem_afiliado = any(eh_afiliado(u) for v in videos for _, u in partes_da_descricao(v["descricao"])[0])
    troca = {"{{AVISO_AFILIADO}}": AVISO_AFILIADO if tem_afiliado else "", "{{CONTEUDO}}": '<div class="lista">\n' + "\n".join(cartao(v) for v in videos) + "\n</div>",
             "{{RESUMO}}": resumo, "{{PLAYLIST}}": PLAYLIST,
             "{{OG_IMAGE}}": "https://brotenatrilha.com.br/analises/compartilhar.jpg",      # imagem fixa e grande (a capa do vídeo, em 480 px, ficava em baixa resolução no WhatsApp)
             "{{JSONLD}}": '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>\n"}
    for k, val in troca.items():
        modelo = modelo.replace(k, val)
    return modelo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="analises/index.html")
    ap.add_argument("--modelo", default=os.path.join(os.path.dirname(__file__), "modelo_analises.tpl"))
    args = ap.parse_args()
    chave = os.environ.get("YOUTUBE_API_KEY", "")
    try:
        videos = videos_pela_api(chave) if chave else videos_pelo_feed()
    except Exception as erro:
        print("Não deu para ler a playlist de análises:", erro)
        return 0
    if not videos:
        print("A playlist de análises veio vazia: a página fica como está.")
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
    with open(args.saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(montar(videos, open(args.modelo, encoding="utf-8").read()))
    print(f"  análises: {len(videos)} vídeos ({'API' if chave else 'feed'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
