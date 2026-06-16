# Importação das bibliotecas necessárias para o funcionamento do servidor e do chatbot
from flask import Flask, render_template, request, jsonify # Framework web para criar a API e servir o site
from flask_cors import CORS # Permite que o frontend acesse o backend de diferentes origens
from engine import TennisEngine # Importa o nosso motor de dados técnicos de tênis
from nltk_utils import tokenize, stem, bag_of_words, extract_entities # Utilitários de Processamento de Linguagem Natural
from session_manager import SessionManager # Gerenciador de sessões com contexto
from query_parser import parse_query # Parser inteligente de queries (país/temporal/superlativo)
from decision_tree import DecisionTree, _fuzzy_match_player, PRONOUN_KEYWORDS, TOURNAMENT_KEYWORDS, _is_records_or_fact_question, is_general_list_query, player_question_beyond_base # Árvore de decisão contextual com follow-ups
from api_client import TennisAPIClient # Cliente de atualização de rankings (ATP/WTA)
import llm_client # Fallback híbrido: consulta um LLM (LM Studio) quando a base não resolve
import web_search # Camada de pesquisa (retrieval Wikipedia) p/ grounding quando a base não cobre
import json # Para manipular arquivos de dados estruturados
import os # Para verificar a existência de arquivos no sistema
import re # Para limpar tags HTML do histórico antes de enviar ao LLM
import random # Para escolher respostas variadas quando houver várias opções
import sys # Para reconfigurar o stdout/stderr do servidor (UTF-8)
from datetime import datetime # Para registrar a data/hora nos logs de aprendizado

# No Windows o console padrão é cp1252 e NÃO encoda "→", acentos crus ou emojis.
# Vários prints de debug usam esses caracteres — web_search ("[WEB_SEARCH] … →"),
# app ("[PESQUISA] … →"), bandeiras (🇮🇹). Em cp1252 eles lançam UnicodeEncodeError;
# como build_grounding engole exceções, isso DESATIVAVA silenciosamente a pesquisa
# web (a IA caía na memória do modelo e alucinava). Forçar UTF-8 (errors=replace)
# torna todo print seguro e mantém o "modo pesquisa" (Wikipedia/DuckDuckGo) funcional.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Regex simples para remover tags HTML (ex.: <span ...>) das respostas do bot
# antes de reaproveitá-las como histórico de contexto para o LLM.
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Inicialização do aplicativo Flask (nosso servidor)
app = Flask(__name__) # Cria a instância global do servidor web
# Ativação do CORS para permitir requisições de outros domínios ou portas locais
CORS(app) # Habilita o compartilhamento de recursos entre origens diferentes

# Atualização automática de rankings no startup (ATP via tennisexplorer, WTA via API oficial)
api_client = TennisAPIClient()
if api_client.refresh_if_needed():
    print("[STARTUP] Rankings atualizados com sucesso!")

# Instanciação do motor técnico que buscará rankings, campeões e perfis
tennis_engine = TennisEngine() # Carrega o "cérebro" de dados em memória (após refresh)

# Instanciação do gerenciador de sessões (mantém contexto de até 20 interações)
session_mgr = SessionManager()

# Instanciação da árvore de decisão contextual
decision_tree = DecisionTree(tennis_engine)

# Caminho para o "diário" de perguntas não reconhecidas (base para o Machine Learning futuro)
UNRECOGNIZED_FILE = 'unrecognized_queries.json' # Define o nome do arquivo de logs de erro

# Lista de termos que remetem a outros esportes e devem ser barrados (Filtro de Contexto)
OFF_TOPIC_KEYWORDS = [
    # Esportes
    "copa", "futebol", " gol ", "basquete", "nba", "baseball", "beisebol",
    "formula 1", "f1", "hamilton", "verstappen", "nascar", "motogp",
    "golf", "golfe", "boxe", "mma", "ufc", "luta", "wrestling",
    "natação", "natacao", "surf", "skate", "skateboard", "ciclismo",
    "vôlei", "voleibol", "handball", "handebol", "rugby", "cricket",
    "nfl", "mlb", "nhl", "premier league", "champions league", "libertadores",
    "flamengo", "corinthians", "palmeiras", "messi", "neymar", "cristiano",
    "lebron", "curry", "jordan",
    # Outros temas
    "buraco negro", "fisica", "física", "química", "quimica",
    "receita", "cozinha", "comida", "bolo", "pizza",
    "politica", "política", "eleição", "eleicao", "presidente", "deputado",
    "bitcoin", "crypto", "criptomoeda", "bolsa de valores",
    "filme", "netflix", "série", "serie", "anime",
    "música", "musica", "cantor", "cantora", "banda",
    "carro", "moto", "avião", "aviao",
    "programação", "programacao", "javascript", "código", "codigo",
    "clima", "previsão", "previsao",
    "religião", "religiao", "igreja",
    # Geografia / conhecimento geral — caem no LLM (ex.: "capital da austrália")
    "capital", "população", "populacao", "habitantes", "moeda", "idioma",
    "continente", "fica em que país", "qual a língua",
    # Ciência / astronomia / acadêmico — caem no LLM (ex.: "distância da terra à lua")
    "planeta", "planetas", "sistema solar", "universo", "galáxia", "galaxia",
    "estrela", "lua", "astronomia", "matemática", "matematica", "biologia",
    "filosofia", "geografia", "equação", "equacao", "raiz quadrada",
]

# Conhecimento geral INEQUÍVOCO → vai direto ao LLM (atalho rápido da Camada 1).
# Curado para NÃO colidir com torneios (por isso nada de "monte"/"rio" cru, que
# fazem parte de "Monte Carlo"/"Rio Open").
GENERAL_KNOWLEDGE_KEYWORDS = [
    "prédio", "predio", "edifício", "edificio", "arranha-céu", "arranha ceu",
    "montanha", "montanhas", "cordilheira", "everest", "vulcão", "vulcao",
    "deserto", "oceano", "cachoeira", "catarata", "geleira", "terremoto",
    "tsunami", "ponte", "torre",
]

# Superlativo de mundo ("… mais alto/longo/profundo do mundo/planeta/terra").
# Apertado de propósito: exige o sufixo geográfico para NÃO pegar "partida mais
# longa da história" nem "melhor jogador do mundo" (que usa "melhor", não "mais").
SUPERLATIVE_WORLD_RE = re.compile(r'\bmais\s+\w+\s+(?:do\s+mundo|do\s+planeta|da\s+terra)\b')

# Vocabulário INEQUÍVOCO de tênis. Note que palavras ambíguas/duais ("alto",
# "país", "altura"/"mede" sozinhas) NÃO entram aqui — é justamente o que deixa o
# Qwen (Camada 3) validar de fato os casos ambíguos.
TENNIS_SIGNAL_WORDS = [
    "tenis", "tênis", "atp", "wta", "jogador", "jogadora", "jogadores", "jogadoras",
    "tenista", "tenistas", "raquete", "saque", "saca", "saibro", "grama", "quadra",
    "superfície", "superficie", "piso", "set", "sets", "game", "games", "ace",
    "tiebreak", "tie-break", "deuce", "break point", "slam", "grand slam", "masters",
    "torneio", "torneios", "campeonato", "campeonatos", "ranking", "rank", "circuito",
    "título", "titulo", "títulos", "titulos", "campeão", "campea", "campeã", "campeoes",
    "campeões", "vencedor", "vencedores", "recorde", "recordes", "partida", "forehand",
    "backhand", "voleio", "estilo", "curiosidade", "curiosidades",
]

# Mensagem única de bloqueio (o bot é FECHADO no tema tênis). Usada sempre que a
# pergunta foge do tênis — seja pelas regras, pela validação do Qwen ou pela
# sentinela FORA_DO_TEMA no fallback.
OFF_TOPIC_BLOCK_MSG = (
    "Desculpe, mas eu respiro apenas Tênis! 🎾\n"
    "Posso te contar sobre o ranking da ATP/WTA, jogadores ou os campeões de Grand "
    "Slam — mas sobre outros assuntos eu prefiro não comentar."
)

# Qualificadores de "maior de todos os tempos" (GOAT). Quando presentes, o
# superlativo "melhor" NÃO deve devolver o #1 atual do ranking — deixamos o
# intent goat_debate (ou o LLM) responder ao debate histórico.
GOAT_QUALIFIERS = [
    "todos os tempos", "da história", "da historia", "na história", "na historia",
    "goat", "maior de todos", "já existiu", "ja existiu",
]

# Keywords que indicam que o usuário quer detalhes/informações sobre um Grand Slam (não campeões)
SLAM_DETAIL_KEYWORDS = [
    "sobre", "detalhes", "detalhe", "fala sobre", "me fala", "conta sobre",
    "o que é", "o que e", "como é", "como e", "onde fica", "onde é",
    "história", "historia", "quando foi criado", "informações", "informacoes",
    "ficha do torneio", "superfície", "superficie", "piso do",
    "premiação", "premiacao", "prize money", "quanto vale", "pontos do",
]

