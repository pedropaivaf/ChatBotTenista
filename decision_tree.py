import random
from nltk_utils import tokenize, stem, extract_entities

# Templates de follow-up abertos (nunca sim/não) organizados por (topic, bot_action)
FOLLOW_UPS = {
    # Ranking
    ("ranking", "showed_ranking"): [
        "Qual desses jogadores você mais admira?",
        "Algum nome dessa lista te surpreende na posição em que está?",
        "Sobre qual desses jogadores você gostaria de saber mais?",
        "Quem dessa lista você acha que vai subir mais posições esse ano?",
    ],
    ("ranking", "showed_country_ranking"): [
        "O que você acha do momento atual do tênis nesse país?",
        "Qual desses jogadores você mais acompanha?",
        "Quer saber mais detalhes sobre algum deles?",
    ],
    # Jogador
    ("player", "showed_player_info"): [
        "O que mais te impressiona no jogo {dele_dela}?",
        "Em qual torneio você mais gosta de acompanhar {ele_ela}?",
        "Quer comparar {ele_ela} com outro jogador?",
        "O que você acha do estilo de jogo {dele_dela}?",
    ],
    ("player", "showed_player_from_context"): [
        "O que mais te chama atenção no estilo de jogo {dele_dela}?",
        "Quer saber como {ele_ela} se compara com os outros do ranking?",
        "Qual torneio você acha que é o forte {dele_dela}?",
    ],
    ("player", "showed_player_country"): [
        "Quer saber mais sobre a carreira {dele_dela}?",
        "Conhece outros jogadores desse país?",
    ],
    ("player", "showed_country_best"): [
        "O que você acha da nova geração desse país no tênis?",
        "Quer ver a ficha completa de algum desses jogadores?",
        "Qual deles você acompanha mais de perto?",
    ],
    # Torneio
    ("tournament", "showed_champions"): [
        "Qual desses campeões te impressionou mais?",
        "O que você acha que define quem vence esse torneio?",
        "Quer saber mais sobre algum desses jogadores?",
    ],
    # Superfície
    ("surface", "showed_surface_info"): [
        "Qual superfície você prefere assistir?",
        "Quem você acha que é o melhor jogador nessa superfície?",
    ],
    # Conversacional genérico
    ("trivia", "showed_trivia"): [
        "Sobre qual tema do tênis você gostaria de saber mais?",
        "Tem algum jogador ou torneio que te interessa?",
    ],
}

# Palavras-chave para detectar tópicos na resposta contextual do usuário
STYLE_KEYWORDS = ["estilo", "forehand", "backhand", "saque", "serviço", "voleio",
                   "movimentação", "jogo", "tática", "agressivo", "defensivo",
                   "destro", "canhoto", "mão"]
TOURNAMENT_KEYWORDS = ["torneio", "slam", "grand slam", "australian", "roland",
                        "wimbledon", "us open", "masters", "finals"]
COMPARISON_KEYWORDS = ["comparar", "comparação", "versus", "vs", "contra",
                        "diferença", "melhor que", "pior que"]
COUNTRY_KEYWORDS_CTX = ["país", "pais", "nacionalidade", "onde nasceu", "da onde", "de onde"]


def _get_pronoun(player_name, engine):
    """Determina pronome (ele/ela, dele/dela) baseado no circuito."""
    wta_legends = ["Haddad Maia", "Swiatek", "Sabalenka", "Williams", "Sharapova",
                   "Bueno", "Jabeur", "Krejcikova", "Gauff", "Rybakina", "Paolini",
                   "Zheng", "Pegula"]
    # Verifica se está no ranking WTA
    for p in engine.data.get("ranking_wta", []):
        if player_name.lower() in p['name'].lower():
            return {"ele_ela": "ela", "dele_dela": "dela"}
    if any(w in player_name for w in wta_legends):
        return {"ele_ela": "ela", "dele_dela": "dela"}
    return {"ele_ela": "ele", "dele_dela": "dele"}


def _pick_follow_up(topic, bot_action, player_name=None, engine=None):
    """Escolhe um follow-up aleatório e formata com pronomes se necessário."""
    key = (topic, bot_action)
    templates = FOLLOW_UPS.get(key, FOLLOW_UPS.get(("trivia", "showed_trivia"), []))
    if not templates:
        return ""
    template = random.choice(templates)
    if player_name and engine and ("{ele_ela}" in template or "{dele_dela}" in template):
        pronouns = _get_pronoun(player_name, engine)
        template = template.format(**pronouns)
    return template


