#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classifica as missões do Nanosats Database e gera os CSVs/JSON do recorte.

Entrada:  cache/nanosats_bruto.json   (produzido por scrape_nanosats.py)
Saída:    nanosats_todos.csv          todas as linhas do banco + classificação
          nanosats_coleta_dados.csv   só o recorte, com todos os campos
          nanosats_coleta_dados.json  o recorte com os campos brutos e links
          custos_nanosats.csv         custos declarados (tabela + fichas + texto)
          resultados_nanosats.csv     resultados e causas de falha publicados
          keywords_nanosats.csv       satélite x palavra-chave do site
"""
import collections
import csv
import json
import os
import re
import sys

import regras_coleta as R

AQUI = os.path.dirname(os.path.abspath(__file__))
BRUTO = os.path.join(AQUI, "cache", "nanosats_bruto.json")

# ficha da missão -> nome de coluna (ordem = prioridade entre rótulos sinônimos)
MAPA = [
    ("nome_ficha", ["Spacecraft name", "Satellite name", "Name", "Spacecraft", "Satellite"]),
    ("tipo_espacial", ["Spacecraft type", "Type"]),
    ("unidades_massa", ["Units or mass", "Form factor"]),
    ("massa_kg", ["Mass in kg"]),
    ("status", ["Status"]),
    ("lancado_em", ["Launched"]),
    ("norad_id", ["NORAD ID"]),
    ("orbita", ["Orbit"]),
    ("deployer", ["Deployer", "Deployment"]),
    ("lancador", ["Launcher", "Rocket"]),
    ("organizacao", ["Organization", "Organisation", "Entity name", "Entity", "Operator"]),
    ("operador", ["Operator"]),
    ("fabricante", ["Manufacturer"]),
    ("instituicao", ["Institution"]),
    ("tipo_entidade", ["Entity type"]),
    ("pais", ["Country", "Nation", "Nation (HQ)"]),
    ("pais_integracao", ["Nation (AIT)"]),
    ("sede", ["Headquarters"]),
    ("intermediario_lancamento", ["Launch brokerer"]),
    ("parceiros", ["Partners"]),
    ("custos_ficha", ["Costs"]),
    ("oneliner", ["Oneliner"]),
    ("descricao", ["Description"]),
    ("resultados", ["Results"]),
    ("causa_falha", ["Failure cause"]),
    ("notas", ["Notes"]),
    ("keywords_ficha", ["Keywords"]),
    ("subsistemas_cots", ["COTS subsystems", "COTS compoments"]),
    ("servico_estacao_solo", ["GS Service"]),
    ("sistema_controle_missao", ["MCS"]),
    ("no_mesmo_lancamento", ["On the same launch"]),
]

# colunas que só entram no recorte (no CSV completo virariam 4 MB de URLs)
TEXTOS_LONGOS = ["descricao", "resultados", "notas", "causa_falha",
                 "subsistemas_cots", "no_mesmo_lancamento", "parceiros",
                 "fontes", "fotos"]


def bate(regras, texto):
    """Rótulos cujas regras dispararam, descontadas as negativas de contexto."""
    achados = []
    for rot, rx in regras:
        neg = R.NEGATIVAS_CONTEXTO.get(rot)
        for m in re.finditer(rx, texto, flags=re.I):
            if neg and re.search(neg, texto[max(0, m.start() - 60):m.end() + 60],
                                 flags=re.I):
                continue                      # o alvo está em órbita, não no solo
            achados.append(rot)
            break
    return achados


def classifica(slug, ficha, keywords_site):
    c = ficha["campos"]
    texto = "\n".join([c.get(k, "") for k in
                       ("Oneliner", "Description", "Notes", "Results", "Keywords")]
                      + [" ".join(sorted(keywords_site))])
    kws = set(keywords_site)
    a1 = bate(R.SR_FORTE, texto) + [f"keyword: {k}" for k in sorted(kws & R.KW_SR)]
    a2 = bate(R.SR_FRACO, texto)
    b = bate(R.DCS, texto) + [f"keyword: {k}" for k in sorted(kws & R.KW_DCS)]
    cc = bate(R.SINAIS, texto) + [f"keyword: {k}" for k in sorted(kws & R.KW_SIN)]
    ctx = [k for k, rx in R.CONTEXTO.items() if re.search(rx, texto, flags=re.I)]

    fora = bool(re.search(R.FORA_DA_TERRA, texto, flags=re.I)) or \
        "Beyond Earth orbit" in kws
    # missão lunar/interplanetária sem nenhuma evidência de alvo terrestre:
    # o instrumento é de sensoriamento remoto, mas não da Terra -> rebaixa
    if fora and a1 and not (set(a1) & R.SR_ESPECIFICO_TERRA):
        a2 = a2 + [f"{r} (alvo fora da Terra)" for r in a1]
        a1 = []
    return {"A1": a1, "A2": a2, "B": b, "C": cc, "ctx": ctx, "fora_da_terra": fora,
            "radioamador": bool(re.search(R.RADIOAMADOR, texto, flags=re.I))}


def achata(lista):
    return "; ".join(lista)


def dinheiro(texto):
    return [m.group(0) for m in re.finditer(R.MOEDA, texto or "", flags=re.I)]


MULT = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "mln": 1e6,
        "b": 1e9, "billion": 1e9}
SIMBOLO = {"$": "USD", "US$": "USD", "AU$": "AUD", "CA$": "CAD", "€": "EUR",
           "£": "GBP", "¥": "JPY", "₹": "INR", "R$": "BRL"}
VALOR = re.compile(
    r"(?P<moeda>(?:US|AU|CA|NZ|HK|S)?\$|€|£|¥|₹|R\$|SEK|EUR|USD|GBP|CHF|NOK|DKK|"
    r"PLN|CZK|JPY|CNY|INR|KRW)\s?(?P<num>\d[\d.,]*)\s?(?P<mult>million|billion|"
    r"thousand|M|K|B)?\b"
    r"|(?P<num2>\d[\d.,]*)\s?(?P<mult2>M|million|billion)\s?(?P<moeda2>SEK|EUR|"
    r"USD|GBP|NOK|DKK|CZK|PLN|JPY|CNY|INR|KRW|euros?|dollars?|pounds?)",
    flags=re.I)


def valor_numerico(texto):
    """Primeiro valor monetário do texto, em (número, moeda). Melhor esforço:
    o texto original continua na coluna `custo` e é a referência."""
    m = VALOR.search(texto or "")
    if not m:
        return "", ""
    num = (m.group("num") or m.group("num2") or "").replace(",", "")
    mult = (m.group("mult") or m.group("mult2") or "").lower()
    moeda = (m.group("moeda") or m.group("moeda2") or "").upper()
    moeda = SIMBOLO.get(moeda, moeda)
    moeda = {"EUROS": "EUR", "EURO": "EUR", "DOLLARS": "USD", "DOLLAR": "USD",
             "POUNDS": "GBP", "POUND": "GBP"}.get(moeda, moeda)
    try:
        v = float(num) * MULT.get(mult, 1)
    except ValueError:
        return "", moeda
    return f"{v:.0f}", moeda


def main():
    d = json.load(open(BRUTO, encoding="utf-8"))
    indice, sats = d["indice"], d["sats"]

    kw_por_sat = collections.defaultdict(set)
    for kw, info in d["keywords"].items():
        for s in info["satelites"]:
            kw_por_sat[s].add(info["titulo"])

    cls = {slug: classifica(slug, f, kw_por_sat.get(slug, set()))
           for slug, f in sats.items()}

    # ------------------------------------------------ uma linha por missão
    linhas = []
    for ln in indice:
        slug = ln["slug"]
        f = sats.get(slug, {"campos": {}, "links": {}, "listas": {}, "fotos": [],
                            "ultima_modificacao": ""})
        c, lk = f["campos"], f.get("links", {})
        k = cls.get(slug, {"A1": [], "A2": [], "B": [], "C": [], "ctx": [],
                           "fora_da_terra": False, "radioamador": False})
        linha = dict(ln)
        for col, rotulos in MAPA:
            v = ""
            for r in rotulos:
                if c.get(r):
                    v = c[r]
                    break
            linha[col] = v
        linha["fontes"] = " | ".join(u for u, _ in lk.get("Sources", []) if u)
        linha["url_custo"] = " | ".join(u for u, _ in lk.get("Costs", []) if u)
        linha["urls_resultados"] = " | ".join(u for u, _ in lk.get("Results", []) if u)
        linha["url_status"] = " | ".join(u for u, _ in lk.get("Status", []) if u)
        linha["keywords_site"] = achata(sorted(kw_por_sat.get(slug, [])))
        linha["fotos"] = " | ".join(f.get("fotos", []))
        linha["n_fontes"] = len([u for u, _ in lk.get("Sources", []) if u])
        linha["n_fotos"] = len(f.get("fotos", []))
        linha["ultima_modificacao"] = f.get("ultima_modificacao", "")

        sr_forte, sr_fraco = bool(k["A1"]), bool(k["A2"]) and not k["A1"]
        cats = []
        if sr_forte:
            cats.append("A - sensoriamento remoto")
        if sr_fraco:
            cats.append("A(fraco) - câmera sem alvo declarado")
        if k["B"]:
            cats.append("B - coleta de plataformas (DCS/IoT)")
        if k["C"]:
            cats.append("C - sinais cooperativos (AIS/ADS-B/RF)")
        linha.update({
            "categoria_coleta": achata(cats) or "—",
            "sr_forte": "sim" if sr_forte else "não",
            "sr_fraco": "sim" if sr_fraco else "não",
            "dcs_iot": "sim" if k["B"] else "não",
            "sinais": "sim" if k["C"] else "não",
            "no_recorte": "sim" if (sr_forte or k["B"] or k["C"]) else "não",
            "evidencia_sr": achata(k["A1"] or k["A2"]),
            "evidencia_dcs": achata(k["B"]),
            "evidencia_sinais": achata(k["C"]),
            "contexto": achata(k["ctx"]),
            "alvo_fora_da_terra": "sim" if k["fora_da_terra"] else "não",
            "carga_radioamador": "sim" if k["radioamador"] else "não",
            "tem_custo_declarado": "sim" if (c.get("Costs") or
                                             dinheiro(c.get("Description", ""))) else "não",
            "tem_resultados": "sim" if c.get("Results") else "não",
        })
        linhas.append(linha)

    colunas = list(linhas[0].keys())
    recorte = [l for l in linhas if l["no_recorte"] == "sim"]

    def escreve(nome, dados, cols):
        caminho = os.path.join(AQUI, nome)
        with open(caminho, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in dados:
                w.writerow(r)
        print(f"  {nome}: {len(dados)} linhas")

    escreve("nanosats_todos.csv", linhas,
            [c for c in colunas if c not in TEXTOS_LONGOS])
    escreve("nanosats_coleta_dados.csv", recorte, colunas)

    # ------------------------------------------------------- JSON do recorte
    detalhe = []
    vistos = set()
    for l in recorte:
        slug = l["slug"]
        if slug in vistos:
            continue
        vistos.add(slug)
        f = sats[slug]
        detalhe.append({
            "slug": slug,
            "url": f["url"],
            "missoes_no_indice": [x["nome_tabela"] for x in indice if x["slug"] == slug],
            "categoria_coleta": l["categoria_coleta"],
            "evidencia": {"sensoriamento_remoto": l["evidencia_sr"],
                          "coleta_plataformas": l["evidencia_dcs"],
                          "sinais": l["evidencia_sinais"],
                          "contexto": l["contexto"]},
            "keywords_site": sorted(kw_por_sat.get(slug, [])),
            "campos": f["campos"],
            "links_por_campo": f["links"],
            "listas": f["listas"],
            "fotos": f["fotos"],
            "ultima_modificacao": f["ultima_modificacao"],
        })
    with open(os.path.join(AQUI, "nanosats_coleta_dados.json"), "w",
              encoding="utf-8") as fh:
        json.dump(detalhe, fh, ensure_ascii=False, indent=1)
    print(f"  nanosats_coleta_dados.json: {len(detalhe)} fichas")

    # ------------------------------------------------------------- custos
    por_slug = {l["slug"]: l for l in linhas}
    custos = []
    for c in d["custos_tabela"]:
        l = por_slug.get(c.get("slug", ""), {})
        custos.append({
            "origem": "tabela CubeSat Costs",
            "slug": c.get("slug", ""),
            "missao": c.get("Project", ""),
            "tamanho": c.get("Size", ""),
            "organizacao": c.get("Organization", ""),
            "integrador_aivt": c.get("Manufactured (AIVT) by", ""),
            "custo": c.get("Costs", ""),
            "financiador": c.get("Funded primarily by", ""),
            "url_fonte": c.get("url_fonte", ""),
            "categoria_coleta": l.get("categoria_coleta", ""),
            "no_recorte": l.get("no_recorte", ""),
            "pais": l.get("pais", "") or l.get("nacao_indice", ""),
            "data_lancamento": l.get("data_lancamento", ""),
        })
    for slug, f in sats.items():
        l = por_slug.get(slug, {})
        campo = f["campos"].get("Costs", "")
        if campo:
            custos.append({
                "origem": "ficha da missão (campo Costs)",
                "slug": slug, "missao": l.get("nome", slug),
                "tamanho": l.get("unidades_massa", "") or l.get("tipo_u_massa", ""),
                "organizacao": l.get("organizacao", "") or l.get("organizacao_indice", ""),
                "integrador_aivt": l.get("fabricante", ""),
                "custo": campo, "financiador": "",
                "url_fonte": " | ".join(u for u, _ in f["links"].get("Costs", []) if u),
                "categoria_coleta": l.get("categoria_coleta", ""),
                "no_recorte": l.get("no_recorte", ""),
                "pais": l.get("pais", "") or l.get("nacao_indice", ""),
                "data_lancamento": l.get("data_lancamento", ""),
            })
        for campo_txt in ("Description", "Notes", "Results"):
            for val in dinheiro(f["campos"].get(campo_txt, "")):
                t = f["campos"][campo_txt]
                i = t.find(val)
                custos.append({
                    "origem": f"texto livre ({campo_txt})",
                    "slug": slug, "missao": l.get("nome", slug),
                    "tamanho": l.get("unidades_massa", "") or l.get("tipo_u_massa", ""),
                    "organizacao": l.get("organizacao", "") or l.get("organizacao_indice", ""),
                    "integrador_aivt": l.get("fabricante", ""),
                    "custo": val,
                    "financiador": "",
                    "url_fonte": "",
                    "trecho": re.sub(r"\s+", " ", t[max(0, i - 120):i + len(val) + 120]),
                    "categoria_coleta": l.get("categoria_coleta", ""),
                    "no_recorte": l.get("no_recorte", ""),
                    "pais": l.get("pais", "") or l.get("nacao_indice", ""),
                    "data_lancamento": l.get("data_lancamento", ""),
                })
    # valor numérico e custo por satélite, quando a fonte os declara
    for c in custos:
        txt = c["custo"]
        sp = re.search(r"Single platform:\s*([^\n]+)", txt, flags=re.I)
        c["custo_por_satelite"] = sp.group(1).strip() if sp else ""
        c["custo"] = re.sub(r"\s*Single platform:\s*[^\n]+", "", txt).strip() or txt
        c["valor_num"], c["moeda"] = valor_numerico(c["custo"])
        c["valor_num_por_satelite"], _ = valor_numerico(c["custo_por_satelite"])
        # "$405,00": separador de milhar incompleto na fonte -> número duvidoso
        c["valor_suspeito"] = "sim" if re.search(r"\d,\d{1,2}(?!\d)", c["custo"]) else ""

    cols_custo = ["origem", "slug", "missao", "tamanho", "organizacao",
                  "integrador_aivt", "custo", "valor_num", "moeda",
                  "valor_suspeito", "custo_por_satelite",
                  "valor_num_por_satelite", "financiador",
                  "trecho", "url_fonte", "categoria_coleta", "no_recorte", "pais",
                  "data_lancamento"]
    escreve("custos_nanosats.csv", custos, cols_custo)

    # --------------------------------------------------------- resultados
    res = [l for l in linhas if l["resultados"] or l["causa_falha"]]
    escreve("resultados_nanosats.csv", res,
            ["nome", "slug", "url_pagina", "data_lancamento", "status",
             "status_indice", "categoria_coleta", "no_recorte", "resultados",
             "urls_resultados", "causa_falha", "organizacao", "pais",
             "unidades_massa", "oneliner"])

    # ----------------------------------------------------------- keywords
    kws = []
    for kw, info in sorted(d["keywords"].items()):
        for s in info["satelites"]:
            l = por_slug.get(s, {})
            kws.append({"keyword": info["titulo"], "slug": s,
                        "missao": l.get("nome", s),
                        "url_keyword": f"https://www.nanosats.eu/keyword/{kw}.html",
                        "categoria_coleta": l.get("categoria_coleta", ""),
                        "no_recorte": l.get("no_recorte", "")})
    escreve("keywords_nanosats.csv", kws,
            ["keyword", "missao", "slug", "categoria_coleta", "no_recorte",
             "url_keyword"])

    # ------------------------------------------------------------ resumo
    print("\nRESUMO")
    print(f"  linhas no banco: {len(linhas)} | fichas distintas: {len(sats)}")
    for rot, chave in (("A  sensoriamento remoto (forte)", "sr_forte"),
                       ("A' câmera sem alvo declarado", "sr_fraco"),
                       ("B  coleta de plataformas (DCS/IoT)", "dcs_iot"),
                       ("C  sinais cooperativos (AIS/ADS-B/RF)", "sinais"),
                       ("   no recorte (A|B|C)", "no_recorte")):
        n = sum(1 for l in linhas if l[chave] == "sim")
        print(f"  {rot}: {n} linhas")
    print(f"  custos declarados: {len(custos)} registros, "
          f"{len({c['slug'] for c in custos})} missões")
    print(f"  resultados publicados: {len(res)} linhas")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
