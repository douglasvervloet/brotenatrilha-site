"""Gera o arquivo de pontos de interesse do Espírito Santo (ferramentas/interesses/interesses.json) para a ferramenta "Desenhar rota".

Os pontos (mirantes, cachoeiras, praias, atrações e museus, locais históricos, cavernas, parques e reservas, e os picos que têm artigo na Wikipédia)
vêm de um arquivo .osm.pbf do OpenStreetMap (o mesmo do gerar_vias.py). A foto e o resumo, quando existem, vêm da Wikipédia ou do Wikidata, pelas
marcas "wikipedia" e "wikidata" do próprio ponto: o OpenStreetMap quase não guarda foto. Só entram pontos com nome.

Uso:  python gerar_interesses.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA]        (precisa do pacote "osmium": pip install osmium)

O arquivo é {"cobertura": {...}, "escala": 100000, "p": [[tipo, lat, lon, nome, foto, pagina, resumo], ...]}, com lat e lon em inteiros de 1e-5 grau.
Tipo: 1 mirante, 2 cachoeira, 3 praia, 4 atração ou museu, 5 histórico ou igreja notável, 6 caverna, 7 parque ou reserva, 8 pico.
"foto" é o endereço de uma miniatura, "pagina" o artigo (ou a página da foto no Commons, onde estão o autor e a licença) e "resumo" uma frase do artigo.
Os dados são do OpenStreetMap (ODbL, © colaboradores) e as fotos e textos, da Wikipédia e do Wikimedia Commons (cada um com a sua licença, na página indicada).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import osmium

ESCALA = 100000
COBERTURA = {"sul": -21.35, "norte": -18.0, "oeste": -41.95, "leste": -39.55}      # a mesma área das vias e dos apoios
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


def dentro(lat, lon):
    return COBERTURA["sul"] <= lat <= COBERTURA["norte"] and COBERTURA["oeste"] <= lon <= COBERTURA["leste"]


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


def foto_do_wikidata(codigo):
    """Foto (P18) de um item do Wikidata: a miniatura do Commons e a página da foto, onde estão o autor e a licença."""
    try:
        d = pegar_json(f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={codigo}&property=P18&format=json")
        arquivo = d["claims"]["P18"][0]["mainsnak"]["datavalue"]["value"]
    except Exception:
        return None, None
    nome = urllib.parse.quote(arquivo.replace(" ", "_"))
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{nome}?width=480", f"https://commons.wikimedia.org/wiki/File:{nome}"


def gerar(pbf, pasta):
    achados = {}
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
        if dentro(lat, lon):
            achados[(round(lat * ESCALA), round(lon * ESCALA), tipo, nome[:50])] = (tags.get("wikipedia"), tags.get("wikidata"))
    lista, com_foto = [], 0
    for (lat, lon, tipo, nome), (artigo, codigo) in sorted(achados.items()):
        if lista and lista[-1][3].lower() == nome.lower() and abs(lista[-1][1] - lat) <= 150 and abs(lista[-1][2] - lon) <= 150:
            continue                                  # o mesmo lugar mapeado duas vezes (ponto e contorno): fica um só
        foto = pagina = resumo = ""
        if artigo or codigo:
            f, p, r = foto_do_artigo(artigo) if artigo else (None, None, None)
            if not f and codigo:
                f, p2 = foto_do_wikidata(codigo)
                p = p or p2
            foto, pagina, resumo = f or "", p or "", r or ""
            palavras = [w for w in nome.lower().replace(",", " ").split() if len(w) >= 5]
            if resumo and not any(w in resumo.lower()[:200] for w in palavras):
                resumo = ""                                # o artigo é de outra coisa (por exemplo, a diocese no lugar da catedral): fica só a foto
            com_foto += bool(foto)
            time.sleep(0.15)                          # sem pressa: os servidores da Wikipédia são comunitários
        lista.append([tipo, lat, lon, nome, foto, pagina, resumo])
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "interesses.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"cobertura": COBERTURA, "escala": ESCALA, "p": lista}, f, ensure_ascii=False, separators=(",", ":"))
    por_tipo = {}
    for item in lista:
        por_tipo[item[0]] = por_tipo.get(item[0], 0) + 1
    print(f"{len(lista)} pontos de interesse ({com_foto} com foto) em {pasta}: {dict(sorted(por_tipo.items()))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "interesses"))
