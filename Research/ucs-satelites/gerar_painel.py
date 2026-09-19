#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monta `painel_metricas.html` (e o fragmento para Artifact) a partir de
`metricas.json`, na mesma identidade visual do relatório do BAI-01.

Página estática: as tabelas já vêm prontas no HTML; o script embarcado só
acrescenta ordenação por coluna, filtro de texto e as dicas dos gráficos.
"""
import csv
import html
import json
import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(AQUI, "metricas.json"), encoding="utf-8"))

CAT = {"A": "Sensoriamento remoto", "B": "Coleta de plataformas",
       "C": "Sinais cooperativos"}


def e(s):
    return html.escape(str(s if s is not None else ""))


def num(v, casas=0):
    if v is None or v == "":
        return "—"
    s = f"{float(v):,.{casas}f}".replace(",", " ")
    return s.replace(".", ",") if casas else s


def barra(valor, maximo, cat=None):
    pct = 0 if not maximo else 100 * valor / maximo
    return (f'<span class="bar{f" s{cat}" if cat else ""}" '
            f'style="--w:{pct:.1f}%" aria-hidden="true"></span>')


def chips(categoria):
    out = []
    for letra in ("A", "B", "C"):
        if re.search(rf"(^|; ){letra} — ", categoria or ""):
            out.append(f'<span class="chip s{letra}" title="{e(CAT[letra])}">'
                       f'{letra}</span>')
    return "".join(out) or '<span class="chip vazio">—</span>'


def tabela(id_, cols, linhas, classe="", filtro=False, nota="", alta=False):
    th = "".join(f'<th class="{al}"{" data-sort" if ordena else ""} '
                 f'scope="col">{e(rot)}</th>' for rot, al, ordena in cols)
    busca = (f'<div class="tf"><input type="search" id="f-{id_}" class="filtro" '
             f'data-alvo="{id_}" placeholder="filtrar…" '
             f'aria-label="Filtrar linhas da tabela">'
             f'<span class="tf-n" id="n-{id_}"></span></div>') if filtro else ""
    nota = f'<p class="nota-pe">{nota}</p>' if nota else ""
    return (f'{busca}<div class="tw{" alta" if alta else ""}">'
            f'<table id="{id_}" class="{classe}"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(linhas)}</tbody></table></div>{nota}')


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
    ps = "".join(f"<p>{p}</p>" for p in paragrafos)
    return (f'<div class="caixa {tipo}"><span class="tit">{ICONES[tipo]}'
            f'{e(titulo)}</span>{ps}</div>')


_ordem = [0]


def secao(id_, titulo, chamada, corpo):
    _ordem[0] += 1
    return (f'<section id="{id_}"><h2><span class="num">{_ordem[0]}</span>'
            f'{e(titulo)}</h2><p class="chamada">{chamada}</p>{corpo}</section>')


def sub(titulo):
    return f'<h3 class="sub">{e(titulo)}</h3>'


def legenda():
    return ('<div class="legenda">' + "".join(
        f'<span><i style="background:var(--s{k})"></i>{k} — {e(v)}</span>'
        for k, v in CAT.items()) + '</div>')


def n2yo(norad, texto=None):
    return (f'<a href="https://www.n2yo.com/satellite/?s={e(norad)}" '
            f'target="_blank" rel="noopener">{e(texto or norad)}</a>')


# --------------------------------------------------------------- gráficos
def grafico_anos():
    dados = [d for d in M["ano"] if d["chave"] >= "2010"]
    antigos = [d for d in M["ano"] if d["chave"] < "2010"]
    if antigos:
        dados.insert(0, {"chave": "≤2009",
                         "A": sum(d["A"] for d in antigos),
                         "B": sum(d["B"] for d in antigos),
                         "C": sum(d["C"] for d in antigos),
                         "linhas": sum(d["linhas"] for d in antigos)})
    W, H = 920, 290
    ml, mr, mt, mb = 46, 12, 18, 44
    pw, ph = W - ml - mr, H - mt - mb
    maxv = max(max(d["A"], d["B"], d["C"]) for d in dados)
    passo = 50 if maxv > 200 else (25 if maxv > 100 else 10)
    topo = math.ceil(maxv / passo) * passo
    gw = pw / len(dados)
    bw = min(12, (gw - 8) / 3 - 2)
    p = []
    for i in range(0, topo + 1, passo):
        y = mt + ph - ph * i / topo
        p.append(f'<line class="grid" x1="{ml}" y1="{y:.1f}" x2="{W-mr}" '
                 f'y2="{y:.1f}"/>')
        p.append(f'<text class="tick" x="{ml-8}" y="{y+4:.1f}" '
                 f'text-anchor="end">{i}</text>')
    for i, d in enumerate(dados):
        x0 = ml + i * gw
        for j, cat in enumerate(("A", "B", "C")):
            v = d[cat]
            if not v:
                continue
            h = ph * v / topo
            x = x0 + (gw - (3 * bw + 4)) / 2 + j * (bw + 2)
            p.append(f'<rect class="b s{cat}" x="{x:.1f}" y="{mt+ph-h:.1f}" '
                     f'width="{bw:.1f}" height="{h:.1f}" rx="2" '
                     f'data-t="{d["chave"]} · {CAT[cat]}: {v} satélites"/>')
        p.append(f'<text class="tick" x="{x0+gw/2:.1f}" y="{H-mb+18}" '
                 f'text-anchor="middle">{d["chave"]}</text>')
    p.append(f'<line class="axis" x1="{ml}" y1="{mt+ph}" x2="{W-mr}" '
             f'y2="{mt+ph}"/>')
    corpo = ["".join(
        f'<tr><td>{e(d["chave"])}</td><td class="n">{d["A"]}</td>'
        f'<td class="n">{d["B"]}</td><td class="n">{d["C"]}</td>'
        f'<td class="n forte">{d["linhas"]}</td></tr>' for d in dados)]
    tab = tabela("t-ano", [("Ano", "", False), ("A", "n", False),
                           ("B", "n", False), ("C", "n", False),
                           ("Total", "n", False)], corpo)
    return (f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
            f'aria-label="Satélites de coleta de dados lançados por ano">'
            f'{"".join(p)}</svg>', tab)


def grafico_vida():
    """Vida prevista (barra) contra idade atual (marcador), por satélite."""
    dados = M["vida_lista"][:18]
    W = 920
    lh = 26
    ml, mr, mt = 250, 74, 26
    H = mt + lh * len(dados) + 30
    pw = W - ml - mr
    topo = math.ceil(max(d["idade"] for d in dados) / 5) * 5
    x = lambda v: ml + pw * v / topo
    p = []
    for t in range(0, topo + 1, 5):
        p.append(f'<line class="grid" x1="{x(t):.1f}" y1="{mt-8}" '
                 f'x2="{x(t):.1f}" y2="{mt+lh*len(dados)-6}"/>')
        p.append(f'<text class="tick" x="{x(t):.1f}" y="{mt+lh*len(dados)+12}" '
                 f'text-anchor="middle">{t}</text>')
    for i, d in enumerate(dados):
        y = mt + i * lh + 6
        p.append(f'<text class="rot" x="{ml-10}" y="{y+4}" text-anchor="end" '
                 f'style="font-size:11px">{e(d["nome"][:34])}</text>')
        p.append(f'<rect class="b sA" x="{ml}" y="{y-5}" '
                 f'width="{max(x(d["vida_prevista"])-ml,1):.1f}" height="10" '
                 f'rx="2" data-t="{e(d["nome"])} · vida prevista '
                 f'{d["vida_prevista"]} anos"/>')
        p.append(f'<line class="faixa" x1="{x(d["vida_prevista"]):.1f}" '
                 f'y1="{y}" x2="{x(d["idade"]):.1f}" y2="{y}"/>')
        p.append(f'<circle class="med" cx="{x(d["idade"]):.1f}" cy="{y}" r="5" '
                 f'data-t="{e(d["nome"])} · {d["idade"]:.1f} anos em órbita '
                 f'({d["excedente"]:.1f} além do previsto)"/>')
        p.append(f'<text class="val" x="{W-mr+8}" y="{y+4}" '
                 f'style="font-size:11px">+{d["excedente"]:.0f} anos</text>')
    corpo = ["".join(
        f'<tr><td>{n2yo(d["norad"], d["nome"][:44])}</td>'
        f'<td class="cat">{chips(d["categoria"])}</td>'
        f'<td>{e(d["operador"][:30])}</td><td>{e(d["lancamento"])}</td>'
        f'<td class="n">{num(d["vida_prevista"],1)}</td>'
        f'<td class="n">{num(d["idade"],1)}</td>'
        f'<td class="n forte">+{num(d["excedente"],1)}</td></tr>'
        for d in M["vida_lista"])]
    tab = tabela("t-vida", [("Satélite", "", True), ("Recorte", "", True),
                            ("Operador", "", True), ("Lançamento", "", True),
                            ("Vida prevista (anos)", "n", True),
                            ("Em órbita há (anos)", "n", True),
                            ("Excedente", "n", True)], corpo,
                  classe="larga", alta=True)
    return (f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
            f'aria-label="Vida prevista contra tempo real em órbita">'
            f'{"".join(p)}</svg>', tab)


# ---------------------------------------------------------------- tabelas
def t_panorama():
    mx = max(d["n"] for d in M["panorama"])
    linhas = [f'<tr{" class=destaque" if d.get("destaque") else ""}>'
              f'<td>{e(d["recorte"])}</td>'
              f'<td class="n barcell">{barra(d["n"], mx)}'
              f'<span>{num(d["n"])}</span></td></tr>' for d in M["panorama"]]
    return tabela("t-pan", [("Recorte", "", False), ("Satélites", "n", False)],
                  linhas)


def t_abc(bloco, rotulo, id_, filtro=False, alta=False):
    dados = M[bloco]
    mx = max(d["linhas"] for d in dados)
    linhas = [f'<tr><td>{e(d["chave"])}</td>'
              f'<td class="n barcell">{barra(d["linhas"], mx)}'
              f'<span>{num(d["linhas"])}</span></td>'
              f'<td class="n sA">{num(d["A"])}</td>'
              f'<td class="n sB">{num(d["B"])}</td>'
              f'<td class="n sC">{num(d["C"])}</td></tr>' for d in dados]
    return tabela(id_, [(rotulo, "", True), ("Satélites", "n", True),
                        ("A", "n", True), ("B", "n", True), ("C", "n", True)],
                  linhas, filtro=filtro, alta=alta)


def t_situacao():
    s = M["situacao_por_recorte"]
    linhas = [f'<tr><td>{e(d["chave"])}</td>'
              f'<td class="n">{num(d["linhas"])}</td>'
              f'<td class="n forte">{num(d["em_orbita"])}</td>'
              f'<td class="n">{num(d["reentrou"])}</td>'
              f'<td class="n">{100*d["em_orbita"]/d["linhas"]:.1f}%</td></tr>'
              .replace(".", ",") for d in s]
    return tabela("t-sit", [("Recorte", "", False), ("No recorte", "n", False),
                            ("Em órbita hoje", "n", False),
                            ("Reentraram", "n", False),
                            ("Sobrevivência", "n", False)], linhas)


def t_reentradas():
    mx = max(d["linhas"] for d in M["reentradas_ano"])
    ano_ = [f'<tr><td>{e(d["chave"])}</td>'
            f'<td class="n barcell">{barra(d["linhas"], mx)}'
            f'<span>{num(d["linhas"])}</span></td></tr>'
            for d in M["reentradas_ano"]]
    mx2 = max(d["linhas"] for d in M["reentradas_operador"])
    op = [f'<tr><td>{e(d["chave"])}</td>'
          f'<td class="n barcell">{barra(d["linhas"], mx2)}'
          f'<span>{num(d["linhas"])}</span></td></tr>'
          for d in M["reentradas_operador"]]
    return (tabela("t-reano", [("Ano da reentrada", "", False),
                               ("Satélites", "n", False)], ano_),
            tabela("t-reop", [("Operador", "", True),
                              ("Satélites que caíram", "n", True)], op))


def t_qualidade():
    linhas = [f'<tr><td>{e(d["nome"][:46])}</td>'
              f'<td>{n2yo(d["norad"])}</td>'
              f'<td>{e(d["n2yo_nome"][:34])}</td>'
              f'<td>{e(d["tipo"])}</td>'
              f'<td>{e(d["operador"][:30])}</td></tr>'
              for d in M["qualidade_lista"]]
    return tabela("t-qual", [("Nome na UCS", "", True), ("NORAD", "", True),
                             ("Objeto no n2yo", "", True), ("Tipo", "", True),
                             ("Operador", "", True)], linhas)


def t_familias():
    mx = max(d["linhas"] for d in M["familias"])
    linhas = [f'<tr><td>{e(d["chave"])}</td>'
              f'<td class="cat">{chips(d["categoria"])}</td>'
              f'<td>{e(d["operador"])}</td><td>{e(d["pais"])}</td>'
              f'<td class="n barcell">{barra(d["linhas"], mx)}'
              f'<span>{num(d["linhas"])}</span></td>'
              f'<td class="txt">{e(d["proposito"])}</td></tr>'
              for d in M["familias"]]
    return tabela("t-fam", [("Família", "", True), ("Recorte", "", True),
                            ("Operador", "", True), ("País", "", True),
                            ("Satélites", "n", True), ("Propósito", "", False)],
                  linhas, classe="larga")


def t_brasil():
    linhas = [f'<tr><td>{n2yo(d["norad"], d["nome"])}</td>'
              f'<td class="cat">{chips(d["categoria"])}</td>'
              f'<td>{e(d["lancamento"])}</td>'
              f'<td>{e(d["operador"])}</td>'
              f'<td class="n">{num(d["massa"])}</td>'
              f'<td>{e(d["orbita"])}</td>'
              f'<td class="n">{num(d["idade"],1)}</td>'
              f'<td>{"<b>sim</b>" if d["em_orbita"]=="sim" else e(d["em_orbita"] or "?")}</td>'
              f'<td class="txt">{e(d["detalhado"] or d["proposito"])}'
              f'{" — " + e(d["comentario"]) if d["comentario"] else ""}</td></tr>'
              for d in M["brasil"]]
    return tabela("t-br", [("Satélite", "", True), ("Recorte", "", True),
                           ("Lançamento", "", True), ("Operador", "", True),
                           ("Massa (kg)", "n", True), ("Órbita", "", True),
                           ("Idade (anos)", "n", True), ("Em órbita", "", True),
                           ("Propósito declarado", "", False)],
                  linhas, classe="larga")


def t_decaimento():
    linhas = [f'<tr><td>{n2yo(d["norad"], d["nome"][:42])}</td>'
              f'<td class="cat">{chips(d["categoria"])}</td>'
              f'<td>{e(d["operador"][:30])}</td>'
              f'<td class="n">{num(d["perigeu_2023"])}</td>'
              f'<td class="n">{num(d["perigeu_hoje"])}</td>'
              f'<td class="n forte">{num(d["delta"],1)}</td>'
              f'<td>{e(d["epoca"])}</td></tr>' for d in M["decaimento"]]
    return tabela("t-dec", [("Satélite", "", True), ("Recorte", "", True),
                            ("Operador", "", True), ("Perigeu 2023 (km)", "n", True),
                            ("Perigeu hoje (km)", "n", True),
                            ("Variação (km)", "n", True),
                            ("Época do TLE", "", True)], linhas,
                  classe="larga")


def t_categorias():
    dados = M["categorias_n2yo"]
    mx = max(d["linhas"] for d in dados) if dados else 1
    linhas = [f'<tr><td>{e(d["chave"])}</td>'
              f'<td class="n barcell">{barra(d["linhas"], mx)}'
              f'<span>{num(d["linhas"])}</span></td></tr>' for d in dados]
    return tabela("t-cat", [("Categoria", "", True),
                            ("Satélites do recorte", "n", True)], linhas)


def t_recorte_completo():
    """Todas as linhas do recorte, com as colunas essenciais."""
    with open(os.path.join(AQUI, "ucs_coleta_dados.csv"), encoding="utf-8-sig") as f:
        rec = list(csv.DictReader(f))
    linhas = []
    for r in sorted(rec, key=lambda x: x["nome"]):
        linhas.append(
            f'<tr><td>{n2yo(r["norad"], r["nome"][:52])}</td>'
            f'<td class="cat">{chips(r["categoria_coleta"])}</td>'
            f'<td>{e(r["operador"][:34])}</td>'
            f'<td>{e(r["pais_operador"])}</td>'
            f'<td>{e(r["data_lancamento"])}</td>'
            f'<td class="n">{num(r["massa_lancamento_kg"])}</td>'
            f'<td>{e(r["classe_orbita"])}</td>'
            f'<td>{"sim" if r.get("n2yo_em_orbita")=="sim" else e(r.get("n2yo_em_orbita") or "?")}</td>'
            f'<td class="txt">{e(r["proposito_detalhado"] or r["proposito"])}</td>'
            f'</tr>')
    return tabela("t-todos", [("Satélite", "", True), ("Recorte", "", True),
                              ("Operador", "", True), ("País", "", True),
                              ("Lançamento", "", True), ("Massa (kg)", "n", True),
                              ("Órbita", "", True), ("Em órbita", "", True),
                              ("Propósito declarado", "", False)],
                  linhas, classe="larga", filtro=True, alta=True,
                  nota="Uma linha por satélite do recorte. O CSV "
                       "<code>ucs_coleta_dados.csv</code> traz as 48 colunas "
                       "completas, com evidência da classificação e órbita atual.")


def kpi(rot, big, sub_):
    return (f'<div class="kpi"><div class="rot">{e(rot)}</div>'
            f'<div class="big">{big}</div><div class="sub">{e(sub_)}</div></div>')


SECOES = [("panorama", "Panorama"), ("situacao", "Situação hoje"),
          ("tempo", "Por ano"), ("orbita", "Órbita e porte"),
          ("vida", "Vida útil"), ("decaimento", "Decaimento"),
          ("quem", "Quem faz"), ("proposito", "Propósitos"),
          ("familias", "Famílias"), ("brasil", "Brasil"),
          ("recorte", "Lista completa")]


def main():
    import painel_estilo as est
    sob = M["sobrevivencia"]
    vida = M["vida"]
    pan = {d["recorte"].split(" —")[0]: d for d in M["panorama"]}
    total_ucs = M["panorama"][4]["n"]

    kpis = "".join([
        kpi("satélites no recorte", num(M["panorama"][3]["n"]),
            f'de {num(total_ucs)} em órbita na base UCS'),
        kpi("ainda em órbita", f'{sob["pct"]:.1f}%'.replace(".", ","),
            f'{num(sob["em_orbita"])} dos {num(sob["recorte"])} — '
            f'{num(sob["reentrados"])} reentraram desde 2023'),
        kpi("passaram da vida prevista", f'{vida["pct"]:.0f}%',
            f'{vida["alem_da_vida"]} de {vida["com_vida_declarada"]} com vida '
            f'declarada'),
        kpi("massa mediana", f'{num(M["massa_resumo"]["mediana"])} kg',
            f'de {num(M["massa_resumo"]["min"])} kg a '
            f'{num(M["massa_resumo"]["max"])} kg'),
        kpi("queda mediana de perigeu", f'{num(M["decaimento_resumo"]["mediana"],1)} km',
            f'em 3 anos, nos {num(M["decaimento_resumo"]["n"])} que seguem em órbita'),
    ])

    graf_ano, tab_ano = grafico_anos()
    graf_vida, tab_vida = grafico_vida()

    corpo = [
        secao("panorama", "Panorama do recorte",
              "A base da UCS declara <em>Purpose</em> e <em>Detailed Purpose</em> "
              "de cada satélite, então o recorte começa pelo campo declarado e "
              "só recorre a operador e comentário quando ele é omisso — o que "
              "acontece justamente com as constelações de IoT, registradas como "
              "“Communications” sem detalhe.",
              t_panorama()
              + caixa("nota", "Duas fontes, dois instantes",
                      "A <strong>UCS Satellite Database</strong> (edição de "
                      "2023-05-01) dá o que cada satélite é: propósito, órbita, "
                      "massa, potência, vida prevista, contratante e operador. "
                      "O <strong>n2yo.com</strong> dá o que ele está fazendo "
                      "agora: se continua em órbita, quando reentrou e o TLE de "
                      "hoje, de onde saem inclinação, período, apogeu e perigeu "
                      "atuais.",
                      "Os recortes A, B e C são os mesmos do levantamento de "
                      "nanossatélites, para que os dois conjuntos sejam "
                      "comparáveis — lá a classificação teve de sair do texto; "
                      "aqui ela sai de campo declarado sempre que existe.")),
        secao("situacao", "O que sobrou em órbita",
              f'Dos {num(sob["recorte"])} satélites do recorte que estavam em '
              f'órbita em maio de 2023, <strong>{num(sob["em_orbita"])} ainda '
              f'estão</strong> — {str(sob["pct"]).replace(".", ",")}%. '
              f'{num(sob["reentrados"])} reentraram nos três anos seguintes.',
              t_situacao()
              + sub("Quando caíram os que caíram")
              + f'<div class="duo">'
                f'<div>{t_reentradas()[0]}</div>'
                f'<div>{t_reentradas()[1]}</div></div>'
              + caixa("atencao", "A base já nascia com atraso",
                      f'{M["reentradas_resumo"]["antes_do_corte"]} satélites do '
                      f'recorte tinham <strong>data de reentrada anterior a '
                      f'2023-05-01</strong>, a própria data de corte da UCS — '
                      f'ou seja, já não estavam em órbita quando a edição foi '
                      f'publicada. A idade mediana na reentrada, entre os que '
                      f'caíram, foi de '
                      f'{num(M["reentradas_resumo"]["idade_mediana"],1)} anos.')),
        secao("tempo", "Lançamentos por ano",
              "Barras agrupadas, não empilhadas: um satélite pode contar em dois "
              "recortes (o Spire faz radio-ocultação <em>e</em> recebe AIS), e "
              "empilhar somaria o mesmo objeto duas vezes. A base é um retrato "
              "de 2023 — o que voou depois não está aqui.",
              f'<div class="painel">{legenda()}{graf_ano}'
              f'<details class="tv"><summary>ver os números</summary>'
              f'{tab_ano}</details></div>'),
        secao("orbita", "Órbita e porte",
              f'Massa mediana de {num(M["massa_resumo"]["mediana"])} kg e '
              f'potência mediana de {num(M["potencia_resumo"]["mediana"])} W '
              f'entre os que declaram — a cauda vai de dezenas de gramas a '
              f'toneladas.',
              f'<div class="duo">'
              f'<div>{sub("Faixa de altitude")}'
              f'{t_abc("altitude", "Altitude", "t-alt")}</div>'
              f'<div>{sub("Massa de lançamento")}'
              f'{t_abc("massa", "Massa", "t-massa")}</div></div>'),
        secao("vida", "Vida prevista contra vida real",
              f'{vida["alem_da_vida"]} dos {vida["com_vida_declarada"]} '
              f'satélites do recorte que ainda estão em órbita e declaram vida '
              f'útil já <strong>passaram do prazo previsto</strong> '
              f'({vida["pct"]:.0f}%). A barra é a vida prevista; o ponto, o '
              f'tempo real em órbita.'.replace(".0%", "%"),
              f'<div class="painel">{graf_vida}</div>'
              + caixa("destaque", "O que isso diz para um projeto novo",
                      f'A vida prevista mediana declarada é de '
                      f'<strong>{num(vida["mediana_vida"],1)} anos</strong>, e a '
                      f'idade mediana de quem continua operando é '
                      f'<strong>{num(vida["mediana_idade"],1)} anos</strong>. '
                      f'Projetar para a vida mínima e operar enquanto o '
                      f'barramento aguentar é o padrão do setor, não a exceção.')
              + sub("Os que mais passaram do prazo") + tab_vida),
        secao("decaimento", "Decaimento orbital em três anos",
              f'Perigeu declarado pela UCS em 2023 contra o perigeu calculado do '
              f'TLE de hoje. Queda mediana de '
              f'{num(M["decaimento_resumo"]["mediana"],1)} km em '
              f'{num(M["decaimento_resumo"]["n"])} satélites; '
              f'{M["decaimento_resumo"]["subiu"]} subiram (manobra de '
              f'manutenção de órbita).',
              t_decaimento()
              + caixa("atencao", "Duas réguas diferentes",
                      "A UCS publica a órbita nominal declarada; o valor de hoje "
                      "vem do TLE, que é a órbita osculante medida. Parte da "
                      "diferença é decaimento real, parte é diferença de método "
                      "— por isso a tabela mostra os dois números lado a lado em "
                      "vez de só a variação.")),
        secao("quem", "Quem faz",
              "Usuário declarado, país do operador e quem constrói. A UCS "
              "distingue operador de contratante, o que deixa ver a cadeia: "
              "quem opera o dado nem sempre é quem monta o satélite.",
              f'<div class="duo">'
              f'<div>{sub("Usuário declarado")}'
              f'{t_abc("usuarios", "Usuário", "t-user")}</div>'
              f'<div>{sub("País do operador")}'
              f'{t_abc("pais", "País", "t-pais")}</div></div>'
              f'<div class="duo" style="margin-top:16px">'
              f'<div>{sub("Operadores")}'
              f'{t_abc("operadores", "Operador", "t-op")}</div>'
              f'<div>{sub("Contratantes (quem constrói)")}'
              f'{t_abc("contratantes", "Contratante", "t-cont")}</div></div>'),
        secao("proposito", "Propósito declarado e categorias do n2yo",
              "À esquerda, o campo <em>Detailed Purpose</em> da UCS. À direita, "
              "as categorias em que o n2yo classifica esses mesmos objetos — "
              "outra taxonomia, montada para rastreamento, não para política "
              "espacial.",
              f'<div class="duo">'
              f'<div>{sub("Propósito detalhado (UCS)")}'
              f'{t_abc("proposito_detalhado", "Propósito", "t-prop")}</div>'
              f'<div>{sub("Categoria no n2yo")}{t_categorias()}'
              f'</div></div>'),
        secao("familias", "Maiores famílias do recorte",
              "Agrupamento por prefixo do nome — é como as constelações "
              "aparecem na base, um satélite por linha.", t_familias()),
        secao("brasil", "Satélites brasileiros no recorte",
              "Tudo que a UCS registra com operador no Brasil dentro do recorte "
              "de coleta de dados, com a situação atual vinda do n2yo.",
              caixa("destaque", "O SCD-1 é o recordista do recorte",
                    "Lançado em 1993 com <strong>3 anos</strong> de vida "
                    "prevista, o SCD-1 está em órbita há <strong>33,6 "
                    "anos</strong> — o maior excedente de vida útil entre os "
                    "1 575 satélites deste recorte, à frente de NOAA-15, "
                    "DMSP F14 e dos Orbcomm da primeira geração. O SCD-2, de "
                    "1998, é o quinto. Os dois são satélites de coleta de "
                    "dados de plataformas no solo: exatamente a classe de "
                    "missão que este anexo recorta.",
                    "A UCS declara para o SCD-1 o NORAD 22491, que no catálogo "
                    "é o corpo do foguete Pegasus do mesmo lançamento. A "
                    "situação acima vem do objeto 22490, cujo nome confere com "
                    "o do satélite — a correção está registrada na coluna "
                    "<code>n2yo_correcao</code>.")
              + t_brasil()
              + caixa("nota", "O que a UCS não vê",
                      "VCUB-1 e Alfa Crux, brasileiros e de coleta de dados, "
                      "ficam fora deste recorte: a UCS os registra como "
                      "“Technology Demonstration” com o comentário “validate "
                      "architecture of satellite”, sem nada sobre a carga útil. "
                      "Quem os pega é o levantamento de nanossatélites, que lê "
                      "a descrição da missão — os dois conjuntos se completam.")),
        secao("recorte", "Lista completa do recorte",
              "Os satélites do recorte, um por linha. Ordene clicando no "
              "cabeçalho; filtre pelo campo acima da tabela.",
              t_recorte_completo()
              + sub("Onde o NORAD declarado não aponta para a carga útil")
              + caixa("nota", "Qualidade do identificador",
                      f'Em {len(M["qualidade_lista"])} casos o número NORAD que '
                      f'a UCS declara corresponde, no catálogo do n2yo, a um '
                      f'corpo de foguete ou detrito do mesmo lançamento — não '
                      f'ao satélite. A coluna <code>n2yo_tipo_objeto</code> do '
                      f'CSV marca todos; a órbita atual desses registros é a do '
                      f'objeto errado e não deve ser usada.')
              + t_qualidade()),
    ]

    nav = "".join(f'<a href="#{i}">{e(r)}</a>' for i, r in SECOES)
    html_out = f"""<title>Satélites de coleta de dados</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fira+Mono:wght@400;500&family=Fira+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<style>{est.CSS}</style>

