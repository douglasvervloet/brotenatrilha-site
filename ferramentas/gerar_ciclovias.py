"""Gera o arquivo das ciclovias do Espírito Santo (ferramentas/ciclovias/ciclovias.json) para a camada "Ciclovias" do Planejar pedal.

As ciclovias vêm de um arquivo .osm.pbf do OpenStreetMap (o mesmo do gerar_vias.py). Entram:
- tipo 1, ciclovia (pista separada): vias highway=cycleway, caminhos com bicicleta designada (bicycle=designated) e ruas com cycleway=track
  (ciclovia ao lado da rua; é desenhada a linha da própria rua);
- tipo 2, ciclofaixa (faixa pintada na rua): ruas com cycleway=lane (também cycleway:left, :right e :both).
Ficam de fora o que está em obra ou proposto e o que é privado ou proibido para bicicleta.

Uso:  python gerar_ciclovias.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA]        (precisa do pacote "osmium": pip install osmium)

O arquivo é {"cobertura": {...}, "escala": 100000, "c": [[tipo, [lat0, lon0, dlat1, dlon1, ...]], ...]}, com as coordenadas em inteiros de 1e-5 grau
(a primeira em valor absoluto, as outras como diferença da anterior); as linhas já saem simplificadas (até uns 2 m de diferença).
Os dados são do OpenStreetMap (ODbL, © colaboradores do OpenStreetMap).
"""
import json
import math
import os
import sys

import osmium

ESCALA = 100000
COBERTURA = {"sul": -21.35, "norte": -18.0, "oeste": -41.95, "leste": -39.55}      # a mesma área das vias, dos apoios e dos pontos de interesse
TOLERANCIA = 2                                                                      # em unidades de 1e-5 grau: uns 2 m
LADOS = ("cycleway", "cycleway:both", "cycleway:left", "cycleway:right")


def tipo_da_ciclovia(tags):
    """1 (ciclovia), 2 (ciclofaixa) ou None se a via não é ciclovia."""
    via = tags.get("highway")
    if not via or tags.get("access") in ("private", "no") and tags.get("bicycle") not in ("yes", "designated"):
        return None
    if tags.get("bicycle") == "no" and via != "cycleway":
        return None
    if via == "cycleway":
        return None if tags.get("bicycle") == "no" else 1
    if via in ("path", "footway", "pedestrian", "track") and tags.get("bicycle") == "designated":
        return 1
    if via in ("construction", "proposed", "motorway", "motorway_link", "trunk", "trunk_link"):
        return None
    valores = {tags.get(k) for k in LADOS if tags.get(k)}
    if valores & {"track", "opposite_track"}:
        return 1
    if valores & {"lane", "opposite_lane"}:
        return 2
    return None


def distancia_ao_segmento(p, a, b):
    ax, ay, bx, by, px, py = a[0], a[1], b[0], b[1], p[0], p[1]
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplificar(pontos, tolerancia):
    """Douglas-Peucker: tira os pontos que ficam a menos de `tolerancia` da linha."""
    if len(pontos) < 3:
        return pontos
    maior, indice = 0, 0
    for i in range(1, len(pontos) - 1):
        d = distancia_ao_segmento(pontos[i], pontos[0], pontos[-1])
        if d > maior:
            maior, indice = d, i
    if maior <= tolerancia:
        return [pontos[0], pontos[-1]]
    return simplificar(pontos[:indice + 1], tolerancia)[:-1] + simplificar(pontos[indice:], tolerancia)


def dentro(lat, lon):
    return COBERTURA["sul"] - 0.1 <= lat <= COBERTURA["norte"] + 0.1 and COBERTURA["oeste"] - 0.1 <= lon <= COBERTURA["leste"] + 0.1


def gerar(pbf, pasta):
    linhas = []
    leitor = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations().with_filter(osmium.filter.KeyFilter("highway"))
    for via in leitor:
        if not via.is_way():
            continue
        tags = {t.k: t.v for t in via.tags}
        tipo = tipo_da_ciclovia(tags)
        if tipo is None:
            continue
        try:
            pontos = [(round(n.lat * ESCALA), round(n.lon * ESCALA)) for n in via.nodes if n.location.valid()]
        except osmium.InvalidLocationError:
            continue
        if len(pontos) < 2 or not dentro(pontos[0][0] / ESCALA, pontos[0][1] / ESCALA):
            continue
        pontos = simplificar(pontos, TOLERANCIA)
        plano = [pontos[0][0], pontos[0][1]]
        for (a, b), (c, d) in zip(pontos, pontos[1:]):
            plano += [c - a, d - b]
        linhas.append([tipo, plano])
    linhas.sort(key=lambda x: (x[0], x[1][0], x[1][1]))
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "ciclovias.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"cobertura": COBERTURA, "escala": ESCALA, "c": linhas}, f, separators=(",", ":"))
    por_tipo = {1: 0, 2: 0}
    for t, _ in linhas:
        por_tipo[t] += 1
    print(f"{len(linhas)} trechos de ciclovia em {pasta}: {por_tipo[1]} ciclovias e {por_tipo[2]} ciclofaixas")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "ciclovias"))
