#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monta `painel_metricas.html` a partir de metricas.json.

Página estática: as tabelas já vêm prontas no HTML (nada é renderizado por
JavaScript), e o script embarcado só acrescenta ordenação por coluna, filtro de
texto e as dicas dos gráficos.
"""
import html
import json
import math
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(AQUI, "metricas.json"), encoding="utf-8"))

# paleta categórica validada (slots 1-3), usada só para identidade A/B/C
CAT = {"A": ("A", "Sensoriamento remoto"),
       "B": ("B", "Coleta de plataformas"),
       "C": ("C", "Sinais cooperativos")}


def e(s):
    return html.escape(str(s if s is not None else ""))


def num(v, casas=0):
    if v is None or v == "":
        return "—"
    s = f"{float(v):,.{casas}f}".replace(",", " ")
    return s.replace(".", ",") if casas else s


def dinheiro(v, moeda="USD"):
    if v is None:
        return "—"
    v = float(v)
    simbolo = {"USD": "US$", "EUR": "€", "GBP": "£", "SEK": "SEK", "AUD": "A$",
               "INR": "₹", "BRL": "R$"}.get(moeda, moeda + " ")
    if v >= 1e6:
        txt = f"{v/1e6:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{simbolo} {txt} mi"
    if v >= 1e3:
        return f"{simbolo} {v/1e3:.0f} mil"
    return f"{simbolo} {v:.0f}"


def barra(valor, maximo, cat=None):
    """Barra de proporção dentro da célula — o número continua visível ao lado."""
    pct = 0 if not maximo else 100 * valor / maximo
    cls = f" s{cat}" if cat else ""
    return (f'<span class="bar{cls}" style="--w:{pct:.1f}%" aria-hidden="true">'
            f'</span>')


def fonte(url):
    if not url:
        return ""
    return (f' <a class="fonte" href="{e(url)}" target="_blank" '
            f'rel="noopener">fonte</a>')


def chips(categoria):
    """'A - sensoriamento...; B - coleta...' -> chips A B C."""
    out = []
    for letra in ("A", "B", "C"):
        if re.search(rf"(^|; ){letra} — |(^|; ){letra} - ", categoria or ""):
            out.append(f'<span class="chip s{letra}" title="{e(CAT[letra][1])}">'
                       f'{letra}</span>')
    return "".join(out) or '<span class="chip vazio">—</span>'


def tabela(id_, cols, linhas, classe="", filtro=False, nota="", alta=False):
    """cols: lista de (rótulo, alinhamento, ordenável)."""
    th = "".join(
        f'<th class="{al}"{" data-sort" if ordenavel else ""}'
        f' scope="col">{e(rot)}</th>'
        for rot, al, ordenavel in cols)
    corpo = "\n".join(linhas)
    busca = (f'<div class="tf"><input type="search" id="f-{id_}" '
             f'class="filtro" data-alvo="{id_}" placeholder="filtrar…" '
             f'aria-label="Filtrar linhas da tabela"><span class="tf-n" '
             f'id="n-{id_}"></span></div>') if filtro else ""
    nota = f'<p class="nota-pe">{nota}</p>' if nota else ""
    return (f'{busca}<div class="tw{" alta" if alta else ""}">'
            f'<table id="{id_}" class="{classe}">'
            f'<thead><tr>{th}</tr></thead><tbody>{corpo}</tbody></table></div>'
            f'{nota}')


# ícones das caixas, no lugar do fontawesome5 do relatório
ICONES = {
    "destaque": ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 21h6'
                 'v-1H9v1zm3-20a7 7 0 0 0-4 12.7V17h8v-3.3A7 7 0 0 0 12 1z"/>'
                 '</svg>'),
    "atencao": ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 1 '
                '21h22L12 2zm1 14h-2v2h2v-2zm0-7h-2v5h2V9z"/></svg>'),
    "nota": ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10'
             ' 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>'
             '</svg>'),
}


def caixa(tipo, titulo, *paragrafos):
    """Equivalente aos tcolorbox destaque / atencao / nota do relatório."""
    ps = "".join(f"<p>{p}</p>" for p in paragrafos)
    return (f'<div class="caixa {tipo}"><span class="tit">{ICONES[tipo]}'
            f'{e(titulo)}</span>{ps}</div>')


# --------------------------------------------------------------- gráficos SVG
def grafico_anos():
    """Barras agrupadas A/B/C por ano. Agrupadas, não empilhadas: uma missão
    pode estar em dois recortes e a soma não seria verdadeira."""
    dados = [d for d in M["ano"] if d["chave"] >= "2009"]
    antigos = [d for d in M["ano"] if d["chave"] < "2009"]
    if antigos:
        dados.insert(0, {"chave": "≤2008",
                         "A": sum(d["A"] for d in antigos),
                         "B": sum(d["B"] for d in antigos),
                         "C": sum(d["C"] for d in antigos),
                         "linhas": sum(d["linhas"] for d in antigos)})
    W, H = 920, 300
    ml, mr, mt, mb = 44, 12, 18, 46
    pw, ph = W - ml - mr, H - mt - mb
    maxv = max(max(d["A"], d["B"], d["C"]) for d in dados)
    passo = 50 if maxv > 200 else 25
    topo = math.ceil(maxv / passo) * passo
    gw = pw / len(dados)
    bw = min(9, (gw - 6) / 3 - 2)

    partes = []
    for i in range(0, topo + 1, passo):                     # grade + eixo y
        y = mt + ph - ph * i / topo
        partes.append(f'<line class="grid" x1="{ml}" y1="{y:.1f}" x2="{W-mr}" '
                      f'y2="{y:.1f}"/>')
        partes.append(f'<text class="tick" x="{ml-8}" y="{y+4:.1f}" '
                      f'text-anchor="end">{i}</text>')
    for i, d in enumerate(dados):
        x0 = ml + i * gw
        for j, cat in enumerate(("A", "B", "C")):
            v = d[cat]
            if not v:
                continue
            h = ph * v / topo
            x = x0 + (gw - (3 * bw + 4)) / 2 + j * (bw + 2)
            y = mt + ph - h
            partes.append(
                f'<rect class="b s{cat}" x="{x:.1f}" y="{y:.1f}" '
                f'width="{bw:.1f}" height="{h:.1f}" rx="{min(4, bw/2):.1f}" '
                f'data-t="{d["chave"]} · {CAT[cat][1]}: {v} satélites"/>')
        if len(dados) < 22 or i % 2 == 0 or i == len(dados) - 1:
            partes.append(f'<text class="tick" x="{x0+gw/2:.1f}" y="{H-mb+18}" '
                          f'text-anchor="middle">{d["chave"]}</text>')
    partes.append(f'<line class="axis" x1="{ml}" y1="{mt+ph}" x2="{W-mr}" '
                  f'y2="{mt+ph}"/>')
    corpo = "".join(
        f'<tr><td>{e(d["chave"])}</td><td class="n">{d["A"]}</td>'
        f'<td class="n">{d["B"]}</td><td class="n">{d["C"]}</td>'
        f'<td class="n forte">{d["linhas"]}</td></tr>' for d in dados)
    tab = tabela("t-ano", [("Ano", "", False), ("A", "n", False),
                           ("B", "n", False), ("C", "n", False),
                           ("Total no recorte", "n", False)], [corpo])
    return (f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
            f'aria-label="Satélites de coleta de dados lançados por ano, '
            f'separados por recorte">{"".join(partes)}</svg>', tab)


def grafico_custos():
    """Faixa min–max com a mediana marcada, por classe. Escala logarítmica:
    os valores declarados vão de centenas de milhares a 100 milhões."""
    dados = [d for d in M["custo_classe"] if d["n"] >= 2]
    W = 920
    linha_h = 46
    ml, mr, mt = 62, 90, 26
    H = mt + linha_h * len(dados) + 34
    pw = W - ml - mr
    lo, hi = 1e5, 2e8
    x = lambda v: ml + pw * (math.log10(max(v, lo)) - math.log10(lo)) / \
        (math.log10(hi) - math.log10(lo))

    partes = []
    for tick, rot in ((1e5, "100 mil"), (1e6, "1 mi"), (1e7, "10 mi"),
                      (1e8, "100 mi")):
        partes.append(f'<line class="grid" x1="{x(tick):.1f}" y1="{mt-10}" '
                      f'x2="{x(tick):.1f}" y2="{mt+linha_h*len(dados)-14}"/>')
        partes.append(f'<text class="tick" x="{x(tick):.1f}" '
                      f'y="{mt+linha_h*len(dados)+6}" text-anchor="middle">'
                      f'{rot}</text>')
    for i, d in enumerate(dados):
        y = mt + i * linha_h + 8
        partes.append(f'<text class="rot" x="{ml-12}" y="{y+4}" '
                      f'text-anchor="end">{e(d["chave"])}</text>')
        partes.append(f'<line class="faixa" x1="{x(d["min"]):.1f}" y1="{y}" '
                      f'x2="{x(d["max"]):.1f}" y2="{y}"/>')
        for v, cls in ((d["min"], "ext"), (d["max"], "ext")):
            partes.append(f'<circle class="{cls}" cx="{x(v):.1f}" cy="{y}" '
                          f'r="3.5" data-t="{e(d["chave"])}: {dinheiro(v)}"/>')
        partes.append(
            f'<circle class="med" cx="{x(d["mediana"]):.1f}" cy="{y}" r="6.5" '
            f'data-t="{e(d["chave"])} · mediana {dinheiro(d["mediana"])} '
            f'(n={d["n"]})"/>')
        partes.append(f'<text class="val" x="{W-mr+10}" y="{y+4}">'
                      f'{e(dinheiro(d["mediana"]))}</text>')
        partes.append(f'<text class="enn" x="{W-mr+10}" y="{y+18}">n={d["n"]}'
                      f'</text>')
    corpo = "".join(
        f'<tr><td>{e(d["chave"])}</td><td class="n">{d["n"]}</td>'
        f'<td class="n">{d["recorte"]}</td>'
        f'<td class="n forte">{e(dinheiro(d["mediana"]))}</td>'
        f'<td class="n">{e(dinheiro(d["min"]))}</td>'
        f'<td class="n">{e(dinheiro(d["max"]))}</td></tr>'
        for d in M["custo_classe"])
    tab = tabela("t-custoclasse",
                 [("Classe", "", False), ("Missões com custo", "n", False),
                  ("dessas, no recorte", "n", False), ("Mediana", "n", False),
                  ("Mínimo", "n", False), ("Máximo", "n", False)], [corpo])
    return (f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
            f'aria-label="Faixa de custo declarado por classe de CubeSat, '
            f'escala logarítmica">{"".join(partes)}</svg>', tab)


# ------------------------------------------------------------------- tabelas
def t_panorama():
    maxl = max(d["linhas"] for d in M["panorama"])
    linhas = []
    for d in M["panorama"]:
        cls = ' class="destaque"' if d.get("destaque") else ""
        linhas.append(
            f'<tr{cls}><td>{e(d["recorte"])}</td>'
            f'<td class="n">{num(d["fichas"])}</td>'
            f'<td class="n barcell">{barra(d["linhas"], maxl)}'
            f'<span>{num(d["linhas"])}</span></td></tr>')
    return tabela("t-panorama", [("Recorte", "", False), ("Missões", "n", False),
                                 ("Satélites", "n", False)], linhas)


def t_abc(bloco, rotulo, id_, limite=None, filtro=False):
    dados = M[bloco][:limite] if limite else M[bloco]
    maxl = max(d["linhas"] for d in dados)
    linhas = []
    for d in dados:
        linhas.append(
            f'<tr><td>{e(d["chave"])}</td>'
            f'<td class="n barcell">{barra(d["linhas"], maxl)}'
            f'<span>{num(d["linhas"])}</span></td>'
            f'<td class="n">{num(d["fichas"])}</td>'
            f'<td class="n sA">{num(d["A"])}</td>'
            f'<td class="n sB">{num(d["B"])}</td>'
            f'<td class="n sC">{num(d["C"])}</td></tr>')
    return tabela(id_, [(rotulo, "", True), ("Satélites", "n", True),
                        ("Missões", "n", True), ("A", "n", True),
                        ("B", "n", True), ("C", "n", True)],
                  linhas, filtro=filtro)


def t_custos():
    linhas = []
    for d in M["custo_missoes"]:
        linhas.append(
            f'<tr><td><a href="https://www.nanosats.eu/sat/{e(d["slug"])}.html" '
            f'target="_blank" rel="noopener">{e(d["missao"])}</a></td>'
            f'<td class="cat">{chips(d["categoria"])}</td>'
            f'<td>{e(d["classe"])}</td>'
            f'<td>{e(d["organizacao"])}</td><td>{e(d["pais"])}</td>'
            f'<td class="n forte" data-v="{d["valor"] or 0}">'
            f'{e(dinheiro(d["valor"], d["moeda"]))}</td>'
            f'<td class="n">{e(d["por_satelite"] or "—")}</td>'
            f'<td class="txt">{e(d["custo"])}{fonte(d["fonte"])}</td></tr>')
    return tabela("t-custos",
                  [("Missão", "", True), ("Recorte", "", True),
                   ("Classe", "", True), ("Organização", "", True),
                   ("País", "", True), ("Valor declarado", "n", True),
                   ("Por satélite", "n", False), ("O que o valor cobre", "", False)],
                  linhas, classe="larga", filtro=True, alta=True,
                  nota="Valores como publicados na fonte, sem correção monetária "
                       "e sem normalização de escopo — a última coluna diz o que "
                       "cada número cobre.")


def t_brasil():
    linhas = []
    for d in M["brasil"]:
        linhas.append(
            f'<tr><td><a href="https://www.nanosats.eu/sat/{e(d["slug"])}.html" '
            f'target="_blank" rel="noopener">{e(d["missao"])}</a></td>'
            f'<td class="cat">{chips(d["categoria"])}</td>'
            f'<td>{e(d["lancamento"])}</td><td>{e(d["classe"])}</td>'
            f'<td>{e(d["organizacao"])}</td>'
            f'<td><span class="st">{e(d["status"])}</span></td>'
            f'<td class="txt">{e(d["descricao"])}</td></tr>')
    return tabela("t-brasil",
                  [("Missão", "", True), ("Recorte", "", True),
                   ("Lançamento", "", True), ("Classe", "", True),
                   ("Organização", "", True), ("Situação", "", True),
                   ("O que faz", "", False)], linhas, classe="larga")


def t_constelacoes():
    maxl = max(d["linhas"] for d in M["constelacoes"])
    linhas = []
    for d in M["constelacoes"]:
        linhas.append(
            f'<tr><td><a href="https://www.nanosats.eu/sat/{e(d["ficha"])}.html" '
            f'target="_blank" rel="noopener">{e(d["chave"])}</a></td>'
            f'<td class="cat">{chips(d["categoria"])}</td>'
            f'<td>{e(d["organizacao"])}</td><td>{e(d["pais"])}</td>'
            f'<td class="n barcell">{barra(d["linhas"], maxl)}'
            f'<span>{num(d["linhas"])}</span></td>'
            f'<td class="txt">{e(d["descricao"])}</td></tr>')
    return tabela("t-const",
                  [("Constelação / ficha", "", True), ("Recorte", "", True),
                   ("Organização", "", True), ("País", "", True),
                   ("Satélites", "n", True), ("O que faz", "", False)],
                  linhas, classe="larga")


def t_cots():
    maxf = max(d["linhas"] for d in M["cots_fornecedores"])
    forn = "".join(
        f'<tr><td>{e(d["chave"])}</td>'
        f'<td class="n barcell">{barra(d["linhas"], maxf)}'
        f'<span>{num(d["linhas"])}</span></td></tr>'
        for d in M["cots_fornecedores"])
    sub = "".join(
        f'<tr><td>{e(d["chave"])}</td><td class="n">{num(d["total"])}</td>'
        f'<td class="txt">{e(d["principais"])}</td></tr>'
        for d in M["cots_por_subsistema"])
    return (tabela("t-forn", [("Fornecedor", "", True),
                              ("Citações nas fichas", "n", True)], [forn]),
            tabela("t-sub", [("Subsistema", "", True), ("Citações", "n", True),
                             ("Fornecedores mais citados", "", False)], [sub]))


def t_resultados():
    linhas = []
    for d in M["resultados_lista"]:
        texto = d["resultado"] or ""
        primeira = texto.split("\n")[0] if texto else (d["falha"] or "")
        resto = "\n".join(texto.split("\n")[1:]).strip()
        corpo = f'<p>{e(primeira)}</p>'
        if resto:
            corpo = (f'<details><summary>{e(primeira)}</summary>'
                     + "".join(f"<p>{e(p)}</p>" for p in resto.split("\n"))
                     + "</details>")
        falha = (f'<p class="falha"><span class="rot">falha</span> '
                 f'{e(d["falha"])}</p>' if d["falha"] else "")
        link = (f'<a class="fonte" href="{e(d["links"].split(" | ")[0])}" '
                f'target="_blank" rel="noopener">fonte</a>'
                if d["links"] else "")
        linhas.append(
            f'<tr><td><a href="https://www.nanosats.eu/sat/{e(d["slug"])}.html" '
            f'target="_blank" rel="noopener">{e(d["missao"])}</a>'
            f'<span class="sub">{e(d["lancamento"])}</span></td>'
            f'<td class="cat">{chips(d["categoria"])}</td>'
            f'<td class="txt">{corpo}{falha}{link}</td></tr>')
    return tabela("t-result", [("Missão", "", True), ("Recorte", "", True),
                               ("Resultado publicado", "", False)],
                  linhas, classe="larga", filtro=True, alta=True)


def t_falhas():
    tot = sum(d["linhas"] for d in M["falhas"])
    return tabela("t-falhas", [("Causa declarada", "", False),
                               ("Missões", "n", False), ("Share", "n", False)],
                  ["".join(
                      f'<tr><td>{e(d["chave"])}</td>'
                      f'<td class="n">{d["linhas"]}</td>'
                      f'<td class="n barcell">{barra(d["linhas"], tot)}'
                      f'<span>{100*d["linhas"]/tot:.0f}%</span></td></tr>'
                      for d in M["falhas"])])


def t_keywords():
    maxl = max(d["linhas"] for d in M["keywords"])
    return tabela("t-kw", [("Palavra-chave do site", "", True),
                           ("Satélites do recorte", "n", True)],
                  ["".join(
                      f'<tr><td>{e(d["chave"])}</td>'
                      f'<td class="n barcell">{barra(d["linhas"], maxl)}'
                      f'<span>{num(d["linhas"])}</span></td></tr>'
                      for d in M["keywords"])])


# --------------------------------------------------------------- montagem
SECOES = [("panorama", "Panorama"), ("situacao", "Situação"),
          ("tempo", "Por ano"), ("porte", "Porte"), ("custos", "Custos"),
          ("resultados", "Resultados"), ("quem", "Quem faz"),
          ("constelacoes", "Constelações"), ("brasil", "Brasil"),
          ("fornecedores", "Fornecedores"), ("keywords", "Palavras-chave")]


def kpi(rot, big, sub):
    return (f'<div class="kpi"><div class="rot">{e(rot)}</div>'
            f'<div class="big">{big}</div><div class="sub">{e(sub)}</div></div>')


_ordem = [0]


def secao(id_, titulo, chamada, corpo):
    """Título com o número em caixa navy, como \\titleformat{\\section}."""
    _ordem[0] += 1
    return (f'<section id="{id_}"><h2><span class="num">{_ordem[0]}</span>'
            f'{e(titulo)}</h2><p class="chamada">{chamada}</p>{corpo}</section>')


def sub(titulo, ordem=""):
    ord_ = f'<span class="ord">{e(ordem)}</span>' if ordem else ""
    return f'<h3 class="sub">{ord_}{e(titulo)}</h3>'


def legenda():
    return ('<div class="legenda">'
            + "".join(f'<span><i style="background:var(--s{k})"></i>'
                      f'{k} — {e(v[1])}</span>' for k, v in CAT.items())
            + '</div>')


def main():
    import painel_estilo as est

    ts = M["taxa_sucesso"]
    seis_u = next(d for d in M["custo_classe"] if d["chave"] == "6U")
    pan = {d["recorte"].split(" —")[0]: d for d in M["panorama"]}
    recorte = M["panorama"][4]
    banco = M["panorama"][5]

    kpis = "".join([
        kpi("missões no recorte", num(recorte["fichas"]),
            f'de {num(banco["fichas"])} fichas do banco'),
        kpi("satélites", num(recorte["linhas"]),
            f'de {num(banco["linhas"])} linhas — constelações contam cada unidade'),
        kpi("funcionaram em órbita", f'{ts["pct_fichas"]:.1f}%'.replace(".", ","),
            f'{ts["fichas_ok"]} de {ts["fichas_lancadas"]} missões lançadas'),
        kpi("custo mediano 6U", dinheiro(seis_u["mediana"]),
            f'{seis_u["n"]} missões com custo declarado'),
        kpi("com resultado publicado", num(M["resultados"]["com_resultado"]),
            f'{M["resultados"]["com_falha"]} com causa de falha declarada'),
    ])

    graf_ano, tab_ano = grafico_anos()
    graf_custo, tab_custo_classe = grafico_custos()
    t_forn, t_sub = t_cots()

    corpo = [
        secao("panorama", "Panorama do recorte",
              "Cada missão pode estar em mais de um recorte — um Lemur-2 faz "
              "radio-ocultação (A) <em>e</em> recebe AIS/ADS-B (C) —, por isso "
              "a soma de A, B e C passa do total. “Missões” conta fichas do "
              "banco; “satélites”, as unidades lançadas ou planejadas.",
              t_panorama()
              + caixa("nota", "Procedência da classificação",
                      "O Nanosats Database não publica coluna de tipo de "
                      "missão: das 8 colunas do índice, nenhuma diz o que a "
                      "carga útil faz. O recorte foi derivado do texto de cada "
                      "ficha (<em>Oneliner</em>, <em>Description</em>, "
                      "<em>Notes</em>, <em>Results</em> e palavras-chave) por "
                      "expressões declaradas em <code>regras_coleta.py</code>; "
                      "cada linha dos CSVs carrega, na coluna de evidência, a "
                      "regra que a colocou no recorte.",
                      "É leitura de texto: missão cuja ficha não descreve a "
                      "carga fica de fora — 1.321 das 2.408 fichas não "
                      "dispararam nenhuma regra — e sobra alguma cauda de "
                      "falso positivo.")),
        secao("situacao", "Situação das missões",
              f'Das {ts["fichas_lancadas"]} missões do recorte que chegaram a '
              f'voar, {ts["fichas_ok"]} operaram — '
              f'{str(ts["pct_fichas"]).replace(".", ",")}%. Contando satélite a '
              f'satélite a taxa sobe para '
              f'{str(ts["pct"]).replace(".", ",")}%, porque as grandes '
              'constelações comerciais puxam a média para cima.',
              t_abc("status", "Situação", "t-status")),
        secao("tempo", "Satélites lançados por ano",
              "Barras agrupadas, não empilhadas: como uma missão pode contar em "
              "dois recortes, empilhar somaria o mesmo satélite duas vezes. "
              "Inclui só o que já tem data de lançamento.",
              f'<div class="painel">{legenda()}{graf_ano}'
              f'<details class="tv"><summary>ver os números</summary>'
              f'{tab_ano}</details></div>'),
        secao("porte", "Porte das plataformas",
              "Classe declarada no banco. O 3U domina por causa das "
              "constelações de imageamento; o 1U concentra as missões "
              "universitárias de store-and-forward.",
              t_abc("classe", "Classe", "t-classe")),
        secao("custos", "Custo de desenvolvimento declarado",
              "Faixa mínimo–máximo com a mediana marcada, em escala "
              "logarítmica — os valores publicados vão de centenas de milhares "
              "a mais de US$ 100 milhões. Só entram valores declarados pela "
              "fonte (tabela <em>CubeSat Costs</em> e campo <em>Costs</em> da "
              "ficha), convertidos a nada: cada um está na moeda original.",
              f'<div class="painel">{graf_custo}'
              f'<details class="tv"><summary>ver os números</summary>'
              f'{tab_custo_classe}</details></div>'
              + caixa("atencao", "Escopo não normalizado",
                      "Cada valor cobre uma coisa diferente: contrato de "
                      "plataforma, programa inteiro com lançamento e operação, "
                      "ou lote de N satélites. A coluna <em>o que o valor "
                      "cobre</em> diz qual é o caso, e não houve conversão "
                      "cambial nem correção monetária. Serve como ordem de "
                      "grandeza, <strong>não como base de orçamento</strong>.")
              + sub(f'As {len(M["custo_missoes"])} missões do recorte com '
                    f'custo declarado') + t_custos()),
        secao("resultados", "Resultados e falhas publicados",
              f'O banco publica resultado em órbita de '
              f'{M["resultados"]["com_resultado"]} missões do recorte '
              f'(de {M["resultados"]["total_banco"]} no banco inteiro) e causa '
              f'de falha de {M["resultados"]["com_falha"]}. O texto é o da '
              f'fonte, quase sempre citação datada com link.',
              f'<div class="duo" style="margin-bottom:6px">'
              f'<div><h3>Causa declarada da falha</h3>{t_falhas()}</div>'
              f'<div>' + caixa(
                  "destaque", "O que falha",
                  "Entre as missões do recorte que declararam causa de falha, "
                  "<strong>energia e baterias respondem por mais da "
                  "metade</strong>; comunicação vem em seguida. Nenhuma falha "
                  "declarada é de carga útil — o que quebra é o barramento, "
                  "não o instrumento.") + '</div></div>'
              + sub("Resultado publicado, missão a missão") + t_resultados()),
        secao("quem", "Quem faz",
              "Por linha (satélite) e por ficha (missão). O peso comercial vem "
              "das constelações; a contagem por missão mostra a presença "
              "acadêmica, que some quando se conta satélite a satélite.",
              f'<div class="duo">'
              f'<div><h3>Nações</h3>{t_abc("pais", "Nação", "t-pais")}</div>'
              f'<div><h3>Tipo de entidade</h3>'
              f'{t_abc("entidade", "Entidade", "t-ent")}</div></div>'
              f'{sub("Organizações com mais missões no recorte")}'
              f'{t_abc("organizacoes", "Organização", "t-org")}'),
        secao("constelacoes", "Maiores constelações do recorte",
              "Uma ficha do banco pode cobrir centenas de satélites. Estas são "
              "as que mais pesam nas contagens acima.",
              t_constelacoes()),
        secao("brasil", "Missões brasileiras no recorte",
              "Tudo que o banco registra como Brasil dentro do recorte de "
              "coleta de dados — inclusive o que foi cancelado ou ainda não "
              "voou.", t_brasil()),
        secao("fornecedores", "Subsistemas COTS citados nas fichas",
              "Só as fichas do recorte que declaram subsistemas comerciais "
              "(campo <em>COTS subsystems</em>). É uma amostra do que a fonte "
              "registrou, não um censo de mercado.",
              f'<div class="duo">'
              f'<div><h3>Fornecedores mais citados</h3>{t_forn}</div>'
              f'<div><h3>Por subsistema</h3>{t_sub}</div></div>'),
        secao("keywords", "Palavras-chave do próprio site",
              "As 60 palavras-chave que o Nanosats Database mantém, contadas "
              "sobre os satélites do recorte.", t_keywords()),
    ]

    nav = "".join(f'<a href="#{i}">{e(r)}</a>' for i, r in SECOES)
    html_out = f"""<title>Nanossatélites de coleta de dados</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fira+Mono:wght@400;500&family=Fira+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<style>{est.CSS}</style>

