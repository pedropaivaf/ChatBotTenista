# AI Tennis ChatBot 🎾

Um ChatBot especializado em Tênis construído com **Python**, **Flask** e **NLTK**.

## 🚀 Funcionalidades
- Respostas sobre jogadores (Federer, Nadal, Djokovic).
- Informações sobre torneios de Grand Slam.
- Explicação sobre o Ranking ATP.
- Interface web premium com design dark/glassmorphism.

## 🛠️ Tecnologias
- **Backend**: Flask (Python)
- **NLP**: NLTK (Tokenização, Stemming)
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6)

## 📦 Como Instalar e Rodar

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute o servidor:
```bash
python app.py
```

4. Acesse no navegador:
`http://127.0.0.1:5000`

## 📂 Estrutura do Projeto
- `/docs`: Documentação detalhada e Guia do Projeto.
- `/static`: CSS (Design Premium) e JavaScript.
- `/templates`: Interface HTML.
- `app.py`: Servidor Flask e lógica principal.
- `engine.py`: Motor de dados técnico interno.
- `tennis_data.json`: Base de dados oficial atualizada (2024/2025).
- `knowledge_base.json`: Base de intenções NLP.
- `nltk_utils.py`: Funções de processamento de texto.

## 🏆 Diferenciais
- **Offline/Autônomo**: Não depende de APIs externas.
- **Conversacional**: Sistema de perguntas de acompanhamento (follow-up).
- **Interface Premium**: Design moderno com Glassmorphism.