# Palavras que indicam pedido de CURIOSIDADE/FATO sobre um jogador. Lista enxuta de
# propósito (evita "fato" solto, que casaria "de fato"): só dispara o roteador de
# curiosidade quando a intenção é clara E há um jogador-alvo (nome ou pronome→foco).
PLAYER_CURIOSITY_KEYWORDS = [
    "curiosidade", "curiosidades", "fato curioso", "fatos curiosos", "fato interessante",
    "algo interessante", "alguma curiosidade", "conta uma curiosidade", "me conta um fato",
]

# Nota anexada ao prompt quando o roteamento JÁ decidiu que é tênis (jogador resolvido,
# lista de jogadores, país/torneio de tênis). O Qwen às vezes erra e devolve a sentinela;
# aqui ela é proibida.
_ON_TOPIC_NOTE = ("IMPORTANTE: esta pergunta É sobre tênis — responda normalmente e NUNCA "
                  "responda com a sentinela FORA_DO_TEMA. ")

# Perguntas sobre um TORNEIO que a base (local, superfície, fundação, premiação, história,
# campeões) NÃO cobre → vão à IA (ex.: preço de ingresso, diretor, transmissão).
TOURNAMENT_BEYOND_KW = [
    "ingresso", "ingressos", "custa", "custo", "preço", "preco", "bilhete", "diretor",
    "presidente", "transmiss", "onde assistir", "como assistir", "onde comprar",
    "como chegar", "hotel", "estacionamento", "credenciamento",
]

# Stop stems portugueses para filtrar do intent matching (evita falsos positivos)
PORTUGUESE_STOP_STEMS = {
    "de", "do", "da", "dos", "das", "o", "a", "os", "as",
    "um", "uma", "uns", "e", "ou", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "se", "ao", "que", "é",
    "quai", "qual", "quem", "como", "?", "!", ".",
    # Palavra-domínio: "tênis"/"tenista" aparece em quase toda pergunta deste bot,
    # então NÃO deve discriminar intent (senão "quem inventou o tênis?" casa qualquer
    # intent curto que contenha "tênis", ex.: brasil_tenis, em 50%). Stems variam com acento.
    "têni", "teni", "tenista", "tennis",
}

# Função que carrega a base de conhecimento (Intents) do arquivo JSON
def load_knowledge_base(): # Define a função de carregamento
    # Abre o arquivo com encoding utf-8 para suportar acentos e caracteres especiais
    with open('knowledge_base.json', 'r', encoding='utf-8') as f: # Abre o arquivo JSON em modo leitura
        return json.load(f) # Converte o texto JSON em um dicionário Python e retorna

# Função para registrar perguntas que o robô ainda não sabe responder
def log_unrecognized_query(query): # Define a função de log
    data = [] # Inicializa uma lista vazia para os dados
    if os.path.exists(UNRECOGNIZED_FILE): # Se o arquivo de logs já existir...
        try: # Tenta realizar a leitura com segurança
            with open(UNRECOGNIZED_FILE, 'r', encoding='utf-8') as f: # Abre para leitura
                data = json.load(f) # Carrega os logs existentes
        except: # Caso o arquivo esteja corrompido ou vazio
            data = [] # Reinicia a lista para evitar travamentos

    # Cria um novo registro com o texto da pergunta e o horário atual
    entry = { # Define o dicionário do log
        "query": query, # Salva a pergunta do usuário
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Salva o momento exato
    }
    data.append(entry) # Adiciona a nova entrada à lista principal

    # Salva a lista atualizada de volta no arquivo JSON
    with open(UNRECOGNIZED_FILE, 'w', encoding='utf-8') as f: # Abre para escrita (sobrescreve)
        json.dump(data, f, indent=4, ensure_ascii=False) # Grava o JSON formatado com indentação

# Monta um "contexto factual" curto e em texto puro para enviar ao LLM no fallback.
# Objetivo: reduzir alucinação ancorando o modelo nos dados reais do projeto
# (perfil do jogador citado e/ou topo do ranking atual). Reaproveita os dados já
# carregados em memória pelo TennisEngine. Retorna string (pode ser vazia).
def build_grounding(msg_lower, player_name=None, force_web=False):
    # player_name: quando o chamador já resolveu o jogador-alvo (ex.: pronome
    # "curiosidade sobre ele" → focus_player). Tem prioridade sobre o fuzzy do texto.
    # force_web: se True, FAZ a pesquisa Wikipedia mesmo quando há perfil local
    # (usado na rota de curiosidade — combina o fato curado da base + a fonte ao vivo,
    # cobrindo jogadores cujo 'fact' local é genérico/curto).
    parts = [] # Acumula os trechos de contexto relevantes
    grounded_player = None  # Jogador que já temos perfil LOCAL (evita pesquisa redundante)
    search_meta = None      # Fontes da pesquisa web (p/ visualização "modo pesquisa" no front)
    try:
        # Fuzzy ENDURECIDO (0.85): evita injetar um perfil errado por match fraco numa pergunta
        # geral/lista (ex.: "cite 10 jogadores canhotos" não pode virar contexto de um jogador).
        matched = player_name or _fuzzy_match_player(msg_lower, tennis_engine.get_all_player_names(), threshold=0.85)
        p = tennis_engine.data.get("player_details", {}).get(matched) if matched else None
        if p:
            grounded_player = matched

        # PESQUISA Wikipedia PRIMEIRO (quando aplicável). Se ela trouxer a fonte autoritativa
        # e atual, OMITIMOS os campos potencialmente desatualizados da base (títulos/curiosidade)
        # para não confundir o modelo — ex.: a base diz "buscando o 1º título" mas a Wikipedia
        # mostra que o jogador já é campeão. Pesquisa só com player-alvo (lista/geral = ruído).
        retrieved = None
        if (force_web or not grounded_player) and llm_client._enabled() and web_search.enabled():
            retrieved = web_search.search_tennis(msg_lower, player_hint=player_name)
            if retrieved:
                search_meta = {"sources": retrieved.get("sources", []), "query": retrieved.get("query"),
                               "context": retrieved.get("context")}

        # (a) Perfil LOCAL do jogador. Campos neutros (país/idade/estilo) sempre; títulos e
        # curiosidade SÓ quando NÃO temos a Wikipedia daquele jogador (evita texto stale).
        if p:
            campos = [f"{matched}"]
            if p.get("country"): campos.append(f"país: {p['country']}")
            if p.get("age"):     campos.append(f"idade: {p['age']}")
            if p.get("style"):   campos.append(f"estilo: {p['style']}")
            # Perguntas de Grand Slam ("quantos/quais slams"): o títulos CURADO traz a
            # divisão por torneio (ex.: "24 (10x Australian Open, 7x Wimbledon…)") que a
            # Wikipedia não detalha — então incluímos mesmo quando há pesquisa web, para
            # a IA poder dizer QUAIS, não só o total.
            _slam_q = any(k in msg_lower for k in ("grand slam", "slam", "slams", "major", "majors"))
            if (not retrieved) or _slam_q:
                if p.get("titles"): campos.append(f"títulos: {p['titles']}")
            if not retrieved:
                if p.get("fact"):   campos.append(f"curiosidade: {p['fact']}")
            parts.append("Jogador(a) — " + "; ".join(campos) + ".")

        # (b) A mensagem é sobre ranking/melhor do mundo? Injeta o Top 5 atual.
        if any(k in msg_lower for k in ["ranking", "top ", "número 1", "numero 1",
                                         "nº1", "n1", "melhor do mundo", "líder", "lider",
                                         "primeiro lugar", "número um", "numero um"]):
            for circuito, chave in (("ATP", "ranking_atp"), ("WTA", "ranking_wta")):
                top = tennis_engine.data.get(chave, [])[:5]
                if top:
                    linha = ", ".join(f"{x['position']}º {x['name']} ({x['country']})" for x in top)
                    parts.append(f"Top 5 {circuito} atual (mar/2026): {linha}.")

        # (c) Pergunta histórica/GOAT? Injeta lendas REAIS para reduzir alucinação
        # (ex.: "melhor brasileiro de todos os tempos" = Guga, não nomes inventados).
        if any(t in msg_lower for t in ["todos os tempos", "da história", "da historia",
                                         "maior de todos", "melhor de todos", "lenda",
                                         "goat", "já existiu", "ja existiu", "da hist"]):
            parts.append(
                "Maiores tenistas da história (referência factual, use isto): "
                "Masculino — Novak Djokovic (24 Grand Slams), Rafael Nadal (22), Roger Federer (20). "
                "Feminino — Serena Williams (23), Steffi Graf (22), Martina Navratilova. "
                "Brasil — Gustavo Kuerten 'Guga' (3x Roland Garros, ex-nº1 do mundo, considerado o maior "
                "tenista brasileiro de todos os tempos), Maria Esther Bueno (19 Grand Slams, maior lenda "
                "feminina do Brasil), Beatriz Haddad Maia (maior brasileira da atualidade) e "
                "João Fonseca (jovem promessa). NÃO invente nomes fora desta lista."
            )

        # (d) Anexa a PESQUISA web (Wikipedia + DuckDuckGo) já recuperada acima.
        if retrieved:
            parts.append(retrieved["text"])
    except Exception:
        pass # Grounding é best-effort: qualquer erro aqui não pode quebrar o chat.
    return "\n".join(parts), search_meta

