# Guia do Projeto: Tennis AI ChatBot

Este documento explica o "porque" e o "como" de cada arquivo do projeto.

---

## Estrutura do Projeto

### 1. `app.py` (O Cerebro)
Servidor principal Flask com logica hibrida de roteamento.
- **Rota `/`**: Carrega a interface visual (HTML).
- **Rota `/predict`**: Recebe a mensagem do usuario e devolve a resposta.
- **Pipeline**: Off-topic -> Contexto -> Query Parser -> Dados Tecnicos -> Intents -> Fallback.
- Integra sessoes, arvore de decisao e parser inteligente.

### 2. `nltk_utils.py` (O Interprete)
Funcoes de Processamento de Linguagem Natural (PLN).
- **Tokenizacao**: Quebra a frase em palavras individuais.
- **Stemming**: Reduz palavras ao radical (ex: "vencendo" e "venceu" viram a mesma raiz).
- **Extracao de Entidades**: Identifica nomes de jogadores e torneios.

### 3. `engine.py` (O Especialista)
Motor de consulta que le `tennis_data.json` e filtra rankings, busca campeoes e detalhes de jogadores.
- `get_ranking_summary()`: Top 10 ATP ou WTA formatado.
- `get_player_info()`: Ficha completa com rank, pais, idade, estilo, titulos e curiosidade.
- `get_filtered_ranking()`: Filtra ranking por pais (ex: "ranking do Brasil").
- `get_best_from_country()`: Retorna os melhores jogadores de um pais.

### 4. `session_manager.py` (A Memoria)
Gerencia sessoes de conversa para manter contexto.
- Cada aba do navegador recebe um UUID unico.
- Rastreia ate 20 turnos de conversa, topico atual, jogador em foco.
- Sessoes expiram apos 30 minutos de inatividade.

### 5. `query_parser.py` (O Detetive)
Analisa a mensagem do usuario para extrair modificadores estruturados.
- Detecta paises ("do brasil", "brasileiro") e traduz para nome canonico.
- Detecta marcadores temporais ("atualmente", "hoje").
- Detecta superlativos ("melhor", "top", "lider").
- Exemplo: "melhor jogador do brasil atualmente" -> `{country: "Brasil", wants_best: True, is_current: True}`.

### 6. `decision_tree.py` (O Contexto)
Arvore de decisao que gera follow-ups abertos e resolve entidades por contexto.
- Apos "ranking atp", usuario diz "Alcaraz" -> bot resolve como Carlos Alcaraz.
- Apos info do Sinner, usuario diz "qual o pais dele" -> bot responde Italia.
- Follow-ups sempre abertos: "Qual desses jogadores voce mais admira?" (nunca sim/nao).

### 7. `api_client.py` (O Atualizador)
Busca rankings atualizados de fontes externas reais.
- **ATP**: Scraping de tennisexplorer.com (HTML, sem bloqueio).
- **WTA**: API JSON oficial da WTA (api.wtatennis.com).
- Atualiza automaticamente no startup se dados tem mais de 24h.
- Traduz paises do ingles para portugues, corrige nomes com acentos.

### 8. `knowledge_base.json` e `tennis_data.json` (Os Dados)
- **`knowledge_base.json`**: Intents conversacionais com padroes e respostas.
- **`tennis_data.json`**: Rankings Top 100 (ATP+WTA), Grand Slams, biografias de ~50 jogadores.

### 9. Pasta `/templates` e `/static` (A Face)
- **`index.html`**: Estrutura semantica do chat.
- **`style.css`**: Design Premium com efeito Glassmorphism e modo escuro.
- **`script.js`**: Comunicacao AJAX/Fetch com envio de `session_id` para contexto.

---

## Pontos Fortes para Apresentacao

1.  **Contexto de 20 Turnos**: O bot mantem contexto entre mensagens, entende "Alcaraz" apos ranking, "qual o pais dele" apos ficha de jogador, e "roland garros" apos curiosidade.
2.  **Tolerancia a Erros de Digitacao**: Fuzzy matching com `difflib` permite que "Medevedev", "Tsitipas" e outros typos sejam resolvidos automaticamente para o jogador correto.
3.  **Parser Inteligente**: "Qual o melhor jogador do brasil atualmente" retorna Joao Fonseca porque reconhece "brasil" + "melhor" + "atualmente" como filtros estruturados.
4.  **Dados em Tempo Real**: Rankings ATP e WTA Top 100 atualizados automaticamente via scraping/API a cada 24h.
5.  **Arquitetura Hibrida**: Combina regras tecnicas (`engine.py`), NLP (`NLTK`), contexto (`decision_tree.py`) e fuzzy matching.
6.  **Design Profissional**: Interface Glassmorphism com console tecnico lateral mostrando logs em tempo real.

---

## Como Explicar o Funcionamento

"Quando o usuario digita 'Qual o melhor jogador do brasil atualmente?', o `app.py` recebe a mensagem, o `query_parser.py` detecta 'brasil' como pais e 'melhor' como superlativo, o `engine.py` filtra o ranking ATP por Brasil e retorna Joao Fonseca como #40 do mundo. O bot pergunta 'Qual deles voce acompanha mais de perto?'. Se o usuario responde 'Fonseca', a `decision_tree.py` resolve isso no contexto e mostra a ficha completa dele."
