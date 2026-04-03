# Arquitetura do ChatBot de Tenis

## Visao Geral

Arquitetura Cliente-Servidor com Flask no backend, NLTK para processamento de linguagem natural, e um sistema hibrido de arvore de decisao + sessoes para manter contexto conversacional de ate 20 interacoes.

**Total: ~2.350 linhas de Python em 7 modulos + 349 linhas de testes.**

---

## Componentes

### 1. Servidor Flask (`app.py` — 415 linhas)
- Gerencia as rotas HTTP (`/` e `/predict`).
- Serve o frontend estatico.
- Integra todos os modulos: session, query parser, decision tree e engine.
- No startup, executa refresh automatico de rankings via `api_client.py`.
- **Filtro off-topic**: 60+ keywords bloqueadas (futebol, bitcoin, politica...).
- **Deteccao de gibberish**: Analisa ratio de vogais, consoantes consecutivas e bigramas para rejeitar texto sem sentido.
- **Pipeline trace**: Cada etapa do processamento gera um step com nome, status e dados extras para o frontend.

### 2. Processador de Linguagem Natural (`nltk_utils.py` — 78 linhas)
- **Tokenizacao**: Divide frases em palavras via `word_tokenize`.
- **Stemming**: Reduz palavras ao radical com PorterStemmer.
- **Extracao de Entidades**: Identifica nomes de jogadores e torneios via matching de stems, com validacao minima de 4 caracteres.

### 3. Motor de Dados (`engine.py` — 266 linhas)
- Classe `TennisEngine` que carrega `tennis_data.json` em memoria.
- **Metodos principais**: `get_ranking_summary()`, `get_last_champions()`, `get_player_info()`, `get_player_country()`.
- **Metodos de filtragem**: `get_filtered_ranking()` (por pais), `get_best_from_country()` (melhor de um pais).
- **Bandeiras**: Emoji flags para 25+ paises com normalizacao de acentos.
- `reload_data()` permite recarregar dados sem reiniciar o servidor.

### 4. Gerenciador de Sessoes (`session_manager.py` — 153 linhas)
- Sessoes in-memory com UUID, TTL de 30 minutos.
- Rastreia ate 20 turnos de conversa por sessao.
- Armazena: topico atual, circuito (ATP/WTA), entidades mencionadas, jogador em foco, follow-up pendente.
- Limpeza automatica de sessoes expiradas.

### 5. Parser Inteligente de Queries (`query_parser.py` — 203 linhas)
- Detecta modificadores na mensagem via string matching direto (sem stems).
- **Pais**: 40+ paises + 50+ gentilicos ("brasileiro" → "Brasil").
- **Temporal**: "atualmente", "hoje", "agora" → flag `is_current`.
- **Superlativo**: "melhor", "top", "lider" → flag `wants_best`.
- **Circuito**: "atp"/"masculino" ou "wta"/"feminino".
- **Limite**: Detecta "top N" para limitar resultados.
- **Protecao**: Remove nomes de torneios antes de detectar pais (evita "Australian Open" → Australia).

### 6. Arvore de Decisao (`decision_tree.py` — 506 linhas)
Maquina de estados contextual — o componente mais complexo do sistema.

**Branches de decisao (em ordem de prioridade):**
1. **Torneio no contexto**: Detecta nomes de torneios quando ha follow-up pendente.
2. **Jogador do contexto**: Resolve nomes parciais ("Alcaraz" apos ranking → Carlos Alcaraz) via fuzzy matching.
3. **Detalhes do jogador**: Quando ha `focus_player`, processa:
   - Comparacoes ("comparar com Djokovic")
   - Pais ("qual o pais dele")
   - Estilo de jogo ("qual o estilo dele")
   - **Reacoes empaticas** a 13 atributos tecnicos (forehand, saque, mental, etc.)
   - **Elogios genericos** ("um dos melhores", "goat", "lenda")
4. **Topico aberto**: Apos trivia, aceita jogador ou torneio como resposta.

**Subsistemas:**
- **Fuzzy matching**: `difflib.SequenceMatcher` com threshold 0.75 e 100+ stop words.
- **Follow-ups**: Mapa `(topico, acao)` → perguntas abertas que mudam de tema.
- **Reacoes**: 13 atributos tecnicos com respostas empaticas e pronomes genero-corretos.
- **Trace**: Cada branch gera um node (icone, nome, matched, detail) para visualizacao.

### 7. Cliente de Dados (`api_client.py` — 377 linhas)
- **ATP**: Scraping de `tennisexplorer.com` (2 paginas, Top 100).
- **WTA**: API JSON oficial `api.wtatennis.com` (fallback: tennisexplorer).
- Cache de 24h — atualiza no maximo 1x por dia no startup.
- Traduz paises (50+ EN→PT, 60+ ISO-3→PT), corrige nomes com acentos (~15 correcoes).

### 8. Base de Conhecimento (`knowledge_base.json`)
- 15+ intents conversacionais com padroes, respostas e follow-ups.
- Tags: saudacao, despedida, feedback_positivo, regras, superficies, equipamento, etc.

### 9. Base de Dados (`tennis_data.json`)
- Rankings ATP e WTA Top 100 (atualizados automaticamente).
- Grand Slams historicos (2024-2026, masculino e feminino).
- Biografias detalhadas de ~50 jogadores (idade, estilo, titulos, pais, curiosidade).

### 10. Interface Web (Frontend)
- HTML semantico, CSS Glassmorphism, JS vanilla com Fetch API.
- Envia `session_id` (UUID) em cada request para manter contexto.
- **Pipeline visual**: Painel lateral com animacao step-by-step mostrando cada etapa do processamento.
- **Fluxograma da arvore**: Branches matched/missed com icones e detalhes.
- **Token pills**: Visualizacao de tokens e stems da tokenizacao NLTK.

---

## Fluxo de Processamento Completo

```
Mensagem do Usuario
        |
  [1. Pre-processamento] Tokenize + Stem (NLTK)
        |
  [2. Filtro Off-Topic] 60+ keywords + gibberish detection
        |           (vowel ratio, consecutive consonants, bigrams)
        |
  [3. Resolucao Contextual] Arvore de decisao
        |    ├── Torneio no contexto?
        |    ├── Jogador do contexto? (fuzzy match)
        |    ├── Detalhe do jogador? (reacao, elogio, pais, estilo)
        |    └── Topico aberto? (pos-trivia)
        |
  [4. Query Parser] Detecta pais/temporal/superlativo/circuito
        |
  [5. Dados Tecnicos] Ranking, Campeoes, Jogadores
        |    ├── Filtragem por pais
        |    ├── Melhor de um pais
        |    └── Fuzzy fallback para jogadores
        |
  [6. Deteccao de Torneio] Roland Garros, Wimbledon, etc.
        |
  [7. Intents Conversacionais] knowledge_base.json (50% threshold)
        |
  [8. Fallback] Log em unrecognized_queries.json
        |
  [9. Enrich] Adiciona follow-up aberto + atualiza sessao
        |
  Resposta JSON + Pipeline Trace → Frontend
```

---

## Diagrama de Dependencias

```
                    app.py (Orchestrator)
                   /    |    \      \
        nltk_utils.py   |   engine.py  api_client.py
                        |       |
              decision_tree.py  tennis_data.json
                        |
              session_manager.py
                        |
              query_parser.py
```