def _resolve_player_from_context(msg_lower, msg_stems, context, engine):
    """
    Tenta resolver uma menção a jogador usando o contexto da conversa.
    Ex: usuário diz "Alcaraz" após ver ranking → resolve para "Carlos Alcaraz".
    """
    mentioned = context.get("mentioned_entities", {}).get("players", [])
    if not mentioned:
        return None

    # Tenta match direto por sobrenome ou nome parcial
    for player_name in mentioned:
        name_parts = player_name.lower().split()
        for part in name_parts:
            if len(part) > 2 and part in msg_lower:
                return player_name

    # Tenta via extract_entities com a lista de mencionados
    result = extract_entities(msg_stems, mentioned)
    return result


class DecisionTree:
    """Máquina de estados contextual que gera follow-ups abertos e resolve entidades."""

    def __init__(self, engine):
        self.engine = engine

    def try_contextual_response(self, msg_lower, msg_stems, context, add_log):
        """
        Tenta interpretar a mensagem usando o contexto da conversa anterior.
        Retorna (response, topic, bot_action, mentioned_players) ou None se não conseguiu.
        """
        pending = context.get("pending_follow_up")
        if not pending:
            return None

        last_topic = context.get("current_topic")
        add_log(f"[CONTEXTO] Tentando resolver via contexto: pending={pending}, topic={last_topic}", "DEBUG")

        # --- Contexto: Jogador mencionado no ranking ---
        if pending in ("player_from_ranking", "player_from_country_ranking", "player_detail"):
            player = _resolve_player_from_context(msg_lower, msg_stems, context, self.engine)
            if player:
                add_log(f"[CONTEXTO] Jogador '{player}' resolvido via contexto!", "SUCCESS")
                info = self.engine.get_player_info(player)
                if info:
                    return (info, "player", "showed_player_from_context", [player])

        # --- Contexto: Detalhes do jogador em foco ---
        if pending == "player_detail":
            # Jogador em foco = último jogador sobre quem o bot deu info detalhada
            focus = context.get("focus_player")

            if any(kw in msg_lower for kw in COMPARISON_KEYWORDS):
                # Usuário quer comparar — tenta encontrar outro jogador
                all_players = self.engine.get_all_player_names()
                other = extract_entities(msg_stems, all_players)
                if other and focus:
                    info_other = self.engine.get_player_info(other)
                    info_focus = self.engine.get_player_info(focus)
                    if info_other and info_focus:
                        response = f"{info_focus}\n\n{'─' * 30}\n\n{info_other}"
                        return (response, "player", "showed_player_info",
                                [focus, other])

            # País do jogador em foco
            if any(kw in msg_lower for kw in COUNTRY_KEYWORDS_CTX):
                if focus:
                    country_info = self.engine.get_player_country(focus)
                    if country_info:
                        return (country_info, "player", "showed_player_country", [focus])

            # Estilo de jogo — re-mostra info do jogador em foco
            if any(kw in msg_lower for kw in STYLE_KEYWORDS):
                if focus:
                    info = self.engine.get_player_info(focus)
                    if info:
                        return (info, "player", "showed_player_info", [focus])

            # Torneio — busca campeões
            if any(kw in msg_lower for kw in TOURNAMENT_KEYWORDS):
                tournaments = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
                target = extract_entities(msg_stems, tournaments)
                if target:
                    result = self.engine.get_last_champions(tournament=target)
                    return (result, "tournament", "showed_champions", [])

        return None

    def enrich_response(self, response, topic, bot_action, context,
                        mentioned_players=None, mentioned_tournaments=None,
                        mentioned_countries=None):
        """
        Adiciona um follow-up aberto à resposta e retorna os dados para atualizar o contexto.
        """
        # Determina o jogador principal para pronomes
        player_for_pronoun = None
        if mentioned_players:
            player_for_pronoun = mentioned_players[-1]
        elif context.get("mentioned_entities", {}).get("players"):
            player_for_pronoun = context["mentioned_entities"]["players"][-1]

        follow_up = _pick_follow_up(topic, bot_action, player_for_pronoun, self.engine)
        if follow_up:
            response += f"\n\n{follow_up}"

        # Determina qual tipo de follow-up esperamos
        pending = None
        if bot_action in ("showed_ranking",):
            pending = "player_from_ranking"
        elif bot_action in ("showed_country_ranking", "showed_country_best"):
            pending = "player_from_country_ranking"
        elif bot_action in ("showed_player_info", "showed_player_from_context",
                            "showed_player_country"):
            pending = "player_detail"
        elif bot_action in ("showed_champions",):
            pending = "player_from_ranking"

        # Define o jogador em foco (último jogador discutido em detalhe)
        focus_player = None
        if bot_action in ("showed_player_info", "showed_player_from_context",
                          "showed_player_country") and mentioned_players:
            focus_player = mentioned_players[-1]

        return {
            "response": response,
            "topic": topic,
            "bot_action": bot_action,
            "pending_follow_up": pending,
            "focus_player": focus_player,
            "mentioned_players": mentioned_players or [],
            "mentioned_tournaments": mentioned_tournaments or [],
            "mentioned_countries": mentioned_countries or [],
        }
