"""Conta os itens dos arquivos por quadrado (ver brasil.py) e falha se forem menos que o mínimo: um mapa quebrado não pode
apagar os dados publicados. Uso:  python contar_quadrados.py PASTA CAMPO MINIMO      (CAMPO: "p" para pontos, "c" para ciclovias)
"""
import json
import os
import sys

pasta, campo, minimo = sys.argv[1], sys.argv[2], int(sys.argv[3])
total = sum(len(json.load(open(os.path.join(pasta, nome), encoding="utf-8"))[campo])
            for nome in os.listdir(pasta) if nome.endswith(".json") and nome != "info.json")
print(f"{pasta}: {total} itens")
if total < minimo:
    print(f"::error::Só {total} itens em {pasta} (o mínimo é {minimo}): algo deu errado, nada foi enviado.")
    sys.exit(1)
