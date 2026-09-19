# Satélites de coleta de dados — UCS + n2yo

Recorte de satélites de porte convencional cuja carga útil coleta dados, no
mesmo método do levantamento de nanossatélites em `D:\nanosats`, para que os
dois conjuntos sejam comparáveis.

Duas fontes, dois instantes:

| Fonte | O que dá | Data |
|---|---|---|
| [UCS Satellite Database](https://www.ucsusa.org/resources/satellite-database) (`UCS-Satellite-Database 5-1-2023.xlsx`) | o que cada satélite **é**: propósito declarado, órbita, massa, potência, vida prevista, operador, contratante, lançamento e fontes | retrato de **2023-05-01** |
| [n2yo.com](https://www.n2yo.com/satellites/) | o que cada satélite **está fazendo agora**: se continua em órbita, quando reentrou, em que categorias o rastreamento o classifica e o TLE atual | consulta em **2026-09-16** |

O `robots.txt` do n2yo não restringe nenhum caminho (`Disallow:` vazio).

## O recorte

A UCS **declara** `Purpose` e `Detailed Purpose`, então a classificação começa
pelo campo declarado — diferente do Nanosats Database, onde tudo teve de sair do
texto. Três recortes, não exclusivos entre si:

| Recorte | Critério |
|---|---|
| **A** — sensoriamento remoto | `Purpose` contém *Earth Observation*, *Earth Science* ou *Meteorological*, ou `Detailed Purpose` é um dos 37 valores de imageamento, radar, meteorologia, ciência da Terra e afins mapeados à mão em `regras_coleta.py` |
| **B** — coleta de plataformas no solo | `Detailed Purpose` = *Internet of Things (IoT)*; **ou** o operador está na lista de constelações de coleta/retransmissão de dados (Orbcomm, Swarm, Kepler, Gonets, Astrocast, Fleet, Hiber, Lacuna, Sateliot, Plan-S, Myriota, Kinéis, OQ, Totum, Aprize, SpaceQuest); **ou** o nome/comentário cita IoT, M2M, store-and-forward, Argos ou coleta de plataformas |
| **C** — sinais cooperativos e RF | AIS, ADS-B, ELINT/SIGINT, monitoramento de espectro, vigilância marítima por RF — por `Detailed Purpose`, por operador (HawkEye 360, Kleos, UnseenLabs, exactEarth) ou por texto |

A lista de operadores do recorte B existe porque a UCS registra **todas** as
constelações de IoT como `Communications` sem propósito detalhado: sem ela, o
equivalente grande do SCD brasileiro ficaria inteiro de fora. A lista está
aberta em `regras_coleta.py`, para ser discutida.

Fora do recorte por decisão explícita: `Detailed Purpose = Data Relay`, que na
base são os SDS da NRO — retransmissão de dados **entre satélites**, não coleta
de plataformas no solo.

Toda linha classificada traz as regras que dispararam nas colunas
`evidencia_sr`, `evidencia_dcs` e `evidencia_sinais`.

## Números

| | |
|---|---:|
| satélites na base UCS | 7.560 |
| **no recorte de coleta de dados (A ∪ B ∪ C)** | **1.575** |
| A — sensoriamento remoto | 1.320 |
| B — coleta de plataformas no solo | 231 |
| C — sinais cooperativos e RF | 349 |
| ainda em órbita em 2026-09-16 | 791 (50,2%) |
| reentraram desde a edição de 2023 | 773 |
| passaram da vida prevista e seguem operando | 284 de 346 (82%) |
| queda mediana de perigeu em 3 anos (só os que seguem em órbita) | −13,6 km |

Dois achados que valem para o planejamento do BAI-01:

- **O SCD-1 é o recordista de longevidade do recorte inteiro.** Lançado em 1993
  com 3 anos de vida prevista, está em órbita há 33,6 anos — mais que NOAA-15,
  DMSP F14 e os Orbcomm de primeira geração. O SCD-2, de 1998, é o quinto.
  Nos dois casos a missão é coleta de dados de plataformas no solo.
- **Metade da frota de 2023 já caiu.** A atrito se concentra nas constelações
  pequenas de órbita baixa: Planet (202 reentrados), Spire (122) e Swarm (90)
  respondem por mais da metade das reentradas.

Duas ressalvas que os dados obrigam a registrar:

- 83 satélites do recorte têm data de reentrada **anterior** a 2023-05-01, a
  própria data de corte da edição da UCS — a base já nascia com atraso.
- 20 registros têm NORAD que, no catálogo, é corpo de foguete ou detrito do
  mesmo lançamento, não a carga útil (entre eles o SCD-1, cujo NORAD correto é
  22490 e não 22491). `gerar_tabelas.py` corrige automaticamente quando o objeto
  vizinho tem nome conferindo com o do satélite — foram 2 casos — e marca os
  demais em `n2yo_tipo_objeto`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `ucs_todos.csv` | 7.560 satélites da UCS, todas as colunas declaradas + a classificação |
| `ucs_coleta_dados.csv` | só o recorte, com as colunas da UCS **e** a situação atual vinda do n2yo (48 colunas) |
| `ucs_coleta_dados.json` | o recorte com os campos brutos, as fontes citadas pela UCS, as categorias do n2yo e o TLE |
| `orbita_ucs_vs_n2yo.csv` | órbita declarada em 2023 contra a calculada do TLE de hoje, com a variação de perigeu e apogeu |
| `n2yo_categorias.csv` | uma linha por par satélite × categoria do n2yo, para todo o catálogo rastreado |
| `metricas.json` | as métricas consolidadas que alimentam o painel |
| `painel_metricas.html` | painel para abrir no disco (autônomo, com `<meta charset>`) |
| `painel_artifact.html` | o mesmo painel no formato de fragmento que o Artifact exige |
| `cache/` | HTML baixado do n2yo e o JSON intermediário da planilha — apague para forçar nova coleta |

### Colunas vindas do n2yo

`n2yo_nome`, `n2yo_em_orbita` (sim/não/?), `n2yo_reentrada`, `n2yo_categorias`,
`n2yo_pais`, `n2yo_local_lancamento`, `n2yo_lancamento`, `n2yo_nota`,
`n2yo_descricao`, `n2yo_tipo_objeto`, `n2yo_epoca_tle`, `n2yo_inclinacao`,
`n2yo_excentricidade`, `n2yo_periodo_min`, `n2yo_apogeu_km`, `n2yo_perigeu_km`,
`n2yo_url`.

Inclinação, excentricidade, período, apogeu e perigeu **não** são lidos de um
campo: saem do TLE publicado na ficha, convertidos aqui — período a partir do
movimento médio, semieixo maior pela terceira lei de Kepler, apogeu e perigeu
descontando o raio equatorial da Terra (6 378,137 km).

## Limites

- A UCS é um retrato de maio de 2023. O que voou depois não está na base, e
  satélites que já haviam reentrado antes dessa data também não.
- A órbita da UCS é a **nominal declarada**; a de hoje é a **osculante medida**
  pelo TLE. Parte da diferença entre as duas é decaimento real, parte é
  diferença de método — por isso as tabelas mostram os dois números lado a lado,
  e não só a variação.
- O campo NORAD da UCS nem sempre aponta para a carga útil: em alguns casos o
  objeto correspondente no catálogo é o corpo de foguete do mesmo lançamento. A
  coluna `n2yo_tipo_objeto` marca esses casos.
- **Custo não existe nesta base.** Quem tem valor declarado é o levantamento de
  nanossatélites (`D:\nanosats\custos_nanosats.csv`).

## Reexecutar

```bash
pip install openpyxl requests
python carregar_ucs.py "D:\Downloads\UCS-Satellite-Database 5-1-2023.xlsx"
python scrape_n2yo.py      # 58 categorias + uma ficha por satélite do recorte
python gerar_tabelas.py
python metricas.py && python gerar_painel.py
```

`python classificar.py` sozinho imprime a contagem por recorte e o ranking das
evidências — é o jeito rápido de ver o efeito de uma mudança nas regras.
