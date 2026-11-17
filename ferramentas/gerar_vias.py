"""Gera os arquivos de vias do Espírito Santo (ferramentas/vias/) para a ferramenta "Desenhar rota".

Para saber o terreno de uma rota (asfalto, terra, calçamento), a página precisa das vias do OpenStreetMap com o tipo de piso.
Em vez de perguntar a um serviço público (o Overpass, que vive ocupado), a página lê quadradinhos de 0,05 grau (uns 5 km)
guardados aqui no próprio site. Este script faz esses quadradinhos a partir de um arquivo .osm.pbf (por exemplo, o do Sudeste
em download.geofabrik.de/south-america/brazil/).

Uso:  python gerar_vias.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA]        (precisa do pacote "osmium": pip install osmium)

Cada quadradinho é um JSON: {"w": [[tipo, [lat0, lon0, dlat1, dlon1, ...]], ...]}, com as coordenadas em inteiros de 1e-5 grau
(a primeira em valor absoluto, as outras como diferença da anterior). Tipo: 1 asfalto, 2 terra, 3 calçamento, 0 sem informação.
O indice.json lista os quadradinhos que existem e a área que eles cobrem. Os dados são do OpenStreetMap (ODbL, © colaboradores do OpenStreetMap).
"""
import json
import math
import os
import sys

import osmium

from gerar_pedais import tipo_do_piso            # a mesma regra do site e do BNT Editor

TELA = 0.05                                      # lado do quadradinho, em graus
MARGEM = 0.0003                                  # o que cada quadradinho guarda além da borda (uns 33 m): a rota é comparada a 25 m das vias
ESCALA = 100000                                  # as coordenadas viram inteiros de 1e-5 grau (cerca de 1 m)
COBERTURA = {"sul": -21.35, "norte": -18.0, "oeste": -41.95, "leste": -39.55}    # a área em que os quadradinhos estão completos
FOLGA_DA_BUSCA = 0.1                             # lê um pouco além da cobertura, para as vias que cruzam a borda não ficarem cortadas
CODIGO = {"Asfalto": 1, "Terra": 2, "Calçamento": 3}
SEM_PISO_NAO_VIA = ("footway", "steps", "pedestrian", "corridor")      # com piso informado, estas não entram (a consulta do Overpass também as tirava)


def tipo_da_via(tags):
    """O tipo (1, 2, 3 ou 0) da via, ou None se a via não interessa para o terreno."""
    via, piso = tags.get("highway"), tags.get("surface")
    if not via:
        return None
    if piso:
        if via in SEM_PISO_NAO_VIA:
            return None
    elif via not in ("track", "path", "bridleway"):
        return None
    return CODIGO.get(tipo_do_piso(piso, via), 0)


def dentro(lat, lon):
    return (COBERTURA["sul"] - FOLGA_DA_BUSCA <= lat <= COBERTURA["norte"] + FOLGA_DA_BUSCA
            and COBERTURA["oeste"] - FOLGA_DA_BUSCA <= lon <= COBERTURA["leste"] + FOLGA_DA_BUSCA)


def telas_do_segmento(a, b):
    """As telas (linha, coluna) que o segmento a-b toca, contando a margem."""
    l0, l1 = sorted((a[0], b[0]))
    c0, c1 = sorted((a[1], b[1]))
    return [(i, j) for i in range(math.floor((l0 - MARGEM) / TELA), math.floor((l1 + MARGEM) / TELA) + 1)
            for j in range(math.floor((c0 - MARGEM) / TELA), math.floor((c1 + MARGEM) / TELA) + 1)]


def inteiros(ponto):
    return round(ponto[0] * ESCALA), round(ponto[1] * ESCALA)


def juntar(telas, tipo, pontos):
    """Põe os segmentos de uma via nas telas que eles tocam, juntando os seguidos numa linha só."""
    abertas = {}                                  # tela -> última linha aberta dela (lista de pontos)
    for a, b in zip(pontos, pontos[1:]):
        for chave in telas_do_segmento(a, b):
            linha = abertas.get(chave)
            if linha is not None and linha[-1] == a:
                linha.append(b)
            else:
                linha = [a, b]
                abertas[chave] = linha
                telas.setdefault(chave, []).append((tipo, linha))


def codificar(linha):
    """[lat0, lon0, dlat, dlon, ...] em inteiros de 1e-5 grau."""
    saida, anterior = [], (0, 0)
    for ponto in linha:
        atual = inteiros(ponto)
        saida += [atual[0] - anterior[0], atual[1] - anterior[1]]
        anterior = atual
    return saida


def gerar(pbf, pasta):
    telas, vias = {}, 0
    leitor = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations().with_filter(osmium.filter.KeyFilter("highway"))
    for via in leitor:                            # os pontos só são lidos para a posição das vias; quem passa pelo filtro e é via segue
        if not via.is_way():
            continue
        tipo = tipo_da_via(via.tags)
        if tipo is None:
            continue
        try:
            pontos = [(n.lat, n.lon) for n in via.nodes if n.location.valid()]
        except osmium.InvalidLocationError:
            continue
        if len(pontos) < 2 or not any(dentro(*p) for p in pontos):
            continue
        juntar(telas, tipo, pontos)
        vias += 1
        if vias % 200000 == 0:
            print(f"  {vias} vias lidas...", flush=True)
    os.makedirs(pasta, exist_ok=True)
    for antigo in os.listdir(pasta):              # quadradinhos de uma rodada anterior que já não existem
        if antigo.endswith(".json"):
            os.remove(os.path.join(pasta, antigo))
    for (linha, coluna), lista in sorted(telas.items()):
        corpo = {"w": [[tipo, codificar(pontos)] for tipo, pontos in lista]}
        with open(os.path.join(pasta, f"{linha}_{coluna}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(corpo, f, separators=(",", ":"))
    indice = {"tela": TELA, "escala": ESCALA, "cobertura": COBERTURA, "telas": [f"{l}_{c}" for l, c in sorted(telas)]}
    with open(os.path.join(pasta, "indice.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(indice, f, separators=(",", ":"))
    print(f"{vias} vias em {len(telas)} quadradinhos, em {pasta}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "vias"))
