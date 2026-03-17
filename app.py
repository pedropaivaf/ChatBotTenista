from flask import Flask, render_template, request, jsonify # Importa as ferramentas necessárias do Flask para criar o servidor web
import json # Importa a biblioteca para manipulação de arquivos JSON (base de dados)
import random # Importa para sortear respostas aleatórias da base de conhecimento
from nltk_utils import tokenize, stem # Importa as funções de Processamento de Linguagem Natural que criamos
from engine import TennisEngine # Importa o nosso motor de dados técnicos oficiais

app = Flask(__name__) # Inicializa a aplicação Flask
tennis_engine = TennisEngine() # Instancia o motor de dados para consultas de rankings e torneios

# Carrega a base de conhecimento local (o arquivo de intenções NLP)
with open('knowledge_base.json', 'r', encoding='utf-8') as f: # Abre o arquivo JSON com codificação UTF-8
    intents = json.load(f) # Converte o conteúdo do arquivo JSON em um dicionário Python

def get_response(msg): # Função principal que decide como o robô deve responder
    sentence = tokenize(msg) # Transforma a frase do usuário em uma lista de palavras (tokens)
    msg_lower = msg.lower() # Converte a mensagem toda para minúsculo para facilitar a comparação
    
    # 1. Tenta buscar informações técnicas no Motor de Dados Oficial
    if any(word in msg_lower for word in ["ranking", "top 10", "melhores do mundo"]): # Se o usuário perguntar por ranking
        return tennis_engine.get_ranking_summary() # Retorna o resumo do ranking ATP que está no tennis_data.json

    if any(word in msg_lower for word in ["campeões", "quem ganhou", "grand slam 2024"]): # Se perguntar por campeões
        return tennis_engine.get_last_champions() # Retorna a lista de campeões de 2024

    # Verifica se o usuário mencionou algum jogador específico que temos detalhes técnicos
    for player in ["sinner", "alcaraz"]: # Loop pelos jogadores principais da base técnica
        if player in msg_lower: # Se o nome do jogador estiver na mensagem
            player_info = tennis_engine.get_player_info(player) # Busca os detalhes (idade, estilo, etc.)
            if player_info: return player_info # Se encontrar, retorna a informação

    # 2. Reconhecimento direto e rápido de Saudações (Oi, Olá, etc.)
    greetings = ["oi", "ola", "ei", "tudo bem", "bom dia", "boa tarde", "boa noite", "opa"] # Lista de saudações comuns
    if any(greet in msg_lower for greet in greetings): # Se a mensagem contiver qualquer uma dessas saudações
        for intent in intents['intents']: # Procura nas intenções do JSON
            if intent['tag'] == 'saudacao': # Quando encontrar a tag 'saudacao'
                resp = random.choice(intent['responses']) # Sorteia uma das respostas de boas-vindas
                return f"{resp} {intent['follow_up']}" # Retorna a saudação concatenada com a pergunta de acompanhamento

    # 3. Processamento NLP Inteligente (Fallback) usando NLTK
    for intent in intents['intents']: # Percorre cada intenção na nossa base
        for pattern in intent['patterns']: # Percorre cada padrão de frase daquela intenção
            pattern_tokens = [stem(w) for w in tokenize(pattern)] # Tokeniza e reduz as palavras do padrão ao radical
            msg_tokens = [stem(w) for w in sentence] # Tokeniza e reduz as palavras da mensagem ao radical
            
            # Se todas as palavras do padrão estiverem presentes na mensagem do usuário
            if all(token in msg_tokens for token in pattern_tokens): # Verificação exata de tokens
                response = random.choice(intent['responses']) # Escolhe uma resposta aleatória
                follow_up = intent.get('follow_up', "") # Busca a pergunta de acompanhamento se houver
                return f"{response} {follow_up}".strip() # Retorna a resposta completa limpa de espaços extras
            
            # Checagem de similaridade (fuzzy matching): se 70% das palavras baterem
            match_count = sum(1 for token in pattern_tokens if token in msg_tokens) # Conta quantos tokens combinam
            if len(pattern_tokens) > 0 and match_count / len(pattern_tokens) > 0.7: # Se a taxa for maior que 70%
                response = random.choice(intent['responses']) # Escolhe a resposta
                follow_up = intent.get('follow_up', "") # Busca o acompanhamento
                return f"{response} {follow_up}".strip() # Retorna a resposta final

    # Caso o bot não entenda nada do que foi dito
    return "Desculpe, ainda estou aprendendo sobre isso. Que tal me perguntar sobre o ranking atual, campeões de 2024 ou sobre lendas como Federer e Nadal?"

@app.route('/') # Define a rota para a página inicial do site
def index(): # Função que será chamada ao acessar o site
    return render_template('index.html') # Renderiza o arquivo HTML na pasta templates

@app.route('/predict', methods=['POST']) # Rota que recebe os dados do chat via método POST
def predict(): # Função que processa a caixa de mensagem do chat
    text = request.get_json().get("message") # Pega o texto que o usuário enviou do frontend (JSON)
    if not text: # Se não houver texto
        return jsonify({"answer": "Por favor, digite algo."}) # Retorna um erro amigável
    
    response = get_response(text) # Chama a nossa inteligência para decidir a resposta
    message = {"answer": response} # Cria um dicionário com a resposta
    return jsonify(message) # Devolve a resposta em formato JSON para o JavaScript mostrar na tela

if __name__ == "__main__": # Ponto de entrada do script
    app.run(debug=True) # Inicia o servidor em modo de depuração (atualiza ao salvar arquivos)
