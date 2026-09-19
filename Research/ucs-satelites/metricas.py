#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolida as métricas do recorte de coleta de dados em `metricas.json`."""
import collections
import csv
import datetime
import json
import os
import re
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
HOJE = datetime.date(2026, 9, 16)


def le(nome):
    with open(os.path.join(AQUI, nome), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def ano(d):
    m = re.match(r"^(\d{4})-", d or "")
    return m.group(1) if m else None


def idade(d):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", d or "")
    if not m:
        return None
    y, mo, dd = (int(x) for x in m.groups())
    return round((HOJE - datetime.date(y, mo, dd)).days / 365.25, 2)


def faixa_massa(v):
    v = num(v)
    if v is None:
        return "não declarada"
    for lim, rot in ((10, "até 10 kg"), (100, "10–100 kg"), (500, "100–500 kg"),
                     (1000, "500 kg–1 t"), (5000, "1–5 t")):
        if v <= lim:
            return rot
    return "acima de 5 t"


def faixa_alt(l):
    cl = (l.get("classe_orbita") or "").upper()
    if cl == "GEO":
        return "GEO (~35 786 km)"
    if cl == "MEO":
        return "MEO"
    if cl == "ELLIPTICAL":
        return "elíptica"
    p = num(l.get("perigeu_km"))
    if p is None:
        return "não declarada"
    for lim, rot in ((400, "LEO até 400 km"), (600, "LEO 400–600 km"),
                     (800, "LEO 600–800 km"), (1200, "LEO 800–1 200 km")):
        if p <= lim:
            return rot
    return "LEO acima de 1 200 km"


CATS = [("A", "sr"), ("B", "dcs_iot"), ("C", "sinais")]


def tabela(linhas, chave, ordem=None, limite=None):
    ag = collections.defaultdict(lambda: {"n": 0, "A": 0, "B": 0, "C": 0})
    for r in linhas:
        k = chave(r)
        if k is None:
            continue
        ag[k]["n"] += 1
        for nome, col in CATS:
            if r.get(col) == "sim":
                ag[k][nome] += 1
    out = [{"chave": k, "linhas": v["n"], "A": v["A"], "B": v["B"], "C": v["C"]}
           for k, v in ag.items()]
    if ordem:
        out.sort(key=lambda x: ordem.index(x["chave"]) if x["chave"] in ordem else 99)
    else:
        out.sort(key=lambda x: -x["linhas"])
    return out[:limite] if limite else out


def main():
    todos = le("ucs_todos.csv")
    rec = le("ucs_coleta_dados.csv")
    orb = le("orbita_ucs_vs_n2yo.csv")
    tam_cat = json.load(open(os.path.join(AQUI, "cache",
                                          "n2yo_categorias_tamanho.json"),
                             encoding="utf-8"))
    M = {}

    # 1. panorama ----------------------------------------------------------
    conta = lambda col: sum(1 for r in todos if r[col] == "sim")
    M["panorama"] = [
        {"recorte": "A — sensoriamento remoto da Terra", "n": conta("sr")},
        {"recorte": "B — coleta de plataformas no solo (DCS/IoT)",
         "n": conta("dcs_iot")},
        {"recorte": "C — sinais cooperativos (AIS/ADS-B/ELINT/RF)",
         "n": conta("sinais")},
        {"recorte": "Recorte de coleta de dados (A ∪ B ∪ C)", "n": len(rec),
         "destaque": True},
        {"recorte": "Base UCS inteira (em órbita em 2023-05-01)",
         "n": len(todos), "destaque": True},
    ]

    # 2. situação hoje, segundo o n2yo -------------------------------------
    sit = collections.Counter(r.get("n2yo_em_orbita", "?") or "?" for r in rec)
    M["situacao"] = [
        {"chave": "ainda em órbita", "linhas": sit.get("sim", 0)},
        {"chave": "reentrou desde 2023", "linhas": sit.get("não", 0)},
        {"chave": "sem elemento orbital publicado", "linhas": sit.get("?", 0)},
    ]
    viv = [r for r in rec if r.get("n2yo_em_orbita") == "sim"]
    M["sobrevivencia"] = {
        "recorte": len(rec), "em_orbita": len(viv),
        "pct": round(100 * len(viv) / len(rec), 1),
        "reentrados": sit.get("não", 0),
    }
    M["situacao_por_recorte"] = [
        {"chave": rot,
         "linhas": sum(1 for r in rec if r[col] == "sim"),
         "em_orbita": sum(1 for r in rec
                          if r[col] == "sim" and r.get("n2yo_em_orbita") == "sim"),
         "reentrou": sum(1 for r in rec
                         if r[col] == "sim" and r.get("n2yo_em_orbita") == "não")}
        for rot, col in (("A — sensoriamento remoto", "sr"),
                         ("B — coleta de plataformas", "dcs_iot"),
                         ("C — sinais cooperativos", "sinais"))]

    # 3. lançamentos por ano ------------------------------------------------
    M["ano"] = sorted(tabela(rec, lambda r: ano(r["data_lancamento"])),
                      key=lambda x: x["chave"])

    # 4. órbita e porte -----------------------------------------------------
    ordem_alt = ["LEO até 400 km", "LEO 400–600 km", "LEO 600–800 km",
                 "LEO 800–1 200 km", "LEO acima de 1 200 km", "MEO",
                 "GEO (~35 786 km)", "elíptica", "não declarada"]
    M["altitude"] = tabela(rec, faixa_alt, ordem=ordem_alt)
    ordem_massa = ["até 10 kg", "10–100 kg", "100–500 kg", "500 kg–1 t",
                   "1–5 t", "acima de 5 t", "não declarada"]
    M["massa"] = tabela(rec, lambda r: faixa_massa(r["massa_lancamento_kg"]),
                        ordem=ordem_massa)
    massas = [num(r["massa_lancamento_kg"]) for r in rec
              if num(r["massa_lancamento_kg"])]
    M["massa_resumo"] = {"n": len(massas), "mediana": statistics.median(massas),
                         "min": min(massas), "max": max(massas)}
    pot = [num(r["potencia_w"]) for r in rec if num(r["potencia_w"])]
    M["potencia_resumo"] = {"n": len(pot), "mediana": statistics.median(pot),
                            "min": min(pot), "max": max(pot)}

    # 5. vida esperada × idade real ----------------------------------------
    vida = []
    for r in viv:
        ve, i = num(r["vida_esperada_anos"]), idade(r["data_lancamento"])
        if ve and i:
            vida.append((r, ve, i))
    alem = [x for x in vida if x[2] > x[1]]
    M["vida"] = {
        "com_vida_declarada": len(vida),
        "alem_da_vida": len(alem),
        "pct": round(100 * len(alem) / len(vida), 1) if vida else 0,
        "mediana_vida": statistics.median([x[1] for x in vida]) if vida else 0,
        "mediana_idade": statistics.median([x[2] for x in vida]) if vida else 0,
    }
    M["vida_lista"] = sorted(
        [{"nome": r["nome"], "norad": r["norad"], "operador": r["operador"],
          "pais": r["pais_operador"], "categoria": r["categoria_coleta"],
          "lancamento": r["data_lancamento"], "vida_prevista": ve,
          "idade": i, "excedente": round(i - ve, 1),
          "url": r.get("n2yo_url", "")}
         for r, ve, i in alem], key=lambda x: -x["excedente"])[:40]

    # 6. quem faz -----------------------------------------------------------
    M["usuarios"] = tabela(rec, lambda r: r["usuarios"] or "não declarado")
    M["pais"] = tabela(rec, lambda r: r["pais_operador"] or "não declarado",
                       limite=15)
    M["operadores"] = tabela(rec, lambda r: r["operador"] or "não declarado",
                             limite=18)
    M["contratantes"] = tabela(rec, lambda r: r["contratante"] or "não declarado",
                               limite=15)
    M["proposito_detalhado"] = tabela(
        rec, lambda r: r["proposito_detalhado"] or "(só o propósito geral)",
        limite=18)
    M["lancadores"] = tabela(rec, lambda r: r["veiculo_lancador"] or
                             "não declarado", limite=12)

    # 7. Brasil -------------------------------------------------------------
    M["brasil"] = [
        {"nome": r["nome"], "norad": r["norad"], "operador": r["operador"],
         "lancamento": r["data_lancamento"], "categoria": r["categoria_coleta"],
         "proposito": r["proposito"], "detalhado": r["proposito_detalhado"],
         "massa": r["massa_lancamento_kg"], "orbita": r["classe_orbita"],
         "em_orbita": r.get("n2yo_em_orbita", ""),
         "idade": idade(r["data_lancamento"]),
         "vida_prevista": r["vida_esperada_anos"],
         "comentario": r["comentarios"], "url": r.get("n2yo_url", "")}
        for r in rec if r["pais_operador"] == "Brazil"]

    # 8. decaimento orbital: 2023 (UCS) × hoje (TLE) ------------------------
    # só quem continua em órbita: para os que reentraram o n2yo guarda o
    # último TLE antes da queda, e comparar com ele mediria a reentrada, não o
    # decaimento de um satélite operando
    dec = [r for r in orb if num(r["delta_perigeu_km"]) is not None
           and r.get("em_orbita") == "sim"]
    quedas = sorted(dec, key=lambda r: num(r["delta_perigeu_km"]))[:25]
    M["decaimento"] = [
        {"nome": r["nome"], "norad": r["norad"], "categoria": r["categoria_coleta"],
         "operador": r["operador"],
         "perigeu_2023": r["perigeu_ucs_km"], "perigeu_hoje": r["perigeu_hoje_km"],
         "delta": r["delta_perigeu_km"], "epoca": r["epoca_tle"]}
        for r in quedas]
    d = [num(r["delta_perigeu_km"]) for r in dec]
    M["decaimento_resumo"] = {
        "n": len(d), "mediana": round(statistics.median(d), 1),
        "caiu": sum(1 for x in d if x < -5), "subiu": sum(1 for x in d if x > 5)}

    # 8a. reentradas: quando caíram os que caíram --------------------------
    mortos = [r for r in rec if r.get("n2yo_em_orbita") == "não"]
    por_ano = collections.Counter(r["n2yo_reentrada"][:4] for r in mortos
                                  if r.get("n2yo_reentrada"))
    M["reentradas_ano"] = [{"chave": k, "linhas": v}
                           for k, v in sorted(por_ano.items())]
    M["reentradas_operador"] = [
        {"chave": k, "linhas": v} for k, v in
        collections.Counter(r["operador"] for r in mortos).most_common(12)]
    antes = [r for r in mortos if r.get("n2yo_reentrada", "") < "2023-05-01"]
    M["reentradas_resumo"] = {
        "total": len(mortos), "com_data": sum(1 for r in mortos
                                              if r.get("n2yo_reentrada")),
        "antes_do_corte": len(antes),
        "idade_mediana": statistics.median(
            [idade(r["data_lancamento"]) - (HOJE - datetime.date(
                *map(int, r["n2yo_reentrada"].split("-")))).days / 365.25
             for r in mortos if r.get("n2yo_reentrada") and
             idade(r["data_lancamento"])]) if mortos else 0}

    # 8b. qualidade do NORAD declarado pela UCS -----------------------------
    tipo = collections.Counter(r.get("n2yo_tipo_objeto") or "sem ficha"
                               for r in rec)
    M["qualidade_norad"] = [{"chave": k, "linhas": v}
                            for k, v in tipo.most_common()]
    M["qualidade_lista"] = [
        {"nome": r["nome"], "norad": r["norad"], "n2yo_nome": r["n2yo_nome"],
         "tipo": r["n2yo_tipo_objeto"], "operador": r["operador"]}
        for r in rec if r.get("n2yo_tipo_objeto") in
        ("corpo de foguete", "detrito")][:30]

    # 9. categorias do n2yo -------------------------------------------------
    catrec = collections.Counter()
    for r in rec:
        for c in filter(None, (r.get("n2yo_categorias") or "").split("; ")):
            catrec[c] += 1
    M["categorias_n2yo"] = [{"chave": k, "linhas": v}
                            for k, v in catrec.most_common(15)]
    M["categorias_n2yo_universo"] = [
        {"chave": k, "linhas": v} for k, v in
        sorted(tam_cat.items(), key=lambda x: -x[1])[:15]]

    # 10. maiores constelações do recorte -----------------------------------
    fam = collections.Counter()
    for r in rec:
        base = re.sub(r"[-\s]*\d+[A-Za-z]?\s*$", "", r["nome"].split("(")[0]).strip()
        fam[base or r["nome"]] += 1
    M["familias"] = []
    for nome, n in fam.most_common(14):
        ex = next(r for r in rec
                  if r["nome"].startswith(nome.split()[0]) if nome)
        M["familias"].append({
            "chave": nome, "linhas": n, "operador": ex["operador"],
            "pais": ex["pais_operador"], "categoria": ex["categoria_coleta"],
            "proposito": ex["proposito_detalhado"] or ex["proposito"]})

    with open(os.path.join(AQUI, "metricas.json"), "w", encoding="utf-8") as f:
        json.dump(M, f, ensure_ascii=False, indent=1)
    print("metricas.json escrito")
    for k, v in M.items():
        print(f"  {k}: {len(v) if isinstance(v, list) else v}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
