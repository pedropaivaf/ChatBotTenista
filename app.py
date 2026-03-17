# Importação das bibliotecas necessárias para o funcionamento do servidor e do chatbot
from flask import Flask, render_template, request, jsonify # Framework web para criar a API e servir o site
from flask_cors import CORS # Permite que o frontend acesse o backend de diferentes origens
from engine import TennisEngine # Importa o nosso motor de dados técnicos de tênis
from nltk_utils import tokenize, stem, bag_of_words # Utilitários de Processamento de Linguagem Natural
import json # Para manipular arquivos de dados estruturados
import os # Para verificar a existência de arquivos no sistema
import random # Para escolher respostas variadas quando houver várias opções
from datetime import datetime # Para registrar a data/hora nos logs de aprendizado

# Inicialização do aplicativo Flask (nosso servidor)
app = Flask(__name__) # Cria a instância global do servidor web
# Ativação do CORS para permitir requisições de outros domínios ou portas locais
CORS(app) # Habilita o compartilhamento de recursos entre origens diferentes

# Instanciação do motor técnico que buscará rankings, campeões e perfis
tennis_engine = TennisEngine() # Carrega o "cérebro" de dados em memória

# Caminho para o "diário" de perguntas não reconhecidas (base para o Machine Learning futuro)
UNRECOGNIZED_FILE = 'unrecognized_queries.json' # Define o nome do arquivo de logs de erro