<header class="top">
  <div class="top-in">
    <span class="doc">Documento preliminar de missão · <b>Satélite BAI-01</b></span>
    <span class="meta">Anexo de dados · UCS + n2yo</span>
  </div>
  <nav class="secs" aria-label="Seções">{nav}</nav>
</header>

<main class="wrap">
  <div class="capa">
    <p class="eyebrow">Anexo de dados · benchmark de missões</p>
    <h1>Satélites de coleta de dados</h1>
    <p class="chamada">O que a base da UCS registra sobre satélites de porte
    convencional cuja carga útil coleta dados, e o que o rastreamento atual diz
    que sobrou deles três anos depois.</p>
  </div>

  <div class="lede">
    <p>Recorte de <strong>{num(M["panorama"][3]["n"])} satélites</strong> dos
    {num(total_ucs)} que a <a href="https://www.ucsusa.org/resources/satellite-database"
    target="_blank" rel="noopener">UCS Satellite Database</a> registrava em
    órbita em 2023-05-01: sensoriamento remoto da Terra
    (<span class="chip sA">A</span>), coleta de plataformas no solo — DCS, IoT,
    store-and-forward (<span class="chip sB">B</span>) — e sinais cooperativos
    AIS, ADS-B, ELINT e monitoramento de espectro
    (<span class="chip sC">C</span>). A situação de cada um hoje vem do
    <a href="https://www.n2yo.com/satellites/" target="_blank" rel="noopener">n2yo.com</a>.</p>
  </div>
  <div class="kpis">{kpis}</div>
  {"".join(corpo)}
  <footer>
    <p><strong>Fontes.</strong> UCS Satellite Database, edição de 2023-05-01
    (7.560 satélites, 28 campos declarados por satélite mais as fontes citadas);
    n2yo.com para situação atual, categorias e TLE, consultado em 2026-09-16. O
    <code>robots.txt</code> do n2yo não restringe nenhum caminho.</p>
    <p><strong>Procedência.</strong> Toda contagem sai de
    <code>metricas.json</code>, gerado por <code>metricas.py</code> a partir de
    <code>ucs_todos.csv</code>, <code>ucs_coleta_dados.csv</code> e
    <code>orbita_ucs_vs_n2yo.csv</code>; a página é escrita por
    <code>gerar_painel.py</code>. Nenhum número foi digitado à mão.</p>
    <p><strong>Limites.</strong> A UCS é um retrato de maio de 2023: o que voou
    depois não aparece, e satélites lançados antes que já haviam reentrado
    também não. A classificação dos que a base registra como “Communications”
    sem propósito detalhado depende da lista de operadores declarada em
    <code>regras_coleta.py</code> — está lá, aberta, para ser discutida.
    Custo não existe nesta base: quem tem valor declarado é o levantamento de
    nanossatélites.</p>
    <p class="ver">v0.1 — documento de trabalho</p>
  </footer>
</main>
<div id="tip" role="status" aria-live="polite"></div>
<script>{est.JS}</script>
"""
    autonomo = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n'
                '<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                f'{html_out}\n</html>\n')
    with open(os.path.join(AQUI, "painel_metricas.html"), "w",
              encoding="utf-8") as f:
        f.write(autonomo)
    with open(os.path.join(AQUI, "painel_artifact.html"), "w",
              encoding="utf-8") as f:
        f.write(html_out)
    print(f"painel_metricas.html — {len(autonomo)/1024:.0f} kB (autônomo)")
    print(f"painel_artifact.html — {len(html_out)/1024:.0f} kB (fragmento)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
