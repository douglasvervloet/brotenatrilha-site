"""Gera os avisos na rota do Brasil para a ferramenta "Planejar pedal" (dados.brotenatrilha.com.br/br/avisos/, no R2 da Cloudflare):
o que obriga quem pedala a parar ou mudar o plano no caminho.

Tipo: 1 porteira ou cancela (barrier=gate, lift_gate, swing_gate, kissing_gate, stile), 2 vau (ford=yes ou stepping_stones:
atravessar o rio por dentro), 3 balsa (route=ferry: entra o embarque e o desembarque), 4 escada (highway=steps: carregar a bike).
Os dados vêm de um arquivo .osm.pbf do OpenStreetMap (o mesmo do gerar_vias.py).

Uso:  python gerar_avisos.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA]        (precisa do pacote "osmium": pip install osmium)

Um arquivo por quadrado de 1 grau (ver brasil.py): {"escala": 100000, "p": [[tipo, lat, lon, nome], ...]}, com lat e lon em
inteiros de 1e-5 grau. Uma via (escada, vau ou balsa) entra pelos seus pontos, para a página achar o aviso onde quer que a rota a cruze.
Os dados são do OpenStreetMap (ODbL, © colaboradores do OpenStreetMap).
"""
import os
import sys

import osmium

import brasil

ESCALA = brasil.ESCALA
PORTEIRAS = ("gate", "lift_gate", "swing_gate", "kissing_gate", "stile")
VAUS = ("yes", "stepping_stones")


def tipo_do_aviso(tags, eh_via):
    """O tipo (1 a 4) do aviso, ou None se não interessa."""
    if tags.get("barrier") in PORTEIRAS and tags.get("access") != "no":
        return 1
    if tags.get("ford") in VAUS:
        return 2
    if eh_via and tags.get("route") == "ferry":
        return 3
    if eh_via and tags.get("highway") == "steps":
        return 4
    return None


def gerar(pbf, pasta):
    pontos = set()
    leitor = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations().with_filter(
        osmium.filter.KeyFilter("barrier", "ford", "route", "highway"))
    for objeto in leitor:
        eh_via = objeto.is_way()
        tipo = tipo_do_aviso(objeto.tags, eh_via)
        if tipo is None:
            continue
        nome = (objeto.tags.get("name") or "").strip()[:40]
        if not eh_via:
            if objeto.location.valid():
                locais = [(objeto.location.lat, objeto.location.lon)]
            else:
                continue
        else:
            try:
                locais = [(n.lat, n.lon) for n in objeto.nodes if n.location.valid()]
            except osmium.InvalidLocationError:
                continue
            if tipo == 3:
                locais = locais[:1] + locais[-1:]                # a balsa: o embarque e o desembarque
        for lat, lon in locais:
            if brasil.dentro(lat, lon):
                pontos.add((round(lat * ESCALA), round(lon * ESCALA), tipo, nome))
    lista = []
    for lat, lon, tipo, nome in sorted(pontos):
        if any(p[0] == tipo and abs(p[1] - lat) <= 10 and abs(p[2] - lon) <= 10 for p in lista[-20:]):
            continue                                            # pontos colados do mesmo aviso (os degraus de uma escada): fica um
        lista.append([tipo, lat, lon, nome])
    por_quadrado = {}
    for item in lista:
        por_quadrado.setdefault(brasil.chave(item[1] / ESCALA, item[2] / ESCALA), []).append(item)
    brasil.gravar_quadrados(pasta, "p", por_quadrado, brasil.data_do_mapa(pbf))
    por_tipo = {}
    for item in lista:
        por_tipo[item[0]] = por_tipo.get(item[0], 0) + 1
    print(f"{len(lista)} avisos em {len(por_quadrado)} quadrados, em {pasta}: {dict(sorted(por_tipo.items()))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "avisos"))
