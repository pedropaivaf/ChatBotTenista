# Arquitetura do ChatBot Tenista

## Visão Geral

Arquitetura **cliente-servidor** com Flask no backend, **PLN clássico (NLTK)** e uma
**árvore de decisão contextual** (memória de até 20 turnos) para o núcleo do domínio, mais
um **LLM local (Qwen2.5-7B via LM Studio)** como **fallback** para perguntas de tênis fora
da base. O fallback tem **"modo pesquisa"**: quando a base não cobre, o bot **busca o fato na
Wikipedia** (`web_search.py`) e injeta como grounding (responde da fonte, não da memória). O bot
é **fechado no tema tênis** — off-topic é bloqueado.

**Total: ~3.620 linhas de Python em 9 módulos da aplicação + ~810 linhas de testes (322 testes).**

---

## Componentes

### 1. Servidor Flask (`app.py` — 860 linhas)
- Rotas: `/` (frontend), `/predict` (pipeline) e `/metrics` (métricas do LLM).
- Orquestra todos os módulos e gera o **pipeline trace** (cada etapa = um step para o frontend).
- **Filtro off-topic** (Camada 1): `OFF_TOPIC_KEYWORDS` (60+) + `looks_like_general_knowledge`.
- **Detecção de gibberish**: ratio de vogais, consoantes consecutivas, bigramas improváveis.
- **Roteamento base→LLM**: aciona o LLM via `try_llm_fallback()` para tênis fora da base;
  bloqueia off-topic via `block_off_topic()`.
- No startup, executa `api_client.refresh_if_needed()`.

### 2. Processador NLP (`nltk_utils.py` — 90 linhas)
- `tokenize` (word_tokenize), `stem` (PorterStemmer), `bag_of_words`, `extract_entities`
  (mín. 4 caracteres para evitar falsos positivos).

### 3. Motor de Dados (`engine.py` — 514 linhas)
- `TennisEngine` carrega `tennis_data.json` em memória.
- Rankings, fichas de jogador, campeões de Grand Slam, detalhes de torneios (Masters
  1000/500/Finals), recordes, filtragem por país, posição no ranking, bandeiras emoji.
- `reload_data()` recarrega sem reiniciar.

### 4. Cliente LLM (`llm_client.py` — 330 linhas) — **camada híbrida**
- `query_llm(user_text, grounding, history)`: chama o LM Studio (`/v1/chat/completions`),
  monta `SYSTEM_PROMPT` + grounding, sanitiza CJK (anti *code-switching*), mede latência.
- `is_on_topic(text)`: classificador autoritativo de tópico via Qwen (Camada 3).
- Sentinela `FORA_DO_TEMA`: se o modelo julgar a pergunta fora de tênis, o app bloqueia.
- Métricas em `llm_metrics.json` + endpoint `/metrics`. **Degradação graciosa**: tudo
  retorna `None` quando `LLM_ENABLED!=1` ou o servidor está fora. Ver [LLM_HYBRID.md](LLM_HYBRID.md).

### 4-B. Cliente de Pesquisa (`web_search.py` — ~150 linhas) — **modo pesquisa (v4)**
- `search_tennis(query, player_hint=None)`: busca o fato de tênis na **Wikipedia** (MediaWiki
  search + REST summary, PT→EN), com cache (só sucessos) e **desambiguação** (só aceita resumo
  com sinal de tênis → senão `None`, honestidade). Acionado por `app.build_grounding` no
  fallback/curiosidade. **Degradação graciosa** (`WEB_SEARCH_ENABLED=0` ou sem rede → `None`).

### 5. Cliente de Dados (`api_client.py` — 416 linhas)
- **ATP**: scraping `tennisexplorer.com` (2 páginas, Top 100).
- **WTA**: API JSON `api.wtatennis.com` (fallback: tennisexplorer).
- `_http_get` com **retry** (3 tentativas, timeout 20s, backoff) em timeout/erro de rede.
- Cache 24h; `last_updated` só é gravado com rankings **completos** (ATP=100, WTA=100).
- Traduz países (50+ EN→PT, 60+ ISO-3→PT), corrige nomes com acentos.

### 6. Parser de Queries (`query_parser.py` — 208 linhas)
- País (40+ + gentílicos), temporal, superlativo, circuito (ATP/WTA, auto-feminino→WTA),
  limite ("top N"). Remove nomes de torneios antes de detectar país.

