# Nanosats Database — missões de coleta de dados

Dados extraídos de <https://www.nanosats.eu/database> (Nanosats Database, de Erik Kulu —
"última grande atualização" declarada na fonte: **2026-07-31**).

Coleta: 2026-09-16 · scripts: `scrape_nanosats.py` + `gerar_tabelas.py`
(Python 3 + requests + beautifulsoup4 + lxml)

O banco cobre **4.938 linhas** (nanossatélites, CubeSats, PocketQubes, picossatélites e
ThinSats — lançados, planejados e cancelados), descritas em **2.408 fichas** de missão:
uma ficha pode cobrir vários satélites (constelações como Flock, Lemur-2 e SpaceBEE).
O que foi baixado: o índice, as 2.408 fichas `/sat/<slug>.html`, as 60 páginas
`/keyword/<slug>.html` e `/tables.html` (de onde sai a tabela *CubeSat Costs*).
O `robots.txt` do site bloqueia `/database/sat/*`, caminho que não é usado aqui.

## O recorte "coleta de dados"

O banco **não publica** uma coluna de tipo/aplicação de missão — as 8 colunas do índice são
nome, organização, nação, tipo (U/massa), data de lançamento, status, descrição curta e foto.
A classificação foi derivada do texto de cada ficha (Oneliner + Description + Notes +
Results + Keywords) por expressões regulares declaradas em `regras_coleta.py`, em três
recortes **não exclusivos**:

| Recorte | O que é | Fichas | Linhas |
|---|---|---:|---:|
| **A** — sensoriamento remoto | o satélite mede o alvo à distância e há evidência de que o alvo é a Terra (imageamento, multi/hiperespectral, IV térmico, SAR, radio-ocultação, aplicações de vegetação, fogo, oceano, atmosfera…) | 526 | 1.848 |
| **A′** — câmera sem alvo declarado | só menciona câmera/imageamento, sem dizer o que observa — **fora** do recorte, marcado para quem quiser ampliar | 349 | 408 |
| **B** — coleta de plataformas (DCS/IoT) | recebe dados de plataformas no solo: *store-and-forward*, IoT/M2M, LoRa/Sigfox, PCDs, Argos, rastreamento de ativos e fauna — é o sentido brasileiro clássico de "coleta de dados" (SCD-1/SCD-2) | 230 | 942 |
| **C** — sinais cooperativos e RF | recebe sinais emitidos por terceiros: AIS (navios), ADS-B (aviação), VDES, GMDSS, geolocalização RF/SIGINT | 130 | 555 |
| **Recorte (A ∪ B ∪ C)** | | **779** | **2.781** |

Toda linha classificada traz **as regras que dispararam** nas colunas `evidencia_sr`,
`evidencia_dcs` e `evidencia_sinais`, de modo que a classificação pode ser conferida à mão
contra o texto da fonte. Colunas auxiliares:

- `contexto` — tecnologia, educação, ciência, comunicação, navegação/PNT, defesa;
- `alvo_fora_da_terra` — missão lunar/interplanetária. Quando a única evidência de
  sensoriamento remoto é instrumental (ex.: "multiespectral") e o alvo é a Lua, a missão é
  rebaixada de A para A′;
- `carga_radioamador` — separa os *store-and-forward* que são digipeaters amadores
  (BIRDS, EASAT, HADES…) dos sistemas de coleta propriamente ditos.

### Limites conhecidos

- É classificação por texto: uma missão cuja ficha não descreve a carga útil fica de fora.
  Das 2.408 fichas, 779 entraram no recorte, 308 dispararam só a regra fraca A′ e 1.321 não
  dispararam nenhuma — a maior parte destas é demonstração tecnológica, propulsão, ciência
  espacial e educação sem carga de dados.
- Sobra alguma cauda de falso positivo (ex.: `beiyou-1` cai em "radar/SAR" porque o texto
  cita *outro* satélite SAR). Por isso a coluna de evidência existe: filtre por ela antes de
  usar qualquer subconjunto em análise fechada.
- "AIS" e "ADS-B" costumam ser cargas secundárias; a ficha não distingue carga principal de
  secundária, e o dataset também não.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `nanosats_todos.csv` | 4.938 linhas — **todas** as missões do banco, todas as colunas do índice + os campos da ficha + a classificação. Sem os textos longos (ficam no recorte) |
| `nanosats_coleta_dados.csv` | 2.781 linhas — só o recorte A∪B∪C, com **as 66 colunas**, incluindo descrição, resultados, notas, subsistemas COTS e fontes |
| `nanosats_coleta_dados.json` | 779 fichas do recorte com os campos **brutos** (rótulo original do site), os links de cada campo, as listas (COTS, mesmo lançamento), as fotos e a data da última modificação da ficha |
| `custos_nanosats.csv` | 186 registros de custo, 101 missões — ver abaixo |
| `resultados_nanosats.csv` | 385 linhas com resultado publicado (308) e/ou causa de falha (115) |
| `keywords_nanosats.csv` | 2.399 pares satélite × palavra-chave, das 60 páginas de keyword do site |
| `cache/` | HTML baixado (só o `#main-content` de cada ficha) + `nanosats_bruto.json`. **Não versionado** — apague para forçar nova coleta |

