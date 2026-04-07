# Importa o módulo random para selecionar respostas aleatórias de listas
import random
# Importa difflib para realizar comparações fuzzy (aproximadas) entre strings
import difflib
# Importa funções utilitárias de processamento de linguagem natural do módulo local nltk_utils
from nltk_utils import tokenize, stem, extract_entities

# Templates de follow-up abertos (nunca sim/não) organizados por (topic, bot_action)
# Dicionário que mapeia tuplas (tópico, ação_do_bot) para listas de perguntas de acompanhamento
FOLLOW_UPS = {
    # Ranking — abre para jogador ou torneio
    ("ranking", "showed_ranking"): [
        "Sobre qual desses jogadores você quer saber mais?",
        "Quer ver os campeões de algum Grand Slam?",
    ],
    ("ranking", "showed_country_ranking"): [
        "Quer ver a ficha de algum deles ou explorar outro tema?",
    ],
    # Jogador — abre para torneio, ranking, outro jogador
    ("player", "showed_player_info"): [
        "Quer explorar algum torneio, ver o ranking ou saber sobre outro jogador?",
        "O que mais te interessa: torneios, ranking ou outro jogador?",
    ],
    ("player", "showed_player_from_context"): [
        "Quer ver algum Grand Slam ou saber sobre outro jogador?",
    ],
    ("player", "showed_player_country"): [
        "Posso te contar sobre torneios, ranking ou outros jogadores!",
    ],
    ("player", "showed_country_best"): [
        "Quer ver a ficha de algum desses ou explorar outro tema?",
    ],
    # Torneio — abre para jogador ou outro torneio
    ("tournament", "showed_champions"): [
        "Quer saber sobre algum desses jogadores ou ver outro torneio?",
    ],
    ("tournament", "showed_slam_details"): [
        "Quer ver os últimos campeões desse torneio ou saber sobre outro Grand Slam?",
        "Posso te mostrar quem ganhou recentemente ou detalhar outro torneio!",
    ],
    ("tournament", "showed_tournament_list"): [
        "Quer saber detalhes sobre algum desses torneios?",
        "Posso te contar mais sobre qualquer um desses!",
    ],
    # Superfície — abre para jogador ou torneio
    ("surface", "showed_surface_info"): [
        "Quer saber sobre algum jogador ou torneio?",
    ],
    # Trivia — abre para qualquer tema
    ("trivia", "showed_trivia"): [
        "Sobre o que mais quer conversar? Jogadores, torneios, curiosidades...",
    ],
}

# Palavras-chave para detectar tópicos na resposta contextual do usuário
# Lista de palavras relacionadas ao estilo de jogo de um tenista
STYLE_KEYWORDS = ["estilo", "forehand", "backhand", "saque", "serviço", "voleio",
                   "movimentação", "jogo", "tática", "agressivo", "defensivo",
                   "destro", "canhoto", "mão"]
# Lista de palavras relacionadas a torneios de tênis
TOURNAMENT_KEYWORDS = ["torneio", "slam", "grand slam", "australian", "roland",
                        "wimbledon", "us open", "masters", "finals", "atp 500",
                        "atp 1000", "indian wells", "miami open", "monte carlo",
                        "madrid open", "roma", "cincinnati", "shanghai",
                        "paris masters", "rio open", "barcelona", "queens",
                        "queen's", "halle", "acapulco", "dubai", "basileia",
                        "viena", "atp finals"]
# Lista de palavras que indicam que o usuário quer comparar jogadores
COMPARISON_KEYWORDS = ["comparar", "comparação", "versus", "vs", "contra",
                        "diferença", "melhor que", "pior que"]
# Lista de palavras relacionadas a país/nacionalidade do jogador
COUNTRY_KEYWORDS_CTX = ["país", "pais", "nacionalidade", "onde nasceu", "da onde", "de onde"]

# Keywords que indicam que o usuário quer saber o vencedor/campeão (sem citar torneio)
WINNER_KEYWORDS_CTX = [
    "ganhou", "ganhador", "ganhadores", "último ganhador", "ultimo ganhador",
    "campeão", "campeões", "campeao", "campeoes", "vencedor", "vencedores",
    "venceu", "quem ganhou", "quem venceu", "último campeão", "ultimo campeao",
    "quem foi o campeão", "quem foi o campeao",
]

# Keywords que indicam pedido de recordes/estatísticas históricas
RECORDS_KEYWORDS = [
    "recorde", "recordes", "mais títulos", "mais titulos", "mais grand slams",
    "mais slams", "maior número", "mais semanas", "mais vitorias",
    "mais vitórias", "partida mais longa", "saque mais rápido",
    "saque mais rapido", "golden slam",
]

# Keywords que indicam pedido de listar torneios (não detalhes de um específico)
TOURNAMENT_LIST_KEYWORDS = [
    "quais são", "quais sao", "quais os", "listar", "lista de",
    "todos os torneios", "todos os campeonatos", "quais torneios",
    "quais campeonatos", "campeonatos", "campeonato",
]

# Keywords que indicam pedido de detalhes/info sobre Grand Slam (não campeões)
SLAM_DETAIL_KEYWORDS_CTX = [
    "sobre", "detalhes", "detalhe", "fala sobre", "história", "historia",
    "onde fica", "onde é", "informações", "informacoes", "superfície",
    "superficie", "piso", "premiação", "premiacao", "como é", "como e",
    "o que é", "o que e", "ficha",
]

