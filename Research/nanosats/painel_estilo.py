#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Folha de estilo e script do painel.

A identidade é a mesma de `config/estilo.tex` do relatório do BAI-01: paleta
bainavy/baiteal/baiambar/baiverde/baicinza, títulos com o número em caixa
navy, cabeçalho de tabela em faixa navy, filetes bailinha, caixas destaque /
atenção / nota e a mesma família tipográfica (Fira Sans nos títulos, tabelas e
gráficos; serifada no corpo; Fira Mono nos identificadores).

Tema único, claro: o relatório é um documento impresso e a página adota o
mesmo "papel". Por isso não há bloco de tema escuro — toda cor, incluindo o
fundo do body, é pintada explicitamente.

As três cores de dado (A/B/C) não são as do texto: `baiteal` e `baiverde`
ficam abaixo do piso de croma e a ΔE entre elas é 8,5 (piso 15). Foram
ancoradas nos matizes da identidade (251°, 58°, 205°) e subidas para a banda
de luminosidade — passam CVD (pior ΔE 16,7), visão normal (19,9) e contraste
≥ 3:1 sobre o papel e sobre o fundo das caixas.
"""

CSS = """
:root{
  color-scheme: light;
  /* paleta do relatório (config/estilo.tex) */
  --navy:#15324f; --teal:#0e7c86; --ambar:#b4651a; --verde:#2e6b4f;
  --cinza:#5a6672; --fundo:#f4f6f8; --linha:#d8dee4;
  --papel:#ffffff; --tinta:#1b2733; --tinta-2:#5a6672; --tinta-3:#8a949e;
  /* cores de dado, ancoradas nos matizes acima e validadas */
  --sA:#19548d; --sB:#b26417; --sC:#1d97a3;
  --sA-bg:#e8eef5; --sB-bg:#f7efe6; --sC-bg:#e5f3f5;
  --sombra:0 1px 2px rgba(21,50,79,.06);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--fundo); color:var(--tinta);
  font-family:"Source Serif 4","Libertinus Serif","Linux Libertine O",
    Georgia,"Times New Roman",serif;
  font-size:16px; line-height:1.52; -webkit-text-size-adjust:100%;
}
.wrap{max-width:1160px; margin:0 auto; padding-inline:16px; padding-block:0 72px}
h1,h2,h3,h4{font-family:"Fira Sans","Segoe UI",system-ui,sans-serif;
  font-weight:600; color:var(--navy); text-wrap:balance; margin:0}
a{color:var(--teal); text-decoration:none; border-bottom:1px solid rgba(14,124,134,.35)}
a:hover{border-bottom-color:var(--teal)}
:focus-visible{outline:2px solid var(--teal); outline-offset:2px; border-radius:2px}
strong{color:var(--navy)}
em{font-style:italic}

/* cabeçalho corrido, no espírito do fancyhdr ---------------------------- */
header.top{position:sticky; top:env(safe-area-inset-top,0px); z-index:30;
  background:var(--fundo); border-bottom:.5pt solid var(--linha)}
.top-in{max-width:1160px; margin:0 auto; padding:9px 16px 7px;
  display:flex; align-items:baseline; justify-content:space-between; gap:14px;
  font-family:"Fira Sans",sans-serif; font-size:12px; color:var(--cinza)}
.top-in .doc{font-weight:500; letter-spacing:.01em}
.top-in .doc b{color:var(--navy); font-weight:600}
nav.secs{max-width:1160px; margin:0 auto; padding:0 16px 9px;
  display:flex; gap:5px; overflow-x:auto; scrollbar-width:thin}
nav.secs a{flex:0 0 auto; font-family:"Fira Sans",sans-serif; font-size:11px;
  font-weight:500; text-transform:uppercase; letter-spacing:.05em;
  color:var(--cinza); border:1px solid var(--linha); border-radius:2px;
  background:var(--papel); padding:3px 9px}
nav.secs a:hover{color:var(--navy); border-color:var(--cinza)}

/* abertura -------------------------------------------------------------- */
.capa{padding-block:34px 0; border-bottom:3px solid var(--navy);
  margin-bottom:22px}
.capa .eyebrow{font-family:"Fira Sans",sans-serif; font-size:11.5px;
  font-weight:600; text-transform:uppercase; letter-spacing:.14em;
  color:var(--teal)}
.capa h1{font-size:34px; line-height:1.12; margin:8px 0 10px;
  letter-spacing:-.015em}
.capa .chamada{font-family:"Fira Sans",sans-serif; font-style:italic;
  color:var(--cinza); font-size:15px; max-width:70ch; margin:0 0 20px}
