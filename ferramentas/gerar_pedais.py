#!/usr/bin/env python3
"""
Gera a página /pedais/ do site a partir do Strava e do canal do YouTube.

- Busca no Strava as atividades públicas cujo nome começa com "Brote na Trilha" (precisa de STRAVA_CLIENT_ID,
  STRAVA_CLIENT_SECRET e STRAVA_REFRESH_TOKEN; o escopo activity:read já deixa de fora as zonas de privacidade).
- Casa cada pedal com o vídeo do canal pelo título (e pelo link do YouTube na descrição do Strava, se houver) e pega o
  link do Komoot da descrição do vídeo (precisa de YOUTUBE_API_KEY; sem a chave, os cartões saem sem vídeo).
- Desenha o traçado em SVG, SEM o começo e o fim: os primeiros e os últimos 800 m são cortados, para não mostrar de onde
  o pedal sai (a casa de quem pedala).
- Grava pedais/index.html (a página é estática, sem JavaScript).

Uso:  python ferramentas/gerar_pedais.py            (usa as variáveis de ambiente)
      python ferramentas/gerar_pedais.py --teste dados.json --saida pasta/index.html
"""
import argparse
import difflib
import html
import json
import math
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import time
from datetime import datetime, timedelta

try:
    from PIL import Image
except ImportError:                                  # sem Pillow o robô desenha só o traçado, sem o mapa de fundo
    Image = None

CANAL_UPLOADS = "UU2uS9f0ACz0LZC7HwZWVBPQ"          # lista de envios do canal (UC... vira UU...)
PREFIXO = re.compile(r"^\s*brote\s+na\s+trilha\s*[-–—:]*\s*", re.I)
CORTE_METROS = 800                                   # tirado do começo e do fim do traçado
MAX_PONTOS = 260
CORRECOES = {"estradrões": "estradões"}              # erros de digitação nos nomes do Strava
MAPA_L, MAPA_A = 800, 480                           # tamanho da imagem do mapa (5:3)
URL_TILE = "https://tile.opentopomap.org/{z}/{x}/{y}.png"   # o mesmo estilo da tela de resumo do BNT Editor
AGENTE = "brotenatrilha.com.br (brotenatrilha@gmail.com)"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]