# Reações empáticas a atributos técnicos de tênis (apenas tema tênis)
# Dicionário que mapeia palavras-chave técnicas para listas de reações empáticas com emojis
REACTION_KEYWORDS = {
    "resistencia": ["A resistência {dele_dela} é realmente absurda! 🎾", "Impressionante! {Ele_Ela} não desiste de nenhum ponto!"],
    "forehand": ["O forehand {dele_dela} é uma arma mortal! 🔥", "O forehand é um dos maiores destaques do jogo {dele_dela}."],
    "backhand": ["O backhand {dele_dela} é de outro nível! 💪", "Um dos backhands mais consistentes do circuito!"],
    "saque": ["O saque {dele_dela} é devastador! ⚡", "O saque é uma das maiores armas {dele_dela}."],
    "mental": ["A força mental {dele_dela} é impressionante! 🧠", "Nos momentos decisivos, {ele_ela} sempre aparece!"],
    "velocidade": ["A velocidade {dele_dela} na quadra é incrível! 💨", "{Ele_Ela} cobre a quadra como poucos!"],
    "movimentacao": ["A movimentação {dele_dela} é fantástica!", "{Ele_Ela} se desloca na quadra como se flutuasse!"],
    "agressivo": ["O jogo agressivo {dele_dela} é eletrizante! 🔥", "{Ele_Ela} não dá tempo pro adversário respirar!"],
    "defesa": ["A defesa {dele_dela} é incrível!", "{Ele_Ela} transforma defesa em ataque como ninguém!"],
    "voleio": ["O voleio {dele_dela} é preciso!", "Jogo de rede é uma arte e {ele_ela} domina!"],
    "rapidez": ["A rapidez {dele_dela} na quadra é incrível! 💨", "{Ele_Ela} cobre a quadra como poucos!"],
    "rapido": ["A velocidade {dele_dela} é impressionante! 💨", "{Ele_Ela} é rápido demais na quadra!"],
    "potencia": ["A potência {dele_dela} é absurda! 💥", "Os golpes {dele_dela} são devastadores!"],
    "consistencia": ["A consistência {dele_dela} é impressionante!", "{Ele_Ela} raramente comete erros não forçados!"],
    "inteligencia": ["A inteligência tática {dele_dela} é de outro nível! 🧠", "{Ele_Ela} sempre lê o jogo do adversário!"],
    "tatica": ["A tática {dele_dela} é brilhante! 🧠", "{Ele_Ela} sempre encontra a jogada certa!"],
}
PLAYER_INFO_KEYWORDS = ["idade", "quantos anos", "titulo", "títulos", "titulos", "curiosidade",
                         "fato", "carreira", "biografia", "ficha",
                         "informação", "informacao", "perfil", "detalhes", "mais sobre",
                         "altura", "quantos titulos", "quantos títulos", "alto", "mede"]

# Keywords para respostas específicas (retorna só o campo pedido, não a ficha toda)
HEIGHT_KEYWORDS = ["altura", "alto", "mede", "qual a altura", "quanto mede", "tamanho"]
AGE_KEYWORDS = ["idade", "quantos anos", "qual a idade"]
TITLES_COUNT_KEYWORDS = ["quantos titulos", "quantos títulos", "quantos titulo",
                         "quais os títulos", "quais os titulos", "quais títulos",
                         "quais titulos", "títulos dele", "titulos dele",
                         "títulos dela", "titulos dela", "lista de títulos"]

# Elogios genéricos que devem ser reconhecidos no contexto de player_detail
GENERIC_PRAISE = [
    "melhores", "o melhor", "o maior", "um dos maiores", "um dos melhores",
    "incrível", "incrivel", "sensacional", "fantástico", "fantastico",
    "lenda", "lendário", "lendario", "goat", "fera", "monstro",
    "demais", "muito bom", "espetacular", "fenomenal", "genial",
    "absurdo", "impressionante", "fora de série",
]

# Palavras que indicam que o usuário quer continuar no mesmo fluxo
CONTINUE_KEYWORDS = [
    "sim", "claro", "quero", "pode ser", "com certeza", "bora",
    "conta mais", "mais", "continue", "vai", "manda", "fala mais",
    "quero saber", "quero sim", "pode falar", "manda ver",
    "outra", "outro", "próximo", "próxima", "seguinte",
    "por favor", "show", "beleza",
]

# Palavras que indicam pedido de ranking dentro de contexto
RANKING_KEYWORDS_CTX = ["ranking", "rank", "top 10", "classificação", "tabela", "posição", "posições"]

# Palavras que indicam pedido de curiosidade/trivia dentro de contexto
CURIOSITY_KEYWORDS_CTX = ["curiosidade", "curiosidades", "fato curioso", "fatos",
                          "conta mais curiosidade", "outra curiosidade", "outro fato"]

# Pronomes implícitos que referem ao jogador em foco
PRONOUN_KEYWORDS = ["sobre ele", "sobre ela", "fala dele", "fala dela",
                    "e ele", "e ela", "desse jogador", "dessa jogadora",
                    "desse tenista", "dessa tenista", "conta dele", "conta dela",
                    "mais dele", "mais dela",
                    "pais dele", "pais dela", "país dele", "país dela",
                    "idade dele", "idade dela",
                    "estilo dele", "estilo dela"]


# Função interna que gera uma reação empática sobre um atributo técnico do jogador em foco
def _build_reaction(msg_lower, focus_player, engine):
    """Gera uma reação empática sobre atributo técnico de tênis do jogador em foco."""
    # Se não há jogador em foco, retorna None pois não é possível gerar reação
    if not focus_player:
        return None
    # Obtém os pronomes corretos (ele/ela, dele/dela) de acordo com o gênero do jogador
    pronouns = _get_pronoun(focus_player, engine)
    # Cria versão com inicial maiúscula para início de frase (Ele_Ela) e junta com pronomes normais
    pronouns_cap = {"Ele_Ela": pronouns["ele_ela"].capitalize(), **pronouns}
    # Percorre cada palavra-chave técnica e suas reações correspondentes
    for keyword, reactions in REACTION_KEYWORDS.items():
        # Se a palavra-chave técnica está presente na mensagem do usuário
        if keyword in msg_lower:
            # Escolhe aleatoriamente uma reação e formata com os pronomes corretos
            return random.choice(reactions).format(**pronouns_cap)
    # Se nenhuma palavra-chave técnica foi encontrada, retorna None
    return None


# Função interna que determina os pronomes corretos (masculino/feminino) para um jogador
def _get_pronoun(player_name, engine):
    """Determina pronome (ele/ela, dele/dela) baseado no circuito."""
    # Lista de sobrenomes de jogadoras famosas do circuito WTA (feminino)
    wta_legends = ["Haddad Maia", "Swiatek", "Sabalenka", "Williams", "Sharapova",
                   "Bueno", "Jabeur", "Krejcikova", "Gauff", "Rybakina", "Paolini",
                   "Zheng", "Pegula"]
    # Verifica se está no ranking WTA
    # Percorre cada jogadora do ranking WTA nos dados do engine
    for p in engine.data.get("ranking_wta", []):
        # Se o nome do jogador está contido no nome de uma jogadora WTA, usa pronomes femininos
        if player_name.lower() in p['name'].lower():
            return {"ele_ela": "ela", "dele_dela": "dela"}
    # Verifica se o sobrenome do jogador corresponde a alguma lenda WTA da lista
    if any(w in player_name for w in wta_legends):
        # Se sim, retorna pronomes femininos
        return {"ele_ela": "ela", "dele_dela": "dela"}
    # Caso padrão: retorna pronomes masculinos (circuito ATP)
    return {"ele_ela": "ele", "dele_dela": "dele"}


