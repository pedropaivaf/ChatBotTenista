# Importa o módulo uuid para gerar identificadores únicos universais para cada sessão
import uuid
# Importa o módulo time para obter o timestamp atual e controlar a expiração das sessões
import time

# Tempo máximo de inatividade antes de expirar a sessão (30 minutos)
SESSION_TTL = 1800
# Número máximo de turnos de conversa rastreados por sessão
MAX_TURNS = 20


# Define a função que cria um novo contexto de sessão com valores iniciais padrão
def _new_context(session_id):
    """Cria um contexto de sessão vazio com valores padrão."""
    # Captura o timestamp atual em segundos desde 1 de janeiro de 1970 (época Unix)
    now = time.time()
    # Retorna um dicionário contendo todas as informações iniciais da sessão
    return {
        # Armazena o identificador único da sessão
        "session_id": session_id,
        # Registra o momento em que a sessão foi criada
        "created_at": now,
        # Registra o momento da última atividade do usuário nesta sessão
        "last_active": now,
        # Contador de turnos de conversa do usuário, começa em zero
        "turn_count": 0,
        # Lista que armazenará o histórico de mensagens trocadas na sessão
        "history": [],
        # Tópico atual da conversa (ex.: ranking, torneios), começa sem tópico definido
        "current_topic": None,
        # Circuito de tênis padrão é ATP (masculino); pode mudar para WTA (feminino)
        "current_circuit": "ATP",
        # Dicionário para rastrear entidades mencionadas: jogadores, torneios e países
        "mentioned_entities": {"players": [], "tournaments": [], "countries": []},
        # Armazena a última ação executada pelo bot (ex.: mostrar ranking, buscar jogador)
        "last_bot_action": None,
        # Indica se há uma pergunta de acompanhamento pendente para o usuário
        "pending_follow_up": None,
        # Jogador em foco na conversa atual, útil para perguntas de contexto
        "focus_player": None,
    }


# Define a classe SessionManager que gerencia todas as sessões ativas do chatbot
class SessionManager:
    """Gerenciador de sessões in-memory para o chatbot de tênis."""

    # Método construtor que inicializa o gerenciador com um dicionário vazio de sessões
    def __init__(self):
        # Dicionário que mapeia session_id para o contexto da sessão correspondente
        self.sessions = {}

    # Método que retorna uma sessão existente ou cria uma nova caso não exista
    def get_or_create(self, session_id=None):
        """Retorna o contexto existente ou cria um novo."""
        # Antes de tudo, remove sessões que já expiraram por inatividade
        self._cleanup_expired()

        # Verifica se o session_id foi fornecido e se já existe uma sessão ativa com esse id
        if session_id and session_id in self.sessions:
            # Obtém o contexto da sessão existente
            ctx = self.sessions[session_id]
            # Atualiza o timestamp de última atividade para evitar expiração
            ctx["last_active"] = time.time()
            # Retorna o contexto da sessão já existente
            return ctx

        # Sessão não existe ou não foi fornecida — cria uma nova
        # Se não foi fornecido um id, gera um UUID aleatório como identificador
        new_id = session_id or str(uuid.uuid4())
        # Cria um novo contexto de sessão com valores padrão usando a função auxiliar
        ctx = _new_context(new_id)
        # Armazena o novo contexto no dicionário de sessões ativas
        self.sessions[new_id] = ctx
        # Retorna o contexto recém-criado para uso imediato
        return ctx

    # Método que atualiza o contexto de uma sessão após cada interação (mensagem do usuário ou do bot)
    def update(self, session_id, role, text, intent=None, bot_action=None,
               topic=None, circuit=None, pending_follow_up=None,
               mentioned_players=None, mentioned_tournaments=None,
               mentioned_countries=None, focus_player=None):
        """Atualiza o contexto da sessão após uma interação."""
        # Se a sessão não existe no dicionário, encerra o método sem fazer nada
        if session_id not in self.sessions:
            return

        # Obtém o contexto da sessão a ser atualizada
        ctx = self.sessions[session_id]
        # Atualiza o timestamp de última atividade para o momento atual
        ctx["last_active"] = time.time()

        # Adiciona ao histórico (máx MAX_TURNS entradas)
        # Insere a nova mensagem no final da lista de histórico com papel, texto e intenção
        ctx["history"].append({"role": role, "text": text, "intent": intent})
        # Se o histórico ultrapassar o dobro do limite de turnos, mantém apenas as entradas mais recentes
        if len(ctx["history"]) > MAX_TURNS * 2:
            # Fatia a lista para manter apenas as últimas MAX_TURNS*2 entradas (descarta as mais antigas)
            ctx["history"] = ctx["history"][-(MAX_TURNS * 2):]

        # Se a mensagem é do usuário, incrementa o contador de turnos até o máximo permitido
        if role == "user":
            # Usa min() para garantir que o contador nunca ultrapasse MAX_TURNS
            ctx["turn_count"] = min(ctx["turn_count"] + 1, MAX_TURNS)

        # Atualiza campos opcionais apenas se fornecidos
        # Se uma ação do bot foi especificada, atualiza o campo correspondente no contexto
        if bot_action is not None:
            ctx["last_bot_action"] = bot_action
        # Se um tópico foi especificado, atualiza o tópico atual da conversa
        if topic is not None:
            ctx["current_topic"] = topic
        # Se um circuito foi especificado (ATP ou WTA), atualiza o circuito atual
        if circuit is not None:
            ctx["current_circuit"] = circuit
        # Se há uma pergunta de acompanhamento pendente, registra no contexto
        if pending_follow_up is not None:
            ctx["pending_follow_up"] = pending_follow_up
        # Se um jogador em foco foi especificado, atualiza o campo correspondente
        if focus_player is not None:
            ctx["focus_player"] = focus_player

        # Acumula entidades mencionadas (sem duplicatas)
        # Obtém a referência ao dicionário de entidades mencionadas nesta sessão
        entities = ctx["mentioned_entities"]
        # Itera sobre cada jogador mencionado (ou lista vazia se nenhum foi fornecido)
        for player in (mentioned_players or []):
            # Adiciona o jogador à lista apenas se ele ainda não estiver presente (evita duplicatas)
            if player not in entities["players"]:
                entities["players"].append(player)
        # Itera sobre cada torneio mencionado (ou lista vazia se nenhum foi fornecido)
        for tournament in (mentioned_tournaments or []):
            # Adiciona o torneio à lista apenas se ele ainda não estiver presente (evita duplicatas)
            if tournament not in entities["tournaments"]:
                entities["tournaments"].append(tournament)
        # Itera sobre cada país mencionado (ou lista vazia se nenhum foi fornecido)
        for country in (mentioned_countries or []):
            # Adiciona o país à lista apenas se ele ainda não estiver presente (evita duplicatas)
            if country not in entities["countries"]:
                entities["countries"].append(country)

    # Método privado que limpa sessões expiradas do dicionário de sessões ativas
    def _cleanup_expired(self):
        """Remove sessões inativas há mais de SESSION_TTL segundos."""
        # Obtém o timestamp atual para comparar com o último acesso de cada sessão
        now = time.time()
        # Cria uma lista com os IDs das sessões cuja inatividade excede o tempo limite (SESSION_TTL)
        expired = [sid for sid, ctx in self.sessions.items()
                   if now - ctx["last_active"] > SESSION_TTL]
        # Itera sobre cada sessão expirada e a remove do dicionário
        for sid in expired:
            # Deleta a sessão expirada do dicionário, liberando a memória associada
            del self.sessions[sid]
