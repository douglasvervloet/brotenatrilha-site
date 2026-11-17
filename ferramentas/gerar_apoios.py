"""Gera o arquivo de pontos de apoio do Espírito Santo (ferramentas/apoios/apoios.json) para a ferramenta "Desenhar rota".

Os pontos (água, mercado e padaria, posto, lanchonete e restaurante, loja ou reparo de bike, banheiro) vêm de um arquivo .osm.pbf do
OpenStreetMap (o mesmo do gerar_vias.py). Lugares mapeados como prédio entram pelo centro do contorno.

Uso:  python gerar_apoios.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA]        (precisa do pacote "osmium": pip install osmium)

O arquivo é {"cobertura": {...}, "escala": 100000, "p": [[tipo, lat, lon, nome], ...]}, com lat e lon em inteiros de 1e-5 grau.
Tipo: 1 água, 2 mercado ou padaria, 3 posto, 4 lanchonete ou restaurante, 5 bike, 6 banheiro.
Os dados são do OpenStreetMap (ODbL, © colaboradores do OpenStreetMap).
"""
import json
import os
import sys

import osmium

ESCALA = 100000
COBERTURA = {"sul": -21.35, "norte": -18.0, "oeste": -41.95, "leste": -39.55}      # a mesma área das vias


def tipo_do_lugar(tags):
    """O tipo (1 a 6) do lugar, ou None se não interessa."""
    amenidade, loja = tags.get("amenity"), tags.get("shop")
    if amenidade in ("drinking_water", "water_point") or (tags.get("man_made") == "water_tap" and tags.get("drinking_water") != "no"):
        return 1
    if loja in ("supermarket", "convenience", "bakery", "general", "kiosk", "greengrocer") or amenidade == "marketplace":
        return 2
    if amenidade == "fuel":
        return 3
    if amenidade in ("cafe", "fast_food", "restaurant", "ice_cream"):
        return 4
    if loja == "bicycle" or amenidade == "bicycle_repair_station":
        return 5
    if amenidade == "toilets":
        return 6
    return None


def dentro(lat, lon):
    return COBERTURA["sul"] <= lat <= COBERTURA["norte"] and COBERTURA["oeste"] <= lon <= COBERTURA["leste"]


def gerar(pbf, pasta):
    pontos = set()
    leitor = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations().with_filter(osmium.filter.KeyFilter("amenity", "shop", "man_made"))
    for objeto in leitor:
        tipo = tipo_do_lugar(objeto.tags)
        if tipo is None:
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
        if not dentro(lat, lon):
            continue
        nome = (objeto.tags.get("name") or objeto.tags.get("brand") or "").strip()[:40]
        pontos.add((round(lat * ESCALA), round(lon * ESCALA), tipo, nome))
    lista = [[tipo, lat, lon, nome] for lat, lon, tipo, nome in sorted(pontos)]
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "apoios.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"cobertura": COBERTURA, "escala": ESCALA, "p": lista}, f, ensure_ascii=False, separators=(",", ":"))
    por_tipo = {}
    for tipo, *_ in lista:
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
    print(f"{len(lista)} pontos de apoio em {pasta}: {dict(sorted(por_tipo.items()))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "apoios"))
