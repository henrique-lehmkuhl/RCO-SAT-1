#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coleta o Nanosats Database (https://www.nanosats.eu/database).

Duas etapas:

1. download  - baixa o índice, as 2408 páginas /sat/<slug>.html, as 60 páginas
               /keyword/<slug>.html e a página /tables.html (que traz a tabela
               de custos). Guarda tudo em `cache/`; só o miolo (#main-content)
               de cada página de satélite é gravado, porque 98% do HTML é o
               menu lateral com todos os satélites.
2. parse     - extrai índice, campos de cada missão, keywords e custos para
               `cache/nanosats_bruto.json`.

Uso:
    python scrape_nanosats.py            # baixa (se preciso) e extrai
    python scrape_nanosats.py --parse    # só extrai, usando o cache

Apague `cache/` para forçar nova coleta.
"""
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

BASE = "https://www.nanosats.eu"
AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "cache")
BRUTO = os.path.join(CACHE, "nanosats_bruto.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-scraper "
      "(analise academica de missao; contato: henrique.lehmkuhl@gmail.com)")

_local = threading.local()
_lock = threading.Lock()
_conta = [0]


# ------------------------------------------------------------------ download
def _sessao():
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        _local.s = s
    return s


def _corta(html):
    """Descarta o menu lateral; devolve só o bloco #main-content."""
    i = html.find('id="main-content"')
    if i < 0:
        return html
    ini = html.rfind("<div", 0, i)
    fim = html.find("</section>", i)
    return html[ini:fim if fim > 0 else len(html)]


def baixa(url, destino, cortar=True, tentativas=3):
    if os.path.exists(destino) and os.path.getsize(destino) > 200:
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
                f.write(_corta(r.text) if cortar else r.text)
            return "ok"
        except Exception as e:                       # rede instável: tenta de novo
            if k == tentativas - 1:
                return f"erro: {e}"
            time.sleep(2 * (k + 1))


def download():
    os.makedirs(CACHE, exist_ok=True)
    idx = os.path.join(CACHE, "database.html")
    print("database.html:", baixa(BASE + "/database.html", idx, cortar=False))
    print("tables.html:  ", baixa(BASE + "/tables.html",
                                  os.path.join(CACHE, "tables.html"), cortar=False))

    html = open(idx, encoding="utf-8").read()
    tabela = html[html.find('<table id="Nanosatellite-Database"'):]
    tabela = tabela[:tabela.find("</table>")]
    slugs = sorted(set(re.findall(r'href="sat/([^"]+)\.html"', tabela)))

    tb = open(os.path.join(CACHE, "tables.html"), encoding="utf-8").read()
    kws = sorted(set(re.findall(r'href="\.\./keyword/([^"]+)\.html"', tb)))
    print(f"{len(slugs)} satélites + {len(kws)} keywords")

    def sat(s):
        return baixa(f"{BASE}/sat/{s}.html", os.path.join(CACHE, "sat", s + ".html"))

    def kw(k):
        return baixa(f"{BASE}/keyword/{k}.html",
                     os.path.join(CACHE, "keyword", k + ".html"))

    erros = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(kw, k): k for k in kws}
        futs.update({ex.submit(sat, s): s for s in slugs})
        for f in as_completed(futs):
            st = f.result()
            with _lock:
                _conta[0] += 1
                if st.startswith("erro") or st == "404":
                    erros.append((futs[f], st))
                if _conta[0] % 400 == 0:
                    print(f"  {_conta[0]}/{len(futs)}", flush=True)
    print(f"download concluído: {_conta[0]} páginas, {len(erros)} erros")
    for e in erros[:20]:
        print("   ", e)


