#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolida as métricas do recorte de coleta de dados em `metricas.json`.

Lê os CSVs gerados por gerar_tabelas.py e monta tabelas prontas para
apresentação (uma linha por item, já ordenadas e com totais).
"""
import csv
import json
import os
import re
import statistics
import collections

AQUI = os.path.dirname(os.path.abspath(__file__))


def le(nome):
    with open(os.path.join(AQUI, nome), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------- normalizações
def classe(t):
    """Classe de tamanho a partir da coluna 'tipo (U/massa)' do banco."""
    t = (t or "").strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*U", t)
    if m:
        u = float(m.group(1))
        if u <= 1:
            return "1U"
        if u <= 2:
            return "2U"
        if u <= 3:
            return "3U"
        if u <= 6:
            return "6U"
        if u <= 12:
            return "12U"
        if u <= 16:
            return "16U"
        return ">16U"
    if re.search(r"\bp\b|pocketqube", t, re.I):
        return "PocketQube"
    if "kg" in t.lower():
        kg = re.match(r"^([\d.]+)", t)
        if kg:
            v = float(kg.group(1))
            return "<1 kg" if v < 1 else ("1-10 kg" if v <= 10 else ">10 kg")
    return "não declarado"


def status(s):
    s = (s or "").lower()
    if "cancelled" in s:
        return "cancelada"
    if "not launched" in s:
        return "não lançada"
    if "launch failure" in s:
        return "falha no lançamento"
    if "deployment failure" in s:
        return "falha na ejeção"
    if "no signal" in s:
        return "sem sinal após o lançamento"
    if "operational" in s and "was" not in s and "semi" not in s:
        return "operou como previsto"
    if "was operational" in s or "semi-operational" in s:
        return "operou e encerrou"
    return "outro / desconhecido"


def ano(d):
    m = re.match(r"^(\d{4})-", d or "")
    return m.group(1) if m else None


CATS = [("A", "sr_forte"), ("B", "dcs_iot"), ("C", "sinais")]


def cats_da_linha(r):
    return [nome for nome, col in CATS if r[col] == "sim"]


def tabela(linhas, chave, ordem=None, limite=None, contar_fichas=True):
    """Conta linhas e fichas por chave, quebrando em A/B/C."""
    ag = collections.defaultdict(lambda: {"linhas": 0, "fichas": set(),
                                          "A": 0, "B": 0, "C": 0})
    for r in linhas:
        k = chave(r)
        if k is None:
            continue
        a = ag[k]
        a["linhas"] += 1
        a["fichas"].add(r["slug"])
        for c in cats_da_linha(r):
            a[c] += 1
    out = [{"chave": k, "linhas": v["linhas"], "fichas": len(v["fichas"]),
            "A": v["A"], "B": v["B"], "C": v["C"]} for k, v in ag.items()]
    if ordem:
        out.sort(key=lambda x: ordem.index(x["chave"])
                 if x["chave"] in ordem else 999)
    else:
        out.sort(key=lambda x: -x["linhas"])
    return out[:limite] if limite else out


def main():
    todos = le("nanosats_todos.csv")
    recorte = [r for r in todos if r["no_recorte"] == "sim"]
    custos = le("custos_nanosats.csv")
    resultados = le("resultados_nanosats.csv")
    kws = le("keywords_nanosats.csv")
    det = json.load(open(os.path.join(AQUI, "nanosats_coleta_dados.json"),
                         encoding="utf-8"))

    fichas = lambda sel: len({r["slug"] for r in sel})
    M = {}

    # 1. panorama do recorte ------------------------------------------------
    M["panorama"] = [
        {"recorte": "A — sensoriamento remoto (alvo terrestre)",
         "fichas": fichas([r for r in todos if r["sr_forte"] == "sim"]),
         "linhas": sum(1 for r in todos if r["sr_forte"] == "sim")},
        {"recorte": "B — coleta de plataformas no solo (DCS/IoT)",
         "fichas": fichas([r for r in todos if r["dcs_iot"] == "sim"]),
         "linhas": sum(1 for r in todos if r["dcs_iot"] == "sim")},
        {"recorte": "C — sinais cooperativos (AIS/ADS-B/RF)",
         "fichas": fichas([r for r in todos if r["sinais"] == "sim"]),
         "linhas": sum(1 for r in todos if r["sinais"] == "sim")},
        {"recorte": "A′ — câmera sem alvo declarado (fora do recorte)",
         "fichas": fichas([r for r in todos if r["sr_fraco"] == "sim"]),
         "linhas": sum(1 for r in todos if r["sr_fraco"] == "sim")},
        {"recorte": "Recorte de coleta de dados (A ∪ B ∪ C)",
         "fichas": fichas(recorte), "linhas": len(recorte), "destaque": True},
        {"recorte": "Banco inteiro", "fichas": fichas(todos),
         "linhas": len(todos), "destaque": True},
    ]

    # 2. situação das missões ----------------------------------------------
    ordem_status = ["operou como previsto", "operou e encerrou",
                    "sem sinal após o lançamento", "falha no lançamento",
                    "falha na ejeção", "não lançada", "cancelada",
                    "outro / desconhecido"]
    M["status"] = tabela(recorte, lambda r: status(r["status_indice"]),
                         ordem=ordem_status)
    lancadas = [r for r in recorte if ano(r["data_lancamento"])]
    ok = [r for r in lancadas if status(r["status_indice"]) in
          ("operou como previsto", "operou e encerrou")]
    fl = {r["slug"] for r in lancadas}
    fok = {r["slug"] for r in ok}
    M["taxa_sucesso"] = {
        "lancadas": len(lancadas), "funcionaram": len(ok),
        "pct": round(100 * len(ok) / len(lancadas), 1),
        "fichas_lancadas": len(fl), "fichas_ok": len(fok),
        "pct_fichas": round(100 * len(fok) / len(fl), 1)}

    # 3. lançamentos por ano ------------------------------------------------
    M["ano"] = sorted(tabela(recorte, lambda r: ano(r["data_lancamento"])),
                      key=lambda x: x["chave"])

    # 4. classe de tamanho --------------------------------------------------
    ordem_classe = ["PocketQube", "<1 kg", "1U", "2U", "3U", "6U", "12U", "16U",
                    ">16U", "1-10 kg", ">10 kg", "não declarado"]
    M["classe"] = tabela(recorte, lambda r: classe(r["tipo_u_massa"]),
                         ordem=ordem_classe)

    # 5. países e 6. entidades ---------------------------------------------
    M["pais"] = tabela(recorte, lambda r: r["nacao_indice"] or "não declarado",
                       limite=15)
    M["entidade"] = tabela(recorte, lambda r: r["tipo_entidade"] or "não declarado")

    # 7. organizações do recorte -------------------------------------------
    por_ficha = {}
    for r in recorte:
        por_ficha.setdefault(r["slug"], r)
    M["organizacoes"] = tabela(list(por_ficha.values()),
                               lambda r: (r["organizacao"] or
                                          r["organizacao_indice"] or "—"),
                               limite=15)

    # 8. custos -------------------------------------------------------------
    melhor = {}
    for c in custos:
        if not c["valor_num"] or c["valor_suspeito"] == "sim":
            continue
        if c["origem"].startswith("texto livre"):
            continue            # menção solta na descrição, não é custo declarado
        k = c["slug"] or c["missao"]
        if k not in melhor or c["origem"].startswith("tabela"):
            melhor[k] = c
    usd = [c for c in melhor.values() if c["moeda"] == "USD"]
    g = collections.defaultdict(list)
    for c in usd:
        g[classe(c["tamanho"])].append(float(c["valor_num"]))
    M["custo_classe"] = []
    for k in ordem_classe:
        if k in g and len(g[k]) >= 1:
            v = sorted(g[k])
            M["custo_classe"].append({
                "chave": k, "n": len(v),
                "mediana": statistics.median(v), "min": min(v), "max": max(v),
                "recorte": sum(1 for c in usd if classe(c["tamanho"]) == k
                               and c["no_recorte"] == "sim")})
    M["custo_missoes"] = sorted(
        [{"missao": c["missao"], "slug": c["slug"], "classe": c["tamanho"],
          "organizacao": c["organizacao"], "pais": c["pais"],
          "categoria": c["categoria_coleta"], "custo": c["custo"],
          "valor": float(c["valor_num"]) if c["valor_num"] else None,
          "moeda": c["moeda"], "por_satelite": c["custo_por_satelite"],
          "financiador": c["financiador"], "fonte": c["url_fonte"],
          "origem": c["origem"]}
         for c in melhor.values() if c["no_recorte"] == "sim"],
        key=lambda x: (x["moeda"], -(x["valor"] or 0)))

    # 9. resultados e falhas ------------------------------------------------
    res_rec = [r for r in resultados if r["no_recorte"] == "sim"]
    M["resultados"] = {
        "com_resultado": len([r for r in res_rec if r["resultados"]]),
        "com_falha": len([r for r in res_rec if r["causa_falha"]]),
        "total_banco": len([r for r in resultados if r["resultados"]]),
    }
    cf = collections.Counter(categoria_falha(r["causa_falha"])
                             for r in res_rec if r["causa_falha"])
    M["falhas"] = [{"chave": k, "linhas": v} for k, v in cf.most_common()]
    M["resultados_lista"] = [
        {"missao": r["nome"], "slug": r["slug"], "categoria": r["categoria_coleta"],
         "lancamento": r["data_lancamento"], "status": r["status_indice"],
         "resultado": r["resultados"], "falha": r["causa_falha"],
         "links": r["urls_resultados"]}
        for r in res_rec if r["resultados"] or r["causa_falha"]]

    # 10. Brasil ------------------------------------------------------------
    M["brasil"] = [
        {"missao": r["nome"], "slug": r["slug"], "lancamento": r["data_lancamento"],
         "classe": r["tipo_u_massa"], "organizacao": r["organizacao"] or
         r["organizacao_indice"], "categoria": r["categoria_coleta"],
         "status": status(r["status_indice"]), "descricao": r["descricao_indice"]}
        for r in recorte if r["nacao_indice"] == "Brazil"]

    # 11. subsistemas COTS --------------------------------------------------
    forn = collections.Counter()
    tipo_forn = collections.defaultdict(collections.Counter)
    slugs_rec = {r["slug"] for r in recorte}
    for f in det:
        if f["slug"] not in slugs_rec:
            continue
        for item in f.get("listas", {}).get("COTS subsystems", []):
            m = re.match(r"\s*([A-Z/ ]+?)\s*-\s*(.+)", item)
            if not m:
                continue
            tipo, fabricante = m.group(1).strip(), m.group(2).strip()
            fabricante = re.split(r"\s+(?:NanoPower|NanoCam|with|\()", fabricante)[0]
            fabricante = canon_fornecedor(fabricante.strip(" .,"))
            if not fabricante or len(fabricante) > 40:
                continue
            forn[fabricante] += 1
            tipo_forn[tipo][fabricante] += 1
    M["cots_fornecedores"] = [{"chave": k, "linhas": v} for k, v in forn.most_common(15)]
    M["cots_por_subsistema"] = [
        {"chave": t, "total": sum(c.values()),
         "principais": ", ".join(f"{n} ({q})" for n, q in c.most_common(3))}
        for t, c in sorted(tipo_forn.items(), key=lambda x: -sum(x[1].values()))[:12]]

    # 12. palavras-chave do site -------------------------------------------
    kr = [k for k in kws if k["no_recorte"] == "sim"]
    limpa_kw = lambda k: re.sub(r"^CubeSats with keyword:\s*", "", k)
    M["keywords"] = [{"chave": limpa_kw(k), "linhas": v} for k, v in
                     collections.Counter(x["keyword"] for x in kr).most_common(15)]

    # 13. maiores constelações do recorte ----------------------------------
    cont = collections.Counter(r["slug"] for r in recorte)
    M["constelacoes"] = []
    for slug, n in cont.most_common(12):
        r = por_ficha[slug]
        M["constelacoes"].append({
            "chave": r["nome"].split(" ")[0] if n > 1 else r["nome"],
            "ficha": slug, "linhas": n,
            "organizacao": r["organizacao"] or r["organizacao_indice"],
            "pais": r["nacao_indice"], "categoria": r["categoria_coleta"],
            "descricao": r["descricao_indice"]})

    with open(os.path.join(AQUI, "metricas.json"), "w", encoding="utf-8") as f:
        json.dump(M, f, ensure_ascii=False, indent=1)
    print("metricas.json escrito")
    for k, v in M.items():
        print(f"  {k}: {len(v) if isinstance(v, list) else v}")


CANONICOS = ["AAC Clyde Space", "Clyde Space", "GomSpace", "NanoAvionics",
             "ISISpace", "ISIS", "Blue Canyon", "EnduroSat", "Sputnix", "Tyvak",
             "Bright Ascension", "Space Inventor", "Open Cosmos", "Pumpkin",
             "CubeSpace", "Hyperion", "Satlantis", "Simera Sense", "Kubos",
             "Berlin Space Technologies", "Dragonfly", "AAC", "DHV", "Adcole",
             "MMA Design", "SCS", "ThrustMe", "Accion", "Nanoavionics"]


def canon_fornecedor(nome):
    """'Clyde Space 40Wh', 'ISIS' e 'AAC Clyde Space' viram o mesmo fornecedor."""
    for c in CANONICOS:
        if nome.lower().startswith(c.lower()):
            nome = c
            break
    return {"AAC Clyde Space": "Clyde Space", "ISIS": "ISISpace",
            "AAC": "Clyde Space", "Nanoavionics": "NanoAvionics"}.get(nome, nome)


FALHAS = [
    ("energia / baterias", r"batter|power|solar (?:panel|cell)|EPS\b|charg"),
    ("comunicação / antena", r"antenna|transmit|receiv|radio|communicat|uplink|downlink|beacon|signal"),
    ("controle de atitude", r"attitude|ADCS|tumbl|spin|magnetorquer|reaction wheel|pointing"),
    ("software / computador", r"software|firmware|OBC|computer|watchdog|reset|memory|bug"),
    ("ejeção / lançamento", r"deploy|launch|separat|rocket|dispenser"),
    ("reentrada precoce", r"re-?entr|decay|orbit lifetime|低"),
    ("desconhecida", r"unknown|unclear|not known|no information"),
]


def categoria_falha(txt):
    for rot, rx in FALHAS:
        if re.search(rx, txt or "", re.I):
            return rot
    return "outra / não classificada"


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
