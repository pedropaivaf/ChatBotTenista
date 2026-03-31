# Arquitetura do ChatBot de Tênis

## Visao Geral
O projeto utiliza uma arquitetura Cliente-Servidor com Flask no backend, NLTK para processamento de linguagem natural, e um sistema de sessoes com arvore de decisao para manter contexto conversacional de ate 20 interacoes.

## Componentes

### 1. Servidor Flask (`app.py`)
- Gerencia as rotas HTTP (`/` e `/predict`).
- Serve o frontend estatico.
- Integra todos os modulos: session, query parser, decision tree e engine.
- No startup, executa refresh automatico de rankings via `api_client.py`.

### 2. Processador de Linguagem Natural (`nltk_utils.py`)
- **Tokenizacao**: Divide frases em palavras via `word_tokenize`.
- **Stemming**: Reduz palavras ao seu radical com PorterStemmer.
- **Extracao de Entidades**: Identifica nomes de jogadores e torneios na mensagem.

### 3. Motor de Dados (`engine.py`)
- Classe `TennisEngine` que carrega `tennis_data.json` em memoria.
- Metodos: `get_ranking_summary()`, `get_last_champions()`, `get_player_info()`, `get_player_country()`.
- **Novos metodos**: `get_filtered_ranking()` (filtra por pais), `get_best_from_country()` (melhor de um pais), `reload_data()`.

### 4. Gerenciador de Sessoes (`session_manager.py`)
- Sessoes in-memory com UUID, TTL de 30 minutos.
- Rastreia ate 20 turnos de conversa por sessao.
- Armazena: topico atual, entidades mencionadas, jogador em foco, follow-up pendente.

### 5. Parser Inteligente de Queries (`query_parser.py`)
- Detecta modificadores na mensagem do usuario via string matching direto (sem stems).
- **Pais**: 40+ paises + gentilicos ("brasileiro" -> "Brasil").
- **Temporal**: "atualmente", "hoje", "agora" -> flag `is_current`.
- **Superlativo**: "melhor", "top", "lider" -> flag `wants_best`.
- **Circuito**: "atp"/"masculino" ou "wta"/"feminino".

### 6. Arvore de Decisao (`decision_tree.py`)
- Maquina de estados contextual com transicoes por topico.
- Gera follow-ups **abertos** (nunca sim/nao).
- Resolve entidades contextualmente: "Alcaraz" apos ranking -> Carlos Alcaraz.
- Rastreia `focus_player` para perguntas como "qual o pais dele".

### 7. Cliente de Dados (`api_client.py`)
- Atualiza rankings ATP e WTA de fontes externas reais.
- **ATP**: Scraping de `tennisexplorer.com` (HTML server-rendered).
- **WTA**: API JSON oficial `api.wtatennis.com` (fallback: tennisexplorer).
- Cache de 24h — atualiza no maximo 1x por dia no startup.
- Traduz paises para portugues, corrige nomes com acentos.

### 8. Base de Conhecimento (`knowledge_base.json`)
- Intents conversacionais com padroes, respostas e follow-ups.
- 15+ intents cobrindo saudacoes, regras, superficies, equipamento, etc.

### 9. Base de Dados (`tennis_data.json`)
- Rankings ATP e WTA Top 100 (atualizados automaticamente).
- Grand Slams historicos (2024-2026).
- Biografias detalhadas de ~50 jogadores.

### 10. Interface Web (Frontend)
- HTML semantico, CSS Glassmorphism, JS vanilla com Fetch API.
- Envia `session_id` em cada request para manter contexto.
- Console tecnico lateral com logs coloridos em tempo real.

---

## Fluxo de Processamento

```
Mensagem do Usuario
        |
  [Pre-processamento] Tokenize + Stem
        |
  [Filtro Off-Topic] Copa, futebol, etc.
        |
  [Resolucao Contextual] Arvore de decisao verifica pending_follow_up
        |
  [Query Parser] Detecta pais/temporal/superlativo
        |
  [Dados Tecnicos] Ranking, Campeoes, Jogadores
        |
  [Intents Conversacionais] knowledge_base.json
        |
  [Fallback] Log + resposta generica
        |
  [Enrich] Adiciona follow-up aberto + atualiza sessao
        |
  Resposta JSON -> Frontend
```
