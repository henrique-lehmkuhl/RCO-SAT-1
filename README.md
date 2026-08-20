# Projeto CubeSat Educacional — Índice

Este diretório contém a documentação de engenharia de sistemas do projeto de um
CubeSat educacional para portfólio, desenvolvido seguindo o processo clássico
de Engenharia de Sistemas (necessidade → requisitos → arquitetura → projeto de
subsistemas → verificação e validação → cronograma), nos moldes usados em
missões CubeSat reais (CubeSat Design Specification, manuais da NASA
CSLI/GSFC e diretrizes ECSS adaptadas a projetos de pequena escala).

## Missão de referência

**Nome de trabalho:** RCO-SAT 1
**Classe:** CubeSat 1U, com arquitetura expansível para 2U/3U
**Tipo de missão:** Demonstração tecnológica — validação em órbita de um
sistema de controle de atitude ativo de baixo custo (magnetorquers + roda de
reação) integrado a um barramento OBDH/EPS/TT&C totalmente autoral, com uma
carga útil de câmera simples para gerar dados de apontamento verificáveis.

> Este é o ponto de partida e será medida que os requisitos forem amadurecendo.

## Estrutura dos documentos

| Arquivo | Fase de SE | Conteúdo |
|---|---|---|
| `01_Necessidade_e_Objetivos.md` | Fase 0 — Análise da necessidade | Motivação, objetivos de missão, CONOPS, restrições |
| `02_Requisitos_de_Sistema.md` | Fase A — Requisitos | Requisitos de missão, funcionais e de desempenho, rastreáveis |
| `03_Arquitetura_e_Orcamentos.md` | Fase A/B — Arquitetura | Arquitetura de blocos, orçamento de massa, potência, dados e link |
| `04_Subsistema_Estrutura.md` | Fase B — Projeto preliminar | EPS mecânica: estrutura, layout, integração |
| `05_Subsistema_EPS.md` | Fase B | Potência elétrica |
| `06_Subsistema_OBDH.md` | Fase B | Computador de bordo e software |
| `07_Subsistema_ADCS.md` | Fase B | Controle de atitude e determinação de órbita |
| `08_Subsistema_TTC.md` | Fase B | Telemetria, telecomando e comunicações |
| `09_Carga_Util.md` | Fase B | Payload (câmera de demonstração) |
| `10_Plano_VV.md` | Fase C/D — Verificação e Validação | Plano de testes, matriz de rastreabilidade |
| `11_Cronograma_e_Marcos.md` | Gestão | EAP, marcos, riscos |