### Colunas de `nanosats_coleta_dados.csv`

Do índice: `nome`, `outros_nomes`, `nome_tabela`, `slug`, `url_pagina`,
`organizacao_indice`, `nacao_indice`, `tipo_u_massa`, `data_lancamento`,
`status_indice`, `descricao_indice`, `foto`.

Da ficha da missão: `nome_ficha`, `tipo_espacial`, `unidades_massa`, `massa_kg`, `status`,
`lancado_em`, `norad_id`, `orbita`, `deployer`, `lancador`, `organizacao`, `operador`,
`fabricante`, `instituicao`, `tipo_entidade`, `pais`, `pais_integracao`, `sede`,
`intermediario_lancamento`, `parceiros`, `custos_ficha`, `oneliner`, `descricao`,
`resultados`, `causa_falha`, `notas`, `keywords_ficha`, `subsistemas_cots`,
`servico_estacao_solo`, `sistema_controle_missao`, `no_mesmo_lancamento`, `fontes`,
`url_custo`, `urls_resultados`, `url_status`, `keywords_site`, `fotos`, `n_fontes`,
`n_fotos`, `ultima_modificacao`.

Da classificação: `categoria_coleta`, `sr_forte`, `sr_fraco`, `dcs_iot`, `sinais`,
`no_recorte`, `evidencia_sr`, `evidencia_dcs`, `evidencia_sinais`, `contexto`,
`alvo_fora_da_terra`, `carga_radioamador`, `tem_custo_declarado`, `tem_resultados`.

Campos ausentes na fonte vêm vazios — o site publica rótulos diferentes conforme a época da
ficha (`Organisation`/`Organization`/`Entity name`, `Nation`/`Country`), e o mapeamento de
sinônimos está no topo de `gerar_tabelas.py`.

## Custos

Três origens, na coluna `origem`:

1. **tabela CubeSat Costs** do site (90 linhas) — traz tamanho, integrador (AIVT),
   financiador e link da fonte;
2. **campo `Costs` da ficha** (79 missões);
3. **texto livre** (17 menções) — valores citados na descrição, com o `trecho` em volta.

`valor_num` + `moeda` são uma leitura numérica **de melhor esforço** do primeiro valor do
texto; `custo_por_satelite` recupera a linha "Single platform: …" quando a fonte a declara.
`valor_suspeito = sim` marca número com separador de milhar incompleto na fonte
(ex.: MIR-SAT1, `$405,00`). **O texto em `custo` é a referência**, não o número.

Atenção ao que cada valor cobre: há contrato de plataforma, programa inteiro com lançamento
e operação, lote de N satélites. A coluna `custo` diz qual é o caso em quase todas as linhas.

Ordem de grandeza por classe, **descontando duplicatas e valores suspeitos**, só para
missões do recorte com valor em dólar (n = 33):

| Classe | n | Mediana (USD) | Faixa (USD) |
|---|---:|---:|---|
| 1U | 2 | 30 mil | 200 – 60 mil |
| 2U | 2 | 935 mil | 300 mil – 1,57 mi |
| 3U | 6 | 1,91 mi | 1,0 – 5,9 mi |
| 6U | 17 | 2,83 mi | 880 mil – 33 mi |
| 8U | 2 | 3,98 mi | 2,0 – 5,95 mi |
| 12U | 1 | 4,7 mi | — |
| 16U | 2 | 6,25 mi | 2,5 – 10 mi |

Considerando **todas** as missões do banco com custo em dólar (n = 77), as medianas ficam em
3U ≈ 1,94 mi, 6U ≈ 2,83 mi e 12U ≈ 4,0 mi — com extremos que são missões de ciência ou
lunares (12U até 105 mi). São valores **declarados em fontes públicas heterogêneas**, sem
correção monetária e sem normalização de escopo: servem como ordem de grandeza, não como
base de orçamento.

## Resultados

`resultados_nanosats.csv` traz o campo `Results` da ficha (308 linhas), que é o que a fonte
publicou de resultado em órbita — normalmente citações datadas com link — e o campo
`Failure cause` (115 linhas). 145 linhas são do recorte de coleta de dados. Para uma leitura
de taxa de sucesso, use `status_indice` de `nanosats_todos.csv`, que distingue operacional,
reentrada, sem sinal, falha de lançamento, cancelada e não lançada.

## Reexecutar

```bash
pip install requests beautifulsoup4 lxml
python scrape_nanosats.py      # baixa (~34 MB em cache) e extrai
python gerar_tabelas.py        # classifica e escreve os CSVs/JSON
```

`python scrape_nanosats.py --parse` reaproveita o cache sem baixar nada.
Para mudar o recorte, edite `regras_coleta.py` e rode só `gerar_tabelas.py`.
