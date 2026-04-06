# Importa o módulo 're' para trabalhar com expressões regulares (regex), usado para encontrar padrões em texto
import re
# Importa o módulo 'unicodedata' para manipular caracteres Unicode, permitindo remover acentos de strings
import unicodedata

# Mapeamento de nomes de países (lowercase, sem acento) para o nome canônico usado no tennis_data.json
# Este dicionário associa variações de nomes de países (com e sem acento, abreviações) ao nome padronizado
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
# Este dicionário mapeia gentílicos (ex: "brasileiro", "brasileira") ao nome padronizado do país
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
# Lista de palavras/expressões que o usuário pode usar para perguntar sobre informações atuais
TEMPORAL_MARKERS = [
    "atualmente", "hoje", "agora", "atual", "no momento", "neste momento",
    "hoje em dia", "em 2026", "nesse momento",
]

# Marcadores de superlativo / "o melhor"
# Lista de palavras que indicam que o usuário quer saber quem é o melhor ou o número 1 do ranking
SUPERLATIVE_MARKERS = [
    "melhor", "top 1", "número 1", "numero 1", "primeiro", "líder",
    "maior", "mais bem", "principal", "destaque",
]

# Marcadores de circuito
# Palavras que identificam se o usuário está perguntando sobre o circuito masculino (ATP)
ATP_MARKERS = ["atp", "masculino", "homens", "homem"]
# Palavras que identificam se o usuário está perguntando sobre o circuito feminino (WTA)
WTA_MARKERS = ["wta", "feminino", "mulheres", "mulher"]

# Preposições a ignorar na detecção de país
# Conjunto de preposições comuns em português que devem ser removidas para facilitar a busca por nomes de países
PREPOSITIONS = {"do", "da", "dos", "das", "de", "no", "na", "nos", "nas"}


# Define a função auxiliar que remove acentos de um texto para permitir comparações sem distinção de acentuação
def _strip_accents(text):
    """Remove acentos para comparação fuzzy."""
    # Normaliza o texto para a forma NFKD, que separa caracteres base dos seus acentos (diacríticos)
    nfkd = unicodedata.normalize('NFKD', text)
    # Reconstrói a string mantendo apenas os caracteres que NÃO são marcas combinantes (ou seja, remove os acentos)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# Define a função que detecta se a mensagem do usuário menciona algum país, retornando o nome canônico
def _detect_country(msg_lower):
    """Detecta menção a um país na mensagem, retornando o nome canônico ou None."""
    # Remove nomes de torneios para evitar "australian open" → "Austrália"
    # Copia a mensagem original para uma variável que será "limpa"
    cleaned = msg_lower
    # Itera sobre uma lista de nomes de torneios conhecidos que poderiam causar falsos positivos
    for tournament in ["australian open", "roland garros", "wimbledon", "us open",
                       "miami open", "indian wells", "monte carlo", "madrid open",
                       "roma", "masters canadá", "masters canada", "cincinnati",
                       "shanghai", "paris masters", "rio open", "barcelona open",
                       "queen's", "queens", "halle", "acapulco", "dubai",
                       "basileia", "viena", "atp finals"]:
        # Substitui cada nome de torneio por uma string vazia, removendo-o da mensagem
        cleaned = cleaned.replace(tournament, "")

    # Primeiro tenta gentílicos (mais específicos)
    # Remove os acentos da mensagem limpa para permitir comparação sem acentos
    msg_no_accents = _strip_accents(cleaned)
    # Percorre cada gentílico e seu país correspondente no dicionário DEMONYM_MAP
    for demonym, country in DEMONYM_MAP.items():
        # Verifica se o gentílico aparece dentro da mensagem sem acentos
        if demonym in msg_no_accents:
            # Se encontrou o gentílico, retorna o nome canônico do país correspondente
            return country

    # Remove preposições comuns para facilitar match de país
    # Divide a mensagem limpa em uma lista de palavras individuais
    words = cleaned.split()
    # Filtra a lista de palavras, removendo aquelas que são preposições comuns (do, da, de, etc.)
    clean_words = [w for w in words if w not in PREPOSITIONS]
    # Junta as palavras filtradas de volta em uma única string separada por espaços
    clean_msg = ' '.join(clean_words)
    # Remove os acentos da mensagem limpa (sem preposições) para facilitar a comparação
    clean_msg_no_accents = _strip_accents(clean_msg)

    # Tenta nomes de países (mais longos primeiro para evitar match parcial)
    # Ordena as chaves do dicionário de países por comprimento decrescente (nomes mais longos primeiro)
    # Isso evita que "reino" faça match antes de "reino unido", por exemplo
    sorted_countries = sorted(COUNTRY_MAP.keys(), key=len, reverse=True)
    # Percorre cada nome de país na lista ordenada
    for country_key in sorted_countries:
        # Remove os acentos da chave do país para comparação sem acentos
        key_no_accents = _strip_accents(country_key)
        # Verifica se o nome do país (sem acentos) aparece na mensagem (sem acentos) OU se aparece com acentos
        if key_no_accents in clean_msg_no_accents or country_key in clean_msg:
            # Se encontrou o país, retorna o nome canônico correspondente do dicionário COUNTRY_MAP
            return COUNTRY_MAP[country_key]

    # Se nenhum país foi encontrado na mensagem, retorna None
    return None