# --------------------------------------------------------------------- parse
def _sopa(caminho):
    with open(caminho, encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


def _limpa(s):
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def _celula(td):
    """Texto da célula (uma linha por parágrafo/item) + links + itens de lista."""
    links = [(a.get("href"), _limpa(a.get_text()))
             for a in td.find_all("a") if a.get("href")]
    itens = [_limpa(li.get_text()) for li in td.find_all("li")]
    txt = re.sub(r"[ \t]+", " ", td.get_text("\n"))
    txt = "\n".join(_limpa(l) for l in txt.split("\n") if _limpa(l))
    return txt, links, itens


def _url(u):
    if not u or u.startswith("http"):
        return u
    return BASE + "/" + u.lstrip("./").replace("../", "")


def parse_indice():
    """As 8 colunas da tabela pública do database."""
    s = _sopa(os.path.join(CACHE, "database.html"))
    linhas = []
    for tr in s.find("table", id="Nanosatellite-Database").find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue
        a = tds[0].find("a")
        nome = _limpa(tds[0].get_text())
        m = re.match(r"^(.*?)\s*\((.*)\)\s*$", nome)
        img = tds[7].find("a") if len(tds) > 7 else None
        linhas.append({
            "nome": m.group(1) if m else nome,
            "outros_nomes": m.group(2) if m else "",
            "nome_tabela": nome,
            "slug": re.sub(r"^sat/|\.html$", "", a["href"]) if a else "",
            "url_pagina": BASE + "/" + a["href"] if a else "",
            "organizacao_indice": _limpa(tds[1].get_text()),
            "nacao_indice": _limpa(tds[2].get_text()),
            "tipo_u_massa": _limpa(tds[3].get_text()),
            "data_lancamento": _limpa(tds[4].get_text()),
            "status_indice": _limpa(tds[5].get_text()),
            "descricao_indice": _limpa(tds[6].get_text()),
            "foto": BASE + "/" + img["href"].replace(" ", "%20") if img else "",
        })
    return linhas


def parse_sat(caminho):
    """Todos os campos da ficha da missão, com os links de cada campo."""
    s = _sopa(caminho)
    slug = os.path.splitext(os.path.basename(caminho))[0]
    campos, links, listas = {}, {}, {}
    tb = s.find("table", id="table-company")
    if tb:
        for tr in tb.find_all("tr"):
            th, td = tr.find("th"), tr.find("td")
            if not th or not td:
                continue
            k = _limpa(th.get_text())
            txt, lk, itens = _celula(td)
            lk = [(_url(u), t) for u, t in lk]
            if k in campos:                     # rótulo repetido: concatena
                campos[k] += "\n" + txt
                links[k] += lk
                continue
            campos[k], links[k] = txt, lk
            if itens:
                listas[k] = itens
    mod = s.find(string=re.compile(r"Last modified"))
    return {
        "slug": slug,
        "url": f"{BASE}/sat/{slug}.html",
        "campos": campos,
        "links": links,
        "listas": listas,
        "fotos": [_url(a["href"]) for a in s.select("a.fancybox-1") if a.get("href")],
        "ultima_modificacao": (_limpa(mod).replace("Last modified:", "").strip()
                               if mod else ""),
    }


def parse_keywords():
    d = os.path.join(CACHE, "keyword")
    mapa = {}
    for fn in sorted(os.listdir(d)):
        s = _sopa(os.path.join(d, fn))
        h = s.find(["h1", "h2"])
        sats = [re.sub(r".*/sat/|\.html$", "", a["href"])
                for a in s.select("a[href]") if "/sat/" in a["href"]]
        mapa[os.path.splitext(fn)[0]] = {
            "titulo": _limpa(h.get_text()) if h else os.path.splitext(fn)[0],
            "satelites": sorted(set(sats)),
        }
    return mapa


def parse_custos():
    """Tabela 'CubeSat Costs' de /tables.html."""
    s = _sopa(os.path.join(CACHE, "tables.html"))
    tb = s.find("table", id="table-costs")
    cabec, out = None, []
    for tr in tb.find_all("tr"):
        cs = tr.find_all(["th", "td"])
        vals = [_limpa(c.get_text()) for c in cs]
        if cs and cs[0].name == "th":
            cabec = vals
            continue
        if not cabec or len(vals) < len(cabec) - 1:
            continue
        linha = dict(zip(cabec, vals))
        a = cs[0].find("a")
        linha["slug"] = (re.sub(r".*/sat/|\.html$", "", a["href"])
                         if a and "/sat/" in a.get("href", "") else "")
        fonte = [c.find("a")["href"] for c in cs
                 if c.find("a") and c.find("a").get("href", "").startswith("http")]
        linha["url_fonte"] = fonte[0] if fonte else ""
        out.append(linha)
    return out


def parse():
    print("índice...", flush=True)
    indice = parse_indice()
    print(f"  {len(indice)} linhas")

    print("fichas de missão...", flush=True)
    d = os.path.join(CACHE, "sat")
    sats = {}
    for i, fn in enumerate(sorted(os.listdir(d)), 1):
        p = parse_sat(os.path.join(d, fn))
        sats[p["slug"]] = p
        if i % 500 == 0:
            print(f"  {i}", flush=True)
    print(f"  {len(sats)} fichas")

    kws = parse_keywords()
    custos = parse_custos()
    print(f"  {len(kws)} keywords, {len(custos)} linhas de custo")

    with open(BRUTO, "w", encoding="utf-8") as f:
        json.dump({"indice": indice, "sats": sats, "keywords": kws,
                   "custos_tabela": custos}, f, ensure_ascii=False)
    print("gravado:", BRUTO)


if __name__ == "__main__":
    if "--parse" not in sys.argv:
        download()
    parse()
