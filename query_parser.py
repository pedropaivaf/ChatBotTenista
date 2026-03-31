import re
import unicodedata

# Mapeamento de nomes de países (lowercase, sem acento) para o nome canônico usado no tennis_data.json
COUNTRY_MAP = {
    "brasil": "Brasil", "espanha": "Espanha", "italia": "Itália", "itália": "Itália",
    "alemanha": "Alemanha", "russia": "Rússia", "rússia": "Rússia", "noruega": "Noruega",
    "polonia": "Polônia", "polônia": "Polônia", "eua": "EUA", "estados unidos": "EUA",
    "america": "EUA", "australia": "Austrália", "austrália": "Austrália",
    "bulgaria": "Bulgária", "bulgária": "Bulgária", "grecia": "Grécia", "grécia": "Grécia",
    "bielorrussia": "Bielorrússia", "bielorrússia": "Bielorrússia",
    "cazaquistao": "Cazaquistão", "cazaquistão": "Cazaquistão",
    "china": "China", "republica tcheca": "Rep. Tcheca", "rep. tcheca": "Rep. Tcheca",
    "ucrania": "Ucrânia", "ucrânia": "Ucrânia", "tunisia": "Tunísia", "tunísia": "Tunísia",
    "croacia": "Croácia", "croácia": "Croácia", "suica": "Suíça", "suíça": "Suíça",
    "reino unido": "Reino Unido", "inglaterra": "Reino Unido",
    "dinamarca": "Dinamarca", "canada": "Canadá", "canadá": "Canadá",
    "chile": "Chile", "franca": "França", "frança": "França",
    "argentina": "Argentina", "holanda": "Holanda", "portugal": "Portugal",
    "hungria": "Hungria", "belgica": "Bélgica", "bélgica": "Bélgica",
    "japao": "Japão", "japão": "Japão", "india": "Índia", "índia": "Índia",
    "egito": "Egito", "colombia": "Colômbia", "colômbia": "Colômbia",
    "eslovaquia": "Eslováquia", "eslováquia": "Eslováquia",
    "mexico": "México", "méxico": "México", "finlandia": "Finlândia", "finlândia": "Finlândia",
    "austria": "Áustria", "áustria": "Áustria", "nova zelandia": "Nova Zelândia",
    "romenia": "Romênia", "romênia": "Romênia", "servia": "Sérvia", "sérvia": "Sérvia",
}

# Gentílicos (masculino e feminino) para o país canônico
DEMONYM_MAP = {
    "brasileiro": "Brasil", "brasileira": "Brasil", "brasileiros": "Brasil", "brasileiras": "Brasil",
    "espanhol": "Espanha", "espanhola": "Espanha", "espanhois": "Espanha",
    "italiano": "Itália", "italiana": "Itália", "italianos": "Itália",
    "alemao": "Alemanha", "alemã": "Alemanha", "alemaes": "Alemanha",
    "russo": "Rússia", "russa": "Rússia", "russos": "Rússia",
    "americano": "EUA", "americana": "EUA", "americanos": "EUA",
    "australiano": "Austrália", "australiana": "Austrália",
    "frances": "França", "francesa": "França", "franceses": "França",
    "argentino": "Argentina", "argentina": "Argentina",
    "portugues": "Portugal", "portuguesa": "Portugal",
    "japones": "Japão", "japonesa": "Japão",
    "chines": "China", "chinesa": "China",
    "canadense": "Canadá", "canadenses": "Canadá",
    "chileno": "Chile", "chilena": "Chile",
    "colombiano": "Colômbia", "colombiana": "Colômbia",
    "mexicano": "México", "mexicana": "México",
    "servio": "Sérvia", "servia": "Sérvia",
    "suico": "Suíça", "suica": "Suíça",
    "noruegues": "Noruega", "norueguesa": "Noruega",
    "grego": "Grécia", "grega": "Grécia",
    "croata": "Croácia", "croatas": "Croácia",
    "belga": "Bélgica", "belgas": "Bélgica",
    "holandes": "Holanda", "holandesa": "Holanda",
    "indiano": "Índia", "indiana": "Índia",
    "romeno": "Romênia", "romena": "Romênia",
}

# Marcadores temporais que indicam "agora/atualmente"
TEMPORAL_MARKERS = [
    "atualmente", "hoje", "agora", "atual", "no momento", "neste momento",
    "hoje em dia", "em 2026", "nesse momento",
]

# Marcadores de superlativo / "o melhor"
SUPERLATIVE_MARKERS = [
    "melhor", "top 1", "número 1", "numero 1", "primeiro", "líder",
    "maior", "mais bem", "principal", "destaque",
]

# Marcadores de circuito
ATP_MARKERS = ["atp", "masculino", "homens", "homem"]
WTA_MARKERS = ["wta", "feminino", "mulheres", "mulher"]

# Preposições a ignorar na detecção de país
PREPOSITIONS = {"do", "da", "dos", "das", "de", "no", "na", "nos", "nas"}


def _strip_accents(text):
    """Remove acentos para comparação fuzzy."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def _detect_country(msg_lower):
    """Detecta menção a um país na mensagem, retornando o nome canônico ou None."""
    # Primeiro tenta gentílicos (mais específicos)
    msg_no_accents = _strip_accents(msg_lower)
    for demonym, country in DEMONYM_MAP.items():
        if demonym in msg_no_accents:
            return country

    # Remove preposições comuns para facilitar match de país
    words = msg_lower.split()
    clean_words = [w for w in words if w not in PREPOSITIONS]
    clean_msg = ' '.join(clean_words)
    clean_msg_no_accents = _strip_accents(clean_msg)

    # Tenta nomes de países (mais longos primeiro para evitar match parcial)
    sorted_countries = sorted(COUNTRY_MAP.keys(), key=len, reverse=True)
    for country_key in sorted_countries:
        key_no_accents = _strip_accents(country_key)
        if key_no_accents in clean_msg_no_accents or country_key in clean_msg:
            return COUNTRY_MAP[country_key]

    return None


def _detect_limit(msg_lower):
    """Detecta pedido de quantidade tipo 'top 5', 'top 20'."""
    match = re.search(r'top\s*(\d+)', msg_lower)
    if match:
        return int(match.group(1))
    return None


def parse_query(msg_lower):
    """
    Analisa a mensagem do usuário e extrai modificadores estruturados.
    Usa string matching direto (não stems) para maior precisão em português.

    Retorna dict com:
        country_filter: str ou None
        is_current: bool
        wants_best: bool
        circuit: str ("ATP", "WTA" ou None)
        limit: int ou None
    """
    country_filter = _detect_country(msg_lower)
    is_current = any(marker in msg_lower for marker in TEMPORAL_MARKERS)
    wants_best = any(marker in msg_lower for marker in SUPERLATIVE_MARKERS)

    circuit = None
    if any(w in msg_lower for w in WTA_MARKERS):
        circuit = "WTA"
    elif any(w in msg_lower for w in ATP_MARKERS):
        circuit = "ATP"

    limit = _detect_limit(msg_lower)

    return {
        "country_filter": country_filter,
        "is_current": is_current,
        "wants_best": wants_best,
        "circuit": circuit,
        "limit": limit,
    }
