# AI Handoff — ChatBot Tenista

Documento de **contexto completo** para outra IA (ou dev) assumir o projeto em outra
máquina **sem perder nada**. Leia isto primeiro; os demais docs aprofundam cada tópico.

> Atualizado em: 2026-06. Estado: **v3 — arquitetura híbrida (Base + LLM)**.

---

## 1. O que é o projeto

Chatbot conversacional sobre **tênis (ATP/WTA), em português brasileiro**. Arquitetura
**híbrida**:

1. **Base de conhecimento** (NLTK + JSON + árvore de decisão contextual) responde primeiro
   — controle e confiabilidade no núcleo do domínio.
2. **LLM local (Qwen2.5-7B-Instruct via LM Studio)** entra como **fallback** para perguntas
   **de tênis** que a base não cobre.

O bot é **FECHADO no tema tênis**: perguntas fora de tênis são **bloqueadas** (nunca vão ao
LLM). Veja [LLM_HYBRID.md](LLM_HYBRID.md) para o roteamento detalhado.

**Stack:** Python 3.12+, Flask, Flask-CORS, NLTK, BeautifulSoup, requests, python-dotenv.
Frontend HTML/CSS/JS vanilla servido pelo Flask. LLM via LM Studio (API compatível com OpenAI).

---

## 2. Como rodar (resumo)

```bash
pip install -r requirements.txt
python app.py            # http://localhost:5000
python run_tests.py      # OBRIGATÓRIO antes de commit — meta: 312/312
```

- O `punkt` do NLTK é baixado automaticamente na 1ª execução.
- **LLM é opcional**: sem o LM Studio ligado, o app funciona (degradação graciosa) —
  responde tênis pela base e bloqueia off-topic; só o complemento de IA fica indisponível.
- Para ligar o LLM: instalar LM Studio, carregar `Qwen2.5-7B-Instruct` (GGUF Q4_K_M),
  Start Server na porta 1234, e copiar `.env.example` → `.env`. Detalhes em
  [`COMO_RODAR.md`](../COMO_RODAR.md) (raiz) e [LLM_HYBRID.md](LLM_HYBRID.md).

---

## 3. Estado atual (números reais)

| Item | Valor |
|---|---|
| Módulos Python da aplicação | **8** (~3.470 linhas) + `run_tests.py` (765) |
| Testes automatizados | **312 em 23 baterias** (rodam com `LLM_ENABLED=0`) |
| Jogadores em `player_details` | **290** |
| Rankings | ATP **100** + WTA **100** (atualizados automaticamente) |
| Grand Slams | 2024–2026 (masculino + feminino) |
| `tournament_details` | 18 (9 Masters 1000, 8 ATP 500, ATP Finals) |
| `records` | 16 recordes históricos |
| `knowledge_base.json` | 49 intents conversacionais |

---

## 4. Módulos e responsabilidades

| Módulo | Linhas | Responsabilidade |
|--------|-------:|-----------------|
| `app.py` | 860 | Servidor Flask, pipeline principal, filtros off-topic/gibberish, roteamento base→LLM, `/metrics` |
| `decision_tree.py` | 899 | Contexto conversacional (20 turnos), follow-ups, reações empáticas, fuzzy matching |
| `engine.py` | 514 | Consultas ao `tennis_data.json` (rankings, jogadores, campeões, torneios, recordes) |
| `llm_client.py` | 330 | Cliente do LLM (LM Studio): `query_llm`, `is_on_topic`, métricas, sanitização CJK |
| `api_client.py` | 416 | Atualização de rankings (scraping ATP + API WTA), retry e cache 24h |
| `query_parser.py` | 208 | Detecta país, temporal, superlativo, circuito, limite |
| `session_manager.py` | 153 | Sessões in-memory (UUID, TTL 30min, 20 turnos) |
| `nltk_utils.py` | 90 | tokenize(), stem(), bag_of_words(), extract_entities() |
| `run_tests.py` | 765 | 312 testes em 23 baterias |

**Dados:** `tennis_data.json` (rankings, player_details, grand_slams, tournament_details,
records), `knowledge_base.json` (intents), `unrecognized_queries.json` (log automático),
`llm_metrics.json` (métricas do LLM, gerado em runtime).

---

## 5. Pipeline de processamento (ordem exata)

Cada mensagem passa por estas etapas; se uma resolve, as seguintes são puladas:

