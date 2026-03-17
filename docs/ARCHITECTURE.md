# Arquitetura do ChatBot de Tênis

## Visão Geral
O projeto é baseado em uma arquitetura Cliente-Servidor simples, onde o Flask atua como o backend que processa as mensagens do usuário usando NLTK e retorna respostas baseadas em uma base de conhecimento.

## Componentes

### 1. Servidor Flask (`app.py`)
- Gerencia as rotas HTTP.
- Serve o frontend estático.
- Endpoint `/chat` para processar mensagens.

### 2. Processador de Linguagem Natural (`nltk_utils.py`)
- **Tokenização**: Divide frases em palavras.
- **Stemming**: Reduz palavras ao seu radical.

### 3. API Handler (`api_handler.py`)
- Gerencia a integração com a **API-Sports Tennis**.
- Provê dados de rankings (Ranking ATP) e placares ao vivo.
- Utiliza `python-dotenv` para segurança de chaves.

### 4. Base de Conhecimento (`knowledge_base.json`)
- Armazena fatos estáticos atualizados (incluindo Sinner e Alcaraz).

### 5. Interface Web (Frontend)
- Utiliza Vanilla HTML e CSS para máxima performance e controle estético.
- JavaScript assíncrono para comunicação fluida com o servidor.
