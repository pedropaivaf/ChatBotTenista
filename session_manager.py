import uuid
import time

# Tempo máximo de inatividade antes de expirar a sessão (30 minutos)
SESSION_TTL = 1800
# Número máximo de turnos de conversa rastreados por sessão
MAX_TURNS = 20


def _new_context(session_id):
    """Cria um contexto de sessão vazio com valores padrão."""
    now = time.time()
    return {
        "session_id": session_id,
        "created_at": now,
        "last_active": now,
        "turn_count": 0,
        "history": [],
        "current_topic": None,
        "current_circuit": "ATP",
        "mentioned_entities": {"players": [], "tournaments": [], "countries": []},
        "last_bot_action": None,
        "pending_follow_up": None,
        "focus_player": None,
    }


class SessionManager:
    """Gerenciador de sessões in-memory para o chatbot de tênis."""

    def __init__(self):
        self.sessions = {}

    def get_or_create(self, session_id=None):
        """Retorna o contexto existente ou cria um novo."""
        self._cleanup_expired()

        if session_id and session_id in self.sessions:
            ctx = self.sessions[session_id]
            ctx["last_active"] = time.time()
            return ctx

        # Sessão não existe ou não foi fornecida — cria uma nova
        new_id = session_id or str(uuid.uuid4())
        ctx = _new_context(new_id)
        self.sessions[new_id] = ctx
        return ctx

    def update(self, session_id, role, text, intent=None, bot_action=None,
               topic=None, circuit=None, pending_follow_up=None,
               mentioned_players=None, mentioned_tournaments=None,
               mentioned_countries=None, focus_player=None):
        """Atualiza o contexto da sessão após uma interação."""
        if session_id not in self.sessions:
            return

        ctx = self.sessions[session_id]
        ctx["last_active"] = time.time()

        # Adiciona ao histórico (máx MAX_TURNS entradas)
        ctx["history"].append({"role": role, "text": text, "intent": intent})
        if len(ctx["history"]) > MAX_TURNS * 2:
            ctx["history"] = ctx["history"][-(MAX_TURNS * 2):]

        if role == "user":
            ctx["turn_count"] = min(ctx["turn_count"] + 1, MAX_TURNS)

        # Atualiza campos opcionais apenas se fornecidos
        if bot_action is not None:
            ctx["last_bot_action"] = bot_action
        if topic is not None:
            ctx["current_topic"] = topic
        if circuit is not None:
            ctx["current_circuit"] = circuit
        if pending_follow_up is not None:
            ctx["pending_follow_up"] = pending_follow_up
        if focus_player is not None:
            ctx["focus_player"] = focus_player

        # Acumula entidades mencionadas (sem duplicatas)
        entities = ctx["mentioned_entities"]
        for player in (mentioned_players or []):
            if player not in entities["players"]:
                entities["players"].append(player)
        for tournament in (mentioned_tournaments or []):
            if tournament not in entities["tournaments"]:
                entities["tournaments"].append(tournament)
        for country in (mentioned_countries or []):
            if country not in entities["countries"]:
                entities["countries"].append(country)

    def _cleanup_expired(self):
        """Remove sessões inativas há mais de SESSION_TTL segundos."""
        now = time.time()
        expired = [sid for sid, ctx in self.sessions.items()
                   if now - ctx["last_active"] > SESSION_TTL]
        for sid in expired:
            del self.sessions[sid]
