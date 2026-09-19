#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica `regras_coleta.py` a cada satélite da base UCS.

Devolve, por satélite, os recortes (A/B/C), os rótulos de evidência que os
justificam e o contexto. Usado tanto pelo scraper do n2yo (para saber quais
NORAD buscar) quanto pelo gerador de tabelas.
"""
import json
import os
import re

import regras_coleta as R

AQUI = os.path.dirname(os.path.abspath(__file__))
BRUTO = os.path.join(AQUI, "cache", "ucs_bruto.json")


def carrega():
    with open(BRUTO, encoding="utf-8") as f:
        return json.load(f)


def classifica(s):
    prop = s.get("proposito", "")
    det = (s.get("proposito_detalhado", "") or "").strip()
    op = (s.get("operador", "") or "").strip()
    texto = " ".join([s.get("nome", ""), s.get("comentarios", ""), det])

    a, b, c = [], [], []

    # --- A: sensoriamento remoto -----------------------------------------
    if det in R.SR_DETALHADO:
        a.append(f"propósito detalhado: {R.SR_DETALHADO[det]}")
    if re.search(R.SR_PROPOSITO, prop, re.I):
        a.append(f"propósito declarado: {prop}")

    # --- B: coleta de plataformas no solo ---------------------------------
    if det in R.DCS_DETALHADO:
        b.append(f"propósito detalhado: {R.DCS_DETALHADO[det]}")
    if op in R.OPERADORES_DCS:
        b.append(f"operador: {R.OPERADORES_DCS[op]}")
    if det not in R.FORA_DO_RECORTE_DETALHADO:
        for rot, rx in R.DCS_TEXTO:
            if re.search(rx, texto, re.I):
                b.append(rot)

    # --- C: sinais cooperativos e RF --------------------------------------
    if det in R.SIN_DETALHADO:
        c.append(f"propósito detalhado: {R.SIN_DETALHADO[det]}")
    if op in R.OPERADORES_SINAIS:
        c.append(f"operador: {R.OPERADORES_SINAIS[op]}")
    if re.search(R.SIN_PROPOSITO, prop, re.I):
        c.append(f"propósito declarado: {prop}")
    for rot, rx in R.SIN_TEXTO:
        if re.search(rx, texto, re.I):
            c.append(rot)

    ctx = [rot for rot, rx in R.CONTEXTO_PROPOSITO.items()
           if re.search(rx, prop, re.I)]
    for chave, rot in R.CONTEXTO_USUARIO.items():
        if chave in (s.get("usuarios", "") or ""):
            ctx.append(rot)

    dedup = lambda x: list(dict.fromkeys(x))
    return {"A": dedup(a), "B": dedup(b), "C": dedup(c), "ctx": dedup(ctx)}


def classifica_todos(sats=None):
    sats = sats if sats is not None else carrega()["satelites"]
    return [(s, classifica(s)) for s in sats]


def no_recorte(k):
    return bool(k["A"] or k["B"] or k["C"])


if __name__ == "__main__":
    import sys
    import collections
    sys.stdout.reconfigure(encoding="utf-8")
    pares = classifica_todos()
    n = collections.Counter()
    for s, k in pares:
        for cat in ("A", "B", "C"):
            if k[cat]:
                n[cat] += 1
        if no_recorte(k):
            n["recorte"] += 1
    print(f"total {len(pares)} | A={n['A']} B={n['B']} C={n['C']} "
          f"| recorte={n['recorte']}")
    ev = collections.Counter()
    for s, k in pares:
        for cat in ("A", "B", "C"):
            for r in k[cat]:
                ev[f"{cat} · {r}"] += 1
    for chave, v in ev.most_common(30):
        print(f"   {v:5d}  {chave}")