# Função interna que escolhe e formata um follow-up aleatório para manter a conversa fluindo
def _pick_follow_up(topic, bot_action, player_name=None, engine=None):
    """Escolhe um follow-up aleatório e formata com pronomes se necessário."""
    # Cria a chave de busca como tupla (tópico, ação)
    key = (topic, bot_action)
    # Busca os templates para essa chave; se não encontrar, usa os templates genéricos de trivia
    templates = FOLLOW_UPS.get(key, FOLLOW_UPS.get(("trivia", "showed_trivia"), []))
    # Se não há templates disponíveis, retorna string vazia
    if not templates:
        return ""
    # Escolhe aleatoriamente um template da lista
    template = random.choice(templates)
    # Se há jogador e engine, e o template contém placeholders de pronome, faz a substituição
    if player_name and engine and ("{ele_ela}" in template or "{dele_dela}" in template):
        # Obtém os pronomes corretos para o jogador
        pronouns = _get_pronoun(player_name, engine)
        # Substitui os placeholders {ele_ela} e {dele_dela} pelos pronomes corretos
        template = template.format(**pronouns)
    # Retorna o template formatado pronto para exibição
    return template


# Palavras comuns do português que não devem fazer fuzzy match com nomes de jogadores
# Conjunto (set) de stop words para evitar falsos positivos no matching fuzzy
_STOP_WORDS = {
    "qual", "quem", "como", "onde", "quando", "porque", "para", "sobre", "dele", "dela",
    "deles", "delas", "ele", "ela", "eles", "elas", "esse", "essa", "este", "esta",
    "isso", "isto", "aqui", "mais", "menos", "muito", "pouco", "bem", "mal", "bom",
    "mau", "melhor", "pior", "maior", "menor", "gosto", "gosta", "conta", "contar",
    "fala", "falar", "fale", "diga", "saber", "quero", "quer", "pode", "acho",
    "voce", "você", "meu", "minha", "seu", "sua", "nos", "nas", "dos", "das",
    "uma", "umas", "uns", "com", "sem", "por", "entre", "até", "após", "desde",
    "durante", "antes", "depois", "ainda", "também", "sempre", "nunca", "algo",
    "tudo", "nada", "cada", "outra", "outro", "nova", "novo", "velha", "velho",
    "curiosidade", "curiosidades", "detalhe", "detalhes", "informação", "informações",
    "historia", "história", "ranking", "dados", "atual", "atualmente", "hoje",
    "brasil", "espanha", "italia", "franca", "alemanha", "russia", "portugal",
    "tenis", "tênis", "jogador", "jogadora", "jogadores", "jogadoras",
    "tenista", "tenistas", "atleta", "atletas", "esporte", "campeonato",
    "torneio", "torneios", "slam", "grand", "open", "masters",
    "cor", "bola", "bolinha", "amarelo", "amarela", "verde", "branca", "branco",
    "quadra", "quadras", "rede", "tipo", "tipos",
    "regra", "regras", "ponto", "pontos", "set", "sets", "game", "games",
    "tempo", "final", "semi", "vitoria", "derrota", "ganhou", "perdeu",
    "favorito", "favorita", "melhor", "pior", "maior", "menor",
    "quantos", "quantas", "quando", "quais", "qual", "quem",
    "joga", "jogar", "jogando", "jogou", "jogo",
    "tem", "tendo", "teve", "tinha", "teria",
    "pode", "poder", "poderia", "seria", "será",
    "sempre", "muito", "demais", "bastante", "incrivel", "incrível",
    "absurda", "absurdo", "lendaria", "lendário", "perfeito", "perfeita",
    "impressiona", "impressionante", "admiro", "adoro", "amo",
    "rapidez", "rápido", "rapido",
}


# Função que realiza matching fuzzy (aproximado) de nomes de jogadores, tolerando erros de digitação
def _fuzzy_match_player(msg_lower, candidates, threshold=0.65):
    """
    Match fuzzy de nome de jogador com tolerância a typos.
    Compara cada palavra da mensagem com cada parte dos nomes candidatos.
    Ignora stop words para evitar falsos positivos (ex: 'dela' vs 'elena').
    """
    # Remove pontuação da mensagem e divide em palavras individuais
    words = msg_lower.replace(',', ' ').replace('.', ' ').replace('?', ' ').replace('!', ' ').split()
    # Filtra stop words e palavras muito curtas
    # Mantém apenas palavras com mais de 2 caracteres que não sejam stop words
    words = [w for w in words if len(w) > 2 and w not in _STOP_WORDS]
    # Se não sobrou nenhuma palavra válida após a filtragem, retorna None
    if not words:
        return None

    # Variável para armazenar o melhor jogador encontrado até agora
    best_match = None
    # Variável para armazenar a melhor taxa de similaridade encontrada
    best_ratio = 0

    # Percorre cada nome de jogador na lista de candidatos
    for player_name in candidates:
        # Divide o nome completo do jogador em partes (nome e sobrenome)
        name_parts = player_name.lower().split()
        # Percorre cada parte do nome do jogador
        for part in name_parts:
            # Ignora partes do nome com 2 caracteres ou menos (ex: "de", "da")
            if len(part) <= 2:
                continue
            # Compara cada palavra da mensagem do usuário com a parte do nome
            for word in words:
                # Calcula a taxa de similaridade entre a palavra e a parte do nome usando SequenceMatcher
                ratio = difflib.SequenceMatcher(None, word, part).ratio()
                # Se a similaridade é maior que a melhor encontrada e está acima do limiar mínimo
                if ratio > best_ratio and ratio >= threshold:
                    # Atualiza a melhor taxa de similaridade
                    best_ratio = ratio
                    # Atualiza o melhor jogador encontrado
                    best_match = player_name

    # Retorna o jogador com maior similaridade ou None se nenhum atingiu o limiar
    return best_match