.lede{max-width:72ch; margin-bottom:6px}
.lede p{margin:0 0 .55em}

.kpis{display:grid; gap:10px; margin:22px 0 4px;
  grid-template-columns:repeat(auto-fit,minmax(186px,1fr))}
.kpi{background:var(--papel); border:1px solid var(--linha);
  border-top:3px solid var(--navy); padding:13px 15px 14px; box-shadow:var(--sombra)}
.kpi .rot{font-family:"Fira Sans",sans-serif; font-size:10.5px; font-weight:600;
  text-transform:uppercase; letter-spacing:.08em; color:var(--cinza)}
.kpi .big{font-family:"Fira Sans",sans-serif; font-size:29px; font-weight:600;
  color:var(--navy); line-height:1.1; margin-top:5px; white-space:nowrap;
  font-variant-numeric:tabular-nums}
.kpi .sub{font-family:"Fira Sans",sans-serif; font-size:12px;
  color:var(--cinza); margin-top:3px; line-height:1.35}

/* seções: número em caixa navy, como \\titleformat{\\section} ------------- */
section{margin-top:46px; scroll-margin-top:116px}
section > h2{font-size:23px; letter-spacing:-.01em; display:flex;
  align-items:baseline; gap:.62em}
section > h2 .num{flex:0 0 auto; background:var(--navy); color:#fff;
  font-size:.72em; font-weight:600; width:1.5em; text-align:center;
  padding:.16em 0; font-variant-numeric:tabular-nums}
section > .chamada{font-family:"Fira Sans",sans-serif; font-style:italic;
  color:var(--cinza); font-size:14px; margin:8px 0 16px; max-width:76ch}
h3.sub{font-size:15px; margin:26px 0 10px; color:var(--navy)}
h3.sub .ord{color:var(--teal); margin-right:.4em; font-weight:600}

.painel{background:var(--papel); border:1px solid var(--linha); padding:14px;
  box-shadow:var(--sombra)}