```
[1]  Tokenização + Stemming (NLTK)                         → nltk_utils.py
[2]  Filtro Off-Topic — Camada 1 (regras)                  → app.py: OFF_TOPIC_KEYWORDS, looks_like_general_knowledge
[3]  Detecção de Gibberish                                 → app.py: is_gibberish()  (BLOQUEIA, nunca vai ao LLM)
[4]  Validação de tópico — Camada 3 (Qwen autoritativo)    → llm_client.is_on_topic()  (só com contexto ativo e sem sinal de tênis)
[5]  Árvore de Decisão contextual                          → decision_tree.try_contextual_response()
[6]  Query Parser (país, temporal, superlativo, circuito)  → query_parser.parse_query()
[7]  Motor de Dados (ranking, jogador, campeões, recordes) → engine.py: TennisEngine
[8]  Roteador de contagem ("quantos … slam/torneio")       → app.py: → LLM (Fix B)
[9]  Intent Matching (knowledge_base.json, threshold 50%)  → app.py
[10] Fallback final → LLM (perguntas de tênis fora da base)→ app.py: try_llm_fallback()
[11] Degradação graciosa → resposta canned (LLM off)       → app.py
[12] Enrich → adiciona follow-up + atualiza sessão         → decision_tree.enrich_response()
```

Cada etapa gera um *step* no **pipeline visual** (painel lateral do frontend).
Métricas registradas: `resolved_by_base`, `resolved_by_llm`, `llm_failures`, `unresolved`.

---

## 6. Roteamento Base × LLM (CRÍTICO — bot fechado em tênis)

- **Fora de tênis** → **BLOQUEADO** com aviso ("respiro apenas Tênis 🎾"). Nunca vai ao LLM.
  - Camada 1: blocklist (`OFF_TOPIC_KEYWORDS`) + conhecimento geral óbvio → bloqueio instantâneo.
  - Camada 3: quando há contexto ativo e a frase não tem sinal de tênis, o **Qwen** decide
    (`is_on_topic`); "não" confiante → bloqueia.
  - O LLM, mesmo acionado, devolve a sentinela `FORA_DO_TEMA` se a pergunta não for de tênis
    → o app bloqueia.
- **Tênis coberto pela base** → responde pela base (`resolved_by_base`).
- **Tênis fora da base** (ex.: jogador fora dos 290, fato histórico) → **Qwen responde**
  em português, com *grounding* leve (injeção de ficha/Top 5/lendas no prompt). `resolved_by_llm`.