# Função que tenta resolver o nome de um jogador usando o contexto da conversa anterior
def _resolve_player_from_context(msg_lower, msg_stems, context, engine):
    """
    Tenta resolver uma menção a jogador usando o contexto da conversa.
    Ex: usuário diz "Alcaraz" após ver ranking → resolve para "Carlos Alcaraz".
    Suporta typos via fuzzy matching (ex: "Medevedev" → "Daniil Medvedev").
    """
    # Obtém a lista de jogadores que foram mencionados anteriormente no contexto da conversa
    mentioned = context.get("mentioned_entities", {}).get("players", [])
    # Se não há jogadores no contexto, não há como resolver — retorna None
    if not mentioned:
        return None

    # 1. Tenta match direto por sobrenome ou nome parcial
    # Percorre cada jogador mencionado no contexto
    for player_name in mentioned:
        # Divide o nome do jogador em partes (nome e sobrenome)
        name_parts = player_name.lower().split()
        # Verifica cada parte do nome
        for part in name_parts:
            # Se a parte tem mais de 2 caracteres e aparece na mensagem do usuário
            if len(part) > 2 and part in msg_lower:
                # Retorna o nome completo do jogador (resolvido pelo contexto)
                return player_name

    # 2. Tenta via extract_entities com a lista de mencionados
    # Usa a função de extração de entidades do NLTK para tentar encontrar o jogador pelos stems
    result = extract_entities(msg_stems, mentioned)
    # Se encontrou um resultado, retorna o jogador identificado
    if result:
        return result

    # 3. Fuzzy match — tolera typos como "Medevedev" → "Medvedev"
    # Última tentativa: usa matching fuzzy para tolerar erros de digitação
    return _fuzzy_match_player(msg_lower, mentioned, threshold=0.65)


