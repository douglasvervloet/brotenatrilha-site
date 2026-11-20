"""O que os geradores de dados do "Planejar pedal" têm em comum: a área do Brasil e os quadrados de 1 grau.

Os pontos de apoio, os pontos de interesse e as ciclovias são gravados num arquivo por quadrado de 1 grau ("-21_-41.json" é o
quadrado de -21 a -20 de latitude e de -41 a -40 de longitude), para a página só baixar os quadrados da rota ou da tela.
Quadrado sem nada não tem arquivo (a página trata o 404 como vazio). Cada pasta tem um info.json com o tamanho e a área.
"""
import json
import math
import os

COBERTURA = {"sul": -34.0, "norte": 5.4, "oeste": -74.1, "leste": -28.8}      # o Brasil, com as ilhas (Fernando de Noronha, Trindade)
QUADRADO = 1                                                                    # lado, em graus, dos arquivos de pontos e de ciclovias
ESCALA = 100000                                                                 # as coordenadas viram inteiros de 1e-5 grau (cerca de 1 m)


def dentro(lat, lon, folga=0.0):
    return (COBERTURA["sul"] - folga <= lat <= COBERTURA["norte"] + folga
            and COBERTURA["oeste"] - folga <= lon <= COBERTURA["leste"] + folga)


def chave(lat, lon):
    """O nome do quadrado de um ponto (em graus)."""
    return f"{math.floor(lat / QUADRADO)}_{math.floor(lon / QUADRADO)}"


def data_do_mapa(pbf):
    """A data (AAAA-MM-DD) da cópia do OpenStreetMap no arquivo .osm.pbf, pelo cabeçalho; "" se ele não disser."""
    try:
        import osmium
        cabecalho = osmium.io.Reader(pbf, osmium.osm.osm_entity_bits.NOTHING).header()
        return (cabecalho.get("osmosis_replication_timestamp") or cabecalho.get("timestamp") or "")[:10]
    except Exception:
        return ""


def gravar_quadrados(pasta, campo, por_chave, data=""):
    """Um arquivo {"escala": ..., campo: [...]} por quadrado, mais o info.json (com a data do mapa);
    apaga os arquivos de uma rodada anterior."""
    os.makedirs(pasta, exist_ok=True)
    for antigo in os.listdir(pasta):
        if antigo.endswith(".json"):
            os.remove(os.path.join(pasta, antigo))
    for k, itens in por_chave.items():
        with open(os.path.join(pasta, f"{k}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"escala": ESCALA, campo: itens}, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(pasta, "info.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"quadrado": QUADRADO, "escala": ESCALA, "cobertura": COBERTURA, "data": data}, f, separators=(",", ":"))