# Heurística GENEROSA: a mensagem tem ALGUMA evidência de tênis? Usada para
# decidir se pulamos a validação do Qwen (Camada 3) e para liberar superlativos
# legítimos ("jogador mais alto do mundo"). Direção segura: na dúvida, True.
def has_tennis_signal(msg_lower, msg_stems, focus=None):
    # 1. Continuação real ("sim", "conta mais") — usa a checagem cuidadosa da árvore
    #    (mensagem é/contém continuador E é curta), evitando o "mais" solto.
    if decision_tree._is_continue(msg_lower):
        return True
    # 2. Vocabulário inequívoco de tênis
    if any(kw in msg_lower for kw in TENNIS_SIGNAL_WORDS):
        return True
    # 3. Referência ao jogador em foco (pronome). Frases específicas ("país dele")
    #    ou pronome solto quando HÁ um jogador em foco.
    if any(kw in msg_lower for kw in PRONOUN_KEYWORDS):
        return True
    if focus and re.search(r'\b(?:dele|dela|deles|delas|ele|ela)\b', msg_lower):
        return True
    # 4. País reconhecido (ex.: "melhor da espanha")
    if parse_query(msg_lower).get("country_filter"):
        return True
    # 5. Nome de torneio por substring direta
    if any(t.lower() in msg_lower for t in tennis_engine.get_all_tournament_names()):
        return True
    # 6. Nome de jogador: exato (com guard de stem >= 4, como o pipeline) ou fuzzy
    #    endurecido. Typos reais ("Alcaras") contam; "alto" já não (virou stop word).
    players = tennis_engine.get_all_player_names()
    cand = extract_entities(msg_stems, players)
    if cand:
        cand_stems = [stem(w) for w in tokenize(cand.lower()) if len(stem(w)) > 2]
        if any(len(s) >= 4 and s in msg_stems for s in cand_stems):
            return True
    # Threshold alto (0.82): typos reais ("Alcaras"→"Alcaraz"=0.857) passam, mas
    # palavras comuns ("mona"→"Simona", "alto"→"Walton") NÃO — é o que deixa o
    # Qwen validar esses casos em vez de a base inventar um jogador.
    if _fuzzy_match_player(msg_lower, players, threshold=0.82):
        return True
    return False


# Conhecimento geral ÓBVIO (atalho rápido por regras da Camada 1). O que escapar
# daqui é decidido "de fato" pelo Qwen na Camada 3.
def looks_like_general_knowledge(msg_lower, msg_stems):
    if any(kw in msg_lower for kw in GENERAL_KNOWLEDGE_KEYWORDS):
        return True
    if SUPERLATIVE_WORLD_RE.search(msg_lower) and not has_tennis_signal(msg_lower, msg_stems):
        return True
    return False


# Rota principal que carrega a interface visual do nosso ChatBot
@app.route('/') # Define que a URL raiz '/' chamará esta função
def home(): # Define a função de carregamento da página inicial
    return render_template('index.html') # Envia o HTML da pasta /templates para o navegador

