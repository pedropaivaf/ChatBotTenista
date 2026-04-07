# Importação das bibliotecas necessárias para o funcionamento do servidor e do chatbot
from flask import Flask, render_template, request, jsonify # Framework web para criar a API e servir o site
from flask_cors import CORS # Permite que o frontend acesse o backend de diferentes origens
from engine import TennisEngine # Importa o nosso motor de dados técnicos de tênis
from nltk_utils import tokenize, stem, bag_of_words # Utilitários de Processamento de Linguagem Natural
from session_manager import SessionManager # Gerenciador de sessões com contexto
from query_parser import parse_query # Parser inteligente de queries (país/temporal/superlativo)
from decision_tree import DecisionTree, _fuzzy_match_player # Árvore de decisão contextual com follow-ups
from api_client import TennisAPIClient # Cliente de atualização de rankings (ATP/WTA)
import json # Para manipular arquivos de dados estruturados
import os # Para verificar a existência de arquivos no sistema
import random # Para escolher respostas variadas quando houver várias opções
from datetime import datetime # Para registrar a data/hora nos logs de aprendizado

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
]

# Keywords que indicam que o usuário quer detalhes/informações sobre um Grand Slam (não campeões)
SLAM_DETAIL_KEYWORDS = [
    "sobre", "detalhes", "detalhe", "fala sobre", "me fala", "conta sobre",
    "o que é", "o que e", "como é", "como e", "onde fica", "onde é",
    "história", "historia", "quando foi criado", "informações", "informacoes",
    "ficha do torneio", "superfície", "superficie", "piso do",
    "premiação", "premiacao", "prize money", "quanto vale", "pontos do",
]

# Stop stems portugueses para filtrar do intent matching (evita falsos positivos)
PORTUGUESE_STOP_STEMS = {
    "de", "do", "da", "dos", "das", "o", "a", "os", "as",
    "um", "uma", "uns", "e", "ou", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "se", "ao", "que", "é",
    "quai", "qual", "como", "?", "!", ".",
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
        return jsonify({"answer": enriched["response"], "logs": current_logs, "pipeline": pipeline_steps})

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
            if consonant_run and len(w) > 6:
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

    if is_off_topic or is_gibber:
        reason = "Texto sem sentido detectado" if is_gibber else "Palavra bloqueada detectada na mensagem"
        add_log("Assunto fora de contexto (Tênis) detectado!", "WARNING")
        add_step("Filtro Off-Topic", "fail", reason)
        log_unrecognized_query(text)
        session_mgr.update(session_id, "user", text)
        resp_text = ("Hmm, não entendi essa mensagem. 🤔\nTenta me perguntar sobre ranking ATP, jogadores ou torneios de Grand Slam!"
                     if is_gibber else
                     "Desculpe, mas eu respiro apenas Tênis! 🎾\nPosso te contar sobre o ranking da ATP ou os campeões de Grand Slam, mas sobre esse assunto eu prefiro não comentar.")
        return jsonify({
            "answer": resp_text,
            "logs": current_logs, "pipeline": pipeline_steps
        })

    # --- Passo 0.5: Resolução Contextual (Árvore de Decisão) ---
    add_step("Filtro Off-Topic", "success", "Mensagem permitida (contexto tênis)")
    pending_ctx = context.get("pending_follow_up")
    focus_ctx = context.get("focus_player")
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
    if not parsed["country_filter"] and parsed["wants_best"] and any(w in msg_lower for w in player_context_words) and not _has_specific_position:
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

        # "melhor jogador do brasil atualmente" ou "jogadores brasileiros" → retorna melhores do país
        rank_keywords_local = ["ranking", "top", "melhores", "rank", "posição", "tabela"]
        is_ranking_query = any(word in msg_lower for word in rank_keywords_local)
        if parsed["wants_best"] or parsed["is_current"] or not is_ranking_query:
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

    # Lógica de Separação Inteligente: Se quer dados e NÃO quer apenas definição/história
    if any(word in msg_lower for word in rank_keywords) and not any(info in msg_lower for info in info_keywords):
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

    if any(token in winner_stems for token in msg_stems) and not has_records: # Se a frase tiver contexto de vitória
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

    # --- Lógica de Jogadores DINÂMICA (NLTK) ---
    players_list = tennis_engine.get_all_player_names()
    target_player = __import__('nltk_utils').extract_entities(msg_stems, players_list)
    if target_player:
        from nltk_utils import stem as _stem, tokenize as _tok
        _p_stems = [_stem(w) for w in _tok(target_player.lower()) if len(_stem(w)) > 2]
        _matched = [s for s in _p_stems if s in msg_stems]
        if not any(len(s) >= 4 for s in _matched):
            target_player = None
    if not target_player:
        target_player = _fuzzy_match_player(msg_lower, players_list, threshold=0.75)
        if target_player:
            add_log(f"Jogador detectado via fuzzy matching: {target_player}", "SUCCESS")

    if target_player:
        add_log(f"Perfil de jogador detectado com NLTK: {target_player}", "SUCCESS")
        add_step("Motor de Dados", "success", f"Jogador identificado: {target_player}")

        country_keywords = ["país", "pais", "nacionalidade", "onde nasceu", "onde é", "da onde", "de onde"]
        country_stems = [stem(w) for w in country_keywords]

        if any(token in country_stems for token in msg_stems):
            add_log(f"Contexto de 'Nacionalidade' para {target_player} detectado.", "INFO")
            result = tennis_engine.get_player_country(target_player)
            return respond(result, topic="player", bot_action="showed_player_country",
                           mentioned_players=[target_player])

        player_info = tennis_engine.get_player_info(target_player)
        if player_info:
            return respond(player_info, topic="player", bot_action="showed_player_info",
                           mentioned_players=[target_player])

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
            score = (matches / len(meaningful_pattern)) * 100 # Calcula % de match

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

    # Resposta padrão de erro/confusão — preserva contexto quando possível
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

# Ponto de entrada que inicia o servidor se o arquivo for executado diretamente
if __name__ == "__main__":
    app.run(debug=True) # Inicia o servidor Flask em modo de depuração/debug
