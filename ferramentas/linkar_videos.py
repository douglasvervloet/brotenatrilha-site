#!/usr/bin/env python3
"""Acrescenta, na descrição de cada vídeo do canal, o link da página do pedal neste site.

Só faz duas chamadas ao YouTube: videos.list (ler o texto atual) e videos.update (gravar o texto novo). Nunca apaga nada:
o texto antigo é guardado em ferramentas/log_links_youtube.json antes de cada gravação, e o script confere que a única
diferença entre o antigo e o novo é a linha do link. O vídeo só é alterado quando a página do pedal já responde no ar.

Sem APLICAR=1 só simula (mostra o que mudaria e não grava nada).
Segredos: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET e YOUTUBE_REFRESH_TOKEN (criados por ferramentas/youtube_autorizar.ps1).
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from xml.etree import ElementTree

SITE = "https://brotenatrilha.com.br"
MARCA = "brotenatrilha.com.br/pedais/"      # se a descrição já tem isto, o vídeo já está com o link
LIMITE_POR_RODADA = 10                       # trava de segurança: um erro de lógica não mexe em dezenas de vídeos
ESPERA_DO_SITE_S = 480                       # tempo máximo esperando o GitHub Pages publicar uma página nova
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_DO_LOG = os.path.join(RAIZ, "ferramentas", "log_links_youtube.json")


def pedais_do_sitemap():
    """{id do vídeo: endereço da página do pedal}, lendo o sitemap e o vídeo incorporado em cada página."""
    sitemap = ElementTree.parse(os.path.join(RAIZ, "sitemap.xml"))
    resultado = {}
    for loc in sitemap.getroot().iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        achou = re.search(r"/pedais/(\d{4}-\d{2}-\d{2}-[^/]+)/$", loc.text.strip())
        pagina = os.path.join(RAIZ, "pedais", achou.group(1), "index.html") if achou else ""
        if not os.path.isfile(pagina):
            continue
        with open(pagina, encoding="utf-8") as f:
            video = re.search(r"youtube-nocookie\.com/embed/([A-Za-z0-9_-]{11})", f.read())
        if video:
            resultado[video.group(1)] = loc.text.strip()
    return resultado


def no_ar(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def esperar_no_ar(urls):
    """Espera as páginas novas aparecerem no ar (o Pages leva um ou dois minutos depois do commit); devolve as que apareceram."""
    pendentes, limite = set(urls), time.time() + ESPERA_DO_SITE_S
    while pendentes and time.time() < limite:
        pendentes = {u for u in pendentes if not no_ar(u)}
        if pendentes:
            time.sleep(30)
    return set(urls) - pendentes


def token_de_acesso():
    corpo = urllib.parse.urlencode({
        "client_id": os.environ["YOUTUBE_CLIENT_ID"], "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    try:
        with urllib.request.urlopen("https://oauth2.googleapis.com/token", corpo, timeout=30) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        if b"invalid_grant" in e.read():
            print("::error::A autorização do YouTube venceu ou foi revogada. Rode ferramentas/youtube_autorizar.ps1 de novo.")
            sys.exit(1)
        raise


def api(token, metodo, url, corpo=None):
    pedido = urllib.request.Request(url, method=metodo, headers={"Authorization": "Bearer " + token},
                                    data=None if corpo is None else json.dumps(corpo).encode())
    if corpo is not None:
        pedido.add_header("Content-Type", "application/json; charset=utf-8")
    with urllib.request.urlopen(pedido, timeout=60) as r:
        return json.load(r)


def descricao_com_link(descricao, url):
    """A descrição com a linha do link depois da última linha 'Strava:' ou 'Komoot:'; sem elas, no fim do texto."""
    linha = "Mapa, dados e clima deste pedal: " + url
    linhas = descricao.rstrip().split("\n")
    ultima = max((i for i, l in enumerate(linhas) if re.match(r"(Strava|Komoot)\s*:", l)), default=-1)
    if ultima >= 0:
        linhas.insert(ultima + 1, linha)
        return "\n".join(linhas)
    return descricao.rstrip() + "\n\n" + linha


def so_a_linha_do_link_mudou(antes, depois, url):
    """Trava de segurança: tirando a linha do link, o texto novo tem de ser igual ao antigo."""
    restante = [l for l in depois.split("\n") if l != "Mapa, dados e clima deste pedal: " + url]
    original = antes.rstrip().split("\n")
    return restante == original or restante[:len(original)] == original


def ler_log():
    if os.path.isfile(ARQUIVO_DO_LOG):
        with open(ARQUIVO_DO_LOG, encoding="utf-8") as f:
            return json.load(f)
    return []


def main():
    aplicar = os.environ.get("APLICAR") == "1"
    if not all(os.environ.get(n) for n in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")):
        print("Segredos do YouTube ainda não cadastrados (ferramentas/youtube_autorizar.ps1): nada a fazer.")
        return
    pedais = pedais_do_sitemap()
    token = token_de_acesso()
    ids = list(pedais)
    atuais = {}
    for i in range(0, len(ids), 50):
        r = api(token, "GET", "https://www.googleapis.com/youtube/v3/videos?part=snippet&maxResults=50&id=" + ",".join(ids[i:i + 50]))
        atuais.update({v["id"]: v["snippet"] for v in r.get("items", [])})

    faltam = [i for i in ids if i in atuais and MARCA not in atuais[i].get("description", "")]
    print(f"{len(pedais)} pedais com vídeo; {len(faltam)} sem o link na descrição.")
    prontos = esperar_no_ar([pedais[i] for i in faltam]) if faltam else set()

    log, gravados = ler_log(), 0
    for id_video in faltam:
        url, s = pedais[id_video], atuais[id_video]
        if url not in prontos:
            print(f"[espera] a página ainda não está no ar: {url}")
            continue
        nova = descricao_com_link(s.get("description", ""), url)
        if not so_a_linha_do_link_mudou(s.get("description", ""), nova, url):
            print(f"::warning::Conferência falhou, vídeo {id_video} não foi alterado.")
            continue
        if gravados >= LIMITE_POR_RODADA:
            print(f"[limite] {LIMITE_POR_RODADA} por rodada; o resto fica para a próxima.")
            break
        print(f"[{'grava' if aplicar else 'simula'}] {s['title']} -> {url}")
        if not aplicar:
            continue
        # videos.update repete o snippet inteiro: o que faltar aqui, o YouTube apaga
        snippet = {"title": s["title"], "description": nova, "categoryId": s["categoryId"]}
        for campo in ("tags", "defaultLanguage", "defaultAudioLanguage"):
            if s.get(campo):
                snippet[campo] = s[campo]
        log.append({"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), "video": id_video,
                    "descricao_antes": s.get("description", "")})
        with open(ARQUIVO_DO_LOG, "w", encoding="utf-8") as f:     # o log vai antes da gravação: nunca fica sem o original
            json.dump(log, f, ensure_ascii=False, indent=1)
        try:
            api(token, "PUT", "https://www.googleapis.com/youtube/v3/videos?part=snippet", {"id": id_video, "snippet": snippet})
        except urllib.error.HTTPError as e:
            print(f"::error::O YouTube recusou a gravação ({e.code}): {e.read().decode()[:300]}")
            log.pop()
            with open(ARQUIVO_DO_LOG, "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=1)
            sys.exit(1)
        gravados += 1
        time.sleep(0.5)
    print(f"Gravados: {gravados}" if aplicar else "Simulação: nada foi gravado.")


if __name__ == "__main__":
    main()