# Lista de termos que remetem a outros esportes e devem ser barrados (Filtro de Contexto)
OFF_TOPIC_KEYWORDS = ["copa", "futebol", "gol", "basquete", "nba", "buraco negro", "fisica", "receita", "politica", "eleição"] # Filtro de segurança anti-offtopic

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
    current_logs = [] # Inicializa uma lista de logs técnicos para enviar ao frontend

    # Função auxiliar interna para preencher a lista de logs do processo
    def add_log(msg, level="INFO"): # Define a função de log interno
        current_logs.append(f"[{level}] {msg}") # Formata e adiciona a mensagem ao log

    # Processamento inicial da mensagem (Pré-processamento)
    msg_lower = text.lower().strip() # Converte tudo para minúsculo e limpa espaços extras
    msg_tokens = tokenize(msg_lower) # Fatias a frase em palavras (tokens) via NLTK
    msg_stems = [stem(w) for w in msg_tokens] # Reduz cada palavra ao seu radical (raiz)

    # --- Passo 0: Filtro de Contexto (Anti-Futebol e Anti-Offtopic) ---
    if any(off in msg_lower for off in OFF_TOPIC_KEYWORDS): # Se detectar palavras禁止
        add_log("Assunto fora de contexto (Tênis) detectado!", "WARNING") # Avisa no log
        log_unrecognized_query(text) # Registra a tentativa de fuga de contexto
        return jsonify({ # Retorna uma resposta amigável de corte
            "answer": "Desculpe, mas eu respiro apenas Tênis! 🎾\nPosso te contar sobre o ranking da ATP ou os campeões de Grand Slam, mas sobre esse assunto eu prefiro não comentar.",
            "logs": current_logs # Envia os logs gerados até aqui
        }) # Finaliza a requisição

    # --- Passo 1: Lógica Técnica (Ranking, Estatísticas e Dados Dinâmicos) ---
    add_log("Consultando base de dados técnica (TennisDB - Março 2026)...") # Registra início da consulta
    
    # Palavras que indicam desejo de ver dados (números/rankings)
    rank_keywords = ["ranking", "top 10", "melhores do mundo", "rank", "posição", "posições", "tabela", "estatística", "estatiscia", "números", "dados"]
    # Palavras que indicam desejo de ver definições (o que é/história)
    info_keywords = ["o que é", "o que significa", "como funciona", "história", "origem", "quem criou"]
    
    # Lógica de Separação Inteligente: Se quer dados e NÃO quer apenas definição/história
    if any(word in msg_lower for word in rank_keywords) and not any(info in msg_lower for info in info_keywords):
        add_log(f"Requisição de dados técnicos detectada através de: {next(w for w in rank_keywords if w in msg_lower)}")
        
        # Identifica o circuito solicitado (Masculino/ATP ou Feminino/WTA)
        circuit = 'WTA' if any(w in msg_lower for w in ['wta', 'feminino', 'mulheres']) else 'ATP'
        
        return jsonify({ # Retorna a resposta do motor técnico
            "answer": tennis_engine.get_ranking_summary(circuit=circuit), # Pega o ranking formatado
            "logs": current_logs # Envia os logs técnicos
        }) # Finaliza aqui se for ranking

    # Verifica se o usuário quer saber sobre campeões ou vencedores
    winner_keywords = ["campeão", "vencedor", "ganhador", "ganhou", "venceu", "título", "campeões", "vencedores"]
    winner_stems = [stem(w) for w in winner_keywords] # Gera radicais das palavras de vitória
    
    if any(token in winner_stems for token in msg_stems): # Se a frase tiver contexto de vitória
        add_log("Contexto de 'Vencedores' identificado. Verificando especificidade...")
        tournaments = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"] # Lista de Slams
        target_tournament = __import__('nltk_utils').extract_entities(msg_stems, tournaments) # Busca o torneio na frase
        
        if target_tournament: # Se um torneio específico foi encontrado
            add_log(f"Torneio detectado com NLTK: {target_tournament}", "SUCCESS")
            return jsonify({ # Retorna campeões do torneio X
                "answer": tennis_engine.get_last_champions(tournament=target_tournament),
                "logs": current_logs
            })
        
        add_log("Resumo genérico solicitado.") # Caso não cite torneio, mostra o geral
        return jsonify({ # Retorna campeões do ano atual
            "answer": tennis_engine.get_last_champions(),
            "logs": current_logs
        })

    # --- Lógica de Jogadores DINÂMICA (NLTK) ---
    # Busca a lista de nomes cadastrados no JSON automaticamente
    players_list = tennis_engine.get_all_player_names() # Lê o banco de dados
    # Tenta extrair o nome de um jogador da frase do usuário
    target_player = __import__('nltk_utils').extract_entities(msg_stems, players_list)
    
    if target_player: # Se o robô reconheceu o jogador citado
        add_log(f"Perfil de jogador detectado com NLTK: {target_player}", "SUCCESS")
        
        # Verifica se o usuário perguntou sobre a nacionalidade/origem
        country_keywords = ["país", "nacionalidade", "onde nasceu", "onde é", "da onde"]
        country_stems = [stem(w) for w in country_keywords] # Gera radicais
        
        if any(token in country_stems for token in msg_stems): # Se for sobre país
            add_log(f"Contexto de 'Nacionalidade' para {target_player} detectado.", "INFO")
            return jsonify({ # Retorna apenas a nacionalidade
                "answer": tennis_engine.get_player_country(target_player),
                "logs": current_logs
            })
        
        # Caso padrão: Mostra a ficha técnica completa do jogador
        player_info = tennis_engine.get_player_info(target_player)
        if player_info: # Se houver informações no JSON
            return jsonify({ # Retorna a ficha completa
                "answer": player_info,
                "logs": current_logs
            })

    # --- Passo 2: Lógica Conversacional (Base de Conhecimento JSON) ---
    add_log("Analisando padrões conversacionais via NLTK...") # Inicia busca por intenções (Intents)
    kb = load_knowledge_base() # Carrega o arquivo knowledge_base.json
    best_match_tag = None # Variável para guardar a melhor etiqueta (tag)
    max_match_score = 0 # Variável para guardar a maior nota de similaridade

    for intent in kb["intents"]: # Percorre cada intenção cadastrada
        for pattern in intent["patterns"]: # Percorre cada frase de exemplo do padrão
            pattern_tokens = tokenize(pattern.lower()) # Tokeniza o padrão
            pattern_stems = [stem(w) for w in pattern_tokens] # Gera radicais do padrão
            matches = sum(1 for s in msg_stems if s in pattern_stems) # Conta coincidências
            score = (matches / len(pattern_stems)) * 100 if pattern_stems else 0 # Calcula % de match

            if score > max_match_score: # Se este match for o melhor até agora...
                max_match_score = score # Atualiza a nota máxima
                best_match_tag = intent["tag"] # Atualiza a tag vencedora

    # Se a similaridade for convincente (>= 50%)
    if max_match_score >= 50:
        add_log(f"Match encontrado! Tag: {best_match_tag} ({max_match_score:.1f}%)", "SUCCESS")
        matched_intent = next(i for i in kb["intents"] if i["tag"] == best_match_tag) # Pega o objeto da tag
        response = random.choice(matched_intent["responses"]) # Escolhe uma resposta aleatória da lista
        if matched_intent.get("follow_up"): # Se houver uma pergunta de acompanhamento
            response += f"\n\n{matched_intent['follow_up']}" # Adiciona ao final da resposta
        return jsonify({"answer": response, "logs": current_logs}) # Retorna a resposta conversacional

    # --- Passo 3: Fallback (Quando o robô não entende a pergunta) ---
    add_log("Nenhum padrão identificado com confiança suficiente.", "WARNING")
    log_unrecognized_query(text) # Registra no banco de aprendizado para revisão humana
    add_log("Pergunta enviada para o banco de aprendizado.", "SYSTEM")
    
    # Resposta padrão de erro/confusão (Mantém o foco no Tênis)
    fallback_response = "Hmm, parece que esse assunto fugiu da minha quadra de tênis... 🤔\n\nEu fui treinado apenas para falar sobre ATP, WTA, Raquetes e as lendas do esporte. Vamos tentar falar sobre o Ranking?"
    return jsonify({"answer": fallback_response, "logs": current_logs}) # Retorna a resposta de fallback

# Ponto de entrada que inicia o servidor se o arquivo for executado diretamente
if __name__ == "__main__":
    app.run(debug=True) # Inicia o servidor Flask em modo de depuração/debug
