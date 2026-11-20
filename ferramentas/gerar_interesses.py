"""Gera os pontos de interesse do Brasil para a ferramenta "Planejar pedal" (dados.brotenatrilha.com.br/br/interesses/, no R2 da Cloudflare).

Os pontos (mirantes, cachoeiras, praias, atrações e museus, locais históricos, cavernas, parques e reservas, e os picos que têm artigo na Wikipédia)
vêm de um arquivo .osm.pbf do OpenStreetMap (o mesmo do gerar_vias.py). A foto e o resumo, quando existem, vêm da Wikipédia ou do Wikidata, pelas
marcas "wikipedia" e "wikidata" do próprio ponto: o OpenStreetMap quase não guarda foto. Só entram pontos com nome.

Uso:  python gerar_interesses.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA] [CACHE.json]        (precisa do pacote "osmium": pip install osmium)

O CACHE guarda a foto, a página e o resumo já consultados (por marca "wikipedia" e "wikidata"): de um mês para o outro só os pontos
novos são consultados. Cada rodada faz no máximo LIMITE_DE_CONSULTAS consultas novas (variável de ambiente; o padrão é 5000); os
pontos que passarem disso ficam sem foto até a próxima rodada.

Um arquivo por quadrado de 1 grau (ver brasil.py): {"escala": 100000, "p": [[tipo, lat, lon, nome, foto, pagina, resumo, credito, pagina_foto], ...]},
com lat e lon em inteiros de 1e-5 grau.
Tipo: 1 mirante, 2 cachoeira, 3 praia, 4 atração ou museu, 5 histórico ou igreja notável, 6 caverna, 7 parque ou reserva, 8 pico.
"foto" é a miniatura (até 480 px) guardada no site ("fotos/abc123.jpg", na pasta ao lado da de saída: o workflow a envia ao R2),
"pagina" o artigo da Wikipédia (mais informações), "resumo" uma frase do artigo, "credito" o autor e a licença da foto e "pagina_foto"
a página da foto no Commons. Só entram fotos do Commons com licença livre (CC BY, CC BY-SA, CC0, domínio público): as de "uso justo"
de algumas Wikipédias ficam de fora.
Os dados são do OpenStreetMap (ODbL, © colaboradores) e as fotos e textos, da Wikipédia e do Wikimedia Commons (cada um com a sua licença, na página indicada).
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import osmium

import brasil

ESCALA = brasil.ESCALA
LIMITE_DE_CONSULTAS = int(os.environ.get("LIMITE_DE_CONSULTAS", "5000"))     # consultas novas à Wikipédia por rodada
AGENTE = "brotenatrilha.com.br (contato@brotenatrilha.com.br)"


def tipo_do_interesse(tags):
    """O tipo (1 a 8) do lugar, ou None se não interessa."""
    turismo, natural, historico, lazer = tags.get("tourism"), tags.get("natural"), tags.get("historic"), tags.get("leisure")
    tem_artigo = bool(tags.get("wikipedia") or tags.get("wikidata"))
    if turismo == "viewpoint":
        return 1
    if natural == "waterfall":
        return 2
    if natural == "beach":
        return 3
    if turismo in ("attraction", "museum", "zoo", "theme_park", "gallery"):
        return 4
    if historico in ("monument", "memorial", "ruins", "castle", "fort", "archaeological_site", "church", "manor") or (
            tags.get("amenity") == "place_of_worship" and (tags.get("heritage") or tem_artigo)):
        return 5
    if natural == "cave_entrance":
        return 6
    if lazer == "nature_reserve" or tags.get("boundary") == "national_park":
        return 7
    if natural == "peak" and tem_artigo:
        return 8
    return None


def pegar_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def foto_do_artigo(marca):
    """Foto, página e resumo de uma marca "pt:Título" (ou "en:Título") da Wikipédia; (None, None, None) se não achar."""
    if ":" not in marca:
        return None, None, None
    idioma, titulo = marca.split(":", 1)
    if len(idioma) > 3:
        return None, None, None
    try:
        d = pegar_json(f"https://{idioma}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(titulo.replace(' ', '_'), safe='')}")
    except Exception:
        return None, None, None
    foto = (d.get("thumbnail") or {}).get("source")
    pagina = (d.get("content_urls") or {}).get("desktop", {}).get("page")
    resumo = (d.get("extract") or "").strip()
    if len(resumo) > 220:
        resumo = resumo[:217].rsplit(" ", 1)[0] + "…"
    return foto, pagina, resumo


def arquivo_do_wikidata(codigo):
    """O nome do arquivo da foto (P18) de um item do Wikidata, no Commons; None se não houver."""
    try:
        d = pegar_json(f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={codigo}&property=P18&format=json")
        return d["claims"]["P18"][0]["mainsnak"]["datavalue"]["value"]
    except Exception:
        return None


def artigo_do_wikidata(codigo):
    """O endereço do artigo da Wikipédia (em português, ou em inglês) de um item do Wikidata; "" se não houver."""
    try:
        d = pegar_json(f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={codigo}&props=sitelinks/urls&sitefilter=ptwiki|enwiki&format=json")
        links = d["entities"][codigo]["sitelinks"]
        for site in ("ptwiki", "enwiki"):
            if site in links:
                return links[site]["url"]
    except Exception:
        pass
    return ""


def arquivo_do_commons(miniatura):
    """O nome do arquivo no Commons a partir do endereço da miniatura (upload.wikimedia.org/wikipedia/commons/...);
    None se a foto não é do Commons (as fotos guardadas só numa Wikipédia podem ser de uso justo)."""
    partes = urllib.parse.urlparse(miniatura).path.split("/")
    if len(partes) < 6 or partes[1] != "wikipedia" or partes[2] != "commons":
        return None
    if partes[3] == "thumb":
        return urllib.parse.unquote(partes[6]) if len(partes) > 6 else None
    return urllib.parse.unquote(partes[5])


def foto_do_commons(arquivo):
    """(miniatura de 480 px, crédito "Autor, licença", página da foto) de um arquivo do Commons; None se não achar.
    O Commons só aceita licenças livres (CC BY, CC BY-SA, CC0, "Attribution", domínio público...): basta guardar o crédito.
    As fotos que só existem numa Wikipédia (que podem ser de uso justo) nem chegam aqui: arquivo_do_commons() as descarta."""
    try:
        d = pegar_json("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=480&titles="
                       + urllib.parse.quote("File:" + arquivo))
        info = next(iter(d["query"]["pages"].values()))["imageinfo"][0]
    except Exception:
        return None
    meta = info.get("extmetadata", {})
    licenca = " ".join(re.sub(r"<[^>]+>", "", (meta.get("LicenseShortName") or {}).get("value", "")).split())[:40] or "licença no Commons"
    if str((meta.get("NonFree") or {}).get("value", "")).lower() == "true":
        return None
    autor = " ".join(re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "")).split())[:80] or "autor no Commons"
    return info.get("thumburl") or info.get("url"), f"{autor}, {licenca}", info.get("descriptionurl", "")


def baixar(url, destino):
    """Grava a miniatura em destino; False se não deu (ou se veio grande demais para uma miniatura)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(req, timeout=30) as r:
            dados = r.read(600001)
    except Exception:
        return False
    if not dados or len(dados) > 600000:
        return False
    with open(destino, "wb") as f:
        f.write(dados)
    return True


