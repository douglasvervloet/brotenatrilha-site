"""Guarda no próprio site a capa do vídeo mais novo de cada playlist da página inicial (capas-playlists/<lista>.webp, 16:9, 640 px).

As playlists vêm do próprio index.html (os botões com data-lista). O vídeo mais novo é o de data de publicação mais recente no feed público da playlist
(sem chave de API). A página inicial usa a imagem de fundo do player antes de o visitante tocar, sem pedir nada ao YouTube.

Uso:  python ferramentas/gerar_capas_playlists.py [index.html] [PASTA_DE_SAIDA]        (precisa do Pillow)
"""
import io
import os
import re
import sys
import urllib.request

from PIL import Image

AGENTE = "brotenatrilha.com.br (contato@brotenatrilha.com.br)"
LARGURA = 640


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def video_mais_novo(lista):
    """(id do vídeo, data de publicação) do vídeo publicado mais recentemente na playlist, pelo feed público."""
    xml = baixar(f"https://www.youtube.com/feeds/videos.xml?playlist_id={lista}").decode("utf-8", "replace")
    entradas = re.findall(r"<entry>.*?</entry>", xml, re.S)
    achados = []
    for e in entradas:
        v, d = re.search(r"<yt:videoId>([^<]+)", e), re.search(r"<published>([^<]+)", e)
        if v and d:
            achados.append((d.group(1), v.group(1)))
    if not achados:
        raise RuntimeError("feed sem vídeos")
    data, video = max(achados)
    return video, data


def capa_16_9(video):
    """A capa do vídeo em 16:9 (a de melhor resolução que existir; a de 4:3 com tarjas pretas é cortada no meio)."""
    for nome in ("maxresdefault", "hqdefault"):
        try:
            imagem = Image.open(io.BytesIO(baixar(f"https://i.ytimg.com/vi/{video}/{nome}.jpg"))).convert("RGB")
        except Exception:
            continue
        largura, altura = imagem.size
        if largura / altura < 1.7:
            nova = round(largura * 9 / 16)
            topo = (altura - nova) // 2
            imagem = imagem.crop((0, topo, largura, topo + nova))
        if imagem.width > LARGURA:
            imagem = imagem.resize((LARGURA, round(LARGURA * imagem.height / imagem.width)), Image.LANCZOS)
        return imagem
    raise RuntimeError("sem capa")


def main():
    home = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    saida = sys.argv[2] if len(sys.argv) > 2 else "capas-playlists"
    listas = re.findall(r'data-lista="([^"]+)"', open(home, encoding="utf-8").read())
    os.makedirs(saida, exist_ok=True)
    feitas = 0
    for lista in dict.fromkeys(listas):
        try:
            video, data = video_mais_novo(lista)
            capa_16_9(video).save(os.path.join(saida, f"{lista}.webp"), "WEBP", quality=80, method=6)
            feitas += 1
            print(f"  playlist {lista}: capa do vídeo {video} ({data[:10]})")
        except Exception as erro:                      # sem a capa nova, fica a que já existe (ou o fundo liso)
            print(f"  playlist {lista}: sem capa nova - {erro}")
    print(f"  capas das playlists: {feitas} de {len(set(listas))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