# Define a função que detecta se o usuário pediu uma quantidade específica, como "top 5" ou "top 10"
def _detect_limit(msg_lower):
    """Detecta pedido de quantidade tipo 'top 5', 'top 20'."""
    # Usa uma expressão regular para procurar o padrão "top" seguido de um número na mensagem
    match = re.search(r'top\s*(\d+)', msg_lower)
    # Se encontrou o padrão "top N" na mensagem
    if match:
        # Extrai o número capturado pelo grupo (\d+) e converte de string para inteiro, retornando-o
        return int(match.group(1))
    # Se não encontrou o padrão, retorna None indicando que nenhum limite foi solicitado
    return None


# Define a função principal do módulo, que analisa a mensagem do usuário e extrai todos os modificadores
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
    # Chama a função _detect_country para verificar se a mensagem menciona algum país
    country_filter = _detect_country(msg_lower)
    # Verifica se algum marcador temporal ("atualmente", "hoje", etc.) aparece na mensagem, retornando True ou False
    is_current = any(marker in msg_lower for marker in TEMPORAL_MARKERS)
    # Verifica se algum marcador de superlativo ("melhor", "top 1", etc.) aparece na mensagem, retornando True ou False
    wants_best = any(marker in msg_lower for marker in SUPERLATIVE_MARKERS)

    # Inicializa a variável de circuito como None (nenhum circuito detectado ainda)
    circuit = None
    # Verifica se algum marcador do circuito feminino (WTA) aparece na mensagem
    if any(w in msg_lower for w in WTA_MARKERS):
        # Se encontrou um marcador feminino, define o circuito como "WTA"
        circuit = "WTA"
    # Caso contrário, verifica se algum marcador do circuito masculino (ATP) aparece na mensagem
    elif any(w in msg_lower for w in ATP_MARKERS):
        # Se encontrou um marcador masculino, define o circuito como "ATP"
        circuit = "ATP"

    # Chama a função _detect_limit para verificar se o usuário pediu um "top N" específico
    limit = _detect_limit(msg_lower)

    # Retorna um dicionário com todos os modificadores extraídos da mensagem do usuário
    return {
        # O filtro de país detectado (string com o nome canônico ou None se nenhum país foi mencionado)
        "country_filter": country_filter,
        # Booleano indicando se o usuário quer informações atuais/do momento presente
        "is_current": is_current,
        # Booleano indicando se o usuário quer saber quem é o melhor/número 1
        "wants_best": wants_best,
        # String indicando o circuito desejado: "ATP" (masculino), "WTA" (feminino) ou None (ambos)
        "circuit": circuit,
        # Número inteiro indicando quantos resultados o usuário quer (ex: top 5) ou None se não especificado
        "limit": limit,
    }
