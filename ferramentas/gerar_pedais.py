#!/usr/bin/env python3
"""
Gera as páginas de pedais do site (a lista /pedais/, uma página por pedal, o "Último pedal" da página inicial e o sitemap)
a partir do Strava e do canal do YouTube.

- Busca no Strava as atividades públicas cujo nome começa com "Brote na Trilha" (precisa de STRAVA_CLIENT_ID,
  STRAVA_CLIENT_SECRET e STRAVA_REFRESH_TOKEN; o escopo activity:read já deixa de fora as zonas de privacidade).
- Casa cada pedal com o vídeo do canal pelo título (e pelo link do YouTube na descrição do Strava, se houver) e pega o
  link do Komoot da descrição do vídeo (precisa de YOUTUBE_API_KEY; sem a chave, os cartões saem sem vídeo).
- Desenha o traçado em SVG, SEM o começo e o fim: os primeiros e os últimos 800 m são cortados, para não mostrar de onde
  o pedal sai (a casa de quem pedala).
- Grava pedais/index.html, pedais/<data-título>/index.html, o bloco 'Último pedal' do index.html e o sitemap.xml
  (páginas estáticas; só a busca e os filtros da lista usam JavaScript).

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
import shutil
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


_token_strava = None                                 # preenchido ao buscar as atividades (usado para baixar o traçado detalhado)


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
    global _token_strava
    _token_strava = tk["access_token"]
    cab = {"Authorization": "Bearer " + _token_strava}
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


RAIO_CASA_M = 500                                    # "perto de casa": saída ou chegada a até 500 m do ponto de CASA_COORD


def coordenada_de_casa():
    """(lat, lon) lida do segredo CASA_COORD ("lat,lon"). A coordenada NÃO fica no repositório (que é público)."""
    try:
        lat, lon = (float(x) for x in os.environ.get("CASA_COORD", "").split(","))
        return lat, lon
    except ValueError:
        return None


def perto_de_casa(pontos):
    """True se o pedal sai ou chega perto de casa. Sem CASA_COORD, vale True: na dúvida, corta (mais seguro)."""
    casa = coordenada_de_casa()
    if casa is None or not pontos:
        return True
    return metros(casa, pontos[0]) <= RAIO_CASA_M or metros(casa, pontos[-1]) <= RAIO_CASA_M


def cortar_pontas(pontos, corte=None):
    """Tira o começo e o fim do traçado (CORTE_METROS), mas só nos pedais que saem de perto de casa."""
    if corte is None:
        corte = CORTE_METROS if perto_de_casa(pontos) else 0
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
ESTATICAS = [("https://brotenatrilha.com.br/privacidade/", "2026-10-12")]


# ----------------------------------------------------------------------------- cidades por onde o pedal passa
_municipios = None


def carregar_municipios():
    """Limites dos municípios do Espírito Santo (IBGE), em ferramentas/municipios_es.json."""
    global _municipios
    if _municipios is None:
        caminho = os.path.join(os.path.dirname(__file__), "municipios_es.json")
        bruto = json.load(open(caminho, encoding="utf-8")) if os.path.exists(caminho) else {}
        _municipios = []
        for nome, poligonos in bruto.items():
            lons = [pt[0] for pol in poligonos for anel in pol for pt in anel]
            lats = [pt[1] for pol in poligonos for anel in pol for pt in anel]
            _municipios.append((nome, (min(lons), min(lats), max(lons), max(lats)), poligonos))
    return _municipios


def dentro_do_anel(lon, lat, anel):
    dentro, j = False, len(anel) - 1
    for i in range(len(anel)):
        xi, yi = anel[i]
        xj, yj = anel[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def municipio_do_ponto(lat, lon):
    for nome, (x0, y0, x1, y1), poligonos in carregar_municipios():
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            continue
        for pol in poligonos:
            if dentro_do_anel(lon, lat, pol[0]) and not any(dentro_do_anel(lon, lat, buraco) for buraco in pol[1:]):
                return nome
    return None


def cidades_do_percurso(pontos, minimo_m=500):
    """(cidade de saída, cidade de chegada, [cidades por onde passa, na ordem]) a partir do traçado completo; passar de
    raspão (menos de 500 m dentro do município) não conta."""
    if len(pontos) < 2 or not carregar_municipios():
        return None, None, []
    nomes = [municipio_do_ponto(la, lo) for la, lo in pontos]
    sai = next((n for n in nomes if n), None)
    chega = next((n for n in reversed(nomes) if n), None)
    dist, ordem = {}, []
    for (a, b), n in zip(zip(pontos, pontos[1:]), nomes):
        if not n:
            continue
        if n not in dist:
            dist[n] = 0.0
            ordem.append(n)
        dist[n] += metros(a, b)
    return sai, chega, [n for n in ordem if dist[n] >= minimo_m or n in (sai, chega)]


def slug_texto(t):
    return re.sub(r"[^a-z0-9]+", "-", sem_acento(t.lower())).strip("-")


def linha_cidades(p, limite=4):
    sai, chega = p.get("_sai"), p.get("_chega")
    passa = [c for c in p.get("_passa", []) if c not in (sai, chega)]
    partes = []
    if sai:
        partes.append(f"Sai de <b>{html.escape(sai)}</b>")
    if chega and chega != sai:
        partes.append(f"chega em <b>{html.escape(chega)}</b>")
    if passa:
        mostra = passa[:limite]
        resto = len(passa) - len(mostra)
        partes.append("passa por " + ", ".join(html.escape(c) for c in mostra) + (f" e mais {resto}" if resto > 0 else ""))
    return f'<p class="cidades">{" · ".join(partes)}</p>' if partes else ""


# ----------------------------------------------------------------------------- GPX para baixar (sem o começo e o fim)
PASSO_GPX_M = 15                                     # um ponto a cada 15 m: arquivo leve e traçado fiel
_strava_limitou = False                              # depois de um 429 (limite de consultas) o robô para de pedir; amanhã continua


def caminho_gpx(pasta_gpx, pedal_id):
    return os.path.join(pasta_gpx, f"{pedal_id}.gpx")


def montar_gpx(titulo, pontos, altitudes, cortado):
    """GPX só com o miolo do percurso (sem horários, para não dizer a que horas alguém saiu/chegou)."""
    trk = []
    for (lat, lon), alt in zip(pontos, altitudes):
        ele = f"<ele>{alt:.1f}</ele>" if alt is not None else ""
        trk.append(f'      <trkpt lat="{lat:.5f}" lon="{lon:.5f}">{ele}</trkpt>')
    nome = html.escape(titulo)
    aviso = f"Percurso sem os primeiros e os últimos {CORTE_METROS} m. " if cortado else ""
    cabecalho = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="Brote na Trilha (brotenatrilha.com.br)" xmlns="http://www.topografix.com/GPX/1/1">',
        f'  <metadata><name>{nome}</name><desc>{aviso}brotenatrilha.com.br</desc></metadata>',
        '  <trk>',
        f'    <name>{nome}</name>',
        '    <trkseg>',
    ]
    return "\n".join(cabecalho + trk + ['    </trkseg>', '  </trk>', '</gpx>', ''])


def gerar_gpx(p, pasta_gpx):
    """Baixa o traçado detalhado do Strava, corta o começo e o fim, afina os pontos e grava pedais/gpx/ID.gpx.
    Devolve True se o arquivo existe (já estava lá ou foi criado agora)."""
    global _strava_limitou
    destino = caminho_gpx(pasta_gpx, p["id"])
    if os.path.exists(destino):
        return True
    if not _token_strava or _strava_limitou:
        return False
    try:
        fluxos = http_json(f"https://www.strava.com/api/v3/activities/{p['id']}/streams?keys=latlng,altitude&key_by_type=true",
                           None, {"Authorization": "Bearer " + _token_strava})
    except urllib.error.HTTPError as erro:
        if erro.code == 429:
            _strava_limitou = True
        print("  sem GPX:", p["name"], "- HTTP", erro.code)
        return False
    except Exception as erro:
        print("  sem GPX:", p["name"], "-", erro)
        return False
    if isinstance(fluxos, list):                       # key_by_type=false devolve lista; garante o formato de dicionário
        fluxos = {f["type"]: f for f in fluxos}
    brutos = [tuple(x) for x in (fluxos.get("latlng") or {}).get("data", [])]
    alts = (fluxos.get("altitude") or {}).get("data", [])
    if len(alts) != len(brutos):
        alts = [None] * len(brutos)
    if len(brutos) < 4:
        return False
    acum = [0.0]
    for a, b in zip(brutos, brutos[1:]):
        acum.append(acum[-1] + metros(a, b))
    total = acum[-1]
    cortado = perto_de_casa(brutos)
    corte = CORTE_METROS if cortado else 0
    if total < 4 * corte:
        return False
    pontos, altitudes, ultimo = [], [], None
    for ponto, alt, d in zip(brutos, alts, acum):
        if d < corte or d > total - corte:
            continue
        if ultimo is None or metros(ultimo, ponto) >= PASSO_GPX_M:
            pontos.append(ponto)
            altitudes.append(alt)
            ultimo = ponto
    if len(pontos) < 5:
        return False
    os.makedirs(pasta_gpx, exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(montar_gpx(titulo_do_pedal(p["name"]), pontos, altitudes, cortado))
    time.sleep(0.5)
    return True


NOTA_GPX = '<p class="nota-gpx">O GPX traz o percurso sem os primeiros e os últimos 800 m, para não mostrar de onde o pedal sai.</p>'


def bloco_gpx(p):
    """Botão de download do GPX no fim da página do pedal (só se o arquivo existe)."""
    if not p.get("_gpx"):
        return ""
    nome = f'{p["_slug"]}.gpx'
    return (f'<a class="botao claro" href="/pedais/gpx/{p["id"]}.gpx" download="{html.escape(nome)}">Baixar GPX</a>')


# ----------------------------------------------------------------------------- bairros e localidades (OpenStreetMap)
NAO_E_BAIRRO = re.compile(r"^(terminal|posto|rodovi|br-|es-|aeroporto|rodovi[aá]ria)", re.I)   # pontos de referência que o OSM marca como lugar
CHAVES_LUGAR = ["suburb", "neighbourhood", "quarter", "city_district", "village", "hamlet"]
CORTE_LUGARES_M = 2500        # não lista os primeiros e os últimos 2,5 km, nos pedais que saem/chegam perto de casa
PASSO_LUGARES_M = 1000        # um ponto a cada 1 km de percurso (a cada 3 km, bairros pequenos passavam batido)
_cache_lugares = None


def caminho_cache_lugares():
    return os.environ.get("CACHE_LUGARES_ARQUIVO") or os.path.join(os.path.dirname(__file__), "cache_lugares.json")


def carregar_cache_lugares():
    global _cache_lugares
    if _cache_lugares is None:
        caminho = caminho_cache_lugares()
        _cache_lugares = json.load(open(caminho, encoding="utf-8")) if os.path.exists(caminho) else {}
    return _cache_lugares


def salvar_cache_lugares():
    if _cache_lugares is not None:
        with open(caminho_cache_lugares(), "w", encoding="utf-8", newline="\n") as f:
            json.dump(_cache_lugares, f, ensure_ascii=False, sort_keys=True, indent=0)


def lugar_do_ponto(lat, lon, orcamento):
    """Bairro ou localidade do ponto (texto; "" se o OpenStreetMap não tem nenhum). None = ainda não deu para consultar."""
    cache = carregar_cache_lugares()
    chave = f"{lat:.3f},{lon:.3f}"
    if chave in cache:
        return cache[chave]
    if orcamento["consultas"] <= 0 or orcamento["falhas"] >= 5:
        return None
    url = (f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=14&addressdetails=1&accept-language=pt-BR"
           f"&lat={lat:.5f}&lon={lon:.5f}&email=brotenatrilha@gmail.com")
    orcamento["consultas"] -= 1
    try:
        req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(req, timeout=30) as r:
            endereco = json.load(r).get("address", {})
        lugar = next((endereco[k] for k in CHAVES_LUGAR if endereco.get(k)), "")
        cache[chave] = lugar
        orcamento["falhas"] = 0
        time.sleep(1.1)                              # a regra do Nominatim: no máximo uma consulta por segundo
        return lugar
    except Exception:
        orcamento["falhas"] += 1
        time.sleep(5)
        return None


def amostras_do_percurso(pontos):
    miolo = cortar_pontas(pontos, CORTE_LUGARES_M if perto_de_casa(pontos) else 0)   # mesma regra do mapa: só corta quem sai de perto de casa
    if len(miolo) < 2:
        return []
    saida, acum = [miolo[0]], 0.0
    for a, b in zip(miolo, miolo[1:]):
        acum += metros(a, b)
        if acum >= PASSO_LUGARES_M:
            saida.append(b)
            acum = 0.0
    return saida


def lugares_do_percurso(pontos, orcamento):
    """[(cidade, [bairros e localidades na ordem do percurso])]; só entra o que o OpenStreetMap conhece."""
    grupos = {}
    for lat, lon in amostras_do_percurso(pontos):
        cidade = municipio_do_ponto(lat, lon)
        lugar = lugar_do_ponto(lat, lon, orcamento)
        if not cidade or not lugar or lugar == cidade or NAO_E_BAIRRO.match(lugar):
            continue
        lista = grupos.setdefault(cidade, [])
        if lugar not in lista:
            lista.append(lugar)
    return [(c, ls) for c, ls in grupos.items()]


def bloco_lugares(p):
    grupos = p.get("_lugares") or []
    if not grupos:
        return ""
    itens = "".join(f"<li><strong>{html.escape(c)}</strong>: {html.escape(', '.join(ls))}</li>" for c, ls in grupos)
    return ('<section class="lugares"><h2>Por onde passa</h2><ul>' + itens + '</ul>'
            '<p class="nota-lugares">Bairros e localidades segundo o OpenStreetMap, na ordem do percurso' + (' e sem o começo e o fim do pedal' if p.get('_cortado') else '') + '.</p></section>')


# ----------------------------------------------------------------------------- clima no início e no fim (Open-Meteo)
PONTOS_CARDEAIS = ["N", "NNE", "NE", "ENE", "L", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
_cache_clima = None
_horas = {}


def caminho_cache_clima():
    return os.environ.get("CACHE_CLIMA_ARQUIVO") or os.path.join(os.path.dirname(__file__), "cache_clima.json")


def carregar_cache_clima():
    global _cache_clima
    if _cache_clima is None:
        caminho = caminho_cache_clima()
        _cache_clima = json.load(open(caminho, encoding="utf-8")) if os.path.exists(caminho) else {}
    return _cache_clima


def salvar_cache_clima():
    if _cache_clima is not None:
        with open(caminho_cache_clima(), "w", encoding="utf-8", newline="\n") as f:
            json.dump(_cache_clima, f, ensure_ascii=False, sort_keys=True, indent=0)


def horas_do_dia(lat, lon, dia):
    """{hora: {temp, vento, dir, rajada}} do dia, para um ponto arredondado a ~11 km (o modelo não é mais fino que isso, e
    assim a coordenada exata de onde o pedal sai nunca vai para fora)."""
    lat, lon = round(lat, 1), round(lon, 1)
    chave = f"{lat},{lon},{dia}"
    if chave in _horas:
        return _horas[chave]
    campos = "temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,wind_gusts_10m,weather_code,precipitation,cloud_cover"
    urls = [f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={dia}&end_date={dia}&hourly={campos}&timezone=America%2FSao_Paulo",
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={campos}&past_days=14&forecast_days=1&timezone=America%2FSao_Paulo"]
    for url in urls:                                  # o arquivo histórico atrasa uns dias: nos dias recentes vale a previsão com "dias passados"
        try:
            h = http_json(url, None, {"User-Agent": AGENTE})["hourly"]
            saida = {}
            for i, t in enumerate(h["time"]):
                if t.startswith(dia) and h["temperature_2m"][i] is not None:
                    saida[int(t[11:13])] = {"temp": h["temperature_2m"][i], "sens": h["apparent_temperature"][i], "vento": h["wind_speed_10m"][i],
                                           "dir": h["wind_direction_10m"][i], "rajada": h["wind_gusts_10m"][i],
                                           "codigo": h["weather_code"][i], "chuva": h["precipitation"][i] or 0,
                                           "nuvens": h["cloud_cover"][i]}
            if saida:
                _horas[chave] = saida
                time.sleep(0.3)
                return saida
        except Exception:
            continue
    return None


def clima_do_pedal(p, pontos, cache):
    """Temperatura e vento na hora mais próxima do começo e do fim do pedal (None se ainda não deu para obter)."""
    chave = str(p["id"])
    if cache.get(chave, {}).get("ok") and "serie" in cache[chave] and all("dir" in r for r in cache[chave]["serie"]):
        return cache[chave]
    if len(pontos) < 2:
        return None
    inicio = datetime.strptime(p["start_date_local"][:19], "%Y-%m-%dT%H:%M:%S")
    fim = inicio + timedelta(seconds=p.get("elapsed_time") or p["moving_time"])
    mesmo_dia = fim.date() == inicio.date()
    ultima = fim.hour if mesmo_dia else 23
    res = {"ok": False, "chuva_mm": 0.0}
    for rotulo, instante, ponto in (("inicio", inicio, pontos[0]), ("fim", fim, pontos[-1])):
        horas = horas_do_dia(ponto[0], ponto[1], instante.strftime("%Y-%m-%d"))
        hora = min(int(round(instante.hour + instante.minute / 60)), 23)
        if not horas or hora not in horas:
            return None
        res[rotulo] = {"hora": instante.strftime("%H:%M"), **horas[hora]}
        if rotulo == "inicio":                         # chuva somada das horas em que o pedal esteve na estrada (no dia da saída)
            res["chuva_mm"] = round(sum((horas.get(h2) or {}).get("chuva", 0) for h2 in range(inicio.hour, ultima + 1)), 1)
            # série hora a hora, de uma hora antes da saída a uma hora depois da chegada, para o gráfico
            res["serie"] = [{"h": h2, **{k: (horas[h2].get(k) or 0) for k in ("temp", "sens", "vento", "dir", "rajada", "chuva")}}
                            for h2 in range(max(0, inicio.hour - 1), min(23, ultima + 1) + 1) if h2 in horas]
            res["janela"] = [round(inicio.hour + inicio.minute / 60, 2),
                             round(fim.hour + fim.minute / 60, 2) if mesmo_dia else 24.0]
    res["ok"] = True
    cache[chave] = res
    return res


CEU = {0: "Céu limpo", 1: "Céu quase limpo", 2: "Parcialmente nublado", 3: "Nublado", 45: "Neblina", 48: "Neblina",
       51: "Garoa fraca", 53: "Garoa", 55: "Garoa forte", 56: "Garoa", 57: "Garoa", 61: "Chuva fraca", 63: "Chuva", 65: "Chuva forte",
       66: "Chuva", 67: "Chuva", 80: "Pancadas de chuva fracas", 81: "Pancadas de chuva", 82: "Pancadas de chuva fortes",
       95: "Trovoada", 96: "Trovoada com granizo", 99: "Trovoada com granizo"}


def descricao_ceu(d):
    return CEU.get(int(d.get("codigo") or 0), "Nublado" if (d.get("nuvens") or 0) > 60 else "Céu parcialmente nublado")


def rosa(graus):
    return PONTOS_CARDEAIS[int((graus % 360) / 22.5 + 0.5) % 16]


def descricao_vento(d):
    if d["vento"] < 2:
        return "vento calmo"
    t = f"vento de {rosa(d['dir'])}, {num(d['vento'])} km/h"
    if d["rajada"] >= 15 and d["rajada"] - d["vento"] >= 10:
        t += f" (rajadas de {num(d['rajada'])} km/h)"
    return t


MOSTRAR_GRAFICO_CLIMA = False                         # desligado a pedido: a página mostra só as colunas de início e fim


def grafico_clima(c):
    """Temperatura, sensação, vento e chuva hora a hora em torno do pedal (SVG); a faixa destacada é a duração do pedal."""
    serie = c.get("serie") or []
    if len(serie) < 2:
        return ""
    W, E, D = 600, 46, 14                                  # largura, margem esquerda e direita
    x0, x1 = serie[0]["h"], serie[-1]["h"]

    def X(h):                                              # 14 de folga em cada ponta para as barras não saírem do quadro
        return E + 14 + (h - x0) / (x1 - x0) * (W - E - D - 28)

    def escala(vmin, vmax, topo, base):
        return lambda v: base - (v - vmin) / ((vmax - vmin) or 1) * (base - topo)

    paineis = {"temp": (14, 116), "vento": (160, 244), "chuva": (318, 382)}
    banda = (f'<rect class="banda" x="{X(max(c["janela"][0], x0)):.1f}" y="6" width="{max(X(min(c["janela"][1], x1)) - X(max(c["janela"][0], x0)), 2):.1f}" '
             f'height="{paineis["chuva"][1] - 0}" rx="4"/>')
    partes = [banda]

    def grade(titulo, topo, base, vmin, vmax, y):
        ticks = {vmin, vmax, round((vmin + vmax) / 2, 1)}
        out = [f'<text class="titulo-painel" x="{E}" y="{topo - 3}">{titulo}</text>']
        for t in sorted(ticks):
            out.append(f'<line class="grade" x1="{E}" x2="{W - D}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>'
                       f'<text class="eixo" x="{E - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{num(t)}</text>')
        return out

    # painel 1: temperatura e sensação
    topo, base = paineis["temp"]
    todos = [v for r in serie for v in (r["temp"], r["sens"])]
    vmin, vmax = math.floor(min(todos)) - 1, math.ceil(max(todos)) + 1
    y = escala(vmin, vmax, topo, base)
    partes += grade("Temperatura (°C)", topo, base, vmin, vmax, y)
    for chave in ("sens", "temp"):
        pts = " ".join(f"{X(r['h']):.1f},{y(r[chave]):.1f}" for r in serie)
        partes.append(f'<polyline class="serie {chave}" points="{pts}"/>')
        for r in serie:
            partes.append(f'<circle class="ponto {chave}" cx="{X(r["h"]):.1f}" cy="{y(r[chave]):.1f}" r="3"><title>{r["h"]:02d}h: {num(r[chave])} °C '
                          f'({"temperatura" if chave == "temp" else "sensação"})</title></circle>')
    for r in serie:
        partes.append(f'<text class="valor" x="{X(r["h"]):.1f}" y="{y(r["temp"]) - 7:.1f}" text-anchor="middle">{num(r["temp"])}</text>')

    # painel 2: vento (barras) e rajadas (traço)
    topo, base = paineis["vento"]
    vmax = max(10, math.ceil(max(r["rajada"] for r in serie) / 10) * 10)
    y = escala(0, vmax, topo, base)
    partes += grade("Vento (km/h)", topo, base, 0, vmax, y)
    partes.append(f'<text class="eixo" x="{E - 6}" y="266" text-anchor="end">vem de</text>')
    larg = (W - E - D - 28) / max(1, (x1 - x0)) * 0.46
    for r in serie:
        x = X(r["h"])
        partes.append(f'<rect class="barra vento" x="{x - larg / 2:.1f}" y="{y(r["vento"]):.1f}" width="{larg:.1f}" height="{base - y(r["vento"]):.1f}" rx="2">'
                      f'<title>{r["h"]:02d}h: vento {num(r["vento"])} km/h, rajadas de {num(r["rajada"])} km/h</title></rect>')
        partes.append(f'<line class="rajada" x1="{x - larg / 2:.1f}" x2="{x + larg / 2:.1f}" y1="{y(r["rajada"]):.1f}" y2="{y(r["rajada"]):.1f}"/>')
        partes.append(f'<text class="valor" x="{x:.1f}" y="{y(max(r["vento"], r["rajada"])) - 5:.1f}" text-anchor="middle">{num(r["vento"])}</text>')
        # seta aponta para onde o vento sopra (a direção do modelo diz de onde ele vem), com a letra de onde vem embaixo
        partes.append(f'<g class="seta vento" transform="translate({x:.1f} 262) rotate({r["dir"] % 360:.0f})"><path d="M0,-8 V7 M-4,2 L0,7 L4,2"/>'
                      f'<title>{r["h"]:02d}h: vento de {rosa(r["dir"])}</title></g>')
        partes.append(f'<text class="eixo" x="{x:.1f}" y="288" text-anchor="middle">{rosa(r["dir"])}</text>')

    # painel 3: chuva
    topo, base = paineis["chuva"]
    vmax = max(2, math.ceil(max(r["chuva"] for r in serie)))
    y = escala(0, vmax, topo, base)
    partes += grade("Chuva (mm por hora)", topo, base, 0, vmax, y)
    for r in serie:
        if r["chuva"] > 0:
            partes.append(f'<rect class="barra chuva" x="{X(r["h"]) - larg / 2:.1f}" y="{y(r["chuva"]):.1f}" width="{larg:.1f}" height="{base - y(r["chuva"]):.1f}" rx="2">'
                          f'<title>{r["h"]:02d}h: {num(r["chuva"], 1)} mm</title></rect>')
    for r in serie:
        partes.append(f'<text class="eixo" x="{X(r["h"]):.1f}" y="402" text-anchor="middle">{r["h"]:02d}h</text>')

    resumo = (f'Gráfico do tempo hora a hora: temperatura entre {num(min(r["temp"] for r in serie))} e {num(max(r["temp"] for r in serie))} °C, '
              f'vento de até {num(max(r["vento"] for r in serie))} km/h e {"chuva" if c.get("chuva_mm", 0) >= 0.2 else "sem chuva"} durante o pedal.')
    legenda = ('<p class="legenda"><span class="l temp">Temperatura</span><span class="l sens">Sensação</span><span class="l vento">Vento</span>'
               '<span class="l rajada">Rajada</span><span class="l seta">Seta: para onde o vento sopra</span><span class="l chuva">Chuva</span><span class="l banda">Duração do pedal</span></p>')
    return (f'<div class="grafico-rolagem"><svg class="grafico-clima" viewBox="0 0 {W} 410" role="img" aria-label="{html.escape(resumo)}">'
            + "".join(partes) + "</svg></div>" + legenda)


def bloco_clima(p):
    c = p.get("_clima")
    if not c:
        return ""

    def coluna(rotulo, d):
        return f'<div><small>{rotulo} · {d["hora"]}</small><strong>{num(d["temp"])} °C</strong><span class="ceu">{descricao_ceu(d)}</span><span>sensação de {num(d["sens"])} °C · {descricao_vento(d)}</span></div>'
    return ('<section class="clima"><h2>Clima</h2><div class="clima-grade">' + coluna("No início", c["inicio"]) + coluna("No fim", c["fim"]) +
            '</div>' + (grafico_clima(c) if MOSTRAR_GRAFICO_CLIMA else "") + '<p class="chuva-pedal">' + ("Sem chuva durante o pedal." if c.get("chuva_mm", 0) < 0.2 else f"Choveu cerca de {num(c['chuva_mm'], 1)} mm durante o pedal.") +
            '</p><p class="nota-clima">Valores estimados por modelo para a região (grade de uns 10 km), na hora mais próxima do começo e do fim. '
            'Dados do tempo: Open-Meteo.com (CC BY 4.0).</p></section>')


def slug_do_pedal(p):
    t = re.sub(r"[^a-z0-9]+", "-", sem_acento(titulo_do_pedal(p["name"]).lower())).strip("-")
    if len(t) > 60:
        t = t[:60].rsplit("-", 1)[0]
    return f'{p["start_date_local"][:10]}-{t}'


def numeros(p):
    km = p["distance"] / 1000
    media = km / (p["moving_time"] / 3600) if p["moving_time"] else 0
    return km, media


def trecho_descricao(video):
    """O primeiro parágrafo da descrição do vídeo (sem links, hashtags e chamadas), para o texto da página do pedal."""
    if not video:
        return ""
    linhas = []
    for linha in video["descricao"].replace("\r", "").split("\n"):
        linha = linha.strip()
        if not linha:
            if linhas:
                break
            continue
        if re.search(r"https?://|^#|strava|komoot|inscreva|^rota[ ,:]|^[-•*]", linha, re.I):
            if linhas:
                break
            continue
        linhas.append(linha)
    t = " ".join(linhas)
    return (t[:480].rsplit(" ", 1)[0] + "…") if len(t) > 480 else t


def mapa_html(p, prefixo_mapas, carregar="lazy"):
    if p.get("_mapa"):
        return (f'<div class="mapa com-fundo"><img src="{prefixo_mapas}{p["id"]}.webp" width="{MAPA_L}" height="{MAPA_A}" '
                f'loading="{carregar}" decoding="async" alt="">{p["_mapa"]}</div>')
    return svg_do_tracado((p.get("map") or {}).get("summary_polyline") or "") or '<div class="mapa vazio">Sem traçado</div>'


def botoes(p, claro_assistir=False, extra="", komoot=True):
    links = []
    if p.get("_video"):
        links.append(f'<a class="botao" href="https://www.youtube.com/watch?v={p["_video"]["id"]}" target="_blank" rel="noopener">Assistir</a>')
    links.append(f'<a class="botao claro" href="https://www.strava.com/activities/{p["id"]}" target="_blank" rel="noopener">Strava</a>')
    if komoot and p.get("_komoot"):
        links.append(f'<a class="botao claro" href="{html.escape(p["_komoot"])}" target="_blank" rel="noopener">Komoot</a>')
    return " ".join(links) + extra


def cartao(p):
    km, media = numeros(p)
    titulo = html.escape(titulo_do_pedal(p["name"]))
    mapa = mapa_html(p, "mapas/")
    return f"""      <article class="pedal" data-ano="{p["start_date_local"][:4]}" data-km="{km:.1f}" data-nome="{html.escape(normalizar(p["name"] + " " + " ".join(p.get("_passa", []))))}" data-sai="{slug_texto(p.get("_sai") or "")}" data-chega="{slug_texto(p.get("_chega") or "")}" data-passa="|{"|".join(slug_texto(c) for c in p.get("_passa", []))}|">
        <a class="mapa-link" href="{p['_slug']}/" aria-label="Ver o pedal {titulo}">{mapa}</a>
        <div class="corpo">
          <h3><a href="{p['_slug']}/">{titulo}</a></h3>
          <p class="data">{data_longa(p["start_date_local"])}</p>
          {linha_cidades(p)}
          <dl>
            <div><dt>Distância</dt><dd>{num(km, 1)} km</dd></div>
            <div><dt>Subida</dt><dd>{num(p["total_elevation_gain"])} m</dd></div>
            <div><dt>Tempo</dt><dd>{duracao(p["moving_time"])}</dd></div>
            <div><dt>Média</dt><dd>{num(media, 1)} km/h</dd></div>
          </dl>
          <p class="links">{botoes(p, extra=" " + bloco_gpx(p) if p.get("_gpx") else "", komoot=False)}</p>
        </div>
      </article>"""


def montar_pagina(pedais, modelo):
    por_ano = {}
    for p in pedais:
        por_ano.setdefault(p["start_date_local"][:4], []).append(p)
    anos = sorted(por_ano, reverse=True)
    blocos = [f'    <div class="bloco-ano">\n    <h2 class="ano">{ano}</h2>\n    <div class="grade">\n'
              + "\n".join(cartao(p) for p in por_ano[ano]) + "\n    </div>\n    </div>" for ano in anos]
    cont_passa, cont_sai, cont_chega = {}, {}, {}
    for p in pedais:
        for c in set(p.get("_passa", [])):
            cont_passa[c] = cont_passa.get(c, 0) + 1
        if p.get("_sai"):
            cont_sai[p["_sai"]] = cont_sai.get(p["_sai"], 0) + 1
        if p.get("_chega"):
            cont_chega[p["_chega"]] = cont_chega.get(p["_chega"], 0) + 1

    def opcoes(cont):
        return "".join(f'<option value="{slug_texto(c)}">{html.escape(c)} ({n})</option>'
                       for c, n in sorted(cont.items(), key=lambda x: (-x[1], sem_acento(x[0]))))
    chips_ano = '<button type="button" class="chip" data-filtro="ano" data-valor="todos" aria-pressed="true">Todos os anos</button>' + "".join(
        f'<button type="button" class="chip" data-filtro="ano" data-valor="{a}" aria-pressed="false">{a}</button>' for a in anos)
    km = sum(p["distance"] for p in pedais) / 1000
    subida = sum(p["total_elevation_gain"] for p in pedais)
    resumo = f'{len(pedais)} pedais · {num(km)} km · {num(subida)} m de subida'
    return (modelo.replace("{{RESUMO}}", resumo).replace("{{CHIPS_ANO}}", chips_ano).replace("{{OPCOES_PASSA}}", opcoes(cont_passa)).replace("{{OPCOES_SAI}}", opcoes(cont_sai)).replace("{{OPCOES_CHEGA}}", opcoes(cont_chega))
            .replace("{{CONTEUDO}}", "\n".join(blocos))
            .replace("{{ATUALIZADO}}", data_longa(datetime.now().strftime("%Y-%m-%d"))))


def montar_pagina_pedal(p, mais_novo, mais_velho, modelo):
    km, media = numeros(p)
    titulo = titulo_do_pedal(p["name"])
    v = p.get("_video")
    texto = trecho_descricao(v)
    descricao_meta = (f"{titulo}: {num(km, 1)} km, {num(p['total_elevation_gain'])} m de subida e {duracao(p['moving_time'])} de pedal "
                      f"em {data_longa(p['start_date_local'])}. Veja o mapa do percurso e o vídeo.")
    url = f"https://brotenatrilha.com.br/pedais/{p['_slug']}/"
    og = f"https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg" if v else "https://brotenatrilha.com.br/compartilhar.jpg"
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Brote na Trilha", "item": "https://brotenatrilha.com.br/"},
        {"@type": "ListItem", "position": 2, "name": "Pedais", "item": "https://brotenatrilha.com.br/pedais/"},
        {"@type": "ListItem", "position": 3, "name": titulo, "item": url}]}]
    if v:
        ld.append({"@context": "https://schema.org", "@type": "VideoObject", "name": v["titulo"],
                   "description": texto or descricao_meta, "thumbnailUrl": [og], "uploadDate": v["data"],
                   "embedUrl": f"https://www.youtube.com/embed/{v['id']}", "contentUrl": f"https://www.youtube.com/watch?v={v['id']}"})
    video = (f'<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/{v["id"]}" title="{html.escape(v["titulo"])}" loading="lazy" '
             'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
             'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>') if v else ""
    nav = []
    if mais_velho:
        nav.append(f'<a class="anterior" href="/pedais/{mais_velho["_slug"]}/"><small>← Pedal anterior</small>{html.escape(titulo_do_pedal(mais_velho["name"]))}</a>')
    if mais_novo:
        nav.append(f'<a class="proximo" href="/pedais/{mais_novo["_slug"]}/"><small>Próximo pedal →</small>{html.escape(titulo_do_pedal(mais_novo["name"]))}</a>')
    nums = (f'<div><dt>Distância</dt><dd>{num(km, 1)} km</dd></div><div><dt>Subida</dt><dd>{num(p["total_elevation_gain"])} m</dd></div>'
            f'<div><dt>Tempo</dt><dd>{duracao(p["moving_time"])}</dd></div><div><dt>Média</dt><dd>{num(media, 1)} km/h</dd></div>')
    troca = {"{{TITULO}}": html.escape(titulo), "{{DESCRICAO_META}}": html.escape(descricao_meta), "{{URL}}": url,
             "{{OG_IMAGE}}": og, "{{DATA_LONGA}}": data_longa(p["start_date_local"]), "{{MAPA}}": mapa_html(p, "/pedais/mapas/", "eager"),
             "{{NUMEROS}}": nums, "{{VIDEO}}": video, "{{TEXTO}}": f"<p class=\"texto\">{html.escape(texto)}</p>" if texto else "",
             "{{CLIMA}}": bloco_clima(p), "{{LUGARES}}": bloco_lugares(p), "{{LINKS}}": botoes(p, extra=" " + bloco_gpx(p)) if p.get("_gpx") else botoes(p), "{{NOTA_GPX}}": NOTA_GPX if p.get("_gpx") and p.get("_cortado") else "",
             "{{NOTA_CORTE}}": "O traçado não mostra o começo nem o fim do percurso. " if p.get("_cortado") else "", "{{CIDADES}}": linha_cidades(p, 99), "{{NAV}}": "".join(nav),
             "{{JSONLD}}": "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + "</script>\n" for x in ld)}
    saida = modelo
    for k, val in troca.items():
        saida = saida.replace(k, val)
    return saida


def bloco_ultimo(p):
    """O 'Último pedal' da página inicial (fica entre os marcadores <!--ULTIMO_PEDAL--> do index.html)."""
    km, media = numeros(p)
    titulo = html.escape(titulo_do_pedal(p["name"]))
    assistir = (f'<a class="botao verde" href="https://www.youtube.com/watch?v={p["_video"]["id"]}" target="_blank" rel="noopener">Assistir no YouTube</a> '
                if p.get("_video") else "")
    return f"""    <div class="ultimo">
      <a class="ultimo-mapa" href="pedais/{p['_slug']}/" aria-label="Ver o pedal {titulo}">{mapa_html(p, "pedais/mapas/")}</a>
      <div class="ultimo-texto">
        <h3><a href="pedais/{p['_slug']}/">{titulo}</a></h3>
        <p class="data">{data_longa(p["start_date_local"])}</p>
        <dl>
          <div><dt>Distância</dt><dd>{num(km, 1)} km</dd></div>
          <div><dt>Subida</dt><dd>{num(p["total_elevation_gain"])} m</dd></div>
          <div><dt>Tempo</dt><dd>{duracao(p["moving_time"])}</dd></div>
          <div><dt>Média</dt><dd>{num(media, 1)} km/h</dd></div>
        </dl>
        <p class="links">{assistir}<a class="botao borda" href="pedais/">Ver todos os pedais</a></p>
      </div>
    </div>"""


def injetar_na_home(caminho, bloco):
    if not (caminho and os.path.exists(caminho)):
        return False
    s = open(caminho, encoding="utf-8").read()
    novo = re.sub(r"(<!--ULTIMO_PEDAL-->).*?(<!--/ULTIMO_PEDAL-->)", lambda m: m.group(1) + "\n" + bloco + "\n    " + m.group(2), s, flags=re.S)
    if novo == s:
        return False
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(novo)
    return True


def escrever_sitemap(caminho, pedais):
    hoje = datetime.now().strftime("%Y-%m-%d")
    urls = [("https://brotenatrilha.com.br/", hoje), ("https://brotenatrilha.com.br/pedais/", hoje)] + ESTATICAS
    urls += [(f"https://brotenatrilha.com.br/pedais/{p['_slug']}/", p["start_date_local"][:10]) for p in pedais]
    corpo = "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + corpo + "</urlset>\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", help="arquivo JSON com atividades no formato da API do Strava (em vez de buscar)")
    ap.add_argument("--saida", default="pedais/index.html")
    ap.add_argument("--modelo", default=os.path.join(os.path.dirname(__file__), "modelo_pedais.tpl"))
    ap.add_argument("--modelo-pedal", default=os.path.join(os.path.dirname(__file__), "modelo_pedal.tpl"))
    ap.add_argument("--home", default="", help="index.html da página inicial, para atualizar o bloco 'Último pedal'")
    ap.add_argument("--sitemap", default="", help="sitemap.xml a reescrever com as páginas dos pedais")
    args = ap.parse_args()

    atividades = json.load(open(args.teste, encoding="utf-8")) if args.teste else atividades_do_strava()
    if atividades is None:
        print("Sem as credenciais do Strava (STRAVA_*): nada a fazer.")
        return 0
    caminho_ajustes = os.path.join(os.path.dirname(__file__), "ajustes_pedais.json")
    ajustes = json.load(open(caminho_ajustes, encoding="utf-8")) if os.path.exists(caminho_ajustes) else {}
    desde = ajustes.get("_desde", "")                  # pedais antes desta data (AAAA-MM-DD) não aparecem
    ocultar = {str(i) for i in ajustes.get("_ocultar", [])}   # números de atividades do Strava que não devem aparecer
    videos = videos_do_canal()
    com_video = set(atividades_dos_videos(videos))   # pedais que o canal linkou na descrição de algum vídeo
    pedais = [a for a in atividades
              if (PREFIXO.match(a.get("name", "")) or str(a["id"]) in com_video)
              and a.get("sport_type", a.get("type")) in ("Ride", "GravelRide", "MountainBikeRide", "EBikeRide")
              and a["start_date_local"][:10] >= desde and str(a["id"]) not in ocultar]
    pedais.sort(key=lambda a: a["start_date_local"], reverse=True)
    casar_videos(pedais, videos, {k: v for k, v in ajustes.items() if not k.startswith("_")})
    usados = set()
    for p in pedais:
        p["_komoot"] = link_komoot(p["_video"])
        p["_cortado"] = perto_de_casa(decodificar((p.get("map") or {}).get("summary_polyline") or ""))   # só esses têm começo e fim cortados
        p["_slug"] = slug_do_pedal(p)
        if p["_slug"] in usados:
            p["_slug"] += f"-{p['id']}"
        usados.add(p["_slug"])

    base = os.path.dirname(os.path.abspath(args.saida))
    pasta_mapas = os.path.join(base, "mapas")
    pasta_cache = os.path.join(os.environ.get("TMPDIR", os.environ.get("TEMP", "/tmp")), "tiles_pedais")
    for p in pedais:
        p["_mapa"] = None
        pontos = cortar_pontas(decodificar((p.get("map") or {}).get("summary_polyline") or ""))
        if Image is not None and len(pontos) >= 5:
            try:
                p["_mapa"] = gerar_mapa(p["id"], pontos, pasta_mapas, pasta_cache)
            except Exception as erro:               # sem mapa de fundo, o cartão mostra só o traçado
                print("  sem mapa de fundo:", p["name"], "-", erro)
    for p in pedais:                                    # cidades: saída e por onde passa (traçado completo, só para isso)
        p["_sai"], p["_chega"], p["_passa"] = cidades_do_percurso(decodificar((p.get("map") or {}).get("summary_polyline") or ""))
    print(f"  cidades: {sum(1 for p in pedais if p['_sai'])} pedais com cidade de saída; "
          f"{len({c for p in pedais for c in p['_passa']})} cidades no total")
    orcamento = {"consultas": int(os.environ.get("ORCAMENTO_LUGARES", "450")), "falhas": 0}
    for p in pedais:                                    # bairros e localidades (a cada rodada vai completando o que falta)
        p["_lugares"] = lugares_do_percurso(decodificar((p.get("map") or {}).get("summary_polyline") or ""), orcamento)
    salvar_cache_lugares()
    print(f"  lugares: {sum(1 for p in pedais if p['_lugares'])} pedais com lista; consultas feitas nesta rodada: "
          f"{int(os.environ.get('ORCAMENTO_LUGARES', '450')) - orcamento['consultas']}; falhas seguidas: {orcamento['falhas']}")
    pasta_gpx = os.path.join(base, "gpx")
    for p in pedais:                                    # arquivo GPX para baixar (só busca no Strava o que ainda não existe)
        p["_gpx"] = gerar_gpx(p, pasta_gpx)
    if os.path.isdir(pasta_gpx):
        atuais_gpx = {f"{p['id']}.gpx" for p in pedais}
        for nome in os.listdir(pasta_gpx):
            if nome.endswith(".gpx") and nome not in atuais_gpx:
                os.remove(os.path.join(pasta_gpx, nome))
                print("  GPX removido:", nome)
    print(f"  gpx: {sum(1 for p in pedais if p['_gpx'])} de {len(pedais)} pedais com GPX para baixar")
    cache_clima = carregar_cache_clima()
    for p in pedais:                                    # temperatura e vento no começo e no fim
        p["_clima"] = clima_do_pedal(p, decodificar((p.get("map") or {}).get("summary_polyline") or ""), cache_clima)
    salvar_cache_clima()
    print(f"  clima: {sum(1 for p in pedais if p['_clima'])} de {len(pedais)} pedais com temperatura e vento")
    if os.path.isdir(pasta_mapas):                      # tira os mapas de pedais que saíram da página
        atuais = {f"{p['id']}.webp" for p in pedais}
        for nome in os.listdir(pasta_mapas):
            if nome.endswith(".webp") and nome not in atuais:
                os.remove(os.path.join(pasta_mapas, nome))
                print("  mapa removido:", nome)
    print(f"  começo e fim cortados em {sum(1 for p in pedais if p['_cortado'])} de {len(pedais)} pedais (os que saem ou chegam perto de casa)")
    print(f"{len(pedais)} pedais; {sum(1 for p in pedais if p['_video'])} com vídeo; {sum(1 for p in pedais if p['_komoot'])} com Komoot; "
          f"{sum(1 for p in pedais if p['_mapa'] or svg_do_tracado((p.get('map') or {}).get('summary_polyline') or ''))} com mapa")
    for p in pedais:
        if not p["_video"]:
            print("  sem vídeo:", p["start_date_local"][:10], p["name"])

    modelo = open(args.modelo, encoding="utf-8").read()
    modelo_pedal = open(args.modelo_pedal, encoding="utf-8").read()
    os.makedirs(base, exist_ok=True)
    with open(args.saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(montar_pagina(pedais, modelo))
    for i, p in enumerate(pedais):                      # uma página para cada pedal
        pasta = os.path.join(base, p["_slug"])
        os.makedirs(pasta, exist_ok=True)
        mais_novo = pedais[i - 1] if i > 0 else None
        mais_velho = pedais[i + 1] if i + 1 < len(pedais) else None
        with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(montar_pagina_pedal(p, mais_novo, mais_velho, modelo_pedal))
    slugs = {p["_slug"] for p in pedais}                # apaga as páginas de pedais que saíram
    for nome in os.listdir(base):
        if nome not in ("mapas", "gpx") and os.path.isdir(os.path.join(base, nome)) and nome not in slugs:
            shutil.rmtree(os.path.join(base, nome))
            print("  página removida:", nome)
    if pedais and injetar_na_home(args.home, bloco_ultimo(pedais[0])):
        print("  home: último pedal atualizado ->", titulo_do_pedal(pedais[0]["name"]))
    if args.sitemap and pedais:
        escrever_sitemap(args.sitemap, pedais)
    return 0


if __name__ == "__main__":
    sys.exit(main())
