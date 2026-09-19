#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cruza a base UCS com o n2yo e escreve os CSVs/JSON do recorte.

Saídas:
    ucs_todos.csv            7.560 satélites da UCS + classificação
    ucs_coleta_dados.csv     o recorte A∪B∪C, com tudo e com a situação atual
    ucs_coleta_dados.json    o recorte com os campos brutos, fontes e TLE
    n2yo_categorias.csv      satélite × categoria do n2yo
    orbita_ucs_vs_n2yo.csv   órbita de 2023 (UCS) contra a de hoje (TLE)
"""
import csv
import datetime
import json
import math
import os
import re
import sys

import classificar

AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE_N2YO = os.path.join(AQUI, "cache", "n2yo")
MU = 398600.4418            # km³/s², constante gravitacional geocêntrica
RT = 6378.137               # km, raio equatorial da Terra


# --------------------------------------------------------------- n2yo: TLE
def elementos(l1, l2):
    """Elementos orbitais atuais a partir do TLE (colunas fixas do formato)."""
    try:
        aa = int(l1[18:20])
        ano = 2000 + aa if aa < 57 else 1900 + aa
        dia = float(l1[20:32])
        epoca = (datetime.datetime(ano, 1, 1) +
                 datetime.timedelta(days=dia - 1)).strftime("%Y-%m-%d")
        inc = float(l2[8:16])
        ecc = float("0." + l2[26:33].strip())
        mm = float(l2[52:63])                      # revoluções por dia
        if mm <= 0:
            return {}
        T = 1440.0 / mm                            # período em minutos
        a = (MU * (T * 60 / (2 * math.pi)) ** 2) ** (1 / 3)
        return {"epoca": epoca, "inclinacao": round(inc, 3),
                "excentricidade": round(ecc, 6), "periodo_min": round(T, 2),
                "apogeu_km": round(a * (1 + ecc) - RT, 1),
                "perigeu_km": round(a * (1 - ecc) - RT, 1)}
    except (ValueError, IndexError):
        return {}


N2YO_COLS = ["n2yo_norad_usado", "n2yo_correcao", "n2yo_nome", "n2yo_em_orbita", "n2yo_reentrada", "n2yo_categorias",
             "n2yo_pais", "n2yo_local_lancamento", "n2yo_lancamento",
             "n2yo_nota", "n2yo_descricao", "n2yo_tipo_objeto",
             "n2yo_epoca_tle", "n2yo_inclinacao", "n2yo_excentricidade",
             "n2yo_periodo_min", "n2yo_apogeu_km", "n2yo_perigeu_km",
             "n2yo_url"]


def le_ficha(norad):
    """Campos do n2yo. Sempre devolve todas as colunas, vazias se não há ficha,
    para que o cabeçalho do CSV não dependa de qual satélite vem primeiro."""
    vazio = {c: "" for c in N2YO_COLS}
    caminho = os.path.join(CACHE_N2YO, "sat", f"{norad}.html")
    if not os.path.exists(caminho):
        return vazio | {"tle": []}
    h = open(caminho, encoding="utf-8").read()
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))

    def campo(rot):
        m = re.search(rf"<B>{rot}</B>\s*:\s*(?:<a[^>]*>)?([^<]*)", h, re.I)
        return m.group(1).strip() if m else ""

    nome = re.search(r"<H1>(.*?)</H1>", h, re.S | re.I)
    nome = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", nome.group(1))).strip() \
        if nome else ""
    cats = re.search(r"is classified as:\s*(.*?)</p>", h, re.S | re.I)
    cats = [re.sub(r"\s+", " ", c).strip()
            for c in re.findall(r">([^<>]{2,60})</a>", cats.group(1), re.I)] \
        if cats else []
    # frase descritiva que o n2yo publica depois dos campos, quando existe
    desc = ""
    m = re.search(r"Launch site</B>:[^<]*(.*?)</div>", h, re.S | re.I)
    if m:
        t = re.sub(r"<[^>]+>", " ", m.group(1))
        t = re.sub(r"Decay date\s*:\s*[\d-]+", " ", t)
        t = re.sub(r"Note:\s*This is a [A-Z ]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip(" .;")
        desc = t if len(t) > 20 else ""
    tle = re.search(r'<div id="tle">\s*<pre>\s*(1 [^\n]+)\n\s*(2 [^\n]+)', h)
    orb = elementos(tle.group(1), tle.group(2)) if tle else {}
    decaiu = "no longer on orbit" in txt.lower()
    nota = re.search(r"<b>\s*Note:\s*([^<]+)</b>", h, re.I)
    return vazio | {
        "n2yo_nome": nome,
        "n2yo_em_orbita": "não" if decaiu else ("sim" if orb else "?"),
        "n2yo_reentrada": campo("Decay date"),
        "n2yo_categorias": "; ".join(cats),
        "n2yo_pais": campo("Source"),
        "n2yo_local_lancamento": campo("Launch site"),
        "n2yo_lancamento": campo("Launch date"),
        "n2yo_nota": nota.group(1).strip() if nota else "",
        "n2yo_descricao": desc,
        "n2yo_tipo_objeto": ("corpo de foguete" if nota and "ROCKET" in nota.group(1).upper()
                             else "detrito" if nota and "DEBRIS" in nota.group(1).upper()
                             else "carga útil"),
        "n2yo_epoca_tle": orb.get("epoca", ""),
        "n2yo_inclinacao": orb.get("inclinacao", ""),
        "n2yo_excentricidade": orb.get("excentricidade", ""),
        "n2yo_periodo_min": orb.get("periodo_min", ""),
        "n2yo_apogeu_km": orb.get("apogeu_km", ""),
        "n2yo_perigeu_km": orb.get("perigeu_km", ""),
        "n2yo_url": f"https://www.n2yo.com/satellite/?s={norad}",
        "tle": [tle.group(1), tle.group(2)] if tle else [],
    }


def _norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def ficha_corrigida(norad, nome_oficial, nome):
    """Quando o NORAD declarado pela UCS aponta para o corpo de foguete ou um
    detrito do mesmo lançamento, tenta o objeto vizinho (±1) e só o aceita se o
    nome no n2yo bater com o nome oficial do satélite."""
    f = le_ficha(norad)
    f["n2yo_norad_usado"] = norad
    if f.get("n2yo_tipo_objeto") in ("", "carga útil") or not norad.isdigit():
        return f
    alvo = _norm(nome_oficial or nome.split("(")[0])
    for viz in (str(int(norad) - 1), str(int(norad) + 1)):
        g = le_ficha(viz)
        if g.get("n2yo_nome") and _norm(g["n2yo_nome"]) == alvo:
            g["n2yo_url"] = f"https://www.n2yo.com/satellite/?s={viz}"
            g["n2yo_norad_usado"] = viz
            g["n2yo_correcao"] = (f"NORAD {norad} da UCS é "
                                  f"{f['n2yo_tipo_objeto']}; usado {viz}, "
                                  f"cujo nome confere")
            return g
    return f


def le_categorias():
    """{norad: [categorias]} e a contagem de objetos por categoria."""
    d = os.path.join(CACHE_N2YO, "cat")
    idx = os.path.join(CACHE_N2YO, "_categorias.html")
    nomes = {}
    if os.path.exists(idx):
        h = open(idx, encoding="utf-8").read()
        for m in re.finditer(r'href="[^"]*\?c=(\d+)"[^>]*>([^<]{2,60})<', h):
            nomes.setdefault(m.group(1), re.sub(r"\s+", " ", m.group(2)).strip())
    por_sat, tamanho = {}, {}
    if not os.path.isdir(d):
        return por_sat, tamanho, nomes
    for fn in sorted(os.listdir(d)):
        c = os.path.splitext(fn)[0]
        h = open(os.path.join(d, fn), encoding="utf-8").read()
        sats = re.findall(r"/satellite/\?s=(\d+)", h)
        tamanho[nomes.get(c, f"c={c}")] = len(set(sats))
        for s in set(sats):
            por_sat.setdefault(s, []).append(nomes.get(c, f"c={c}"))
    return por_sat, tamanho, nomes


# ----------------------------------------------------------------- saídas
def escreve(nome, linhas, cols):
    caminho = os.path.join(AQUI, nome)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in linhas:
            w.writerow(r)
    print(f"  {nome}: {len(linhas)} linhas")


def num(v):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def main():
    base = classificar.carrega()
    pares = classificar.classifica_todos(base["satelites"])
    cat_por_sat, tamanho_cat, nomes_cat = le_categorias()
    print(f"n2yo: {len(cat_por_sat)} objetos catalogados em "
          f"{len(tamanho_cat)} categorias")

    linhas, detalhe = [], []
    for s, k in pares:
        norad = s.get("norad", "")
        dentro = classificar.no_recorte(k)
        n2 = (ficha_corrigida(norad, s.get("nome_oficial", ""), s["nome"])
              if dentro else {c: "" for c in N2YO_COLS})
        cats = []
        if k["A"]:
            cats.append("A — sensoriamento remoto")
        if k["B"]:
            cats.append("B — coleta de plataformas (DCS/IoT)")
        if k["C"]:
            cats.append("C — sinais cooperativos (AIS/ADS-B/RF)")

        linha = dict(s)
        linha.pop("fontes", None)
        linha["fontes"] = " | ".join(s.get("fontes", []))
        linha.update({
            "categoria_coleta": "; ".join(cats) or "—",
            "sr": "sim" if k["A"] else "não",
            "dcs_iot": "sim" if k["B"] else "não",
            "sinais": "sim" if k["C"] else "não",
            "no_recorte": "sim" if dentro else "não",
            "evidencia_sr": "; ".join(k["A"]),
            "evidencia_dcs": "; ".join(k["B"]),
            "evidencia_sinais": "; ".join(k["C"]),
            "contexto": "; ".join(k["ctx"]),
            "n2yo_categorias_indice": "; ".join(cat_por_sat.get(norad, [])),
        })
        linha.update({c: v for c, v in n2.items() if c != "tle"})
        linhas.append(linha)

        if dentro:
            detalhe.append({
                "nome": s["nome"], "norad": norad, "cospar": s["cospar"],
                "categoria_coleta": "; ".join(cats),
                "evidencia": {"sensoriamento_remoto": k["A"],
                              "coleta_plataformas": k["B"], "sinais": k["C"],
                              "contexto": k["ctx"]},
                "ucs": s,
                "n2yo": n2,
                "n2yo_categorias_indice": cat_por_sat.get(norad, []),
            })

    ucs_cols = [c for c in linhas[0] if not c.startswith("n2yo_")]
    base_cols = ucs_cols + N2YO_COLS
    recorte = [l for l in linhas if l["no_recorte"] == "sim"]

    escreve("ucs_todos.csv", linhas, ucs_cols)
    escreve("ucs_coleta_dados.csv", recorte, base_cols)

    with open(os.path.join(AQUI, "ucs_coleta_dados.json"), "w",
              encoding="utf-8") as f:
        json.dump({"fonte_ucs": base["fonte"], "data_corte_ucs": base["data_corte"],
                   "fonte_situacao": "https://www.n2yo.com/satellites/",
                   "satelites": detalhe}, f, ensure_ascii=False, indent=1)
    print(f"  ucs_coleta_dados.json: {len(detalhe)} satélites")

    # categorias do n2yo, uma linha por par satélite × categoria
    porr = {l["norad"]: l for l in recorte}
    cats = [{"norad": n, "categoria_n2yo": c,
             "nome": porr.get(n, {}).get("nome", ""),
             "categoria_coleta": porr.get(n, {}).get("categoria_coleta", ""),
             "no_recorte": "sim" if n in porr else "não"}
            for n, cs in sorted(cat_por_sat.items(), key=lambda x: int(x[0]))
            for c in cs]
    escreve("n2yo_categorias.csv", cats,
            ["norad", "nome", "categoria_n2yo", "categoria_coleta", "no_recorte"])

    # órbita declarada (2023) contra a rastreada hoje
    orb = []
    for l in recorte:
        if not l.get("n2yo_periodo_min"):
            continue
        p23, pn = num(l.get("perigeu_km")), num(l.get("n2yo_perigeu_km"))
        a23, an = num(l.get("apogeu_km")), num(l.get("n2yo_apogeu_km"))
        orb.append({
            "nome": l["nome"], "norad": l["norad"],
            "categoria_coleta": l["categoria_coleta"],
            "operador": l["operador"], "pais_operador": l["pais_operador"],
            "em_orbita": l.get("n2yo_em_orbita", ""),
            "epoca_tle": l.get("n2yo_epoca_tle", ""),
            "perigeu_ucs_km": l.get("perigeu_km", ""),
            "perigeu_hoje_km": l.get("n2yo_perigeu_km", ""),
            "delta_perigeu_km": round(pn - p23, 1) if p23 and pn else "",
            "apogeu_ucs_km": l.get("apogeu_km", ""),
            "apogeu_hoje_km": l.get("n2yo_apogeu_km", ""),
            "delta_apogeu_km": round(an - a23, 1) if a23 and an else "",
            "inclinacao_ucs": l.get("inclinacao_graus", ""),
            "inclinacao_hoje": l.get("n2yo_inclinacao", ""),
            "periodo_ucs_min": l.get("periodo_min", ""),
            "periodo_hoje_min": l.get("n2yo_periodo_min", ""),
        })
    escreve("orbita_ucs_vs_n2yo.csv", orb, list(orb[0].keys()) if orb else ["nome"])

    with open(os.path.join(AQUI, "cache", "n2yo_categorias_tamanho.json"), "w",
              encoding="utf-8") as f:
        json.dump(tamanho_cat, f, ensure_ascii=False, indent=1)

    print("\nRESUMO")
    print(f"  satélites na UCS: {len(linhas)} | no recorte: {len(recorte)}")
    for rot, col in (("A sensoriamento remoto", "sr"),
                     ("B coleta de plataformas", "dcs_iot"),
                     ("C sinais cooperativos", "sinais")):
        print(f"  {rot}: {sum(1 for l in linhas if l[col] == 'sim')}")
    viv = sum(1 for l in recorte if l.get("n2yo_em_orbita") == "sim")
    mor = sum(1 for l in recorte if l.get("n2yo_em_orbita") == "não")
    print(f"  situação hoje (n2yo): {viv} em órbita, {mor} reentraram, "
          f"{len(recorte) - viv - mor} sem resposta")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