# Rota de processamento (API) que recebe a mensagem e retorna a resposta
@app.route('/predict', methods=['POST']) # Define que apenas o método POST é aceito nesta rota
def predict(): # Função principal de "predição" ou resposta
    text = request.get_json().get("message") # Extrai a mensagem enviada pelo usuário via JSON
    session_id = request.get_json().get("session_id") # Extrai o ID da sessão para contexto
    current_logs = [] # Inicializa uma lista de logs técnicos para enviar ao frontend
    pipeline_steps = [] # Pipeline visual estruturado para o frontend

    # Carrega ou cria a sessão do usuário
    context = session_mgr.get_or_create(session_id)
    session_id = context["session_id"]

    # Função auxiliar interna para preencher a lista de logs do processo
    def add_log(msg, level="INFO"): # Define a função de log interno
        current_logs.append(f"[{level}] {msg}") # Formata e adiciona a mensagem ao log

    def add_step(name, status, detail=None, data=None):
        """Adiciona um passo visual ao pipeline. status: waiting/active/success/skipped/fail"""
        pipeline_steps.append({"name": name, "status": status, "detail": detail or "", "data": data or {}})

    # Função auxiliar para enviar resposta e atualizar sessão
    def respond(answer, topic=None, bot_action=None, mentioned_players=None,
                mentioned_tournaments=None, mentioned_countries=None):
        """Enriquece a resposta com follow-up contextual e atualiza a sessão."""
        enriched = decision_tree.enrich_response(
            answer, topic or context.get("current_topic", "trivia"),
            bot_action or "showed_trivia", context,
            mentioned_players=mentioned_players,
            mentioned_tournaments=mentioned_tournaments,
            mentioned_countries=mentioned_countries,
        )
        # Registra a mensagem do usuário no histórico
        session_mgr.update(session_id, "user", text)
        # Registra a resposta do bot no histórico com metadados
        session_mgr.update(
            session_id, "bot", enriched["response"],
            intent=enriched["bot_action"],
            bot_action=enriched["bot_action"],
            topic=enriched["topic"],
            pending_follow_up=enriched["pending_follow_up"],
            mentioned_players=enriched["mentioned_players"],
            mentioned_tournaments=enriched["mentioned_tournaments"],
            mentioned_countries=enriched["mentioned_countries"],
            focus_player=enriched.get("focus_player"),
        )
        add_log(f"[SESSÃO] Turno {context['turn_count']}, Tópico: {enriched['topic']}, Pendente: {enriched['pending_follow_up']}, Foco: {enriched.get('focus_player')}", "DEBUG")
        add_step("Resposta Final", "success", f"Tópico: {enriched['topic']} | Ação: {enriched['bot_action']}", {"follow_up": enriched['pending_follow_up'], "focus": enriched.get('focus_player')})
        llm_client.record("resolved_by_base") # Métrica: pergunta resolvida pela base de conhecimento
        return jsonify({"answer": enriched["response"], "logs": current_logs, "pipeline": pipeline_steps})

    # Bloqueia uma pergunta fora de tênis: registra e devolve o aviso canned. O bot
    # é fechado no tema; off-topic NUNCA é respondido pelo LLM.
    def block_off_topic(detail):
        add_step("Filtro Off-Topic", "fail", detail)
        add_log(f"Bloqueado (fora de tênis): {detail}", "WARNING")
        log_unrecognized_query(text)
        session_mgr.update(session_id, "user", text)
        llm_client.record("unresolved")
        return jsonify({"answer": OFF_TOPIC_BLOCK_MSG, "logs": current_logs, "pipeline": pipeline_steps})

    # Aciona o LLM (LM Studio) para perguntas de TÊNIS que a base local não cobre.
    # Retorna:
    #   - Response com a resposta de tênis gerada pelo Qwen; OU
    #   - Response de BLOQUEIO se o Qwen classificar como fora de tênis (sentinela
    #     FORA_DO_TEMA) — o bot é fechado no tema; OU
    #   - None quando o LLM está desligado/indisponível (o chamador usa o canned).
    def try_llm_fallback(step_detail="Base não resolveu (tênis) — acionando LLM",
                          grounding=None, search_meta=None, extra_system=None, temperature=None):
        # grounding: contexto factual já pronto (ex.: perfil do jogador + pesquisa web).
        #            Se None, montamos a partir da mensagem.
        # search_meta: fontes da pesquisa web (Wikipedia/DuckDuckGo) p/ o painel "modo pesquisa".
        # extra_system: instrução extra ao LLM (ex.: "modo curiosidade").
        add_step("LLM · LM Studio", "active", step_detail) # Acende a etapa LLM no pipeline visual
        add_log("Acionando LLM (LM Studio) para pergunta de tênis fora da base...", "SYSTEM")
        if grounding is None:
            grounding, search_meta = build_grounding(msg_lower) # Contexto factual (anti-alucinação)
        # Transparência ("modo pesquisa"): se a busca web entrou no grounding, mostra a etapa
        # com as FONTES (engine + título + url + trecho) para o painel lateral do front.
        if search_meta and search_meta.get("sources"):
            engines = ", ".join(sorted({s.get("engine", "?") for s in search_meta["sources"]}))
            add_step("🔎 Pesquisa na web", "success",
                     f"{len(search_meta['sources'])} fonte(s) consultada(s): {engines}",
                     data={"search": search_meta})
            for s in search_meta["sources"]:
                add_log(f"[PESQUISA] {s.get('engine')}: {s.get('title')} — {s.get('url')}", "SUCCESS")
            print(f"[PESQUISA] '{search_meta.get('query')}' → {len(search_meta['sources'])} fonte(s): {engines}")
        # NÃO enviamos histórico ao LLM: o contexto de tênis (ex.: a ficha de um jogador)
        # confunde modelos pequenos e dispara troca de idioma (chinês). Follow-ups de
        # tênis já são resolvidos pela base (árvore de decisão); aqui o LLM responde a
        # pergunta isolada, o que deixa a resposta mais estável e mais rápida (sem retry).
        result = llm_client.query_llm(text, grounding=grounding, history=None,
                                      extra_system=extra_system, temperature=temperature)
        if not result: # LLM indisponível ou sem resposta → deixa o canned assumir
            add_step("LLM · LM Studio", "fail", "LLM indisponível ou sem resposta")
            add_log("LLM indisponível — usando resposta padrão.", "WARNING")
            return None
        answer = result["answer"]
        # Sentinela: o Qwen confirmou que a pergunta NÃO é de tênis → bloquear.
        if llm_client.OFF_TOPIC_SENTINEL in answer.upper().replace(" ", "_"):
            add_step("LLM · LM Studio", "fail", "Qwen classificou como fora de tênis")
            return block_off_topic("Validação Qwen: pergunta fora de tênis → bloqueada")
        lat = result.get("latency") or 0
        usage = result.get("usage") or {}
        comp = usage.get("completion_tokens")
        tps = round(comp / lat, 1) if (comp and lat) else None
        add_step("LLM · LM Studio", "success", f"Respondido pelo LLM em {lat:.1f}s", data={"llm": {
            "request": result.get("request", {}),
            "answer": answer,
            "latency": round(lat, 2),
            "usage": usage,
            "finish_reason": result.get("finish_reason"),
            "tokens_per_s": tps,
        }})
        add_log(f"Resposta gerada pelo LLM ({lat:.2f}s).", "SUCCESS")
        session_mgr.update(session_id, "user", text)
        session_mgr.update(session_id, "bot", answer, bot_action="showed_llm",
                           topic=context.get("current_topic"))
        return jsonify({"answer": answer, "logs": current_logs, "pipeline": pipeline_steps})

    # Processamento inicial da mensagem (Pré-processamento)
    add_log(f">> Comando recebido: {text}", "INFO")
    msg_lower = text.lower().strip()
    msg_tokens = tokenize(msg_lower)
    msg_stems = [stem(w) for w in msg_tokens]
    add_log(f"[NLTK] Tokens: {msg_tokens}", "DEBUG")
    add_log(f"[NLTK] Radicais estruturados: {msg_stems}", "DEBUG")

    # Pipeline visual: Entrada + Tokenização
    add_step("Entrada do Usuário", "success", text, {"original": text})
    add_step("Tokenização NLTK", "success", " → ".join(msg_tokens), {"tokens": msg_tokens, "stems": msg_stems})

    # --- Passo 0: Filtro de Contexto (Anti-Offtopic + Gibberish) ---
    # Detecta gibberish: palavras longas com padrões não-naturais
    import re as _re
    def is_gibberish(text_to_check):
        words = [w for w in text_to_check.split() if len(w) > 5 and w.isalpha()]
        if not words:
            return False
        vowels = set('aeiouáéíóúâêîôûãõ')
        for w in words:
            # Proporção de vogais muito baixa ou alta
            ratio = sum(1 for c in w if c in vowels) / len(w)
            if ratio < 0.15 or ratio > 0.85:
                return True
            # 4+ consoantes consecutivas (raro em português/inglês)
            consonant_run = _re.search(r'[^aeiouáéíóúâêîôûãõ]{4,}', w)
            if consonant_run and len(w) > 5:
                return True
            # Mesma letra repetida 3+ vezes
            if _re.search(r'(.)\1{2,}', w):
                return True
            # Palavra muito longa (>10 chars) sem nenhum bigrama comum do português
            if len(w) > 10:
                common_bigrams = {'de', 'er', 'ar', 'en', 'an', 'es', 'al', 'or', 'os', 'ra',
                                  'te', 'co', 'se', 'ta', 'do', 'in', 'on', 're', 'ao', 'ão',
                                  'ca', 'to', 'is', 'la', 'ma', 'da', 'na', 'ad', 'qu', 'pa',
                                  'si', 'le', 'ei', 'ir', 'as', 'il', 'br', 'ro', 'at', 'it',
                                  'io', 'ia', 'ri', 'li', 'lo', 'me', 'no', 'ti', 'sa', 'ni'}
                bigrams = {w[i:i+2] for i in range(len(w)-1)}
                if len(bigrams & common_bigrams) < 2:
                    return True
        return False

    is_off_topic = any(off in msg_lower for off in OFF_TOPIC_KEYWORDS)
    is_gibber = is_gibberish(msg_lower)

    # Gibberish (texto sem sentido) continua BLOQUEADO — não faz sentido gastar o
    # LLM com "Xyfzq123". Tem prioridade sobre o filtro off-topic.
    if is_gibber:
        add_log("Texto sem sentido detectado!", "WARNING")
        add_step("Filtro Off-Topic", "fail", "Texto sem sentido detectado")
        log_unrecognized_query(text)
        session_mgr.update(session_id, "user", text)
        llm_client.record("unresolved") # Métrica: não resolvida
        resp_text = "Hmm, não entendi essa mensagem. 🤔\nTenta me perguntar sobre ranking ATP, jogadores ou torneios de Grand Slam!"
        return jsonify({"answer": resp_text, "logs": current_logs, "pipeline": pipeline_steps})

    # Fora do contexto de tênis → AVISAR E BLOQUEAR. O bot é fechado no tema; off-topic
    # NÃO vai para o LLM (o LLM só responde perguntas DE tênis fora da base local).
    # Camada 1 (atalho por regras): blocklist + conhecimento geral ÓBVIO
    # ("prédio mais alto do mundo") — bloqueio instantâneo, sem custo de LLM.
    if is_off_topic or looks_like_general_knowledge(msg_lower, msg_stems):
        return block_off_topic("Pergunta fora do tema (regras) — bloqueada")

    # --- Passo 0.5: Resolução Contextual (Árvore de Decisão) ---
    add_step("Filtro Off-Topic", "success", "Mensagem permitida (contexto tênis)")
    pending_ctx = context.get("pending_follow_up")
    focus_ctx = context.get("focus_player")

    # --- Camada 3: VALIDAÇÃO AUTORITATIVA VIA QWEN (BLOQUEIO) ---
    # A blocklist nunca cobre todo assunto fora de tênis. Quando há contexto ativo
    # (janela em que a árvore "sequestraria" a resposta com dados do jogador em foco)
    # e a frase NÃO tem sinal de tênis, o Qwen decide "de fato" se é tênis. Se for
    # off-topic → BLOQUEIA antes da árvore. Disparo estreito ⇒ não pesa nos turnos
    # normais. Com LLM off, is_on_topic() retorna None e o fluxo segue idêntico ao de
    # hoje (testes determinísticos).
    if pending_ctx and not has_tennis_signal(msg_lower, msg_stems, focus_ctx):
        if llm_client.is_on_topic(text) is False:  # Quem decidiu foi o Qwen
            return block_off_topic("Validação Qwen: fora de tênis (contexto ativo) — bloqueada")

    contextual_result = decision_tree.try_contextual_response(msg_lower, msg_stems, context, add_log)

    # try_contextual_response retorna (resp, topic, action, players, trace) ou (None, trace)
    if contextual_result is not None and contextual_result[0] is not None:
        resp_text, topic, bot_action, mentioned_players, trace = contextual_result
        # Para torneios resolvidos pela árvore, extrai o nome do torneio do trace
        ctx_mentioned_t = None
        if bot_action in ("showed_slam_details", "showed_champions"):
            for node in trace:
                detail = node.get("detail", "")
                if "Detalhes de " in detail:
                    ctx_mentioned_t = [detail.replace("Detalhes de ", "")]
                elif "Campeão de " in detail:
                    ctx_mentioned_t = [detail.replace("Campeão de ", "")]
                elif " detectado" in detail:
                    ctx_mentioned_t = [detail.replace(" detectado", "")]
        add_log(f"[CONTEXTO] Resposta resolvida via árvore de decisão! Ação: {bot_action}", "SUCCESS")
        add_step("Árvore de Decisão", "success",
                 f"Resolvido → {bot_action}",
                 {"pending": pending_ctx, "focus": focus_ctx, "topic": context.get("current_topic"),
                  "turn": context.get("turn_count", 0), "trace": trace})
        return respond(resp_text, topic=topic, bot_action=bot_action,
                       mentioned_players=mentioned_players,
                       mentioned_tournaments=ctx_mentioned_t)

    # Não resolveu — extrai trace mesmo assim para visualização
    trace = contextual_result[1] if contextual_result is not None else []
    add_step("Árvore de Decisão", "success" if pending_ctx else "skipped",
             f"Contexto: {pending_ctx or 'nenhum'}" + (f" | Foco: {focus_ctx}" if focus_ctx else "") + " → pipeline normal",
             {"pending": pending_ctx, "focus": focus_ctx, "topic": context.get("current_topic"),
              "turn": context.get("turn_count", 0), "trace": trace})

    # --- Passo 0.7: Parser Inteligente de Query (País/Temporal/Superlativo) ---
    parsed = parse_query(msg_lower)
    parser_detail = []
    if parsed["country_filter"]: parser_detail.append(f"País: {parsed['country_filter']}")
    if parsed["wants_best"]: parser_detail.append("Superlativo: melhor")
    if parsed["is_current"]: parser_detail.append("Temporal: atual")
    if parsed["circuit"]: parser_detail.append(f"Circuito: {parsed['circuit']}")
    add_step("Query Parser", "success" if parser_detail else "skipped",
             " | ".join(parser_detail) if parser_detail else "Nenhum modificador detectado",
             {"country": parsed["country_filter"], "best": parsed["wants_best"], "current": parsed["is_current"], "circuit": parsed["circuit"]})
    # "quem é o numero 1 do mundo" → sem país, com superlativo + contexto de jogador → mostra #1
    player_context_words = ["jogador", "jogadora", "tenista", "numero 1", "número 1", "mundo", "ranking"]
    feminine_words = ["jogadora", "tenista feminina", "mulher", "feminino"]
    # Verifica se a mensagem tem um número específico > 1 (ex: "número 100") → não é superlativo
    import re as _re_check
    _specific_num = _re_check.search(r'(?:número|numero|n[°º]|top|posição|posicao|atual)\s*(\d{1,3})', msg_lower)
    _has_specific_position = _specific_num and int(_specific_num.group(1)) > 1
    # GOAT: "melhor tenista de todos os tempos" NÃO é o #1 atual.
    _is_goat_query = any(q in msg_lower for q in GOAT_QUALIFIERS)
    if _is_goat_query and parsed["country_filter"]:
        # "melhor brasileiro de todos os tempos" (Guga): a base só tem o debate
        # global (Big Three), então o LLM responde o melhor histórico do país.
        llm_resp = try_llm_fallback("GOAT histórico de um país → LLM")
        if llm_resp is not None:
            return llm_resp
    if _is_goat_query and parsed["wants_best"] and any(w in msg_lower for w in player_context_words):
        # Debate do GOAT (maior de todos os tempos) — serve a resposta curada da base,
        # evitando tanto o #1 atual quanto o intent genérico players_tenis.
        goat_intent = next((i for i in load_knowledge_base()["intents"] if i["tag"] == "goat_debate"), None)
        if goat_intent:
            add_log("[PARSER] Pergunta histórica/GOAT → goat_debate", "SUCCESS")
            add_step("Base de Conhecimento", "success", "Intent: goat_debate (histórico)")
            return respond(random.choice(goat_intent["responses"]), topic="trivia", bot_action="showed_trivia")
    # Se a mensagem NOMEIA um jogador específico (ex.: "qual o melhor ranking do João
    # Fonseca"), o "melhor" se refere A ELE — NÃO é "o #1 do mundo". Não dispara o atalho
    # do líder (que mostraria o Sinner). Deixa seguir p/ o bloco de jogador (ficha) ou IA.
    _sup_named = extract_entities(msg_stems, tennis_engine.get_all_player_names())
    if _sup_named:
        _sn_stems = [stem(w) for w in tokenize(_sup_named.lower()) if len(stem(w)) > 2]
        if not any(len(s) >= 4 and s in msg_stems for s in _sn_stems):
            _sup_named = None
    if not parsed["country_filter"] and parsed["wants_best"] and any(w in msg_lower for w in player_context_words) and not _has_specific_position and not _is_goat_query and not _sup_named and not _is_records_or_fact_question(msg_lower):
        # Detecta se é feminino → WTA
        circuit = parsed["circuit"] or ('WTA' if any(w in msg_lower for w in feminine_words) else 'ATP')
        ranking_data = tennis_engine.data.get(f"ranking_{circuit.lower()}", [])
        if ranking_data:
            top_player = ranking_data[0]['name']
            add_log(f"[PARSER] Superlativo sem país → #1 {circuit}: {top_player}", "SUCCESS")
            add_step("Motor de Dados", "success", f"#1 {circuit}: {top_player}")
            info = tennis_engine.get_player_info(top_player)
            if info:
                return respond(info, topic="player", bot_action="showed_player_info",
                               mentioned_players=[top_player])

    if parsed["country_filter"]:
        add_log(f"[PARSER] País detectado: {parsed['country_filter']}, Melhor: {parsed['wants_best']}, Atual: {parsed['is_current']}", "DEBUG")

        # GUARDA: pergunta de país ALÉM da base (ex.: "tenista mais rico do brasil",
        # "jogador brasileiro mais polêmico", "treinador brasileiro") → IA. A base só
        # responde "melhores RANQUEADOS do país"; o resto não é premeditável.
        if player_question_beyond_base(msg_lower):
            add_log("[ROUTER] País + pergunta além da base → IA", "SYSTEM")
            add_step("País → IA", "active", "Pergunta de país além da base → IA")
            llm_resp = try_llm_fallback("Pergunta de país além da base → IA",
                extra_system=_ON_TOPIC_NOTE + "Responda direto e curto; NÃO invente nomes/números; se não souber, admita.")
            if llm_resp is not None:
                return llm_resp

        # "melhor jogador do brasil atualmente" ou "jogadores brasileiros" → retorna melhores do país
        rank_keywords_local = ["ranking", "top", "melhores", "rank", "posição", "tabela"]
        is_ranking_query = any(word in msg_lower for word in rank_keywords_local)
        # "melhor brasileiro de todos os tempos" (Guga) não é o melhor ATUAL → deixa goat/LLM
        if (parsed["wants_best"] or parsed["is_current"] or not is_ranking_query) and not _is_goat_query:
            result = tennis_engine.get_best_from_country(parsed["country_filter"])
            return respond(result, topic="player", bot_action="showed_country_best",
                           mentioned_countries=[parsed["country_filter"]])

        # "ranking atp do brasil" → filtra ranking por país
        if is_ranking_query:
            circuit = parsed["circuit"] or 'ATP'
            limit = parsed["limit"] or 10
            filtered = tennis_engine.get_filtered_ranking(circuit, country=parsed["country_filter"], limit=limit)
            if filtered:
                flag = tennis_engine._get_flag(parsed["country_filter"])
                result = f"🏆 <span class='msg-highlight'>Ranking {circuit} — {flag} {parsed['country_filter']}:</span>\n\n"
                for p in filtered:
                    result += f"<span class='msg-highlight'>{p['position']}º</span>. {p['name']} — <span class='msg-highlight'>{p['points']} pts</span>\n"
                return respond(result, topic="ranking", bot_action="showed_country_ranking",
                               mentioned_players=[p['name'] for p in filtered],
                               mentioned_countries=[parsed["country_filter"]])

    # --- Passo 0.9: Detecção de posição específica no ranking ("número 20", "top 20", "posição 20") ---
    import re as _re
    pos_match = _re.search(r'(?:número|numero|n[°º]|top|posição|posicao|atual)\s*(\d{1,3})', msg_lower)
    if not pos_match:
        pos_match = _re.search(r'(\d{1,3})\s*(?:º|°|do mundo|do ranking)', msg_lower)
    if pos_match:
        position = int(pos_match.group(1))
        if 1 <= position <= 100:
            circuit = parsed["circuit"] or ('WTA' if any(w in msg_lower for w in ['wta', 'feminino', 'mulheres']) else 'ATP')
            info, player_name = tennis_engine.get_player_by_position(position, circuit)
            if info:
                add_log(f"Posição {position} do ranking {circuit} detectada: {player_name}", "SUCCESS")
                add_step("Motor de Dados", "success", f"#{position} {circuit}: {player_name}")
                pronoun = "dela" if circuit == "WTA" else "dele"
                suffix = f"\n\nQuer saber mais sobre algum jogador ou ver o ranking {'WTA' if circuit == 'ATP' else 'ATP'}?"
                return respond(info + suffix, topic="player", bot_action="showed_player_info",
                               mentioned_players=[player_name])

    # --- Passo 1: Lógica Técnica (Ranking, Estatísticas e Dados Dinâmicos) ---
    add_log("Consultando base de dados técnica (TennisDB - Março 2026)...")

    # Palavras que indicam desejo de ver dados (números/rankings)
    rank_keywords = ["ranking", "top 10", "melhores do mundo", "rank", "posição", "posições", "tabela", "estatística", "estatiscia", "números", "dados"]
    # Palavras que indicam desejo de ver definições (o que é/história)
    info_keywords = ["o que é", "o que significa", "como funciona", "história", "origem", "quem criou"]

    # Lógica de Separação Inteligente: Se quer dados e NÃO quer apenas definição/história.
    # GUARDA: se a mensagem NOMEIA um jogador específico ("qual o melhor ranking do João
    # Fonseca"), não despejamos o Top 10 — a pergunta é sobre ELE; segue p/ o bloco de
    # jogador (ficha) ou para a IA. (_sup_named já validado com guard de stem >= 4.)
    if any(word in msg_lower for word in rank_keywords) and not any(info in msg_lower for info in info_keywords) and not _sup_named:
        add_log(f"Requisição de dados técnicos detectada através de: {next(w for w in rank_keywords if w in msg_lower)}")
        circuit = parsed["circuit"] or ('WTA' if any(w in msg_lower for w in ['wta', 'feminino', 'mulheres']) else 'ATP')
        add_step("Motor de Dados", "success", f"Ranking {circuit} Top 10 solicitado")
        ranking_text = tennis_engine.get_ranking_summary(circuit=circuit)
        ranking_data = tennis_engine.data.get(f"ranking_{circuit.lower()}", [])
        top_players = [p['name'] for p in ranking_data[:10]]
        return respond(ranking_text, topic="ranking", bot_action="showed_ranking",
                       mentioned_players=top_players)

    # Verifica se o usuário quer saber sobre campeões ou vencedores
    # (Pula se a mensagem contém "recordes" — deixa cair no intent matching)
    winner_keywords = ["campeão", "vencedor", "ganhador", "ganhou", "venceu", "título", "campeões", "vencedores"]
    winner_stems = [stem(w) for w in winner_keywords]
    records_kw = ["recorde", "recordes", "record", "records"]
    # "mais títulos" + contexto de pergunta genérica (sem torneio específico) = recorde
    records_phrases = ["mais títulos", "mais titulos", "mais grand slams", "mais slams",
                       "mais semanas", "mais vitórias", "mais vitorias"]
    has_records = any(kw in msg_lower for kw in records_kw) or any(kw in msg_lower for kw in records_phrases)

    # Se detectou recordes, buscar o melhor intent de recordes na knowledge_base
    if has_records:
        add_log("Contexto de 'Recordes' detectado — buscando intent de recordes")
        kb = load_knowledge_base()
        record_tags = ["recordes_grand_slams", "recordes_titulos", "recordes_gerais",
                        "partida_mais_longa", "saque_mais_rapido", "golden_slam"]
        best_tag, best_score, best_intent = None, 0, None
        for intent in kb["intents"]:
            if intent["tag"] in record_tags:
                for pattern in intent["patterns"]:
                    pattern_tokens = tokenize(pattern.lower())
                    pattern_stems = [stem(w) for w in pattern_tokens]
                    meaningful = [s for s in pattern_stems if s not in PORTUGUESE_STOP_STEMS]
                    msg_meaningful = [s for s in msg_stems if s not in PORTUGUESE_STOP_STEMS]
                    if meaningful and msg_meaningful:
                        matches = sum(1 for s in meaningful if s in msg_meaningful)
                        score = matches / max(len(meaningful), len(msg_meaningful)) * 100
                        if score > best_score:
                            best_score = score
                            best_tag = intent["tag"]
                            best_intent = intent
        if best_intent and best_score >= 40:
            response = __import__('random').choice(best_intent["responses"])
            add_step("Motor de Dados", "success", f"Recorde: {best_tag} ({best_score:.0f}%)")
            return respond(response, topic="trivia", bot_action="showed_trivia")

    # GUARDA: se a mensagem NOMEIA um jogador e NÃO cita um torneio, "título/ganhou" é
    # sobre ESSE jogador (ex.: "qual o título mais importante do Fonseca") — não é pedido
    # de campeões genéricos. Deixa seguir para o roteamento de jogador (ficha/IA).
    _winner_has_tourney = any(t.lower() in msg_lower for t in tennis_engine.get_all_tournament_names())
    if any(token in winner_stems for token in msg_stems) and not has_records and not (_sup_named and not _winner_has_tourney): # Se a frase tiver contexto de vitória
        add_log("Contexto de 'Vencedores' identificado. Verificando especificidade...")
        all_tournaments = tennis_engine.get_all_tournament_names()
        target_tournament = None
        for t in all_tournaments:
            if t.lower() in msg_lower:
                target_tournament = t
                break

        if target_tournament: # Se um torneio específico foi encontrado
            add_log(f"Torneio detectado com NLTK: {target_tournament}", "SUCCESS")
            # Grand Slams têm histórico detalhado de campeões
            grand_slams = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
            if target_tournament in grand_slams:
                result = tennis_engine.get_last_champions(tournament=target_tournament)
                return respond(result, topic="tournament", bot_action="showed_champions",
                               mentioned_tournaments=[target_tournament])
            # ATP 1000/500/Finals: mostra detalhes (inclui campeões recentes)
            detail = tennis_engine.get_grand_slam_details(target_tournament)
            if detail:
                return respond(detail, topic="tournament", bot_action="showed_slam_details",
                               mentioned_tournaments=[target_tournament])

        add_log("Resumo genérico solicitado.") # Caso não cite torneio, mostra o geral
        result = tennis_engine.get_last_champions()
        return respond(result, topic="tournament", bot_action="showed_champions")

    # --- Passo 1.5: Detecção direta de torneio por nome (ANTES de jogadores) ---
    # Usa match direto por texto (mais confiável que stems para nomes de torneios)
    all_tournaments = tennis_engine.get_all_tournament_names()
    grand_slams = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
    target_tournament = None
    for t in all_tournaments:
        if t.lower() in msg_lower:
            target_tournament = t
            break
    if target_tournament:
        add_log(f"Torneio detectado diretamente: {target_tournament}", "SUCCESS")
        # GUARDA: pergunta sobre o torneio que a base NÃO cobre (ingresso, diretor,
        # transmissão…) → IA. A base tem local/superfície/fundação/premiação/história/campeões.
        if any(kw in msg_lower for kw in TOURNAMENT_BEYOND_KW):
            add_log("[ROUTER] Torneio + pergunta além da base → IA", "SYSTEM")
            add_step("Torneio → IA", "active", f"Pergunta sobre {target_tournament} além da base → IA")
            llm_resp = try_llm_fallback(f"Pergunta sobre {target_tournament} além da base → IA",
                extra_system=_ON_TOPIC_NOTE + "Responda direto e curto; NÃO invente; se não souber, admita.")
            if llm_resp is not None:
                return llm_resp
        # Verifica se o usuário quer detalhes/info sobre o torneio (não campeões)
        has_detail_intent = any(kw in msg_lower for kw in SLAM_DETAIL_KEYWORDS)
        if has_detail_intent or target_tournament not in grand_slams:
            detail = tennis_engine.get_grand_slam_details(target_tournament)
            if detail:
                add_step("Motor de Dados", "success", f"Detalhes de {target_tournament}")
                return respond(detail, topic="tournament", bot_action="showed_slam_details",
                               mentioned_tournaments=[target_tournament])
        # Grand Slams sem detail keywords: mostra campeões
        result = tennis_engine.get_last_champions(tournament=target_tournament)
        return respond(result, topic="tournament", bot_action="showed_champions",
                       mentioned_tournaments=[target_tournament])

    # --- Passo 1.6: Listagem genérica de torneios ---
    if not target_tournament:
        tournament_generic_kw = ["torneio", "torneios", "campeonato", "campeonatos"]
        has_tournament_kw = any(kw in msg_lower for kw in tournament_generic_kw)
        has_winner_kw = any(token in winner_stems for token in msg_stems)
        if has_tournament_kw and not has_winner_kw:
            add_step("Motor de Dados", "success", "Listagem de torneios")
            result = tennis_engine.get_tournaments_list()
            return respond(result, topic="tournament", bot_action="showed_tournament_list")

    # --- Passo 1.7: Pergunta que a base NÃO cobre → IA (sem despejar a ficha) ---
    # Princípio reitor: a IA RESPONDE a pergunta (não "premedita" mostrando a tabela).
    # Dois casos vão para a IA (grounding perfil local + PESQUISA Wikipedia):
    #   (i)  Pergunta-LISTA/geral ("cite 10 jogadores canhotos") — a base não enumera.
    #   (ii) Pergunta sobre um JOGADOR além da base (curiosidade, raquete, treinador…),
    #        por nome explícito ou pronome ao foco.
    # Campos da base (país/idade/altura/títulos/estilo/piso/ranking), reação, comparação,
    # elogio e pedido de ficha continuam sendo respondidos pela base (blocos abaixo).
    players_list = tennis_engine.get_all_player_names()

    # Função local: monta grounding + chama a IA e devolve a resposta (ou canned sem ficha).
    def _route_to_ai(step_name, detail, *, player=None, curiosity=False, focus_after=None):
        add_log(f"[ROUTER] {detail}", "SYSTEM")
        add_step(step_name, "active", detail)
        # Pesquisa web só com JOGADOR-alvo (página/consulta específica). Para listas/gerais
        # (sem alvo), a recuperação por jogador vira ruído → não força.
        grounding, search_meta = build_grounding(msg_lower, player_name=player, force_web=bool(player))
        # Já decidimos que isto É tênis (jogador resolvido / lista de jogadores). O modelo
        # às vezes erra e devolve a sentinela; aqui ela é proibida.
        on_topic_note = ("IMPORTANTE: esta pergunta É sobre tênis — responda normalmente e "
                         "NUNCA responda com a sentinela FORA_DO_TEMA. ")
        if curiosity:
            extra = on_topic_note + (f"Conte UMA curiosidade sobre {player} em 1 a 2 frases curtas. "
                     "Se houver 'Contexto recuperado (Wikipedia)', ele é a fonte AUTORITATIVA e "
                     "ATUAL — baseie-se NELE (o perfil local pode estar desatualizado). "
                     "Use EXCLUSIVAMENTE fatos que aparecem LITERALMENTE no contexto acima. "
                     "Escolha o fato MAIS NOTÁVEL "
                     "disponível (um Grand Slam vencido, ser nº1 do mundo, ATP/WTA Finals, um "
                     "recorde, um 'primeiro/mais jovem a...'). Se citar um título, local ou ano, "
                     "ele PRECISA estar escrito no contexto — NÃO invente torneios, cidades ou "
                     "datas, e NÃO troque o ano. Evite frases vagas ('consolidou-se no top 100'). "
                     "NÃO liste a ficha (idade, ranking, lista de títulos). Se o contexto não tiver "
                     "nada específico, admita que não encontrou uma curiosidade confiável.")
        elif player:
            extra = on_topic_note + (f"Responda em 1 a 2 frases curtas a pergunta sobre {player}, usando "
                     "SOMENTE os fatos do contexto (perfil, 'Contexto recuperado (Wikipedia)' com os "
                     "'Dados (Wikipedia infobox)' como mão/treinador/altura, E os 'Resultados da web "
                     "(DuckDuckGo)' — que podem vir em espanhol/inglês; entenda-os e responda em PT-BR). "
                     "NÃO invente dados (raquete, patrocínios, datas…). Responda EXATAMENTE o item "
                     "perguntado (raquete, tênis/calçado, raqueteira, cordas, roupa) — NÃO troque um "
                     "equipamento por outro (se perguntarem o TÊNIS/calçado ou a RAQUETEIRA, NÃO responda "
                     "a raquete). Se o contexto NÃO tiver a "
                     "resposta EXATA mas trouxer um fato RELACIONADO (ex.: perguntaram se é 'casada' e o "
                     "contexto fala em noivado/pedido de casamento/namorado(a)), RELATE esse fato em vez "
                     "de dizer que não há informação; só diga que não encontrou se não houver NADA relacionado. "
                     "Quando não houver o dado exato, complemente com o mais relevante que o contexto tiver "
                     "(ex.: perguntaram a raquete e não há, mas há a mão ou o treinador → mencione). NÃO liste a ficha inteira. "
                     "Se perguntarem QUANTOS/QUAIS Grand Slams e o contexto (títulos) trouxer a divisão "
                     "por torneio (ex.: '10x Australian Open, 7x Wimbledon…'), informe o TOTAL E a "
                     "divisão por torneio.")
        else:
            extra = on_topic_note + ("Responda à pergunta de tênis de forma direta. Se for uma LISTA "
                     "(ex.: jogadores canhotos, brasileiros, especialistas em saibro), cite APENAS "
                     "jogadores dos quais você tem CERTEZA quanto ao critério pedido (ex.: Rafael "
                     "Nadal é canhoto). É MELHOR citar poucos nomes corretos — ou dizer que não tem "
                     "uma lista confiável — do que arriscar nomes errados. NUNCA invente nem chute "
                     "(não complete o número pedido com nomes incertos). Use o contexto se houver.")
        # Listas/gerais respondem melhor com um pouco mais de soltura (recall); jogador fica fiel a 0.2.
        _temp = 0.2 if player else 0.4
        llm_resp = try_llm_fallback(detail, grounding=grounding, search_meta=search_meta,
                                    extra_system=extra, temperature=_temp)
        if llm_resp is not None:
            return llm_resp
        # IA indisponível → canned curto, SEM ficha (degradação graciosa).
        add_step(step_name, "fail", "IA indisponível — resposta curta sem ficha")
        llm_client.record("unresolved")
        session_mgr.update(session_id, "user", text)
        if player:
            canned = (f"Boa pergunta sobre {player}! 🎾 No momento a IA de pesquisa está "
                      "indisponível, então não consigo trazer esse detalhe agora. "
                      "Quer ver o ranking, um torneio de Grand Slam ou saber de outro jogador?")
        else:
            canned = ("Boa pergunta! 🎾 No momento a IA de pesquisa está indisponível para montar "
                      "essa lista. Posso te mostrar o ranking, torneios ou a ficha de um jogador!")
        session_mgr.update(session_id, "bot", canned, bot_action="ai_unavailable",
                           topic=context.get("current_topic"),
                           focus_player=(player or focus_after),
                           pending_follow_up=("player_detail" if player else context.get("pending_follow_up")))
        return jsonify({"answer": canned, "logs": current_logs, "pipeline": pipeline_steps})

    # (i-bis) Lista de CANHOTOS/DESTROS → respondida DIRETO da base (mão dominante curada
    # em player_details). É um caso em que o LLM erra muito (chuta handedness), então a
    # base curada é mais confiável que o Qwen+Wikipedia/DuckDuckGo. Só dispara em pergunta
    # de LISTA que cite mão dominante; o resto das listas segue para a IA (item (i)).
    HAND_LEFT_KW = ("canhoto", "canhotos", "canhota", "canhotas", "esquerdino", "esquerdina",
                    "mão esquerda", "mao esquerda", "com a esquerda", "de esquerda")
    HAND_RIGHT_KW = ("destro", "destros", "destra", "destras", "mão direita", "mao direita",
                     "com a direita", "de direita")
    _hand = None
    if is_general_list_query(msg_lower):
        if any(k in msg_lower for k in HAND_LEFT_KW):
            _hand = "left"
        elif any(k in msg_lower for k in HAND_RIGHT_KW):
            _hand = "right"
    if _hand:
        nomes = tennis_engine.get_players_by_handedness(_hand)
        if nomes:
            _num = re.search(r'\b(\d{1,2})\b', msg_lower)
            _lim = max(1, min(int(_num.group(1)), 30)) if _num else 12
            sel = nomes[:_lim]
            rotulo = "canhotos(as) — mão esquerda" if _hand == "left" else "destros(as) — mão direita"
            body = f"🎾 <span class='msg-highlight'>Jogadores(as) {rotulo}:</span>\n\n"
            body += "".join(f"<span class='msg-highlight'>•</span> {n}\n" for n in sel)
            if len(nomes) > len(sel):
                body += f"\n<span class='msg-highlight'>(+{len(nomes) - len(sel)} outros(as) na base)</span>"
            add_log(f"[BASE] Lista de {'canhotos' if _hand=='left' else 'destros'} respondida pela base curada ({len(sel)} de {len(nomes)})", "SUCCESS")
            add_step("Motor de Dados", "success", f"Mão dominante ({_hand}) — base curada")
            return respond(body.strip(), topic="player", bot_action="showed_handedness_list",
                           mentioned_players=sel)

    # (i) Pergunta-LISTA / geral → IA (a base não enumera jogadores por atributo).
    if is_general_list_query(msg_lower):
        return _route_to_ai("Pergunta geral → IA", "Pergunta-lista/geral de tênis → IA")

    # (ii) Pergunta sobre um JOGADOR além da base (curiosidade OU atributo não-coberto).
    is_curiosity = any(k in msg_lower for k in PLAYER_CURIOSITY_KEYWORDS)
    cur_player = extract_entities(msg_stems, players_list)
    if cur_player:
        _cp_stems = [stem(w) for w in tokenize(cur_player.lower()) if len(stem(w)) > 2]
        if not any(len(s) >= 4 and s in msg_stems for s in _cp_stems):
            cur_player = None
    if not cur_player:
        cur_player = _fuzzy_match_player(msg_lower, players_list, threshold=0.82)
    if not cur_player and re.search(r'\b(dele|dela|deles|delas|ele|ela)\b', msg_lower) and context.get("focus_player"):
        cur_player = context["focus_player"]
    if cur_player and (is_curiosity or player_question_beyond_base(msg_lower)):
        return _route_to_ai("Jogador → IA", f"Pergunta sobre {cur_player} além da base → IA",
                            player=cur_player, curiosity=is_curiosity)

    # --- Lógica de Jogadores DINÂMICA (NLTK) ---
    # GUARDA DE CONTEXTO: se a mensagem usa pronome ("dele/dela/seu/sua") e há um
    # jogador em FOCO, o pronome se refere ao foco — NUNCA trocar por um fuzzy match
    # fraco (ex.: "qual a mão dominante dele" não pode virar outro jogador). Só troca
    # se a mensagem nomear EXPLICITAMENTE outro jogador (match forte por entidade).
    if re.search(r'\b(dele|dela|deles|delas|seu|sua)\b', msg_lower) and context.get("focus_player"):
        _focus_now = context["focus_player"]
        _explicit = __import__('nltk_utils').extract_entities(msg_stems, players_list)
        if not _explicit or _explicit == _focus_now:
            add_log(f"[CONTEXTO] Pronome refere o foco ({_focus_now}); mantendo o jogador.", "SUCCESS")
            add_step("Motor de Dados", "success", f"Pronome → mantém foco: {_focus_now}")
            _info = tennis_engine.get_player_info(_focus_now)
            if _info:
                return respond(_info, topic="player", bot_action="showed_player_info",
                               mentioned_players=[_focus_now])
    target_player = __import__('nltk_utils').extract_entities(msg_stems, players_list)
    if target_player:
        from nltk_utils import stem as _stem, tokenize as _tok
        _p_stems = [_stem(w) for w in _tok(target_player.lower()) if len(_stem(w)) > 2]
        _matched = [s for s in _p_stems if s in msg_stems]
        if not any(len(s) >= 4 for s in _matched):
            target_player = None
    if not target_player:
        # 0.82: tolera typos reais ("Alcaras"→"Alcaraz") sem deixar palavras comuns
        # ("mona", "alto") se passarem por sobrenomes e sequestrarem off-topics.
        target_player = _fuzzy_match_player(msg_lower, players_list, threshold=0.82)
        if target_player:
            add_log(f"Jogador detectado via fuzzy matching: {target_player}", "SUCCESS")

    if target_player:
        add_log(f"Jogador detectado: {target_player}", "SUCCESS")
        
        # --- 1. TESTA SE QUER O PISO (PRIORIDADE) ---
        surface_keywords = ["piso", "superfície", "superficie", "quadra", "grama", "saibro", "terra", "rápida", "duro"]
        if any(w in msg_lower for w in surface_keywords):
            add_log(f"Requisição de PISO para {target_player}", "INFO")
            result = tennis_engine.get_player_surface_info(target_player)
            return respond(result, topic="player", bot_action="showed_player_surface",
                           mentioned_players=[target_player])

        # --- 2. TESTA SE QUER O PAÍS ---
        country_keywords = ["país", "pais", "nacionalidade", "onde nasceu"]
        if any(w in msg_lower for w in country_keywords):
            result = tennis_engine.get_player_country(target_player)
            return respond(result, topic="player", bot_action="showed_player_country",
                           mentioned_players=[target_player])

        # --- 3. SE NÃO FOR NADA ESPECÍFICO, MOSTRA A FICHA COMPLETA ---
        player_info = tennis_engine.get_player_info(target_player)
        return respond(player_info, topic="player", bot_action="showed_player_info",
                       mentioned_players=[target_player])

    if target_player:
        add_log(f"Perfil de jogador detectado: {target_player}", "SUCCESS")
        
        # --- NOVO BLOCO: Verificação de Piso/Superfície ---
        surface_keywords = ["piso", "superfície", "superficie", "quadra", "grama", "saibro", "terra", "rápida"]
        surface_stems = [stem(w) for w in surface_keywords]
        
        if any(token in surface_stems for token in msg_stems):
            add_log(f"Contexto de 'Piso Favorito' para {target_player} detectado.", "INFO")
            # Aqui você deve ter um método no seu engine que retorne essa info específica
            result = tennis_engine.get_player_surface_preference(target_player) 
            return respond(result, topic="player", bot_action="showed_player_surface",
                           mentioned_players=[target_player])
        # ------------------------------------------------
        
        # Se não perguntou sobre piso nem país, aí sim mostra o info geral
        player_info = tennis_engine.get_player_info(target_player)
        # ... resto do código
    
    
    
    
        player_info = tennis_engine.get_player_info(target_player)
        if player_info:
            return respond(player_info, topic="player", bot_action="showed_player_info",
                           mentioned_players=[target_player])

    # --- Roteamento ao LLM: pergunta de CONTAGEM sobre torneio/slam ---
    # "quantos grand slams o X conquistou" é factual e a base não cobre (não há contagem
    # de slams por jogador). Sem este desvio, o intent genérico "grand_slam" casa em 100%
    # (pattern curto "grand slam") e devolve a DEFINIÇÃO em vez do fato. Vai ao LLM; se
    # indisponível, segue o fluxo normal (degradação graciosa para a base/canned).
    if any(q in msg_lower for q in ["quantos", "quantas"]) and any(kw in msg_lower for kw in TOURNAMENT_KEYWORDS):
        add_log("[ROUTER] Pergunta de contagem sobre torneio/slam → LLM", "SYSTEM")
        llm_resp = try_llm_fallback("Pergunta de contagem sobre torneio/slam → LLM")
        if llm_resp is not None:
            return llm_resp

    # --- Passo 2: Lógica Conversacional (Base de Conhecimento JSON) ---
    add_step("Motor de Dados", "skipped", "Nenhum ranking/jogador/torneio detectado")
    add_log("Analisando padrões conversacionais via NLTK...") # Inicia busca por intenções (Intents)
    kb = load_knowledge_base() # Carrega o arquivo knowledge_base.json
    best_match_tag = None # Variável para guardar a melhor etiqueta (tag)
    max_match_score = 0 # Variável para guardar a maior nota de similaridade

    meaningful_msg = [s for s in msg_stems if s not in PORTUGUESE_STOP_STEMS]
    for intent in kb["intents"]: # Percorre cada intenção cadastrada
        for pattern in intent["patterns"]: # Percorre cada frase de exemplo do padrão
            pattern_tokens = tokenize(pattern.lower()) # Tokeniza o padrão
            pattern_stems = [stem(w) for w in pattern_tokens] # Gera radicais do padrão
            meaningful_pattern = [s for s in pattern_stems if s not in PORTUGUESE_STOP_STEMS]
            if not meaningful_pattern: # Pula patterns sem stems significativos
                continue
            matches = sum(1 for s in meaningful_msg if s in meaningful_pattern) # Conta coincidências significativas
            # Score estilo Jaccard (relativo ao lado MAIOR) — evita que um pattern curto
            # infle o % com uma única palavra. Sem isso, qualquer frase casava intents
            # curtos em 50%, "forçando" a base em vez de mandar a pergunta ao LLM.
            denom = max(len(meaningful_pattern), len(meaningful_msg))
            score = (matches / denom) * 100 if denom else 0
            # Guarda anti-falso-positivo: 1 só stem em comum entre pergunta e pattern,
            # ambos com 2+ stems, é fraco demais (ex.: "love no tênis" casando wta_explicacao).
            if matches < 2 and len(meaningful_pattern) >= 2 and len(meaningful_msg) >= 2:
                score = 0

            if score > max_match_score: # Se este match for o melhor até agora...
                max_match_score = score # Atualiza a nota máxima
                best_match_tag = intent["tag"] # Atualiza a tag vencedora

        # Log detalhado da tentativa de match
        if score > 0:
            add_log(f"Testando tag '{intent['tag']}': {score:.1f}% de compatibilidade.", "DEBUG")

    # Tags conversacionais que não devem sobrescrever um contexto ativo
    CONTEXT_OVERRIDE_TAGS = {"confirmacao_positiva", "confirmacao_negativa", "feedback_positivo"}

    # Se a similaridade for convincente (>= 50%)
    if max_match_score >= 50:
        # Limiar adaptativo: com contexto ativo, exige 65% para sobrescrever
        effective_threshold = 65 if pending_ctx else 50
        # Se contexto ativo e intent é genérico → não usar, preservar contexto
        if pending_ctx and best_match_tag in CONTEXT_OVERRIDE_TAGS:
            add_log(f"[GUARD] Intent '{best_match_tag}' bloqueado — contexto ativo (pending={pending_ctx})", "DEBUG")
            add_step("Base de Conhecimento", "skipped", f"Intent '{best_match_tag}' bloqueado por contexto ativo")
        elif pending_ctx and max_match_score < effective_threshold:
            add_log(f"[GUARD] Intent '{best_match_tag}' ({max_match_score:.0f}%) abaixo do limiar contextual (65%)", "DEBUG")
            add_step("Base de Conhecimento", "skipped", f"Intent '{best_match_tag}' ({max_match_score:.0f}%) abaixo do limiar contextual")
        else:
            add_log(f"Match encontrado! Tag: {best_match_tag} ({max_match_score:.1f}%)", "SUCCESS")
            add_step("Base de Conhecimento", "success", f"Intent: {best_match_tag} ({max_match_score:.0f}%)")
            matched_intent = next(i for i in kb["intents"] if i["tag"] == best_match_tag)
            response = random.choice(matched_intent["responses"])
            return respond(response, topic="trivia", bot_action="showed_trivia")

    # --- Passo 3: Fallback (Quando o robô não entende a pergunta) ---
    add_step("Base de Conhecimento", "skipped", f"Melhor match: {max_match_score:.0f}% (mínimo 50%)")
    add_step("Fallback", "fail", "Nenhum padrão identificado com confiança")
    add_log("Nenhum padrão identificado com confiança suficiente.", "WARNING")
    log_unrecognized_query(text)
    add_log("Pergunta enviada para o banco de aprendizado.", "SYSTEM")

    # Antes de desistir, aciona o LLM (LM Studio) como fallback universal.
    llm_resp = try_llm_fallback("Base não resolveu — acionando LLM")
    if llm_resp is not None:
        return llm_resp

    # LLM indisponível/desligado → resposta padrão (preserva contexto quando possível)
    llm_client.record("unresolved") # Métrica: não resolvida (nem base nem LLM)
    if context.get("focus_player"):
        fallback_response = f"Não entendi bem essa pergunta... 🤔 Quer que eu continue falando sobre {context['focus_player']} ou prefere mudar de assunto?\n\nPosso mostrar ranking, torneios de Grand Slam ou curiosidades!"
    elif context.get("current_topic"):
        fallback_response = "Não entendi bem... 🤔 Pode reformular? Estou aqui para falar sobre ranking, jogadores, torneios e curiosidades do tênis! 🎾"
    else:
        fallback_response = "Hmm, parece que esse assunto fugiu da minha quadra de tênis... 🤔\n\nEu fui treinado apenas para falar sobre ATP, WTA, Raquetes e as lendas do esporte. Vamos tentar falar sobre o Ranking?"
    session_mgr.update(session_id, "user", text)
    session_mgr.update(session_id, "bot", fallback_response, bot_action="fallback",
                       pending_follow_up=context.get("pending_follow_up"),
                       topic=context.get("current_topic"))
    return jsonify({"answer": fallback_response, "logs": current_logs, "pipeline": pipeline_steps})

# Rota de métricas: resumo de quantas perguntas foram resolvidas pela base vs LLM
# e o tempo médio de resposta do LLM. Alimenta a seção "Resultados e Discussão"
# do relatório e pode ser exibida no vídeo de demonstração.
@app.route('/metrics', methods=['GET'])
def metrics():
    return jsonify(llm_client.metrics_snapshot())

# Ponto de entrada que inicia o servidor se o arquivo for executado diretamente
if __name__ == "__main__":
    app.run(debug=True) # Inicia o servidor Flask em modo de depuração/debug