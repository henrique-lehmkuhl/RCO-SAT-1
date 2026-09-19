#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enriquece a base UCS com a situação atual de cada satélite no n2yo.com.

A UCS é um retrato de 2023-05-01; o n2yo rastreia o catálogo hoje. Para cada
satélite do recorte de coleta de dados busca-se `/satellite/?s=<NORAD>`, que
diz se o objeto ainda está em órbita, a data de reentrada quando saiu, as
categorias em que o n2yo o classifica e o TLE atual — de onde saem inclinação,
excentricidade, período, apogeu e perigeu de agora.

Também baixa as 58 listas de categoria (`/satellites/?c=N&p=A`), que dão o
universo do que está catalogado em órbita hoje.

O robots.txt do n2yo não restringe nenhum caminho (Disallow vazio).

Uso:
    python scrape_n2yo.py            # categorias + fichas do recorte
    python scrape_n2yo.py --cats     # só as categorias
"""
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

import classificar

BASE = "https://www.n2yo.com"
AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "cache", "n2yo")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-scraper "
      "(analise academica de missao; contato: henrique.lehmkuhl@gmail.com)")

_local = threading.local()
_lock = threading.Lock()
_n = [0]


def _sessao():
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        _local.s = s
    return s


def _corta(html, ini='<div id="satinfo">'):
    i = html.find(ini)
    if i < 0:
        return re.sub(r"<script.*?</script>", "", html, flags=re.S)
    return re.sub(r"<script.*?</script>", "", html[i:], flags=re.S)


def baixa(url, destino, ini='<div id="satinfo">', tentativas=3):
    if os.path.exists(destino) and os.path.getsize(destino) > 150:
        return "cache"
    for k in range(tentativas):
        try:
            r = _sessao().get(url, timeout=45)
            if r.status_code == 404:
                return "404"
            r.raise_for_status()
            r.encoding = "utf-8"
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8") as f:
                f.write(_corta(r.text, ini))
            time.sleep(0.15)               # gentileza com o servidor
            return "ok"
        except Exception as e:
            if k == tentativas - 1:
                return f"erro: {e}"
            time.sleep(2 * (k + 1))


def categorias():
    """Baixa o índice e a lista completa de cada categoria."""
    os.makedirs(CACHE, exist_ok=True)
    idx = os.path.join(CACHE, "_categorias.html")
    print("índice de categorias:", baixa(BASE + "/satellites/", idx, ini="<!DOC"))
    h = open(idx, encoding="utf-8").read()
    ids = sorted({int(x) for x in re.findall(r"\?c=(\d+)", h)})
    print(f"{len(ids)} categorias")
    for c in ids:
        st = baixa(f"{BASE}/satellites/?c={c}&p=A",
                   os.path.join(CACHE, "cat", f"{c}.html"), ini="<!DOC")
        if st not in ("ok", "cache"):
            print(f"   c={c}: {st}")
    return ids


def fichas(norads):
    print(f"{len(norads)} fichas de satélite a buscar")

    def job(n):
        return n, baixa(f"{BASE}/satellite/?s={n}",
                        os.path.join(CACHE, "sat", f"{n}.html"))

    erros = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(job, n) for n in norads]
        for f in as_completed(futs):
            n, st = f.result()
            with _lock:
                _n[0] += 1
                if st not in ("ok", "cache"):
                    erros.append((n, st))
                if _n[0] % 200 == 0:
                    print(f"   {_n[0]}/{len(norads)}", flush=True)
    print(f"fim: {_n[0]} fichas, {len(erros)} erros")
    for e in erros[:20]:
        print("   ", e)


def vizinhos():
    """Para cada ficha que veio como corpo de foguete ou detrito, busca o
    objeto ±1 do mesmo lançamento — é lá que costuma estar a carga útil."""
    import gerar_tabelas as G
    d = os.path.join(CACHE, "sat")
    alvos = []
    for fn in os.listdir(d):
        n = os.path.splitext(fn)[0]
        f = G.le_ficha(n)
        if f.get("n2yo_tipo_objeto") in ("corpo de foguete", "detrito"):
            alvos += [str(int(n) - 1), str(int(n) + 1)]
    alvos = [a for a in alvos
             if not os.path.exists(os.path.join(d, a + ".html"))]
    if alvos:
        print(f"{len(alvos)} objetos vizinhos a conferir")
        fichas(alvos)


def main():
    categorias()
    if "--cats" in sys.argv:
        return
    norads = []
    for s, k in classificar.classifica_todos():
        if classificar.no_recorte(k) and s.get("norad", "").isdigit():
            norads.append(s["norad"])
    fichas(sorted(set(norads), key=int))
    vizinhos()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
