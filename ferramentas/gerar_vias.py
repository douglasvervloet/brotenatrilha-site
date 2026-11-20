"""Gera os arquivos de vias do Brasil para a ferramenta "Planejar pedal" (o terreno da rota e a camada "Piso das ruas").

Para saber o terreno de uma rota (asfalto, terra, calçamento), a página precisa das vias do OpenStreetMap com o tipo de piso.
Em vez de perguntar a um serviço público (o Overpass, que vive ocupado), a página lê quadradinhos de 0,05 grau (uns 5 km)
guardados no R2 da Cloudflare (dados.brotenatrilha.com.br/br/vias/). Este script faz esses quadradinhos a partir de um arquivo
.osm.pbf (o do Brasil, em download.geofabrik.de/south-america/brazil-latest.osm.pbf).

Uso:  python gerar_vias.py ARQUIVO.osm.pbf [PASTA_DE_SAIDA]        (precisa do pacote "osmium": pip install osmium)

Cada quadradinho é um JSON: {"w": [[tipo, [lat0, lon0, dlat1, dlon1, ...]], ...]}, com as coordenadas em inteiros de 1e-5 grau
(a primeira em valor absoluto, as outras como diferença da anterior). Tipo: 1 asfalto, 2 terra, 3 calçamento, 0 sem informação.
Quadradinho sem vias não tem arquivo (a página trata o 404 como vazio). O indice.json traz o tamanho, a escala e a área coberta.
Os dados são do OpenStreetMap (ODbL, © colaboradores do OpenStreetMap).

O Brasil inteiro não cabe na memória de uma vez: a leitura do mapa grava cada via num arquivo temporário por faixa de latitude
(FAIXA graus), e cada faixa é montada e gravada separadamente.
"""
import json
import math
import os
import shutil
import struct
import sys
import tempfile
from array import array

import osmium

import brasil
from gerar_pedais import tipo_do_piso            # a mesma regra do site e do BNT Editor

TELA = 0.05                                      # lado do quadradinho, em graus
MARGEM = 0.0003                                  # o que cada quadradinho guarda além da borda (uns 33 m): a rota é comparada a 25 m das vias
ESCALA = brasil.ESCALA
FOLGA_DA_BUSCA = 0.1                             # lê um pouco além da cobertura, para as vias que cruzam a borda não ficarem cortadas
FAIXA = 2.0                                      # graus de latitude montados de cada vez
CODIGO = {"Asfalto": 1, "Terra": 2, "Calçamento": 3}
SEM_PISO_NAO_VIA = ("footway", "steps", "pedestrian", "corridor")      # com piso informado, estas não entram (a consulta do Overpass também as tirava)
CABECALHO = struct.Struct("<bI")                 # no arquivo temporário: tipo e número de pontos de cada via, seguidos das coordenadas (int32)


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


def telas_do_segmento(a, b):
    """As telas (linha, coluna) que o segmento a-b toca, contando a margem."""
    l0, l1 = sorted((a[0], b[0]))
    c0, c1 = sorted((a[1], b[1]))
    return [(i, j) for i in range(math.floor((l0 - MARGEM) / TELA), math.floor((l1 + MARGEM) / TELA) + 1)
            for j in range(math.floor((c0 - MARGEM) / TELA), math.floor((c1 + MARGEM) / TELA) + 1)]


def faixa_da_linha(i):
    """A faixa de latitude da linha i de quadradinhos (pelo meio dela, para não depender do arredondamento da borda)."""
    return math.floor((i + 0.5) * TELA / FAIXA)


def juntar(telas, tipo, pontos, inteiros, faixa):
    """Põe os segmentos de uma via nas telas da faixa que eles tocam, juntando os seguidos numa linha só.
    A posição em graus (pontos) escolhe as telas; o que se guarda são os mesmos pontos em inteiros de 1e-5 grau."""
    abertas = {}                                  # tela -> última linha aberta dela (lista de pontos em inteiros)
    for k in range(len(pontos) - 1):
        a, b, ia, ib = pontos[k], pontos[k + 1], inteiros[k], inteiros[k + 1]
        for chave in telas_do_segmento(a, b):
            if faixa_da_linha(chave[0]) != faixa:
                continue
            linha = abertas.get(chave)
            if linha is not None and linha[-1] == ia:
                linha.append(ib)
            else:
                linha = [ia, ib]
                abertas[chave] = linha
                telas.setdefault(chave, []).append((tipo, linha))


