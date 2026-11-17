"""Gera o arquivo de pontos de apoio do Espírito Santo (ferramentas/apoios/apoios.json) para a ferramenta "Planejar pedal".

Os pontos (água, mercado e padaria, posto, lanchonete e restaurante, loja ou reparo de bike, banheiro) vêm de um arquivo .osm.pbf do
OpenStreetMap (o mesmo do gerar_vias.py). Lugares mapeados como prédio entram pelo centro do contorno.

Uso:  python gerar_apoios.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA]        (precisa do pacote "osmium": pip install osmium)

O arquivo é {"cobertura": {...}, "escala": 100000, "p": [[tipo, lat, lon, nome], ...]}, com lat e lon em inteiros de 1e-5 grau.
Tipo: 1 água, 2 mercado ou padaria, 3 posto, 4 lanchonete ou restaurante, 5 bike, 6 banheiro.
Os dados são do OpenStreetMap (ODbL, © colaboradores do OpenStreetMap).

Lugares que o OpenStreetMap não tem entram à mão em apoios_manuais.json (ao lado deste script), e o robô mensal não os apaga:
[{"nome": "Padaria Exemplo", "tipo": "mercado", "lat": -20.31, "lon": -40.43}]. O tipo é agua, mercado, posto, lanchonete, bike ou banheiro.
"""
import json
import os
import re
import sys

import osmium

ESCALA = 100000
TIPOS_MANUAIS = {"agua": 1, "mercado": 2, "posto": 3, "lanchonete": 4, "bike": 5, "banheiro": 6}
COBERTURA = {"sul": -21.35, "norte": -18.0, "oeste": -41.95, "leste": -39.55}      # a mesma área das vias


PADARIA = re.compile(r"padaria|panificadora|padoca|confeitaria|\bp[ãa]es\b", re.I)


def tipo_do_lugar(tags):
    """O tipo (1 a 6) do lugar, ou None se não interessa."""
    amenidade, loja = tags.get("amenity"), tags.get("shop")
    if amenidade != "fuel" and (loja == "bakery" or "bakery" in (tags.get("cuisine") or "") or PADARIA.search(tags.get("name") or "")):
        return 2          # padaria: no mapa vem como shop=bakery, mas muitas estão como café ou lanchonete (com "padaria" no nome ou na cozinha)
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
    manuais = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apoios_manuais.json")
    if os.path.exists(manuais):
        for item in json.load(open(manuais, encoding="utf-8")):
            if item["tipo"] not in TIPOS_MANUAIS or not dentro(item["lat"], item["lon"]):
                sys.exit(f"apoios_manuais.json: item inválido ou fora do Espírito Santo: {item}")
            pontos.add((round(item["lat"] * ESCALA), round(item["lon"] * ESCALA), TIPOS_MANUAIS[item["tipo"]], item["nome"].strip()[:40]))
    lista = []
    for lat, lon, tipo, nome in sorted(pontos):
        if nome and any(p[3].lower() == nome.lower() and abs(p[1] - lat) <= 60 and abs(p[2] - lon) <= 60 for p in lista[-40:]):
            continue          # o mesmo lugar mapeado duas vezes (por exemplo, como loja e como café): fica um só
        lista.append([tipo, lat, lon, nome])
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