# Classe principal que implementa a árvore de decisão contextual do chatbot
class DecisionTree:
    """Máquina de estados contextual que gera follow-ups abertos e resolve entidades."""

    # Método construtor que recebe a referência ao engine principal do chatbot
    def __init__(self, engine):
        # Armazena a referência ao engine para acessar dados e funções do chatbot
        self.engine = engine

    def _is_continue(self, msg_lower):
        """Detecta se o usuário quer continuar no mesmo fluxo sem novo tópico."""
        msg_clean = msg_lower.strip().rstrip('!?.').strip()
        # Mensagem é exatamente um continuador
        if msg_clean in CONTINUE_KEYWORDS:
            return True
        # Mensagem curta (até 5 palavras) contendo um continuador
        words = msg_clean.split()
        if len(words) <= 5 and any(kw in msg_lower for kw in CONTINUE_KEYWORDS):
            return True
        return False

    def _get_random_curiosity(self):
        """Retorna uma curiosidade aleatória da knowledge_base."""
        import json
        try:
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                kb = json.load(f)
            for intent in kb["intents"]:
                if intent["tag"] == "curiosidades":
                    return random.choice(intent["responses"])
        except Exception:
            pass
        return None

    # Método principal que tenta interpretar a mensagem usando o contexto da conversa
    def try_contextual_response(self, msg_lower, msg_stems, context, add_log):
        """
        Tenta interpretar a mensagem usando o contexto da conversa anterior.
        Retorna (response, topic, bot_action, mentioned_players, trace) ou (None, trace).
        O trace é uma lista de decisões tomadas para visualização no pipeline.
        """
        pending = context.get("pending_follow_up")
        trace = []  # Trace visual de cada decisão

        if not pending:
            trace.append({"branch": "Contexto", "icon": "💤", "matched": False, "detail": "Sem pendência — pipeline normal"})
            return None, trace

        last_topic = context.get("current_topic")
        focus = context.get("focus_player")
        add_log(f"[CONTEXTO] Tentando resolver via contexto: pending={pending}, topic={last_topic}", "DEBUG")

        # --- Pré-branch: Resolução de pronome implícito ---
        if focus:
            has_pronoun = any(kw in msg_lower for kw in PRONOUN_KEYWORDS)
            if has_pronoun:
                # Verificar se é pergunta sobre país
                has_country_q = any(kw in msg_lower for kw in COUNTRY_KEYWORDS_CTX)
                if has_country_q:
                    country_info = self.engine.get_player_country(focus)
                    if country_info:
                        reaction = _build_reaction(msg_lower, focus, self.engine)
                        if reaction:
                            country_info = f"{reaction}\n\n{country_info}"
                        trace.append({"branch": "Pronome → País", "icon": "📍", "matched": True, "detail": f"País de {focus}"})
                        return (country_info, "player", "showed_player_country", [focus], trace)
                # Verificar se é campo específico (altura, idade, títulos)
                specific_field = None
                if any(kw in msg_lower for kw in HEIGHT_KEYWORDS):
                    specific_field = "height"
                elif any(kw in msg_lower for kw in AGE_KEYWORDS):
                    specific_field = "age"
                elif any(kw in msg_lower for kw in TITLES_COUNT_KEYWORDS):
                    specific_field = "titles_count"
                if specific_field:
                    field_result = self.engine.get_player_field(focus, specific_field)
                    if field_result:
                        trace.append({"branch": f"Pronome → {specific_field}", "icon": "🔍", "matched": True, "detail": f"{specific_field} de {focus}"})
                        return (field_result, "player", "showed_player_info", [focus], trace)
                # Verificar se é pergunta sobre estilo/info
                has_style = any(kw in msg_lower for kw in STYLE_KEYWORDS)
                has_info_q = any(kw in msg_lower for kw in PLAYER_INFO_KEYWORDS)
                if has_style or has_info_q:
                    info = self.engine.get_player_info(focus)
                    if info:
                        trace.append({"branch": "Pronome → Info", "icon": "📋", "matched": True, "detail": f"Info de {focus}"})
                        return (info, "player", "showed_player_info", [focus], trace)
                # Pronome genérico sem especificidade → mostrar info do jogador
                info = self.engine.get_player_info(focus)
                if info:
                    trace.append({"branch": "Pronome → Jogador", "icon": "👤", "matched": True, "detail": f"Pronome resolve para {focus}"})
                    return (info, "player", "showed_player_info", [focus], trace)

        # --- Branch 0.5: Se pede ranking, devolver ao pipeline normal ---
        if any(kw in msg_lower for kw in RANKING_KEYWORDS_CTX):
            trace.append({"branch": "Ranking detectado", "icon": "📊", "matched": True, "detail": "Pedido de ranking → pipeline normal"})
            return None, trace

        # --- Branch 0.7: "Quem foi o último ganhador?" com torneio no contexto ---
        # Só dispara se a mensagem NÃO menciona outro torneio explicitamente
        if any(kw in msg_lower for kw in WINNER_KEYWORDS_CTX):
            all_tournaments = self.engine.get_all_tournament_names()
            has_explicit_tournament = any(t.lower() in msg_lower for t in all_tournaments)
            if not has_explicit_tournament:
                ctx_tournaments = context.get("mentioned_entities", {}).get("tournaments", [])
                if ctx_tournaments:
                    last_tournament = ctx_tournaments[-1]
                    winner_info = self.engine.get_last_winner(last_tournament)
                    if winner_info:
                        trace.append({"branch": "Último Ganhador", "icon": "🏆", "matched": True, "detail": f"Campeão de {last_tournament}"})
                        add_log(f"[CONTEXTO] Último ganhador de '{last_tournament}' via contexto!", "SUCCESS")
                        return (winner_info, "tournament", "showed_champions", [], trace)

        # --- Branch 1: Torneio ---
        if pending in ("player_from_ranking", "player_from_country_ranking", "player_detail"):
            grand_slams = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
            all_tournaments = self.engine.get_all_tournament_names()
            target_t = extract_entities(msg_stems, all_tournaments)
            if not target_t:
                for t in all_tournaments:
                    if t.lower() in msg_lower:
                        target_t = t
                        break
            if target_t:
                # Para ATP 1000/500: sempre mostra detalhes (inclui campeões recentes)
                has_detail = any(kw in msg_lower for kw in SLAM_DETAIL_KEYWORDS_CTX)
                if has_detail or target_t not in grand_slams:
                    detail = self.engine.get_grand_slam_details(target_t)
                    if detail:
                        trace.append({"branch": "Detalhes Torneio", "icon": "🏟️", "matched": True, "detail": f"Detalhes de {target_t}"})
                        add_log(f"[CONTEXTO] Detalhes de '{target_t}' via contexto!", "SUCCESS")
                        return (detail, "tournament", "showed_slam_details", [], trace)
                # Grand Slams sem detail keywords: campeões
                trace.append({"branch": "Torneio", "icon": "🏆", "matched": True, "detail": f"{target_t} detectado"})
                add_log(f"[CONTEXTO] Torneio '{target_t}' detectado no contexto!", "SUCCESS")
                result = self.engine.get_last_champions(tournament=target_t)
                return (result, "tournament", "showed_champions", [], trace)
            elif any(kw in msg_lower for kw in TOURNAMENT_KEYWORDS):
                # Verifica se quer listar torneios ou ver campeões
                if any(kw in msg_lower for kw in TOURNAMENT_LIST_KEYWORDS):
                    trace.append({"branch": "Lista Torneios", "icon": "📋", "matched": True, "detail": "Listagem de torneios"})
                    result = self.engine.get_tournaments_list()
                    return (result, "tournament", "showed_tournament_list", [], trace)
                trace.append({"branch": "Torneio (genérico)", "icon": "🏆", "matched": True, "detail": "Pedido genérico de torneios"})
                add_log("[CONTEXTO] Pedido genérico de torneios detectado!", "SUCCESS")
                result = self.engine.get_last_champions()
                return (result, "tournament", "showed_champions", [], trace)
            else:
                trace.append({"branch": "Torneio", "icon": "🏆", "matched": False, "detail": "Nenhum Grand Slam na mensagem"})

        # --- Branch 2: Jogador do contexto ---
        if pending in ("player_from_ranking", "player_from_country_ranking", "player_detail"):
            player = _resolve_player_from_context(msg_lower, msg_stems, context, self.engine)
            if player:
                trace.append({"branch": "Jogador (contexto)", "icon": "👤", "matched": True, "detail": f"{player}"})
                add_log(f"[CONTEXTO] Jogador '{player}' resolvido via contexto!", "SUCCESS")
                info = self.engine.get_player_info(player)
                if info:
                    return (info, "player", "showed_player_from_context", [player], trace)
            else:
                trace.append({"branch": "Jogador (contexto)", "icon": "👤", "matched": False, "detail": "Nenhum nome reconhecido"})

        # --- Branch 3: Detalhes do jogador em foco ---
        if pending == "player_detail":
            reaction = _build_reaction(msg_lower, focus, self.engine)
            reaction_kw = None
            if reaction:
                for kw in REACTION_KEYWORDS:
                    if kw in msg_lower:
                        reaction_kw = kw
                        break

            # Sub-branch: Comparação
            has_comparison = any(kw in msg_lower for kw in COMPARISON_KEYWORDS)
            if has_comparison:
                all_players = self.engine.get_all_player_names()
                other = extract_entities(msg_stems, all_players)
                if other and focus:
                    info_other = self.engine.get_player_info(other)
                    info_focus = self.engine.get_player_info(focus)
                    if info_other and info_focus:
                        trace.append({"branch": "Comparação", "icon": "⚔️", "matched": True, "detail": f"{focus} vs {other}"})
                        response = f"{info_focus}\n\n{'─' * 30}\n\n{info_other}"
                        return (response, "player", "showed_player_info", [focus, other], trace)

            # Sub-branch: País
            has_country = any(kw in msg_lower for kw in COUNTRY_KEYWORDS_CTX)
            if has_country and focus:
                country_info = self.engine.get_player_country(focus)
                if country_info:
                    if reaction:
                        trace.append({"branch": "Reação empática", "icon": "🗣️", "matched": True, "detail": f"{reaction_kw} → reação sobre {focus}"})
                        country_info = f"{reaction}\n\n{country_info}"
                    trace.append({"branch": "País do jogador", "icon": "📍", "matched": True, "detail": f"País de {focus}"})
                    return (country_info, "player", "showed_player_country", [focus], trace)

            # Sub-branch: Posição específica no ranking → devolver ao pipeline
            import re as _re
            if _re.search(r'(?:número|numero|n[°º]|top|posição|posicao|atual)\s*\d{1,3}', msg_lower) or _re.search(r'\d{1,3}\s*(?:º|°|do mundo|do ranking)', msg_lower):
                trace.append({"branch": "Posição ranking", "icon": "📊", "matched": True, "detail": "Posição específica → pipeline normal"})
                return None, trace

            # Sub-branch: Campo específico (altura, idade, títulos) → resposta curta
            if focus:
                specific_field = None
                if any(kw in msg_lower for kw in HEIGHT_KEYWORDS):
                    specific_field = "height"
                elif any(kw in msg_lower for kw in AGE_KEYWORDS):
                    specific_field = "age"
                elif any(kw in msg_lower for kw in TITLES_COUNT_KEYWORDS):
                    specific_field = "titles_count"
                if specific_field:
                    field_result = self.engine.get_player_field(focus, specific_field)
                    if field_result:
                        trace.append({"branch": "Campo específico", "icon": "🔍", "matched": True, "detail": f"{specific_field} de {focus}"})
                        return (field_result, "player", "showed_player_info", [focus], trace)

            # Sub-branch: Estilo / Info pessoal
            has_style = any(kw in msg_lower for kw in STYLE_KEYWORDS)
            has_info = any(kw in msg_lower for kw in PLAYER_INFO_KEYWORDS)
            if (has_style or has_info) and focus:
                info = self.engine.get_player_info(focus)
                if info:
                    if reaction:
                        trace.append({"branch": "Reação empática", "icon": "🗣️", "matched": True, "detail": f"{reaction_kw} → reação sobre {focus}"})
                        info = f"{reaction}\n\n{info}"
                    label = "Estilo de jogo" if has_style else "Info pessoal"
                    trace.append({"branch": label, "icon": "🎾", "matched": True, "detail": f"Dados de {focus}"})
                    return (info, "player", "showed_player_info", [focus], trace)

            # Sub-branch: Reação pura (opinião sem pedido técnico)
            if reaction and focus:
                info = self.engine.get_player_info(focus)
                if info:
                    trace.append({"branch": "Reação empática", "icon": "🗣️", "matched": True, "detail": f"{reaction_kw} → reação sobre {focus}"})
                    trace.append({"branch": "Ficha do jogador", "icon": "📋", "matched": True, "detail": f"Re-exibindo {focus}"})
                    return (f"{reaction}\n\n{info}", "player", "showed_player_info", [focus], trace)

            # Sub-branch: Elogio genérico ("um dos melhores", "lenda", "goat")
            if any(p in msg_lower for p in GENERIC_PRAISE) and focus:
                pronouns = _get_pronoun(focus, self.engine)
                pronouns_cap = {"Ele_Ela": pronouns["ele_ela"].capitalize(), **pronouns}
                praise_reactions = [
                    "Concordo! {Ele_Ela} é realmente especial! 🎾",
                    "Com certeza! {Ele_Ela} marcou a história do tênis! 🏆",
                    "Sem dúvida! Uma verdadeira lenda do esporte!",
                    "{Ele_Ela} é daqueles talentos únicos que aparecem uma vez na vida! ✨",
                ]
                praise_text = random.choice(praise_reactions).format(**pronouns_cap)
                trace.append({"branch": "Elogio genérico", "icon": "👏", "matched": True, "detail": f"Reação a elogio sobre {focus}"})
                return (praise_text, "player", "showed_player_info", [focus], trace)

            # Sub-branch: Troca para ranking
            if any(kw in msg_lower for kw in RANKING_KEYWORDS_CTX):
                trace.append({"branch": "Troca → Ranking", "icon": "📊", "matched": True, "detail": "Pedido de ranking durante player_detail"})
                add_log(f"[CONTEXTO] Troca de tópico: player_detail → ranking", "SUCCESS")
                circuit = 'WTA' if any(w in msg_lower for w in ['wta', 'feminino', 'mulheres']) else 'ATP'
                ranking_text = self.engine.get_ranking_summary(circuit=circuit)
                ranking_data = self.engine.data.get(f"ranking_{circuit.lower()}", [])
                top_players = [p['name'] for p in ranking_data[:10]]
                return (ranking_text, "ranking", "showed_ranking", top_players, trace)

            # Sub-branch: Troca para curiosidade
            if any(kw in msg_lower for kw in CURIOSITY_KEYWORDS_CTX):
                curiosity = self._get_random_curiosity()
                if curiosity:
                    trace.append({"branch": "Troca → Curiosidade", "icon": "💡", "matched": True, "detail": "Pedido de curiosidade durante player_detail"})
                    return (curiosity, "trivia", "showed_trivia", [], trace)

            # Sub-branch: Troca para torneio (com detecção de torneio específico)
            if any(kw in msg_lower for kw in TOURNAMENT_KEYWORDS):
                grand_slams = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
                all_tournaments = self.engine.get_all_tournament_names()
                target_t = extract_entities(msg_stems, all_tournaments)
                if not target_t:
                    for t in all_tournaments:
                        if t.lower() in msg_lower:
                            target_t = t
                            break
                if target_t:
                    has_detail = any(kw in msg_lower for kw in SLAM_DETAIL_KEYWORDS_CTX)
                    if has_detail or target_t not in grand_slams:
                        detail = self.engine.get_grand_slam_details(target_t)
                        if detail:
                            trace.append({"branch": "Troca → Detalhes Torneio", "icon": "🏟️", "matched": True, "detail": f"Detalhes de {target_t}"})
                            return (detail, "tournament", "showed_slam_details", [], trace)
                    trace.append({"branch": "Troca → Torneio", "icon": "🏆", "matched": True, "detail": f"Campeões de {target_t}"})
                    result = self.engine.get_last_champions(tournament=target_t)
                    return (result, "tournament", "showed_champions", [], trace)
                if any(kw in msg_lower for kw in TOURNAMENT_LIST_KEYWORDS):
                    trace.append({"branch": "Troca → Lista Torneios", "icon": "📋", "matched": True, "detail": "Listagem de torneios durante player_detail"})
                    result = self.engine.get_tournaments_list()
                    return (result, "tournament", "showed_tournament_list", [], trace)
                trace.append({"branch": "Troca → Torneios", "icon": "🏆", "matched": True, "detail": "Pedido genérico de torneios durante player_detail"})
                add_log("[CONTEXTO] Troca de tópico: player_detail → torneios", "SUCCESS")
                result = self.engine.get_last_champions()
                return (result, "tournament", "showed_champions", [], trace)

            # Sub-branch: Continuação genérica ("sim", "conta mais", "quero saber")
            if self._is_continue(msg_lower) and focus:
                info = self.engine.get_player_info(focus)
                if info:
                    continue_reactions = [
                        f"Claro! Aqui vai mais sobre {focus}:",
                        f"Com certeza! Vamos continuar falando de {focus}:",
                        f"Bora! Mais sobre {focus}:",
                    ]
                    intro = random.choice(continue_reactions)
                    trace.append({"branch": "Continuação", "icon": "🔄", "matched": True, "detail": f"Continuando sobre {focus}"})
                    return (f"{intro}\n\n{info}", "player", "showed_player_info", [focus], trace)

            # Nenhum sub-branch matched
            if not has_comparison: trace.append({"branch": "Comparação", "icon": "⚔️", "matched": False, "detail": "Não solicitado"})
            if not has_country: trace.append({"branch": "País do jogador", "icon": "📍", "matched": False, "detail": "Não solicitado"})
            if not reaction: trace.append({"branch": "Reação empática", "icon": "🗣️", "matched": False, "detail": "Nenhum atributo técnico detectado"})
            if not has_style and not has_info: trace.append({"branch": "Estilo/Info", "icon": "🎾", "matched": False, "detail": "Não solicitado"})

        # --- Branch 4: Open topic ---
        if pending == "open_topic":
            add_log("[CONTEXTO] Tentando resolver resposta aberta (open_topic)...", "DEBUG")
            grand_slams = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
            all_tournaments = self.engine.get_all_tournament_names()
            target_tournament = extract_entities(msg_stems, all_tournaments)
            if not target_tournament:
                for t in all_tournaments:
                    if t.lower() in msg_lower:
                        target_tournament = t
                        break
            if target_tournament:
                has_detail = any(kw in msg_lower for kw in SLAM_DETAIL_KEYWORDS_CTX)
                if has_detail or target_tournament not in grand_slams:
                    detail = self.engine.get_grand_slam_details(target_tournament)
                    if detail:
                        trace.append({"branch": "Detalhes Torneio (aberto)", "icon": "🏟️", "matched": True, "detail": f"Detalhes de {target_tournament}"})
                        add_log(f"[CONTEXTO] Detalhes de '{target_tournament}' via open_topic!", "SUCCESS")
                        return (detail, "tournament", "showed_slam_details", [], trace)
                trace.append({"branch": "Torneio (aberto)", "icon": "🏆", "matched": True, "detail": f"{target_tournament}"})
                add_log(f"[CONTEXTO] Torneio '{target_tournament}' resolvido via open_topic!", "SUCCESS")
                result = self.engine.get_last_champions(tournament=target_tournament)
                return (result, "tournament", "showed_champions", [], trace)
            elif any(kw in msg_lower for kw in TOURNAMENT_KEYWORDS):
                if any(kw in msg_lower for kw in TOURNAMENT_LIST_KEYWORDS):
                    trace.append({"branch": "Lista Torneios (aberto)", "icon": "📋", "matched": True, "detail": "Listagem de torneios em open_topic"})
                    result = self.engine.get_tournaments_list()
                    return (result, "tournament", "showed_tournament_list", [], trace)
                trace.append({"branch": "Torneios (genérico)", "icon": "🏆", "matched": True, "detail": "Pedido genérico de torneios em open_topic"})
                add_log("[CONTEXTO] Pedido genérico de torneios via open_topic!", "SUCCESS")
                result = self.engine.get_last_champions()
                return (result, "tournament", "showed_champions", [], trace)
            else:
                trace.append({"branch": "Torneio (aberto)", "icon": "🏆", "matched": False, "detail": "Nenhum torneio na mensagem"})

            all_players = self.engine.get_all_player_names()
            player = extract_entities(msg_stems, all_players)
            # Validação extra: rejeitar matches fracos (1 stem curto como "mai" → Mai Hontama)
            if player:
                player_stems = [stem(w) for w in tokenize(player.lower()) if len(stem(w)) > 2]
                matched_stems = [s for s in player_stems if s in msg_stems]
                # Exigir pelo menos 1 match com stem de 4+ caracteres
                if not any(len(s) >= 4 for s in matched_stems):
                    player = None
            if player:
                trace.append({"branch": "Jogador (aberto)", "icon": "👤", "matched": True, "detail": f"{player}"})
                add_log(f"[CONTEXTO] Jogador '{player}' resolvido via open_topic!", "SUCCESS")
                info = self.engine.get_player_info(player)
                if info:
                    return (info, "player", "showed_player_from_context", [player], trace)
            else:
                trace.append({"branch": "Jogador (aberto)", "icon": "👤", "matched": False, "detail": "Nenhum jogador encontrado"})

            # Sub-branch: País/info do focus_player ativo em open_topic
            if focus:
                has_country_ot = any(kw in msg_lower for kw in COUNTRY_KEYWORDS_CTX)
                if has_country_ot:
                    country_info = self.engine.get_player_country(focus)
                    if country_info:
                        trace.append({"branch": "País (open_topic)", "icon": "📍", "matched": True, "detail": f"País de {focus}"})
                        return (country_info, "player", "showed_player_country", [focus], trace)
                has_style_ot = any(kw in msg_lower for kw in STYLE_KEYWORDS)
                has_info_ot = any(kw in msg_lower for kw in PLAYER_INFO_KEYWORDS)
                if has_style_ot or has_info_ot:
                    info = self.engine.get_player_info(focus)
                    if info:
                        trace.append({"branch": "Info jogador (open_topic)", "icon": "📋", "matched": True, "detail": f"Info de {focus}"})
                        return (info, "player", "showed_player_info", [focus], trace)

            # Sub-branch: Ranking pedido em open_topic
            if any(kw in msg_lower for kw in RANKING_KEYWORDS_CTX):
                trace.append({"branch": "Ranking (aberto)", "icon": "📊", "matched": True, "detail": "Pedido de ranking"})
                add_log(f"[CONTEXTO] Ranking solicitado via open_topic", "SUCCESS")
                circuit = 'WTA' if any(w in msg_lower for w in ['wta', 'feminino', 'mulheres']) else 'ATP'
                ranking_text = self.engine.get_ranking_summary(circuit=circuit)
                ranking_data = self.engine.data.get(f"ranking_{circuit.lower()}", [])
                top_players = [p['name'] for p in ranking_data[:10]]
                return (ranking_text, "ranking", "showed_ranking", top_players, trace)

            # Sub-branch: Curiosidade pedida em open_topic
            if any(kw in msg_lower for kw in CURIOSITY_KEYWORDS_CTX):
                curiosity = self._get_random_curiosity()
                if curiosity:
                    trace.append({"branch": "Curiosidade (aberta)", "icon": "💡", "matched": True, "detail": "Nova curiosidade"})
                    return (curiosity, "trivia", "showed_trivia", [], trace)

            # Sub-branch: Continuação no mesmo tópico
            if self._is_continue(msg_lower):
                if last_topic == "trivia":
                    curiosity = self._get_random_curiosity()
                    if curiosity:
                        trace.append({"branch": "Continuar trivia", "icon": "🔄", "matched": True, "detail": "Mais curiosidade"})
                        return (curiosity, "trivia", "showed_trivia", [], trace)
                elif last_topic == "ranking":
                    circuit = context.get("current_circuit", "ATP")
                    ranking_text = self.engine.get_ranking_summary(circuit=circuit)
                    ranking_data = self.engine.data.get(f"ranking_{circuit.lower()}", [])
                    top_players = [p['name'] for p in ranking_data[:10]]
                    trace.append({"branch": "Continuar ranking", "icon": "🔄", "matched": True, "detail": f"Re-exibindo ranking {circuit}"})
                    return (ranking_text, "ranking", "showed_ranking", top_players, trace)
                elif last_topic == "player" and context.get("focus_player"):
                    fp = context["focus_player"]
                    info = self.engine.get_player_info(fp)
                    if info:
                        trace.append({"branch": "Continuar jogador", "icon": "🔄", "matched": True, "detail": f"Re-exibindo {fp}"})
                        return (info, "player", "showed_player_info", [fp], trace)
                # Genérico: oferece opções
                trace.append({"branch": "Continuar genérico", "icon": "🔄", "matched": True, "detail": "Sem tópico claro"})
                return ("Claro! Posso te contar sobre ranking ATP/WTA, jogadores, torneios de Grand Slam ou curiosidades do tênis. O que prefere? 🎾", "trivia", "showed_trivia", [], trace)

        trace.append({"branch": "Resultado", "icon": "➡️", "matched": False, "detail": "Sem resolução → pipeline normal"})
        return None, trace

    # Método que enriquece a resposta adicionando follow-ups e preparando dados de contexto
    def enrich_response(self, response, topic, bot_action, context,
                        mentioned_players=None, mentioned_tournaments=None,
                        mentioned_countries=None):
        """
        Adiciona um follow-up aberto à resposta e retorna os dados para atualizar o contexto.
        """
        # Determina o jogador principal para pronomes
        # Inicializa variável para o jogador que será usado nos pronomes do follow-up
        player_for_pronoun = None
        # Se há jogadores mencionados na resposta atual, usa o último da lista
        if mentioned_players:
            player_for_pronoun = mentioned_players[-1]
        # Senão, tenta usar o último jogador mencionado no contexto anterior
        elif context.get("mentioned_entities", {}).get("players"):
            player_for_pronoun = context["mentioned_entities"]["players"][-1]

        # Escolhe um follow-up aleatório apropriado para o tópico e ação atual
        follow_up = _pick_follow_up(topic, bot_action, player_for_pronoun, self.engine)
        # Se um follow-up foi gerado, adiciona-o ao final da resposta com uma linha em branco
        if follow_up:
            response += f"\n\n{follow_up}"

        # Determina qual tipo de follow-up esperamos
        # Inicializa o tipo de pending como None
        pending = None
        # Se o bot mostrou o ranking geral, espera que o usuário mencione um jogador do ranking
        if bot_action in ("showed_ranking",):
            pending = "player_from_ranking"
        # Se mostrou ranking por país ou melhores do país, espera jogador do ranking por país
        elif bot_action in ("showed_country_ranking", "showed_country_best"):
            pending = "player_from_country_ranking"
        # Se mostrou info de jogador, espera mais detalhes sobre esse jogador
        elif bot_action in ("showed_player_info", "showed_player_from_context",
                            "showed_player_country"):
            pending = "player_detail"
        # Se mostrou campeões ou detalhes de um torneio, espera jogador ou outro torneio
        elif bot_action in ("showed_champions", "showed_slam_details", "showed_tournament_list"):
            pending = "player_from_ranking"
        # Se mostrou trivia/curiosidade, espera uma resposta aberta sobre qualquer tema
        elif bot_action in ("showed_trivia",):
            pending = "open_topic"

        # Define o jogador em foco (último jogador discutido em detalhe)
        # Inicializa como None — só será definido se a ação envolveu info detalhada de jogador
        focus_player = None
        # Se a ação foi de mostrar detalhes de jogador e há jogadores mencionados
        if bot_action in ("showed_player_info", "showed_player_from_context",
                          "showed_player_country") and mentioned_players:
            # Define o último jogador mencionado como o jogador em foco para o próximo turno
            focus_player = mentioned_players[-1]

        # Retorna um dicionário com todos os dados necessários para atualizar o contexto da conversa
        return {
            "response": response,                                   # Resposta final com follow-up
            "topic": topic,                                         # Tópico atual da conversa
            "bot_action": bot_action,                               # Ação que o bot executou
            "pending_follow_up": pending,                           # Tipo de resposta esperada do usuário
            "focus_player": focus_player,                           # Jogador em foco para o próximo turno
            "mentioned_players": mentioned_players or [],           # Lista de jogadores mencionados
            "mentioned_tournaments": mentioned_tournaments or [],   # Lista de torneios mencionados
            "mentioned_countries": mentioned_countries or [],       # Lista de países mencionados
        }