def codificar(linha):
    """[lat0, lon0, dlat, dlon, ...] em inteiros de 1e-5 grau (os pontos já vêm em inteiros)."""
    saida, anterior = [], (0, 0)
    for atual in linha:
        saida += [atual[0] - anterior[0], atual[1] - anterior[1]]
        anterior = atual
    return saida


def separar_por_faixa(pbf, temporaria):
    """Lê o mapa uma vez e grava cada via que interessa no arquivo de cada faixa de latitude que ela toca."""
    arquivos, vias = {}, 0
    leitor = osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY).with_locations().with_filter(osmium.filter.KeyFilter("highway"))
    for via in leitor:                            # os pontos só são lidos para a posição das vias; quem passa pelo filtro e é via segue
        if not via.is_way():
            continue
        tipo = tipo_da_via(via.tags)
        if tipo is None:
            continue
        try:
            pontos = [(round(n.lat * ESCALA), round(n.lon * ESCALA)) for n in via.nodes if n.location.valid()]
        except osmium.InvalidLocationError:
            continue
        if len(pontos) < 2 or not any(brasil.dentro(p[0] / ESCALA, p[1] / ESCALA, FOLGA_DA_BUSCA) for p in pontos):
            continue
        lats = [p[0] / ESCALA for p in pontos]
        registro = CABECALHO.pack(tipo, len(pontos)) + array("i", [v for p in pontos for v in p]).tobytes()
        for faixa in range(math.floor((min(lats) - MARGEM) / FAIXA), math.floor((max(lats) + MARGEM) / FAIXA) + 1):
            if faixa not in arquivos:
                arquivos[faixa] = open(os.path.join(temporaria, f"faixa_{faixa}.bin"), "wb")
            arquivos[faixa].write(registro)
        vias += 1
        if vias % 500000 == 0:
            print(f"  {vias} vias lidas...", flush=True)
    for f in arquivos.values():
        f.close()
    return sorted(arquivos), vias


def ler_faixa(caminho):
    """As vias (tipo, [(lat, lon), ...] em inteiros) de um arquivo temporário."""
    with open(caminho, "rb") as f:
        while True:
            cabecalho = f.read(CABECALHO.size)
            if not cabecalho:
                return
            tipo, n = CABECALHO.unpack(cabecalho)
            coords = array("i")
            coords.frombytes(f.read(8 * n))
            yield tipo, list(zip(coords[0::2], coords[1::2]))


def gerar(pbf, pasta):
    os.makedirs(pasta, exist_ok=True)
    for antigo in os.listdir(pasta):              # quadradinhos de uma rodada anterior
        if antigo.endswith(".json"):
            os.remove(os.path.join(pasta, antigo))
    temporaria = tempfile.mkdtemp(prefix="vias_", dir=os.path.dirname(os.path.abspath(pasta)))
    try:
        faixas, vias = separar_por_faixa(pbf, temporaria)
        total = 0
        for faixa in faixas:
            telas = {}
            for tipo, inteiros in ler_faixa(os.path.join(temporaria, f"faixa_{faixa}.bin")):
                pontos = [(lat / ESCALA, lon / ESCALA) for lat, lon in inteiros]
                juntar(telas, tipo, pontos, inteiros, faixa)
            for (linha, coluna), lista in telas.items():
                corpo = {"w": [[tipo, codificar(pts)] for tipo, pts in lista]}
                with open(os.path.join(pasta, f"{linha}_{coluna}.json"), "w", encoding="utf-8", newline="\n") as f:
                    json.dump(corpo, f, separators=(",", ":"))
            total += len(telas)
            print(f"  faixa {faixa * FAIXA:+.0f}°: {len(telas)} quadradinhos", flush=True)
            os.remove(os.path.join(temporaria, f"faixa_{faixa}.bin"))
    finally:
        shutil.rmtree(temporaria, ignore_errors=True)
    indice = {"tela": TELA, "escala": ESCALA, "cobertura": brasil.COBERTURA, "data": brasil.data_do_mapa(pbf)}
    with open(os.path.join(pasta, "indice.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(indice, f, separators=(",", ":"))
    print(f"{vias} vias em {total} quadradinhos, em {pasta}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "vias"))
