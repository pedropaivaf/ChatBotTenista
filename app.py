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
app = Flask(__name__)
# Ativação do CORS para permitir requisições de outros domínios ou portas locais
CORS(app)

# Instanciação do motor técnico que buscará rankings e campeões
tennis_engine = TennisEngine()

# Caminho para o "diário" de perguntas não reconhecidas (base para o Machine Learning futuro)
UNRECOGNIZED_FILE = 'unrecognized_queries.json'

# Lista de termos que remetem a outros esportes e devem ser barrados (Filtro de Contexto)
OFF_TOPIC_KEYWORDS = ["copa", "futebol", "gol", "basquete", "nba", "buraco negro", "fisica", "receita", "politica", "eleição"]

# Função que carrega a base de conhecimento (Intents) do arquivo JSON
def load_knowledge_base():
    # Abre o arquivo com encoding utf-8 para suportar acentos e caracteres especiais
    with open('knowledge_base.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Função para registrar perguntas que o robô ainda não sabe responder
def log_unrecognized_query(query):
    # Inicializa uma lista vazia para os dados
    data = []
    # Se o arquivo já existir, carrega as perguntas anteriores para não perdê-las
    if os.path.exists(UNRECOGNIZED_FILE):
        try:
            with open(UNRECOGNIZED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
    
    # Cria um novo registro com o texto da pergunta e o horário atual
    # Março 2026 detectado: o sistema já usa a data do servidor para este log
    entry = {
        "query": query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # Adiciona a nova pergunta à lista
    data.append(entry)
    
    # Salva a lista atualizada de volta no arquivo JSON
    with open(UNRECOGNIZED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Rota principal que carrega a interface visual do nosso ChatBot
@app.route('/')
def home():
    # Renderiza o arquivo HTML que está na pasta /templates
    return render_template('index.html')

# Rota principal de processamento (API) que recebe a mensagem e retorna a resposta
@app.route('/predict', methods=['POST'])
def predict():
    # Captura a mensagem enviada pelo usuário via JSON
    text = request.get_json().get("message")
    # Inicializa uma lista de logs para enviar informações técnicas ao terminal do frontend
    current_logs = []

    # Função auxiliar para adicionar logs ao terminal do frontend de forma organizada
    def add_log(msg, level="INFO"):
        # Adiciona o nível do log (ex: [SUCCESS], [WARNING]) para o CSS colorir corretamente
        current_logs.append(f"[{level}] {msg}")

    # Faz o pré-processamento básico da mensagem (converte para minúsculas e remove espaços)
    msg_lower = text.lower().strip()
    # Transforma a frase em uma lista de palavras (tokens) usando NLTK
    msg_tokens = tokenize(msg_lower)
    # Gera a raiz (stem) de cada palavra para facilitar as comparações
    msg_stems = [stem(w) for w in msg_tokens]

    # --- Passo 0: Filtro de Contexto (Anti-Futebol e Anti-Offtopic) ---
    # Se detectar palavras proibidas como "copa" ou "buraco negro", corta o processamento
    if any(off in msg_lower for off in OFF_TOPIC_KEYWORDS):
        add_log("Assunto fora de contexto (Tênis) detectado!", "WARNING")
        # Registra no log de aprendizado para análise
        log_unrecognized_query(text)
        return jsonify({
            "answer": "Desculpe, mas eu respiro apenas Tênis! 🎾\nPosso te contar sobre o ranking da ATP ou os campeões de Grand Slam, mas sobre esse assunto eu prefiro não comentar.",
            "logs": current_logs
        })

    # --- Passo 1: Lógica Técnica (O "Cérebro" de Dados do Motor) ---
    add_log("Consultando base de dados técnica (TennisDB - Março 2026)...")
    
    # Verifica se o usuário quer ver o ranking ATP
    if any(word in msg_lower for word in ["ranking", "top 10", "melhores do mundo"]):
        add_log("Processando requisição de Ranking ATP Atualizado.")
        # Retorna o resultado formatado direto do motor técnico (Já com dados de 2026)
        return jsonify({"answer": tennis_engine.get_ranking_summary(), "logs": current_logs})

    # Verifica se o usuário quer saber sobre campeões ou vencedores
    winner_keywords = ["campeão", "vencedor", "ganhador", "ganhou", "venceu", "título", "campeões", "vencedores"]
    # Compara os radicais (stems) da mensagem com as palavras-chave de vitória
    winner_stems = [stem(w) for w in winner_keywords]
    
    # IMPORTANTE: Só entra aqui se for sobre vitória E tiver algo de tênis (torneio ou jogador)
    # Isso evita que "quem ganhou o reality show?" caia aqui
    if any(token in winner_stems for token in msg_stems):
        add_log("Contexto de 'Vencedores' identificado. Verificando especificidade...")
        
        # Lista de torneios conhecidos para tentar identificar na pergunta
        tournaments = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]
        # Usa o utilitário NLTK para extrair o nome do torneio da frase
        target_tournament = __import__('nltk_utils').extract_entities(msg_stems, tournaments)
        
        # Se achou o torneio ou o usuário já estabeleceu contexto de tênis antes
        if target_tournament:
            add_log(f"Torneio detectado com NLTK: {target_tournament}", "SUCCESS")
            return jsonify({"answer": tennis_engine.get_last_champions(tournament=target_tournament), "logs": current_logs})
        
        # Se for uma pergunta genérica (ex: "quem ganhou?"), só responde se não houver termos suspeitos
        add_log("Resumo genérico solicitado.")
        return jsonify({"answer": tennis_engine.get_last_champions(), "logs": current_logs})

    # Verifica se a pergunta é sobre jogadores específicos conhecidos
    players_list = ["Jannik Sinner", "Carlos Alcaraz", "Novak Djokovic", "Roger Federer", "Rafael Nadal"]
    # Tenta extrair o nome de um desses jogadores da frase usando NLTK
    target_player = __import__('nltk_utils').extract_entities(msg_stems, players_list)
    
    if target_player:
        add_log(f"Perfil de jogador detectado com NLTK: {target_player}", "SUCCESS")
        
        # --- NOVO: Identificação de Nacionalidade ---
        # Se a pergunta contiver palavras como pais ou nacionalidade, focamos só nisso
        country_keywords = ["país", "nacionalidade", "onde nasceu", "onde é", "da onde"]
        country_stems = [stem(w) for w in country_keywords]
        
        if any(token in country_stems for token in msg_stems):
            add_log(f"Contexto de 'Nacionalidade' para {target_player} detectado.", "INFO")
            # Busca especificamente o país do jogador no motor de dados
            return jsonify({"answer": tennis_engine.get_player_country(target_player), "logs": current_logs})
        
        # Caso contrário, mostra a ficha técnica completa (comportamento padrão)
        player_info = tennis_engine.get_player_info(target_player)
        if player_info: 
            return jsonify({"answer": player_info, "logs": current_logs})

    # --- Passo 2: Lógica Conversacional (Base de Conhecimento JSON) ---
    add_log("Analisando padrões conversacionais via NLTK...")
    # Carrega os intents (intenções) da base de conhecimento
    kb = load_knowledge_base()
    best_match_tag = None
    max_match_score = 0

    # Percorre cada intenção cadastrada no arquivo JSON
    for intent in kb["intents"]:
        # Para cada intenção, verifica todos os padrões de frase possíveis
        for pattern in intent["patterns"]:
            # Tokeniza e gera os radicais das frases de exemplo do JSON
            pattern_tokens = tokenize(pattern.lower())
            pattern_stems = [stem(w) for w in pattern_tokens]
            
            # Calcula quantas palavras o usuário enviou que batem com as do padrão (match simples)
            matches = sum(1 for s in msg_stems if s in pattern_stems)
            # Calcula a porcentagem de similaridade
            score = (matches / len(pattern_stems)) * 100 if pattern_stems else 0

            # Atualiza o melhor match encontrado até agora
            if score > max_match_score:
                max_match_score = score
                best_match_tag = intent["tag"]

    # Se a similaridade for maior que uma margem de segurança (ajustada para 50% para evitar 'buraco negro' error)
    if max_match_score >= 50:
        add_log(f"Match encontrado! Tag: {best_match_tag} ({max_match_score:.1f}%)", "SUCCESS")
        # Busca o objeto completo da intenção vencedora
        matched_intent = next(i for i in kb["intents"] if i["tag"] == best_match_tag)
        # Escolhe uma resposta aleatória da lista de respostas dessa intenção
        response = random.choice(matched_intent["responses"])
        # Se houver um follow-up (pergunta complementar), adiciona ao final
        if matched_intent.get("follow_up"):
            response += f"\n\n{matched_intent['follow_up']}"
        return jsonify({"answer": response, "logs": current_logs})

    # --- Passo 3: Fallback (Quando o robô não entende nada) ---
    add_log("Nenhum padrão identificado com confiança suficiente.", "WARNING")
    # Registra a pergunta no banco de dados de aprendizado para Machine Learning futuro
    log_unrecognized_query(text)
    add_log("Pergunta enviada para o banco de aprendizado.", "SYSTEM")
    
    # Resposta padrão de quem está confuso (educada e focada no tema)
    fallback_response = "Hmm, parece que esse assunto fugiu da minha quadra de tênis... 🤔\n\nEu fui treinado apenas para falar sobre ATP, WTA, Raquetes e as lendas do esporte. Vamos tentar falar sobre o Ranking?"
    return jsonify({"answer": fallback_response, "logs": current_logs})

# Ponto de entrada que inicia o servidor se o arquivo for executado diretamente
if __name__ == "__main__":
    # Rodamos o app no modo de depuração para ver erros no terminal e atualizar o código sem reiniciar manualmente
    app.run(debug=True)
