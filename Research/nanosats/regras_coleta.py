#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regras que separam, no Nanosats Database, as missões de coleta de dados.

O banco não publica uma coluna "tipo de missão": a classificação tem de sair do
texto de cada ficha (Oneliner + Description + Notes + Results + Keywords). Cada
regra é um par (rótulo, expressão regular); o rótulo de toda regra que disparou
entra na coluna `evidencia` do CSV, de modo que qualquer linha pode ser
conferida à mão contra o texto da fonte.

Três recortes, não exclusivos entre si:

    A - sensoriamento remoto (o satélite mede o alvo à distância)
        A1 forte: há evidência de que o alvo é a Terra ou sua atmosfera
        A2 fraco: só se menciona câmera/imageamento, sem dizer o alvo
    B - coleta de dados de plataformas no solo (DCS/IoT/M2M, store-and-forward)
    C - recepção de sinais cooperativos (AIS, ADS-B, VDES) e sensoriamento RF

"Coleta de dados" no sentido brasileiro clássico (SCD-1/SCD-2, Sistema
Brasileiro de Coleta de Dados) é o recorte B. O recorte A é o que corresponde à
meta M.1 do BAI-01 ("adquirir dados de imageamento do território nacional").
"""

# --------------------------------------------------- A. sensoriamento remoto
SR_FORTE = [
    ("observação da Terra", r"\bearth[- ]observation\b|\bremote sensing\b|\bearth[- ]sensing\b|\bEO (?:mission|payload|satellite|constellation|data|imag\w+)\b"),
    ("imagens da Terra", r"\bearth imag\w+\b|\bimag\w+ of (?:the )?(?:earth|ground|land|ocean|sea|terrain|surface|territory)\b|\b(?:image|photograph)\w* (?:the )?(?:earth|ground|land|ocean)\b|\bsatellite imagery\b|\bimagery (?:of|for|product)\w*\b|\bground sampling distance\b|\bGSD\b"),
    ("multiespectral/pancromático", r"\bmulti[- ]?spectral\b|\bpanchromatic\b|\bspectral bands?\b"),
    ("hiperespectral", r"\bhyper[- ]?spectral\b"),
    ("infravermelho/térmico", r"\bthermal (?:infrared|imag\w+|camera|sensor|band)\w*\b|\b(?:mid|long|short)[- ]?wave infrared\b|\bMWIR\b|\bLWIR\b|\bSWIR\b|\bTIR\b|\bthermography\b|\binfrared imag\w+\b"),
    ("radar/SAR", r"\bSAR\b|\bsynthetic aperture radar\b|\bradar imag\w+\b|\bscatterometer\b|\bradar altimeter\b|\bInSAR\b"),
    ("radio-ocultação/GNSS-R", r"\bradio occultation\b|\bGNSS[- ]?RO\b|\bGPS[- ]?RO\b|\bGNSS[- ]?R\b|\breflectometr\w+\b"),
    ("atmosfera/meteorologia", r"\bweather (?:data|forecast\w*|monitoring|satellite|model)\w*\b|\batmospheric (?:sounding|profil\w+|monitoring|measurement|composition)\w*\b|\baerosols?\b|\bcloud (?:cover|imag\w+|profil\w+|structure)\w*\b|\bprecipitation\b(?! of (?:trapped|energetic|particles|electrons))|\bozone\b|\bmeteorolog\w+\b"),
    ("gases de efeito estufa", r"\bmethane\b|\bgreenhouse gas\w*\b|\bCO2 (?:emission|monitor\w*|measur\w*|column)\w*\b|\bcarbon (?:monitoring|emissions|flux|dioxide measur\w*)\b"),
    ("vegetação/agricultura", r"\bagricultur\w+\b|\bcrops?\b|\bNDVI\b|\bvegetation\b|\bdeforestation\b|\bforestry\b|\bland (?:use|cover)\b|\bbiomass\b|\bprecision farming\b"),
    ("fogo/desastres", r"\bwildfires?\b|\bfire detection\b|\bforest fires?\b|\bfloods?\b|\bdisaster (?:monitoring|management|response|mitigation)\b|\bhot ?spots?\b|\bearly warning (?:of|for|system)\b"),
    ("oceano/criosfera", r"\bocean colou?r\b|\bsea surface temperature\b|\bsea ice\b|\bglaciers?\b|\bbathymetr\w+\b|\bchlorophyll\b|\bocean monitoring\b"),
    ("solo/água", r"\bsoil moisture\b|\bwater quality\b|\bhydrolog\w+\b|\bsnow cover\b|\bdrought\b"),
    ("aplicação territorial", r"\bland management\b|\bmapping of\b|\bcartograph\w+\b|\burban (?:monitoring|planning|heat)\b|\bnight ?lights?\b|\bborder monitoring\b|\bmining (?:monitoring|activity)\b|\bpipeline monitoring\b|\billegal (?:logging|fishing|mining)\b"),
]

SR_FRACO = [
    ("câmera a bordo", r"\bcameras?\b|\bimagers?\b|\bimaging (?:payload|system|experiment)\b|\btake (?:pictures|photos|images)\b|\bimaging\b"),
]

# ------------------------------- B. coleta de dados de plataformas (DCS/IoT)
DCS = [
    ("IoT/M2M", r"\bIoT\b|\binternet of things\b|\bM2M\b|\bmachine[- ]to[- ]machine\b|\bNB[- ]?IoT\b"),
    ("store-and-forward", r"\bstore[ -](?:and|&)[ -]forward\b|\bmessage (?:store|forwarding)\b"),
    ("sistema de coleta de dados", r"\bdata[- ]collection (?:platform|system|transponder|service|network|mission|payload)\w*\b|\bremote data collection\b|\bDCS\b|\bDCP\b|\bARGOS\b(?!\s*-\s*MINOTAUR)|\bcollect\w* (?:environmental |sensor |telemetry )?data from (?:ground|remote|distributed|in[- ]situ|sensors?|platforms?|buoys?|stations?|terminals?)\b"),
    ("LoRa/Sigfox", r"\bLoRa\w*\b|\bSigfox\b"),
    ("sensores/plataformas remotas", r"\b(?:remote|unattended|environmental|in[- ]situ|distributed|ground[- ]based)[- ](?:sensors?|stations?|terminals?|nodes?|platforms?|devices?)\b|\bsensor networks?\b|(?<!space )(?<!solar )\bweather (?:buoys?|stations?)\b|\bocean buoys?\b|\bPCD\b"),
    ("rastreamento de ativos/fauna", r"\basset tracking\b|\btrack\w* (?:of )?(?:animals|mammals|birds|wildlife|containers|livestock|vehicles|assets|cargo|fleets?)\b|\banimal (?:tracking|migration)\b|\bwildlife tracking\b|\bfleet management\b"),
    ("conectividade de dispositivos remotos", r"\bconnect\w* (?:remote |unconnected |isolated )?(?:devices|assets|sensors|things|machines|terminals)\b|\bnarrow ?band (?:communication|service|connectivity|payload)\w*\b|\bsatellite messaging\b|\btwo[- ]way (?:data )?(?:messaging|communication) (?:with|for) (?:devices|sensors|terminals)\b"),
    ("telemetria de clientes/SCADA", r"\bSCADA\b|\btelemetry from (?:ground|remote|customer|field)\w*\b|\bfield devices\b|\bsmart (?:meter|agriculture|farming)\w*\b"),
]

# Se a expressão abaixo aparecer na vizinhança (±60 caracteres) do trecho que
# disparou a regra, o rótulo é descartado: o alvo está em órbita, não no solo.
NEGATIVAS_CONTEXTO = {
    "sensores/plataformas remotas": r"space[- ]based|in orbit|orbital|inter[- ]?satellite|space weather|onboard sensors",
}

# ----------------------------- C. recepção de sinais cooperativos e RF
SINAIS = [
    ("AIS (navios)", r"\bAIS\b|\bautomatic identification system\b"),
    ("ADS-B (aviação)", r"\bADS[- ]?B\b|\bautomatic dependent surveillance\b"),
    ("VDES/VDE-SAT", r"\bVDES\b|\bVDE[- ]?SAT\b"),
    ("socorro/GMDSS", r"\bGMDSS\b|\bCOSPAS\b|\bSARSAT\b|\bemergency beacons?\b|\bdistress (?:signals?|beacons?|alerts?)\b|\bsearch and rescue\b"),
    ("geolocalização RF/SIGINT", r"\bRF (?:geolocation|detection|monitoring|sensing|intelligence|mapping)\b|\bSIGINT\b|\bsignals? intelligence\b|\bspectrum (?:monitoring|mapping|survey|awareness)\b|\bmaritime domain awareness\b|\bdark (?:vessels?|ships?)\b|\bvessel (?:monitoring|detection|tracking)\b|\bradio frequency mapping\b"),
]

# ------------------------------------------- contexto (qualifica, não recorta)
CONTEXTO = {
    "tecnologia": r"\btechnolog\w+ demonstrat\w+\b|\bin[- ]orbit (?:demonstrat\w+|validation)\b|\bIOD\b|\bproof of concept\b|\bdemonstrat\w+ (?:a |the )?(?:new|novel)\b|\bqualif\w+ (?:in orbit|the platform)\b",
    "educação": r"\beducational\b|\bstudents?\b|\bhands[- ]on\b|\buniversity (?:project|program|team)\w*\b|\btrain\w+ (?:students|engineers|personnel)\b|\bcapacity building\b",
    "ciência": r"\bscientific\b|\bscience mission\b|\bspace weather\b|\bionospher\w+\b|\bmagnetospher\w+\b|\bastronom\w+\b|\bastrophysic\w+\b|\bgamma[- ]ray\w*\b|\bX[- ]ray\w*\b|\bcosmic rays?\b|\bexoplanets?\b|\bbiolog\w+\b|\bmicrogravity\b|\bradiation (?:measurement|environment|dosimet\w+|belt)\w*\b|\bthermosphere\b",
    "comunicação": r"\bcommunicat\w+\b|\bbroadband\b|\bbackhaul\b|\btranspond\w+\b|\bamateur radio\b|\bham radio\b|\bAPRS\b|\bdigipeater\b|\bvoice repeater\b|\b5G\b|\bdirect[- ]to[- ](?:cell|device)\b|\bintersatellite links?\b",
    "navegação/PNT": r"\bnavigation\b|\bPNT\b|\bGNSS augmentation\b|\btiming service\b",
    "defesa/militar": r"\bmilitary\b|\bdefen[cs]e\b|\barmy\b|\bnavy\b|\bair force\b|\btactical\b|\bintelligence, surveillance\b|\bISR\b",
}

# palavras-chave publicadas pelo próprio site que reforçam cada recorte
KW_SR = {"Hyperspectral"}
KW_DCS = {"LoRa", "Constellation-As-A-Service"}
KW_SIN = {"AIS", "ADS-B", "VDES"}

# carga útil de radioamador: muitos "store-and-forward" do recorte B são
# digipeaters amadores, úteis de separar numa coluna própria
RADIOAMADOR = (r"\bamateur radio\b|\bham radio\b|\bradio ?amateur\w*\b|\bAMSAT\b|"
               r"\bdigipeater\b|\bAPRS\b|\bIARU\b|\blinear transponder\b")

# ------------------------- alvo fora da órbita terrestre (Lua, Marte, etc.)
FORA_DA_TERRA = (r"\blunar\b|\bmoon\b|\bmars\b|\bmartian\b|\basteroids?\b|"
                 r"\bcomets?\b|\bvenus\b|\bjupiter\b|\binterplanetary\b|"
                 r"\bdeep space\b|\bcislunar\b|\bheliocentric\b")

# rótulos de SR_FORTE que provam que o alvo é a Terra: uma missão lunar que
# também observa a Terra continua contando como sensoriamento remoto terrestre
SR_ESPECIFICO_TERRA = {
    "observação da Terra", "imagens da Terra", "atmosfera/meteorologia",
    "gases de efeito estufa", "vegetação/agricultura", "fogo/desastres",
    "oceano/criosfera", "solo/água", "aplicação territorial",
    "radio-ocultação/GNSS-R",
}

# valores monetários no texto livre (custos citados fora do campo "Costs")
MOEDA = (r"(?:(?:US|AU|CA|NZ|HK|S)?\$|€|£|¥|₹|R\$|SEK|EUR|USD|GBP|CHF|NOK|DKK|"
         r"PLN|CZK|JPY|CNY|RMB|INR|KRW|AED)\s?[\d][\d.,]*\s?"
         r"(?:million|billion|thousand|[MmKkBb]\b)?"
         r"|\b[\d][\d.,]*\s?(?:million|billion)\s?"
         r"(?:SEK|EUR|USD|GBP|NOK|DKK|CZK|PLN|JPY|CNY|INR|KRW|euros?|dollars?|"
         r"pounds?|yen|crowns?)\b")
