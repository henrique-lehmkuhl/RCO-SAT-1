#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lê a UCS Satellite Database (.xlsx) e grava `cache/ucs_bruto.json`.

Fonte: Union of Concerned Scientists, edição de 2023-05-01 — 7.560 satélites
em órbita na data de corte, com propósito, órbita, massa, potência, vida
esperada, contratante, lançamento e fontes declarados pela própria base.

A planilha tem 68 colunas: 0–27 são os dados, 28 é um transbordo do campo
Comments (5 linhas), 29–36 são as fontes e 37–67 são um bloco residual com a
palavra "Estimated" repetida, que a própria UCS deixou na planilha e não
corresponde a nenhum cabeçalho — descartado aqui.
"""
import json
import os
import sys
import datetime

import openpyxl

AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "cache")
PADRAO = r"D:\Downloads\UCS-Satellite-Database 5-1-2023.xlsx"

# coluna da planilha -> nome da coluna nos CSVs
COLUNAS = [
    ("Name of Satellite, Alternate Names", "nome"),
    ("Current Official Name of Satellite", "nome_oficial"),
    ("Country/Org of UN Registry", "registro_un"),
    ("Country of Operator/Owner", "pais_operador"),
    ("Operator/Owner", "operador"),
    ("Users", "usuarios"),
    ("Purpose", "proposito"),
    ("Detailed Purpose", "proposito_detalhado"),
    ("Class of Orbit", "classe_orbita"),
    ("Type of Orbit", "tipo_orbita"),
    ("Longitude of GEO (degrees)", "longitude_geo"),
    ("Perigee (km)", "perigeu_km"),
    ("Apogee (km)", "apogeu_km"),
    ("Eccentricity", "excentricidade"),
    ("Inclination (degrees)", "inclinacao_graus"),
    ("Period (minutes)", "periodo_min"),
    ("Launch Mass (kg.)", "massa_lancamento_kg"),
    ("Dry Mass (kg.)", "massa_seca_kg"),
    ("Power (watts)", "potencia_w"),
    ("Date of Launch", "data_lancamento"),
    ("Expected Lifetime (yrs.)", "vida_esperada_anos"),
    ("Contractor", "contratante"),
    ("Country of Contractor", "pais_contratante"),
    ("Launch Site", "local_lancamento"),
    ("Launch Vehicle", "veiculo_lancador"),
    ("COSPAR Number", "cospar"),
    ("NORAD Number", "norad"),
    ("Comments", "comentarios"),
]


def limpa(v):
    if v is None:
        return ""
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).strip()


def main(caminho=PADRAO):
    os.makedirs(CACHE, exist_ok=True)
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    it = ws.iter_rows(values_only=True)
    cab = [limpa(h) for h in next(it)]
    idx = {}
    vistos = set()
    for i, h in enumerate(cab):                 # "Source" repete 7 vezes
        if h and h not in vistos:
            idx[h] = i
            vistos.add(h)
    cols_fonte = [i for i, h in enumerate(cab) if h == "Source"]
    i_orbital = cab.index("Source Used for Orbital Data")

    sats = []
    for r in it:
        if not r or not limpa(r[0]):
            continue
        d = {destino: limpa(r[idx[origem]]) if origem in idx and idx[origem] < len(r)
             else "" for origem, destino in COLUNAS}
        # transbordo do campo Comments (coluna 28, sem cabeçalho)
        if len(r) > 28 and limpa(r[28]):
            d["comentarios"] = (d["comentarios"] + " " + limpa(r[28])).strip()
        d["fonte_dados_orbitais"] = limpa(r[i_orbital]) if i_orbital < len(r) else ""
        d["fontes"] = [limpa(r[i]) for i in cols_fonte
                       if i < len(r) and limpa(r[i])]
        sats.append(d)

    saida = os.path.join(CACHE, "ucs_bruto.json")
    with open(saida, "w", encoding="utf-8") as f:
        json.dump({"fonte": os.path.basename(caminho),
                   "data_corte": "2023-05-01",
                   "satelites": sats}, f, ensure_ascii=False)
    print(f"{len(sats)} satélites → {saida}")
    n = sum(1 for s in sats if s["norad"])
    print(f"   com NORAD: {n} | com comentário: "
          f"{sum(1 for s in sats if s['comentarios'])} | com fonte: "
          f"{sum(1 for s in sats if s['fontes'])}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1] if len(sys.argv) > 1 else PADRAO)