.duo{display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
.duo h3{font-family:"Fira Sans",sans-serif; font-size:13.5px; margin-bottom:9px;
  color:var(--navy)}

/* caixas destaque / atenção / nota, como os tcolorbox do relatório ------- */
.caixa{border-left:3px solid var(--cor); background:var(--fundo);
  padding:12px 14px 12px; margin:16px 0; position:relative}
.caixa > .tit{position:absolute; top:-11px; left:-3px; background:var(--cor);
  color:#fff; font-family:"Fira Sans",sans-serif; font-size:11px;
  font-weight:600; padding:2px 9px; display:inline-flex; align-items:center;
  gap:6px}
.caixa > .tit svg{width:12px; height:12px; fill:currentColor}
.caixa > p{margin:10px 0 0; font-size:14px; color:var(--tinta-2)}
.caixa > p:first-of-type{margin-top:8px}
.caixa.destaque{--cor:var(--teal)}
.caixa.atencao{--cor:var(--ambar); background:#fdf7f1}
.caixa.nota{--cor:var(--cinza)}

.nota-pe{font-family:"Fira Sans",sans-serif; font-size:12px;
  color:var(--cinza); margin:10px 2px 0; max-width:78ch}

/* tabelas: faixa de cabeçalho navy, filetes bailinha --------------------- */
.tw{overflow:auto; border:1px solid var(--linha); background:var(--papel)}
.tw.alta{max-height:min(68vh,640px)}
table{border-collapse:collapse; width:100%;
  font-family:"Fira Sans","Segoe UI",sans-serif; font-size:13px}
thead th{position:sticky; top:0; z-index:2; background:var(--navy); color:#fff;
  font-size:11px; font-weight:600; text-align:left; padding:8px 10px;
  white-space:nowrap; letter-spacing:.01em}
thead th.n{text-align:right}
thead th[data-sort]{cursor:pointer; user-select:none}
thead th[data-sort]::after{content:"\\2195"; opacity:.45; margin-left:5px}
thead th[data-sort]:hover::after{opacity:.9}
thead th[data-dir="asc"]::after{content:"\\2191"; opacity:1}
thead th[data-dir="desc"]::after{content:"\\2193"; opacity:1}
tbody td{padding:7px 10px; border-bottom:.5pt solid var(--linha);
  vertical-align:top; line-height:1.45}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:#fbfcfd}
td.n{text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap}
td.forte{font-weight:600; color:var(--navy)}
td.txt{color:var(--tinta-2); font-size:12.5px; min-width:220px}
table.larga td.txt{max-width:520px}
table.larga td:first-child{min-width:150px}
td a{border-bottom-color:transparent}
td a:hover{border-bottom-color:var(--teal)}
td .sub{display:block; font-family:"Fira Mono",monospace; font-size:10.5px;
  color:var(--tinta-3)}
td.cat{white-space:nowrap}
.st{font-size:12px; color:var(--tinta-2)}
td.sA{color:var(--sA)} td.sB{color:var(--sB)} td.sC{color:var(--sC)}
thead th:first-child, tbody td:first-child{padding-left:12px}
tr.destaque td{background:var(--fundo); font-weight:600; color:var(--navy)}

td.barcell{display:flex; gap:9px; align-items:center; justify-content:flex-end}
.bar{flex:0 0 56px; height:5px; background:var(--linha); position:relative;
  overflow:hidden}
.bar::after{content:""; position:absolute; inset:0 auto 0 0; width:var(--w);
  background:var(--navy)}
.bar.sA::after{background:var(--sA)} .bar.sB::after{background:var(--sB)}
.bar.sC::after{background:var(--sC)}

/* etiquetas: mesmo desenho de \\atributo (fundo tênue, texto na cor) ----- */
.chip{display:inline-block; min-width:18px; text-align:center;
  font-family:"Fira Sans",sans-serif; font-size:10.5px; font-weight:600;
  padding:1px 6px; margin-right:3px}
.chip.sA{background:var(--sA-bg); color:var(--sA)}
.chip.sB{background:var(--sB-bg); color:var(--sB)}
.chip.sC{background:var(--sC-bg); color:var(--sC)}
.chip.vazio{background:var(--fundo); color:var(--tinta-3)}

.tf{display:flex; align-items:center; gap:10px; margin-bottom:9px}
.filtro{flex:1 1 240px; max-width:330px; font-family:"Fira Sans",sans-serif;
  font-size:13px; padding:6px 10px; border:1px solid var(--linha);
  background:var(--papel); color:var(--tinta)}
.filtro:focus{border-color:var(--teal)}
.tf-n{font-family:"Fira Sans",sans-serif; font-size:11.5px; color:var(--cinza)}

/* gráficos -------------------------------------------------------------- */
.chart{width:100%; height:auto; display:block}
.chart .grid{stroke:var(--linha); stroke-width:1}
.chart .axis{stroke:var(--cinza); stroke-width:.8}
.chart .tick{fill:var(--cinza); font-family:"Fira Sans",sans-serif; font-size:11px}
.chart .rot{fill:var(--navy); font-family:"Fira Sans",sans-serif; font-size:12px;
  font-weight:600}
.chart .val{fill:var(--navy); font-family:"Fira Sans",sans-serif; font-size:12px;
  font-weight:600}
.chart .enn{fill:var(--cinza); font-family:"Fira Sans",sans-serif; font-size:10.5px}
.chart .b{transition:opacity .12s}
.chart .b:hover{opacity:.72}
.chart .b.sA{fill:var(--sA)} .chart .b.sB{fill:var(--sB)}
.chart .b.sC{fill:var(--sC)}
.chart .faixa{stroke:var(--linha); stroke-width:3; stroke-linecap:round}
.chart .ext{fill:var(--cinza)}
.chart .med{fill:var(--navy); stroke:var(--papel); stroke-width:2}
.legenda{display:flex; gap:16px; flex-wrap:wrap; margin:2px 2px 12px;
  font-family:"Fira Sans",sans-serif; font-size:12.5px; color:var(--tinta-2)}
.legenda span{display:inline-flex; align-items:center; gap:7px}
.legenda i{width:10px; height:10px; display:inline-block}
.tv{margin-top:12px}
.tv > summary{cursor:pointer; font-family:"Fira Sans",sans-serif; font-size:11px;
  font-weight:600; text-transform:uppercase; letter-spacing:.05em;
  color:var(--cinza); list-style:none}
.tv > summary::-webkit-details-marker{display:none}
.tv > summary::before{content:"\\25B8"; display:inline-block; margin-right:6px;
  transition:transform .15s}
.tv[open] > summary::before{transform:rotate(90deg)}
.tv > summary:hover{color:var(--navy)}
.tv > .tw{margin-top:9px}

details summary{cursor:pointer}
td.txt details summary{color:var(--tinta-2)}
td.txt details[open] summary{color:var(--navy); font-weight:500}
td.txt p{margin:0 0 5px}
.falha{color:var(--ambar); font-size:12px; margin-top:4px}
.falha .rot{font-family:"Fira Sans",sans-serif; font-size:9.5px; font-weight:600;
  text-transform:uppercase; letter-spacing:.06em; background:var(--ambar);
  color:#fff; padding:1px 5px; margin-right:5px}
a.fonte{font-family:"Fira Mono",monospace; font-size:10px;
  text-transform:uppercase; letter-spacing:.04em; color:var(--cinza);
  border-bottom:1px solid var(--linha)}
a.fonte:hover{color:var(--navy); border-bottom-color:var(--cinza)}

#tip{position:fixed; z-index:60; pointer-events:none; opacity:0;
  transition:opacity .1s; background:var(--navy); color:#fff;
  font-family:"Fira Sans",sans-serif; font-size:11.5px; padding:5px 9px;
  max-width:300px}
footer{margin-top:58px; padding-top:18px; border-top:.5pt solid var(--linha);
  font-family:"Fira Sans",sans-serif; color:var(--cinza); font-size:12px}
footer p{margin:0 0 8px; max-width:84ch}
footer .ver{font-family:"Fira Mono",monospace; font-size:10.5px;
  color:var(--tinta-3)}
@media (max-width:640px){
  body{font-size:15px}
  .capa h1{font-size:26px}
  section > h2{font-size:19px}
  .kpi .big{font-size:25px}
  td.txt{min-width:180px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
@media print{
  header.top,nav.secs,.tf{display:none}
  body{background:#fff} .tw{max-height:none}
}
"""

JS = """
(function(){
  function valor(td){
    if(!td) return "";
    var v = td.getAttribute("data-v");
    if(v !== null) return parseFloat(v) || 0;
    var t = td.textContent.trim();
    if(/^[\\s\\d.,\\u00a0%+-]+$/.test(t) && /\\d/.test(t)){
      var n = t.replace(/[\\s\\u00a0%+]/g,"").replace(/\\./g,"").replace(",",".");
      var f = parseFloat(n);
      if(!isNaN(f)) return f;
    }
    return t.toLowerCase();
  }
  document.querySelectorAll("th[data-sort]").forEach(function(th){
    th.setAttribute("role","button");
    th.tabIndex = 0;
    function ordena(){
      var table = th.closest("table");
      var i = Array.prototype.indexOf.call(th.parentNode.children, th);
      var dir = th.getAttribute("data-dir") === "asc" ? "desc" : "asc";
      table.querySelectorAll("th[data-sort]").forEach(function(o){
        o.removeAttribute("data-dir");
      });
      th.setAttribute("data-dir", dir);
      var tb = table.tBodies[0];
      var rows = Array.prototype.slice.call(tb.rows);
      rows.sort(function(a,b){
        var x = valor(a.cells[i]), y = valor(b.cells[i]);
        if(typeof x === "number" && typeof y === "number") return x - y;
        return String(x).localeCompare(String(y), "pt-BR");
      });
      if(dir === "desc") rows.reverse();
      rows.forEach(function(r){ tb.appendChild(r); });
    }
    th.addEventListener("click", ordena);
    th.addEventListener("keydown", function(ev){
      if(ev.key === "Enter" || ev.key === " "){ ev.preventDefault(); ordena(); }
    });
  });

  document.querySelectorAll("input.filtro").forEach(function(inp){
    var alvo = document.getElementById(inp.dataset.alvo);
    if(!alvo) return;
    var saida = document.getElementById("n-" + inp.dataset.alvo);
    var rows = Array.prototype.slice.call(alvo.tBodies[0].rows);
    function conta(n){
      if(saida) saida.textContent = n + " de " + rows.length + " linhas";
    }
    conta(rows.length);
    inp.addEventListener("input", function(){
      var q = inp.value.trim().toLowerCase(), n = 0;
      rows.forEach(function(r){
        var ok = !q || r.textContent.toLowerCase().indexOf(q) >= 0;
        r.hidden = !ok;
        if(ok) n++;
      });
      conta(n);
    });
  });

  var tip = document.getElementById("tip");
  function mostra(ev){
    var t = ev.currentTarget.getAttribute("data-t");
    if(!t) return;
    tip.textContent = t;
    tip.style.opacity = "1";
    tip.style.left = Math.max(8, Math.min(ev.clientX + 14,
                     window.innerWidth - 310)) + "px";
    tip.style.top = (ev.clientY + 16) + "px";
  }
  document.querySelectorAll("[data-t]").forEach(function(el){
    el.addEventListener("mouseenter", mostra);
    el.addEventListener("mousemove", mostra);
    el.addEventListener("mouseleave", function(){ tip.style.opacity = "0"; });
  });
})();
"""