Configuração em `.env` (não commitado): `LLM_ENABLED` (default 0), `LLM_BASE_URL`,
`LLM_MODEL`, `LLM_TIMEOUT`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`. Veja [LLM_HYBRID.md](LLM_HYBRID.md).

---

## 7. Constantes críticas (não remover sem entender o impacto)

| Constante | Arquivo | Função |
|---|---|---|
| `OFF_TOPIC_KEYWORDS` | app.py | 60+ palavras que bloqueiam assuntos fora de tênis |
| `TENNIS_SIGNAL_WORDS` / `PRONOUN_KEYWORDS` | app.py | Heurística `has_tennis_signal` (libera continuações/pronomes) |
| `SYSTEM_PROMPT` / `OFF_TOPIC_SENTINEL` | llm_client.py | Persona do LLM + sentinela `FORA_DO_TEMA` |
| `RECORDS_FACT_KEYWORDS` | decision_tree.py | Perguntas factuais/recorde que NÃO viram "campeões genéricos" |
| `TOURNAMENT_KEYWORDS` | decision_tree.py | Detecção de torneio na árvore |
| `REACTION_KEYWORDS` | decision_tree.py | Reações empáticas a atributos técnicos |
| `_STOP_WORDS` | decision_tree.py | 100+ palavras excluídas do fuzzy matching |
| `FOLLOW_UPS` | decision_tree.py | Mapa de follow-ups por (tópico, ação) |
| `COUNTRY_MAP` / `DEMONYM_MAP` | query_parser.py | 80+ mapeamentos país/gentílico |
| `CACHE_TTL` / `MAX_RETRIES` / `REQUEST_TIMEOUT` | api_client.py | Política de atualização de rankings |

---

## 8. Regras críticas (calibrações que NÃO devem mudar sem testes)

1. **Fuzzy matching threshold = 0.75** — abaixo gera falsos positivos, acima não detecta typos.
2. **Stem mínimo = 4 chars** no entity matching — protege contra matches curtos ("mai" → Mai Hontama).
3. **Prioridade torneio > jogador** na árvore — evita "Monte Carlo" → "Carlos Alcaraz".
4. **Reações empáticas** só disparam com `focus_player` definido.
5. **Off-topic**: não adicionar palavras que conflitem com tênis ("jogo", "voleio" → usar "voleibol").
6. **Follow-ups**: sempre 1 por resposta, nunca sim/não, sempre muda de tema.
7. **Pergunta factual que menciona torneio ≠ pedido de campeões** — ver seção 9.

---

## 9. Correções recentes importantes (contexto para continuar)

### 9.1 `api_client.py` — ranking ATP completo no startup
- `_http_get` com **retry** (`MAX_RETRIES=3`, `REQUEST_TIMEOUT=20`, backoff incremental) em
  timeout/erro de rede, aplicado a ATP, API WTA e fallback WTA.
- ATP só é considerado **sucesso completo** com **100** jogadores (antes `>=50` mascarava
  fetch parcial da página 2).
- `last_updated` (cache 24h) só é gravado quando **ambos** os rankings vêm completos; se vier
  parcial, **não trava** o cache — o próximo start tenta de novo.

### 9.2 Roteamento de perguntas factuais/recorde (3 camadas "gulosas" corrigidas)
Sintoma: "Quantos Grand Slams o Boris Becker conquistou?" / "Quem foi o primeiro tenista a
completar o Golden Slam?" caíam em **campeões genéricos** (`showed_champions`) em vez de seguir
para o LLM/recordes. Causa: 3 camadas capturavam por palavra-chave sem checar se podiam
responder. Correções:
- **decision_tree.py** — `_is_records_or_fact_question()` + `RECORDS_FACT_KEYWORDS`; 3 guardas
  nos branches genéricos de torneio (player_from_ranking, player_detail, open_topic): pergunta
  factual que só *menciona* "slam"/"grand slam" não vira "últimos campeões" — segue o pipeline.
- **app.py (Fix A)** — o atalho "superlativo → #1 do ranking" não dispara em pergunta
  factual/histórica ("primeiro a completar…").
- **app.py (Fix B)** — roteador: `"quantos/quantas" + torneio/slam` → vai ao **LLM** antes do
  intent genérico de definição (que casava "grand slam" em 100% por ser pattern curto).
- Cobertura: **BATERIA 23** em `run_tests.py` (3 casos do bug + 1 não-regressão).

---

## 10. Como adicionar conteúdo (mapa rápido)

| Tarefa | Onde |
|---|---|
| Novo jogador | `tennis_data.json` → `player_details` |
| Novo intent conversacional | `knowledge_base.json` |
| Nova reação empática | `decision_tree.py` → `REACTION_KEYWORDS` |
| Novo país/gentílico | `query_parser.py` (`COUNTRY_MAP`/`DEMONYM_MAP`), `engine.py` (`COUNTRY_FLAGS`), `api_client.py` (`COUNTRY_EN_TO_PT`/`COUNTRY_CODE_TO_PT`) |
| Nova keyword off-topic | `app.py` → `OFF_TOPIC_KEYWORDS` (cuidado com conflito com tênis) |
| Ajustar comportamento do LLM | `llm_client.py` (`SYSTEM_PROMPT`) e `.env` |

Detalhes de schema em [DATABASE_AND_SCRAPING.md](DATABASE_AND_SCRAPING.md) e [CLAUDE.md](CLAUDE.md).

---

## 11. Roadmap (backlog)

1. **RAG com busca vetorial** (embeddings) em vez de *grounding* por keyword.
2. **Head-to-Head** entre jogadores.
3. **Estatísticas avançadas** (aces, % 1º serviço, duplas faltas).
4. **Cache de respostas do LLM** + avaliação automática de alucinação.
5. **Mais jogadores/lendas** fora do Top 100.
6. **Calendário ATP/WTA** completo (datas e locais).

---

## 12. Índice da documentação

| Doc | Conteúdo |
|---|---|
| [AI_HANDOFF.md](AI_HANDOFF.md) | **Este arquivo** — contexto completo para continuar |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura, módulos e fluxo de processamento |
| [LLM_HYBRID.md](LLM_HYBRID.md) | Camada LLM (Qwen/LM Studio), roteamento, grounding, métricas |
| [PROJECT_GUIDE.md](PROJECT_GUIDE.md) | Guia módulo a módulo (o "porquê" de cada arquivo) |
| [CLAUDE.md](CLAUDE.md) | Manual de treino/aperfeiçoamento (branches, reações, follow-ups) |
| [DATABASE_AND_SCRAPING.md](DATABASE_AND_SCRAPING.md) | Schema dos JSON + scraping/API + retry/cache |
| [TESTS_AND_RESULTS.md](TESTS_AND_RESULTS.md) | 312 testes em 23 baterias + bugs corrigidos |
| [QUICK_START.md](QUICK_START.md) | Início rápido (base + LLM) |
| [CODING_STANDARDS.md](CODING_STANDARDS.md) | Regras de codificação (comentários PT-BR, etc.) |
| [RELATORIO.md](RELATORIO.md) | Relatório acadêmico do trabalho final |
| [TODO_GRAND_SLAMS.md](TODO_GRAND_SLAMS.md) | Backlog histórico (boa parte já concluída) |
| [`COMO_RODAR.md`](../COMO_RODAR.md) | Guia passo a passo para rodar em máquina nova (raiz) |