### 7. Árvore de Decisão (`decision_tree.py` — 899 linhas) — **componente mais complexo**
Máquina de estados contextual. Branches em ordem de prioridade:
1. **Pronome implícito** (focus + "dele/dela") → país/campo/info do jogador em foco.
2. **Torneio no contexto** → detalhes ou campeões.
3. **Jogador do contexto** (fuzzy match) → ficha.
4. **Detalhe do jogador em foco** → comparação, país, estilo, **reação empática**, elogio.
5. **Tópico aberto** (pós-trivia) → jogador ou torneio.

Subsistemas: fuzzy matching (threshold 0.75, 100+ stop words), follow-ups abertos,
reações empáticas (pronomes gênero-corretos), trace visual. **Guarda factual/recorde**:
`_is_records_or_fact_question()` impede que perguntas factuais que apenas mencionam "slam"
sejam tratadas como pedido genérico de campeões.

### 8. Gerenciador de Sessões (`session_manager.py` — 153 linhas)
- Sessões in-memory (UUID, TTL 30min), até 20 turnos, limpeza automática.

### Dados
- **`tennis_data.json`**: rankings ATP/WTA (100+100), `player_details` (290), `grand_slams`
  (2024–2026), `tournament_details` (18), `records` (16).
- **`knowledge_base.json`**: 49 intents conversacionais.
- **`unrecognized_queries.json`**: log automático de não reconhecidas.
- **`llm_metrics.json`**: métricas do LLM (runtime).

### Frontend (`templates/`, `static/`)
- HTML semântico, CSS Glassmorphism, JS vanilla (Fetch API com `session_id`).
- **Pipeline visual** animado + fluxograma da árvore + token pills. Numa resposta de IA,
  mostra requisição/resposta/métricas do LM Studio (latência, tokens, tok/s).

---

## Fluxo de Processamento Completo

```
Mensagem do Usuário
        |
  [1] Tokenize + Stem (NLTK)
        |
  [2] Filtro Off-Topic — Camada 1 (regras)  ── off-topic? → BLOQUEIA (aviso)
        |
  [3] Gibberish?  ── sim → BLOQUEIA (nunca vai ao LLM)
        |
  [4] Validação Qwen — Camada 3 (só com contexto ativo, sem sinal de tênis) ── "não"? → BLOQUEIA
        |
  [5] Árvore de Decisão (contexto, pronome, torneio, jogador, reação, open_topic)
        |    └── guarda: pergunta factual/recorde mencionando torneio → segue (não vira campeões)
        |
  [6] Query Parser (país/temporal/superlativo/circuito)
        |    └── guarda: superlativo "primeiro a…" não vira #1 do ranking (Fix A)
        |
  [7] Motor de Dados (ranking, jogador, campeões, recordes, posição, país)
        |
  [7.5] Curiosidade/fato sobre JOGADOR → IA (grounding perfil + PESQUISA Wikipedia), SEM ficha
        |
  [8] Roteador "quantos … slam/torneio" → LLM (Fix B)
        |
  [9] Intent Matching (knowledge_base.json, 50% / 65% com contexto)
        |
  [10] Fallback final → LLM (tênis fora da base, com grounding + PESQUISA Wikipedia) ── FORA_DO_TEMA? → BLOQUEIA
        |
  [11] LLM indisponível → resposta canned (degradação graciosa)
        |
  [12] Enrich → follow-up aberto + atualiza sessão
        |
  Resposta JSON + Pipeline Trace → Frontend
  (métrica: resolved_by_base | resolved_by_llm | unresolved)
```

---

## Diagrama de Dependências

```
                         app.py (Orquestrador, /predict, /metrics)
        ┌────────────┬──────────┬───────────┬────────────┬───────────┬────────────┐
   nltk_utils.py  engine.py  llm_client.py  web_search.py  api_client.py  query_parser.py
                     │            │              │              │
              tennis_data.json  LM Studio    Wikipedia   tennisexplorer / wtatennis
                     │         (Qwen2.5)    (REST/MediaWiki)
              decision_tree.py
                     │
              session_manager.py
```

`app.py` importa de `decision_tree`: `DecisionTree`, `_fuzzy_match_player`,
`PRONOUN_KEYWORDS`, `TOURNAMENT_KEYWORDS`, `_is_records_or_fact_question`.
