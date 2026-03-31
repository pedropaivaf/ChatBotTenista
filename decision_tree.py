import random
import difflib
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


# Palavras comuns do português que não devem fazer fuzzy match com nomes de jogadores
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
}


def _fuzzy_match_player(msg_lower, candidates, threshold=0.65):
    """
    Match fuzzy de nome de jogador com tolerância a typos.
    Compara cada palavra da mensagem com cada parte dos nomes candidatos.
    Ignora stop words para evitar falsos positivos (ex: 'dela' vs 'elena').
    """
    words = msg_lower.replace(',', ' ').replace('.', ' ').replace('?', ' ').replace('!', ' ').split()
    # Filtra stop words e palavras muito curtas
    words = [w for w in words if len(w) > 2 and w not in _STOP_WORDS]
    if not words:
        return None

    best_match = None
    best_ratio = 0

    for player_name in candidates:
        name_parts = player_name.lower().split()
        for part in name_parts:
            if len(part) <= 2:
                continue
            for word in words:
                ratio = difflib.SequenceMatcher(None, word, part).ratio()
                if ratio > best_ratio and ratio >= threshold:
                    best_ratio = ratio
                    best_match = player_name

    return best_match


def _resolve_player_from_context(msg_lower, msg_stems, context, engine):
    """
    Tenta resolver uma menção a jogador usando o contexto da conversa.
    Ex: usuário diz "Alcaraz" após ver ranking → resolve para "Carlos Alcaraz".
    Suporta typos via fuzzy matching (ex: "Medevedev" → "Daniil Medvedev").
    """
    mentioned = context.get("mentioned_entities", {}).get("players", [])
    if not mentioned:
        return None

    # 1. Tenta match direto por sobrenome ou nome parcial
    for player_name in mentioned:
        name_parts = player_name.lower().split()
        for part in name_parts:
            if len(part) > 2 and part in msg_lower:
                return player_name

    # 2. Tenta via extract_entities com a lista de mencionados
    result = extract_entities(msg_stems, mentioned)
    if result:
        return result

    # 3. Fuzzy match — tolera typos como "Medevedev" → "Medvedev"
    return _fuzzy_match_player(msg_lower, mentioned, threshold=0.65)


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

        # --- Prioridade: Torneio detectado? (evita "roland garros" fazer match com jogador) ---
        if pending in ("player_from_ranking", "player_from_country_ranking", "player_detail"):
            tournaments = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
            target_t = extract_entities(msg_stems, tournaments)
            if not target_t:
                for t in tournaments:
                    if t.lower() in msg_lower:
                        target_t = t
                        break
            if target_t:
                add_log(f"[CONTEXTO] Torneio '{target_t}' detectado no contexto!", "SUCCESS")
                result = self.engine.get_last_champions(tournament=target_t)
                return (result, "tournament", "showed_champions", [])

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
            focus = context.get("focus_player")

            if any(kw in msg_lower for kw in COMPARISON_KEYWORDS):
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

        # --- Contexto: Resposta aberta (trivia perguntou sobre jogador/torneio) ---
        if pending == "open_topic":
            add_log("[CONTEXTO] Tentando resolver resposta aberta (open_topic)...", "DEBUG")

            # Tenta resolver como torneio
            tournaments = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
            target_tournament = extract_entities(msg_stems, tournaments)
            if not target_tournament:
                # Fallback: verifica keywords de torneio no texto
                for t in tournaments:
                    if t.lower() in msg_lower:
                        target_tournament = t
                        break
            if target_tournament:
                add_log(f"[CONTEXTO] Torneio '{target_tournament}' resolvido via open_topic!", "SUCCESS")
                result = self.engine.get_last_champions(tournament=target_tournament)
                return (result, "tournament", "showed_champions", [])

            # Tenta resolver como jogador (fuzzy match contra toda a base)
            all_players = self.engine.get_all_player_names()
            player = _fuzzy_match_player(msg_lower, all_players, threshold=0.75)
            if not player:
                player = extract_entities(msg_stems, all_players)
            if player:
                add_log(f"[CONTEXTO] Jogador '{player}' resolvido via open_topic!", "SUCCESS")
                info = self.engine.get_player_info(player)
                if info:
                    return (info, "player", "showed_player_from_context", [player])

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
        elif bot_action in ("showed_trivia",):
            pending = "open_topic"

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
