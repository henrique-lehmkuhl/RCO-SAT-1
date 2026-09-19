#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regras que separam, na UCS Satellite Database, as missões de coleta de dados.

Mesmos três recortes usados no levantamento de nanossatélites
(`D:\\nanosats\\regras_coleta.py`), para que os dois conjuntos sejam comparáveis:

    A - sensoriamento remoto: o satélite mede a Terra à distância
    B - coleta de plataformas no solo: DCS, IoT/M2M, store-and-forward
    C - sinais cooperativos e RF: AIS, ADS-B, VDES, ELINT, monitoramento espectral

A diferença é a procedência. O Nanosats Database não declara tipo de missão e
tudo teve de sair do texto; a UCS **declara** `Purpose` e `Detailed Purpose`,
então a classificação começa pelos campos declarados e só recorre a nome,
operador e comentário quando o campo declarado é omisso — que é o caso das
grandes constelações de IoT, registradas como "Communications" sem detalhe.

Cada regra que dispara grava seu rótulo na coluna de evidência do CSV.
"""

# ------------------------------------------------ A. sensoriamento remoto
# valores do campo `Purpose` que já definem o recorte
SR_PROPOSITO = (r"earth observation|earth science|meteorolog|"
                r"earth/space observation")

# valores do campo `Detailed Purpose` (a lista é fechada: são 53 valores na
# base, todos classificados à mão aqui)
SR_DETALHADO = {
    "Optical Imaging": "imageamento óptico",
    "Optical Imaging (video)": "imageamento óptico",
    "Optical Stereo Imaging": "imageamento óptico",
    "Optical/Video Imaging": "imageamento óptico",
    "Video Imaging": "imageamento óptico",
    "Imaging": "imageamento",
    "Multispectral Imaging": "multiespectral",
    "Hyperspectral Imaging": "hiperespectral",
    "Optical/Hyperspectral Imaging": "hiperespectral",
    "Infrared Imaging": "infravermelho",
    "Optical/Infrared Imaging": "infravermelho",
    "Optical Imaging/Infrared Imaging": "infravermelho",
    "Optical, Near-Infrared": "infravermelho",
    "Thermal Imaging": "infravermelho térmico",
    "Radar Imaging": "radar",
    "Radar Imaging (SAR)": "radar (SAR)",
    "Synthetic Aperture Radar (SAR)": "radar (SAR)",
    "Synthetic Aperture Imaging": "radar (SAR)",
    "Radar Surveillance": "radar",
    "Radar Imaging/Earth Science": "radar + ciência da Terra",
    "Radar Imaging/Electronic Intelligence": "radar",
    "Meteorology/Radar": "meteorologia + radar",
    "Laser Imaging": "lidar",
    "Subsurface Imaging": "subsuperfície",
    "Microwave Radiometer": "radiômetro de micro-ondas",
    "Earth Science": "ciência da Terra",
    "Earth Science/Meterology": "ciência da Terra + meteorologia",
    "Meteorology/Earth Science": "ciência da Terra + meteorologia",
    "Meteorology": "meteorologia",
    "Meteorology, Automatic Identification System (AIS)": "meteorologia",
    "Optical Imaging/Meterology": "imageamento óptico + meteorologia",
    "Optical Imaging/Meteorology": "imageamento óptico + meteorologia",
    "Optical Imaging/Automatic Identification System (AIS)": "imageamento óptico",
    "Remote Sensing": "sensoriamento remoto",
    "AI Remote Sensing": "sensoriamento remoto",
    "Maritime Observation": "observação marítima",
    "Early Warning": "alerta antecipado (IV)",
}

# ------------------------------- B. coleta de plataformas no solo (DCS/IoT)
DCS_DETALHADO = {
    "Internet of Things (IoT)": "IoT declarado",
    "Internet of Things (IoT)/Amateur Radio": "IoT declarado",
}

# Operadores cujo serviço é coleta/retransmissão de dados de terminais no solo.
# A UCS registra todos como "Communications" sem propósito detalhado, então sem
# esta lista as constelações de IoT — que são o equivalente grande do SCD
# brasileiro — ficariam de fora do recorte.
OPERADORES_DCS = {
    "ORBCOMM Inc.": "constelação M2M/IoT",
    "Swarm Technologies": "constelação IoT (SpaceBEE)",
    "Kepler Communications": "constelação IoT/backhaul de dados",
    "Gonets Satcom": "store-and-forward (Gonets-M)",
    "Astrocast": "constelação IoT/M2M",
    "Fleet Space Technologies": "constelação IoT",
    "Hiber Global": "constelação IoT",
    "Lacuna Space": "IoT por LoRa",
    "Lacuna Space/NanoAvionics": "IoT por LoRa",
    "Sateliot IoT": "constelação IoT (NB-IoT)",
    "Plan-S": "constelação IoT (Connecta)",
    "SpaceQuest, Ltd.": "carga de IoT/AIS",
    "Myriota": "constelação IoT",
    "Kineis": "coleta de dados (sucessor do Argos)",
    "OQ Technology": "constelação NB-IoT",
    "Totum Labs": "constelação IoT",
    "Aprize Satellite, Argentina": "mensageria M2M + AIS (AprizeSat)",
    "Aprize Satellite, Canada": "mensageria M2M + AIS (AprizeSat)",
}

# texto livre (nome + comentários), quando nada acima pegou
DCS_TEXTO = [
    ("IoT/M2M no texto", r"\bIoT\b|\binternet of things\b|\bM2M\b|"
                         r"machine[- ]to[- ]machine\b|\bNB[- ]?IoT\b"),
    ("store-and-forward no texto", r"\bstore[ -](?:and|&)[ -]forward\b"),
    ("coleta de plataformas no texto",
     r"\bdata[- ]collect\w*\b|\bArgos\b(?! Neo on a Generic)|\bDCP\b|\bPCD\b|"
     r"\bcollect\w* data from (?:ground|remote|sensors?|platforms?|buoys?)\b|"
     # o arquétipo do recorte tem nome em português: SCD-1/SCD-2 do INPE,
     # que a UCS registra como "Meteorology/Earth Science"
     r"coleta de dados|colecta de datos|"
     r"\bcollects?\b[^.]{0,40}\b(?:environmental|meteorological)\b[^.]{0,20}\bdata\b"),
    ("rastreamento de ativos no texto",
     r"\basset tracking\b|\btrack\w* (?:of )?(?:containers|livestock|assets|"
     r"cargo|fleets?|animals|wildlife)\b"),
]

# ------------------------------- C. sinais cooperativos e sensoriamento RF
SIN_DETALHADO = {
    "Automatic Identification System (AIS)": "AIS (navios)",
    "Meteorology, Automatic Identification System (AIS)": "AIS (navios)",
    "Optical Imaging/Automatic Identification System (AIS)": "AIS (navios)",
    "ADS-B Receiver": "ADS-B (aviação)",
    "Electronic Intelligence": "inteligência eletrônica (ELINT)",
    "Radar Imaging/Electronic Intelligence": "inteligência eletrônica (ELINT)",
    "Signals Intelligence": "inteligência de sinais (SIGINT)",
    "Radio Spectrum Monitoring": "monitoramento de espectro",
    "Radio Frequency Monitoring": "monitoramento de espectro",
    "Maritime Surveillance": "vigilância marítima por RF",
}

SIN_PROPOSITO = r"maritime tracking"

OPERADORES_SINAIS = {
    "HawkEye 360": "geolocalização de RF",
    "Kleos Space": "geolocalização de RF",
    "UnseenLabs": "geolocalização de RF",
    "exactEarth": "AIS (navios)",
    "Indian Space Research Organization (ISRO)/exactEarth": "AIS (navios)",
}

SIN_TEXTO = [
    ("AIS no texto", r"\bAIS\b|\bautomatic identification system\b"),
    ("ADS-B no texto", r"\bADS[- ]?B\b|automatic dependent surveillance"),
    ("VDES no texto", r"\bVDES\b"),
    ("ELINT/SIGINT no texto", r"\bELINT\b|\bSIGINT\b|signals? intelligence|"
                              r"electronic intelligence"),
    ("espectro/RF no texto", r"spectrum monitoring|radio frequency monitoring|"
                             r"RF geolocation|dark (?:vessels?|ships?)"),
]

# ------------------------------------------------- contexto (qualifica só)
CONTEXTO_PROPOSITO = {
    "comunicação": r"^communications",
    "tecnologia": r"technology (?:development|demonstration)",
    "navegação/PNT": r"navigation|positioning",
    "ciência espacial": r"space science|space observation",
    "vigilância": r"surveillance",
    "educação": r"educational",
}
CONTEXTO_USUARIO = {"Military": "militar", "Commercial": "comercial",
                    "Government": "governo", "Civil": "civil"}

# fora do recorte por definição, mesmo citando "data relay": os SDS da NRO
# retransmitem dados *entre satélites*, não coletam de plataformas no solo
FORA_DO_RECORTE_DETALHADO = {"Data Relay"}