# ----------------------------------------------------------------------------- rede
def http_json(url, dados=None, cabecalhos=None):
    corpo = urllib.parse.urlencode(dados).encode() if dados is not None else None
    req = urllib.request.Request(url, data=corpo, headers=cabecalhos or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def atividades_do_strava():
    cid, segredo, refresh = (os.environ.get(k, "") for k in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"))
    if not (cid and segredo and refresh):
        return None
    tk = http_json("https://www.strava.com/oauth/token", {"client_id": cid, "client_secret": segredo,
                                                        "grant_type": "refresh_token", "refresh_token": refresh})
    if tk.get("refresh_token") and tk["refresh_token"] != refresh:
        # o Strava pode trocar o refresh token a cada renovação: o robô grava o novo (ver pedais.yml)
        with open(os.environ.get("NOVO_REFRESH_ARQUIVO", "novo_refresh.txt"), "w") as f:
            f.write(tk["refresh_token"])
    cab = {"Authorization": "Bearer " + tk["access_token"]}
    todas, pagina = [], 1
    while True:
        lote = http_json(f"https://www.strava.com/api/v3/athlete/activities?per_page=200&page={pagina}", None, cab)
        if not lote:
            break
        todas += lote
        pagina += 1
    return todas


def videos_do_canal():
    chave = os.environ.get("YOUTUBE_API_KEY", "")
    if not chave:
        return []
    itens, token = [], ""
    while True:
        url = ("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=" + CANAL_UPLOADS
               + "&key=" + chave + (("&pageToken=" + token) if token else ""))
        r = http_json(url)
        itens += r.get("items", [])
        token = r.get("nextPageToken", "")
        if not token:
            break
    videos = []
    for i in range(0, len(itens), 50):
        ids = ",".join(x["snippet"]["resourceId"]["videoId"] for x in itens[i:i + 50])
        r = http_json("https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + ids + "&key=" + chave)
        for v in r.get("items", []):
            s = v["snippet"]
            videos.append({"id": v["id"], "titulo": s["title"], "descricao": s.get("description", ""),
                           "data": s["publishedAt"][:10]})
    return videos


# ----------------------------------------------------------------------------- texto
def sem_acento(t):
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def normalizar(t):
    t = PREFIXO.sub("", t)
    t = sem_acento(t.lower())
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def titulo_do_pedal(nome):
    t = PREFIXO.sub("", nome).strip()
    for errado, certo in CORRECOES.items():
        t = t.replace(errado, certo)
    return t[:1].upper() + t[1:] if t else nome


def atividade_do_link(url, cache):
    """Número da atividade do Strava a partir de um link da descrição (strava.com/activities/N ou strava.app.link/xxxx)."""
    m = re.search(r"strava\.com/activities/(\d+)", url)
    if m:
        return m.group(1)
    if url in cache:
        return cache[url]
    achado = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            corpo = r.read(400000).decode("utf-8", "ignore")
        m = re.search(r"strava\.com/activities/(\d+)", corpo)
        achado = m.group(1) if m else None
    except Exception:
        pass
    cache[url] = achado
    time.sleep(0.2)
    return achado


def atividades_dos_videos(videos):
    """{número da atividade: vídeo} pelos links do Strava que o próprio canal põe na descrição de cada vídeo."""
    cache, mapa = {}, {}
    for v in videos:
        for url in re.findall(r"https?://(?:strava\.app\.link|(?:www\.)?strava\.com/activities)/[^\s)\"'<>]+", v["descricao"]):
            ativ = atividade_do_link(url.rstrip(".,;"), cache)
            if ativ and ativ not in mapa:
                mapa[ativ] = v
    return mapa


def nota_do_par(pedal, video):
    """0 a 1: quanto o vídeo parece ser deste pedal (título, descrição do Strava e data de publicação)."""
    dia = datetime.strptime(pedal["start_date_local"][:10], "%Y-%m-%d")
    pub = datetime.strptime(video["data"], "%Y-%m-%d")
    if not (dia - timedelta(days=1) <= pub <= dia + timedelta(days=150)):
        return 0.0
    alvo, outro = normalizar(pedal["name"]), normalizar(video["titulo"])
    a, b = set(alvo.split()), set(outro.split())
    if not a or not b:
        return 0.0
    n = 0.6 * difflib.SequenceMatcher(None, alvo, outro).ratio() + 0.4 * (len(a & b) / len(a | b))
    if a <= b:                                   # todas as palavras do nome do pedal estão no título do vídeo
        n = max(n, 0.9)
    elif len(a & b) / len(a) >= 0.8:
        n = max(n, 0.7)
    desc = normalizar(pedal.get("description") or "")
    if len(desc) >= 8 and desc in normalizar(video["titulo"] + " " + video["descricao"]):
        n += 0.4                                 # ex.: "São Gabriel x Águia Branca" escrito nos dois
    return n


def casar_videos(pedais, videos, ajustes):
    """Um vídeo para cada pedal (e um pedal para cada vídeo): as melhores notas primeiro; ajustes manuais valem mais."""
    por_id = {v["id"]: v for v in videos}
    for p in pedais:
        p["_video"] = None
    usados = set()
    por_link = atividades_dos_videos(videos)      # 0) o link do Strava na descrição do vídeo: casamento exato
    for p in pedais:
        v = por_link.get(str(p["id"]))
        if v and v["id"] not in usados:
            p["_video"] = v
            usados.add(v["id"])
    for p in pedais:                              # 1) o link do YouTube na descrição do Strava e os ajustes manuais
        if p["_video"] is not None:
            continue
        m = re.search(r"(?:youtu\.be/|v=)([A-Za-z0-9_-]{11})", p.get("description") or "")
        escolha = ajustes.get(str(p["id"]), m.group(1) if m else "")
        if escolha == "-":                        # "-" no arquivo de ajustes: este pedal não tem vídeo
            p["_video"] = False
        elif escolha in por_id:
            p["_video"] = por_id[escolha]
            usados.add(escolha)
    pares = sorted(((nota_do_par(p, v), i, v["id"]) for i, p in enumerate(pedais) if p["_video"] is None for v in videos
                    if v["id"] not in usados), reverse=True)
    for nota, i, vid in pares:                    # 2) o resto, pela melhor nota
        if nota < 0.55:
            break
        if pedais[i]["_video"] is None and vid not in usados:
            pedais[i]["_video"] = por_id[vid]
            usados.add(vid)
    for p in pedais:
        p["_video"] = p["_video"] or None


def link_komoot(video):
    if not video:
        return None
    m = re.search(r"https?://(?:www\.)?komoot\.[a-z.]+/[^\s)\"'<>]+", video["descricao"])
    return m.group(0).rstrip(".,;") if m else None


def data_longa(iso):
    d = datetime.strptime(iso[:10], "%Y-%m-%d")
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def duracao(seg):
    h, m = divmod(int(seg) // 60, 60)
    return f"{h}h{m:02d}" if h else f"{m} min"


def num(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ----------------------------------------------------------------------------- mapa
def decodificar(poli):
    pontos, i, lat, lon = [], 0, 0, 0
    while i < len(poli):
        for eixo in (0, 1):
            deslocamento, resultado = 0, 0
            while True:
                b = ord(poli[i]) - 63
                i += 1
                resultado |= (b & 0x1F) << deslocamento
                deslocamento += 5
                if b < 0x20:
                    break
            delta = ~(resultado >> 1) if resultado & 1 else resultado >> 1
            if eixo == 0:
                lat += delta
            else:
                lon += delta
        pontos.append((lat / 1e5, lon / 1e5))
    return pontos


def metros(a, b):
    k = 111320.0
    dy = (b[0] - a[0]) * k
    dx = (b[1] - a[1]) * k * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def cortar_pontas(pontos, corte=CORTE_METROS):
    if len(pontos) < 4:
        return []
    acum = [0.0]
    for p, q in zip(pontos, pontos[1:]):
        acum.append(acum[-1] + metros(p, q))
    total = acum[-1]
    if total < 4 * corte:
        return []
    return [p for p, d in zip(pontos, acum) if corte <= d <= total - corte]


def svg_do_tracado(poli, w=400, h=240, margem=14):
    pontos = cortar_pontas(decodificar(poli)) if poli else []
    if len(pontos) < 5:
        return None
    if len(pontos) > MAX_PONTOS:
        passo = len(pontos) / MAX_PONTOS
        pontos = [pontos[int(i * passo)] for i in range(MAX_PONTOS)] + [pontos[-1]]
    lat0 = sum(p[0] for p in pontos) / len(pontos)
    c = math.cos(math.radians(lat0))
    xs = [p[1] * c for p in pontos]
    ys = [-p[0] for p in pontos]
    dx, dy = max(xs) - min(xs) or 1e-9, max(ys) - min(ys) or 1e-9
    esc = min((w - 2 * margem) / dx, (h - 2 * margem) / dy)
    ox = (w - dx * esc) / 2 - min(xs) * esc
    oy = (h - dy * esc) / 2 - min(ys) * esc
    d = "M" + " L".join(f"{x * esc + ox:.1f} {y * esc + oy:.1f}" for x, y in zip(xs, ys))
    return (f'<svg class="mapa" viewBox="0 0 {w} {h}" role="img" aria-label="Traçado do percurso, sem o começo e o fim">'
            f'<path d="{d}"/></svg>')


# ----------------------------------------------------------------------------- mapa de relevo (como o resumo do BNT Editor)
def pixel_global(lat, lon, z):
    n = 256 * 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


_tiles = {}


def baixar_tile(z, x, y, pasta_cache):
    chave = (z, x, y)
    if chave in _tiles:
        return _tiles[chave]
    arq = os.path.join(pasta_cache, f"{z}_{x}_{y}.png")
    if os.path.exists(arq):
        img = Image.open(arq).convert("RGB")
    else:
        for tentativa in range(3):
            try:
                req = urllib.request.Request(URL_TILE.format(z=z, x=x, y=y), headers={"User-Agent": AGENTE})
                with urllib.request.urlopen(req, timeout=30) as r:
                    dados = r.read()
                os.makedirs(pasta_cache, exist_ok=True)
                with open(arq, "wb") as f:
                    f.write(dados)
                img = Image.open(arq).convert("RGB")
                time.sleep(0.3)                      # sem pressa: o servidor de mapas é comunitário
                break
            except Exception:
                time.sleep(1.5 * (tentativa + 1))
        else:
            raise RuntimeError(f"tile {z}/{x}/{y} indisponível")
    _tiles[chave] = img
    return img


def gerar_mapa(pedal_id, pontos, pasta_mapas, pasta_cache):
    """Monta o mapa de fundo (WebP) deste pedal, se ainda não existir, e devolve o SVG do traçado por cima dele."""
    lats = [p[0] for p in pontos]
    lons = [p[1] for p in pontos]
    z = 8
    for zz in range(14, 7, -1):
        x0, y1 = pixel_global(min(lats), min(lons), zz)
        x1, y0 = pixel_global(max(lats), max(lons), zz)
        if (x1 - x0) <= MAPA_L * 0.86 and (y1 - y0) <= MAPA_A * 0.86:
            z = zz
            break
    x0, y1 = pixel_global(min(lats), min(lons), z)
    x1, y0 = pixel_global(max(lats), max(lons), z)
    ox = int((x0 + x1) / 2 - MAPA_L / 2)             # canto do recorte, em pixels globais
    oy = int((y0 + y1) / 2 - MAPA_A / 2)
    arquivo = os.path.join(pasta_mapas, f"{pedal_id}.webp")
    if not os.path.exists(arquivo):
        tela = Image.new("RGB", (MAPA_L, MAPA_A), (207, 224, 196))
        for tx in range(ox // 256, (ox + MAPA_L - 1) // 256 + 1):
            for ty in range(oy // 256, (oy + MAPA_A - 1) // 256 + 1):
                if 0 <= tx < 2 ** z and 0 <= ty < 2 ** z:
                    tela.paste(baixar_tile(z, tx, ty, pasta_cache), (tx * 256 - ox, ty * 256 - oy))
        os.makedirs(pasta_mapas, exist_ok=True)
        tela.save(arquivo, "WEBP", quality=80, method=6)
    if len(pontos) > MAX_PONTOS:
        passo = len(pontos) / MAX_PONTOS
        pontos = [pontos[int(i * passo)] for i in range(MAX_PONTOS)] + [pontos[-1]]
    coords = []
    for lat, lon in pontos:
        x, y = pixel_global(lat, lon, z)
        coords.append(f"{x - ox:.1f} {y - oy:.1f}")
    d = "M" + " L".join(coords)
    return (f'<svg viewBox="0 0 {MAPA_L} {MAPA_A}" role="img" aria-label="Traçado do percurso sobre o mapa, sem o começo e o fim">'
            f'<path class="halo" d="{d}"/><path class="linha" d="{d}"/></svg>')


# ----------------------------------------------------------------------------- página
def cartao(p):
    km = p["distance"] / 1000
    media = km / (p["moving_time"] / 3600) if p["moving_time"] else 0
    if p.get("_mapa"):
        mapa = (f'<div class="mapa com-fundo"><img src="mapas/{p["id"]}.webp" width="{MAPA_L}" height="{MAPA_A}" '
                f'loading="lazy" decoding="async" alt="">{p["_mapa"]}</div>')
    else:
        mapa = svg_do_tracado((p.get("map") or {}).get("summary_polyline") or "") or '<div class="mapa vazio">Sem traçado</div>'
    links = []
    if p.get("_video"):
        links.append(f'<a class="botao" href="https://www.youtube.com/watch?v={p["_video"]["id"]}" target="_blank" rel="noopener">Assistir</a>')
    links.append(f'<a class="botao claro" href="https://www.strava.com/activities/{p["id"]}" target="_blank" rel="noopener">Strava</a>')
    if p.get("_komoot"):
        links.append(f'<a class="botao claro" href="{html.escape(p["_komoot"])}" target="_blank" rel="noopener">Komoot</a>')
    return f"""      <article class="pedal">
        {mapa}
        <div class="corpo">
          <h3>{html.escape(titulo_do_pedal(p["name"]))}</h3>
          <p class="data">{data_longa(p["start_date_local"])}</p>
          <dl>
            <div><dt>Distância</dt><dd>{num(km, 1)} km</dd></div>
            <div><dt>Subida</dt><dd>{num(p["total_elevation_gain"])} m</dd></div>
            <div><dt>Tempo</dt><dd>{duracao(p["moving_time"])}</dd></div>
            <div><dt>Média</dt><dd>{num(media, 1)} km/h</dd></div>
          </dl>
          <p class="links">{" ".join(links)}</p>
        </div>
      </article>"""


def montar_pagina(pedais, modelo):
    por_ano = {}
    for p in pedais:
        por_ano.setdefault(p["start_date_local"][:4], []).append(p)
    blocos = []
    for ano in sorted(por_ano, reverse=True):
        blocos.append(f'    <h2 class="ano">{ano}</h2>\n    <div class="grade">\n' + "\n".join(cartao(p) for p in por_ano[ano]) + "\n    </div>")
    km = sum(p["distance"] for p in pedais) / 1000
    subida = sum(p["total_elevation_gain"] for p in pedais)
    resumo = f'{len(pedais)} pedais · {num(km)} km · {num(subida)} m de subida'
    return (modelo.replace("{{RESUMO}}", resumo).replace("{{CONTEUDO}}", "\n".join(blocos))
            .replace("{{ATUALIZADO}}", data_longa(datetime.now().strftime("%Y-%m-%d"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", help="arquivo JSON com atividades no formato da API do Strava (em vez de buscar)")
    ap.add_argument("--saida", default="pedais/index.html")
    ap.add_argument("--modelo", default=os.path.join(os.path.dirname(__file__), "modelo_pedais.tpl"))
    args = ap.parse_args()

    atividades = json.load(open(args.teste, encoding="utf-8")) if args.teste else atividades_do_strava()
    if atividades is None:
        print("Sem as credenciais do Strava (STRAVA_*): nada a fazer.")
        return 0
    videos = videos_do_canal()
    com_video = set(atividades_dos_videos(videos))   # pedais que o canal linkou na descrição de algum vídeo
    pedais = [a for a in atividades
              if (PREFIXO.match(a.get("name", "")) or str(a["id"]) in com_video)
              and a.get("sport_type", a.get("type")) in ("Ride", "GravelRide", "MountainBikeRide", "EBikeRide")]
    pedais.sort(key=lambda a: a["start_date_local"], reverse=True)
    caminho_ajustes = os.path.join(os.path.dirname(__file__), "ajustes_pedais.json")
    ajustes = json.load(open(caminho_ajustes, encoding="utf-8")) if os.path.exists(caminho_ajustes) else {}
    casar_videos(pedais, videos, {k: v for k, v in ajustes.items() if not k.startswith("_")})
    for p in pedais:
        p["_komoot"] = link_komoot(p["_video"])
    pasta_mapas = os.path.join(os.path.dirname(os.path.abspath(args.saida)), "mapas")
    pasta_cache = os.path.join(os.environ.get("TMPDIR", os.environ.get("TEMP", "/tmp")), "tiles_pedais")
    for p in pedais:
        p["_mapa"] = None
        pontos = cortar_pontas(decodificar((p.get("map") or {}).get("summary_polyline") or ""))
        if Image is not None and len(pontos) >= 5:
            try:
                p["_mapa"] = gerar_mapa(p["id"], pontos, pasta_mapas, pasta_cache)
            except Exception as erro:               # sem mapa de fundo, o cartão mostra só o traçado
                print("  sem mapa de fundo:", p["name"], "-", erro)
    print(f"{len(pedais)} pedais; {sum(1 for p in pedais if p['_video'])} com vídeo; {sum(1 for p in pedais if p['_komoot'])} com Komoot; "
          f"{sum(1 for p in pedais if p['_mapa'] or svg_do_tracado((p.get('map') or {}).get('summary_polyline') or ''))} com mapa")
    for p in pedais:
        if not p["_video"]:
            print("  sem vídeo:", p["start_date_local"][:10], p["name"])
    modelo = open(args.modelo, encoding="utf-8").read()
    os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
    with open(args.saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(montar_pagina(pedais, modelo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