def consultar(artigo, codigo, pasta_fotos):
    """[foto, pagina, resumo, credito, pagina_foto] (o resumo sem a checagem do nome) de um ponto com marca da Wikipédia ou do Wikidata."""
    miniatura, pagina, resumo = foto_do_artigo(artigo) if artigo else (None, None, None)
    arquivo = arquivo_do_commons(miniatura) if miniatura else None
    if not arquivo and codigo:
        arquivo = arquivo_do_wikidata(codigo)
    if not pagina and codigo:
        pagina = artigo_do_wikidata(codigo)
    foto = credito = pagina_foto = ""
    if arquivo:
        achada = foto_do_commons(arquivo)
        if achada:
            extensao = os.path.splitext(urllib.parse.urlparse(achada[0]).path)[1].lower()
            nome = hashlib.sha1(arquivo.encode("utf-8")).hexdigest()[:16] + (extensao if extensao in (".jpg", ".jpeg", ".png", ".webp", ".gif") else ".jpg")
            if baixar(achada[0], os.path.join(pasta_fotos, nome)):
                foto, credito, pagina_foto = "fotos/" + nome, achada[1], achada[2]
    time.sleep(0.15)                              # sem pressa: os servidores da Wikipédia são comunitários
    return [foto, pagina or "", resumo or "", credito, pagina_foto]