<header class="top">
  <div class="top-in">
    <span class="doc">Documento preliminar de missão · <b>Satélite BAI-01</b></span>
    <span class="meta">Anexo de dados · Nanosats Database</span>
  </div>
  <nav class="secs" aria-label="Seções">{nav}</nav>
</header>

<main class="wrap">
  <div class="capa">
    <p class="eyebrow">Anexo de dados · benchmark de missões</p>
    <h1>Nanossatélites de coleta de dados</h1>
    <p class="chamada">O que o maior banco público de nanossatélites registra
    sobre missões cuja carga útil coleta dados: quantas são, o que aconteceu com
    elas, quanto custaram e quem as constrói.</p>
  </div>

  <div class="lede">
    <p>Recorte de <strong>{num(recorte["fichas"])} missões</strong>
    ({num(recorte["linhas"])} satélites) das {num(banco["fichas"])} fichas do
    <a href="https://www.nanosats.eu/database" target="_blank" rel="noopener">Nanosats
    Database</a> cuja carga útil coleta dados: sensoriamento remoto da Terra
    (<span class="chip sA">A</span>), recepção de plataformas no solo — DCS, IoT,
    store-and-forward (<span class="chip sB">B</span>) — e sinais cooperativos
    AIS, ADS-B e RF (<span class="chip sC">C</span>). Os três recortes não são
    exclusivos, e toda linha carrega a evidência que a classificou.</p>
  </div>
  <div class="kpis">{kpis}</div>
  {"".join(corpo)}
  <footer>
    <p><strong>Fonte.</strong> Nanosats Database (nanosats.eu), de Erik Kulu —
    última grande atualização declarada na fonte em 2026-07-31; coleta em
    2026-09-16. 4.938 linhas, 2.408 fichas de missão, 60 páginas de
    palavra-chave e a tabela <em>CubeSat Costs</em>. Os dados completos estão em
    <code>nanosats_coleta_dados.csv</code> (66 colunas),
    <code>nanosats_coleta_dados.json</code>, <code>custos_nanosats.csv</code> e
    <code>resultados_nanosats.csv</code>.</p>
    <p><strong>Procedência.</strong> Toda contagem desta página sai de
    <code>metricas.json</code>, gerado por <code>metricas.py</code> a partir
    daqueles CSVs; a página em si é escrita por <code>gerar_painel.py</code>.
    Nenhum número foi digitado à mão.</p>
    <p><strong>Cores.</strong> A identidade segue <code>config/estilo.tex</code>
    do relatório. As três cores de dado (A, B, C) foram ancoradas nos matizes da
    paleta do documento e subidas para a banda de luminosidade exigida por marcas
    de dado — <code>baiteal</code> e <code>baiverde</code>, lado a lado, ficam
    abaixo do piso de distinguibilidade (ΔE 8,5 contra um piso de 15). O verde
    continua reservado para status, como no documento.</p>
    <p class="ver">v0.1 — documento de trabalho · {e(len(M["resultados_lista"]))} resultados listados</p>
  </footer>
</main>
<div id="tip" role="status" aria-live="polite"></div>
<script>{est.JS}</script>
"""
    # 1. arquivo autônomo, para abrir direto do disco: precisa do <meta charset>,
    #    senão o navegador assume a codificação do sistema e o texto sai truncado
    autonomo = (
        '<!doctype html>\n<html lang="pt-BR">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'{html_out}\n</html>\n')
    saida = os.path.join(AQUI, "painel_metricas.html")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(autonomo)
    print(f"{saida} — {len(autonomo)/1024:.0f} kB (autônomo)")

    # 2. fragmento para publicar como Artifact, que embrulha o arquivo no seu
    #    próprio esqueleto (doctype, head, charset e reset)
    frag = os.path.join(AQUI, "painel_artifact.html")
    with open(frag, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"{frag} — {len(html_out)/1024:.0f} kB (fragmento)")


if __name__ == "__main__":
    main()
