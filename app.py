from flask import Flask, render_template, request, jsonify
import json
import random
from nltk_utils import tokenize, stem
from engine import TennisEngine

app = Flask(__name__)
tennis_engine = TennisEngine()

# Carregar base de conhecimento (NLP)
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    intents = json.load(f)

def get_response(msg):
    sentence = tokenize(msg)
    msg_lower = msg.lower()
    
    # 1. Verificar consultas no Motor de Dados Técnico (Dados Oficiais)
    if any(word in msg_lower for word in ["ranking", "top 10", "melhores do mundo"]):
        return tennis_engine.get_ranking_summary()

    if any(word in msg_lower for word in ["campeões", "quem ganhou", "grand slam 2024"]):
        return tennis_engine.get_last_champions()

    # Verificar se perguntou por um jogador específico na base técnica
    for player in ["sinner", "alcaraz"]:
        if player in msg_lower:
            player_info = tennis_engine.get_player_info(player)
            if player_info: return player_info

    # 2. Reconhecimento Direto de Saudações
    greetings = ["oi", "ola", "ei", "tudo bem", "bom dia", "boa tarde", "boa noite", "opa"]
    if any(greet in msg_lower for greet in greetings):
        for intent in intents['intents']:
            if intent['tag'] == 'saudacao':
                resp = random.choice(intent['responses'])
                return f"{resp} {intent['follow_up']}"

    # 3. Fallback para base de conhecimento local (NLP)
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            pattern_tokens = [stem(w) for w in tokenize(pattern)]
            msg_tokens = [stem(w) for w in sentence]
            
            if all(token in msg_tokens for token in pattern_tokens):
                response = random.choice(intent['responses'])
                follow_up = intent.get('follow_up', "")
                return f"{response} {follow_up}".strip()
            
            match_count = sum(1 for token in pattern_tokens if token in msg_tokens)
            if len(pattern_tokens) > 0 and match_count / len(pattern_tokens) > 0.7:
                response = random.choice(intent['responses'])
                follow_up = intent.get('follow_up', "")
                return f"{response} {follow_up}".strip()

    return "Desculpe, ainda estou aprendendo sobre isso. Que tal me perguntar sobre o ranking atual, campeões de 2024 ou sobre lendas como Federer e Nadal?"



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    text = request.get_json().get("message")
    if not text:
        return jsonify({"answer": "Por favor, digite algo."})
    
    response = get_response(text)
    message = {"answer": response}
    return jsonify(message)

if __name__ == "__main__":
    app.run(debug=True)