def gerar(pbf, pasta, arquivo_cache=None):
    cache = {}
    if arquivo_cache and os.path.exists(arquivo_cache):
        cache = json.load(open(arquivo_cache, encoding="utf-8"))
    achados, consultas = {}, 0
    pasta_fotos = os.path.join(os.path.dirname(os.path.abspath(pasta)), "fotos")      # só as fotos novas: as antigas já estão no R2
    os.makedirs(pasta_fotos, exist_ok=True)
    leitor = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations().with_filter(
        osmium.filter.KeyFilter("tourism", "natural", "historic", "leisure", "amenity", "boundary"))
    for objeto in leitor:
        tags = {t.k: t.v for t in objeto.tags}
        tipo = tipo_do_interesse(tags)
        nome = (tags.get("name") or "").strip()
        if tipo is None or not nome:
            continue
        if objeto.is_node():
            if not objeto.location.valid():
                continue
            lat, lon = objeto.location.lat, objeto.location.lon
        else:
            try:
                locais = [(n.lat, n.lon) for n in objeto.nodes if n.location.valid()]
            except osmium.InvalidLocationError:
                continue
            if not locais:
                continue
            lat, lon = sum(p[0] for p in locais) / len(locais), sum(p[1] for p in locais) / len(locais)
        if brasil.dentro(lat, lon):
            achados[(round(lat * ESCALA), round(lon * ESCALA), tipo, nome[:50])] = (tags.get("wikipedia"), tags.get("wikidata"))
    lista, com_foto = [], 0
    for (lat, lon, tipo, nome), (artigo, codigo) in sorted(achados.items()):
        if lista and lista[-1][3].lower() == nome.lower() and abs(lista[-1][1] - lat) <= 150 and abs(lista[-1][2] - lon) <= 150:
            continue                                  # o mesmo lugar mapeado duas vezes (ponto e contorno): fica um só
        foto = pagina = resumo = credito = pagina_foto = ""
        if artigo or codigo:
            marca = f"{artigo or ''}|{codigo or ''}"
            if marca not in cache and consultas < LIMITE_DE_CONSULTAS:
                cache[marca] = consultar(artigo, codigo, pasta_fotos)
                consultas += 1
                if consultas % 500 == 0:
                    print(f"  {consultas} consultas à Wikipédia...", flush=True)
            foto, pagina, resumo, credito, pagina_foto = cache.get(marca, ["", "", "", "", ""])
            palavras = [w for w in nome.lower().replace(",", " ").split() if len(w) >= 5]
            if resumo and not any(w in resumo.lower()[:200] for w in palavras):
                resumo = ""                                # o artigo é de outra coisa (por exemplo, a diocese no lugar da catedral): fica só a foto
            com_foto += bool(foto)
        lista.append([tipo, lat, lon, nome, foto, pagina, resumo, credito, pagina_foto])
    por_quadrado = {}
    for item in lista:
        por_quadrado.setdefault(brasil.chave(item[1] / ESCALA, item[2] / ESCALA), []).append(item)
    brasil.gravar_quadrados(pasta, "p", por_quadrado, brasil.data_do_mapa(pbf))
    if arquivo_cache:
        with open(arquivo_cache, "w", encoding="utf-8", newline="\n") as f:
            json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  {consultas} consultas novas à Wikipédia (limite {LIMITE_DE_CONSULTAS}); {len(cache)} marcas no cache")
    por_tipo = {}
    for item in lista:
        por_tipo[item[0]] = por_tipo.get(item[0], 0) + 1
    print(f"{len(lista)} pontos de interesse ({com_foto} com foto) em {len(por_quadrado)} quadrados, em {pasta}: {dict(sorted(por_tipo.items()))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "interesses"),
          sys.argv[3] if len(sys.argv) > 3 else None)
