# Camada Híbrida: LLM (Qwen2.5 via LM Studio)

Este documento descreve a camada de **LLM de fallback** — o que é, como roteia, como evita
alucinação e *code-switching*, como configurar e como medir. Implementação em
[`llm_client.py`](../llm_client.py); roteamento em [`app.py`](../app.py).

---

## 1. Princípio: Base primeiro, LLM como fallback

A **base de conhecimento** (`knowledge_base.json` + `tennis_data.json` + árvore de decisão)
responde **primeiro** — controle e confiabilidade no núcleo do domínio. O **LLM** entra
**apenas** quando a base não cobre a pergunta — e **somente para perguntas de tênis**.

> **O bot é FECHADO no tema tênis.** Perguntas fora de tênis são **bloqueadas**, nunca
> respondidas pelo LLM. Esta é a diferença mais importante a entender no roteamento.

---

## 2. O modelo e o servidor

- **Modelo:** `Qwen2.5-7B-Instruct` (GGUF, quantização `Q4_K_M`, ~4,7 GB; roda em ~8 GB RAM).
  - Forte em **português**, *instruction-tuned*, **não-gated** no Hugging Face.
  - **Evitar a variante `-1M`** (contexto longo): troca de idioma (chinês) com mais frequência.
  - Alternativa leve: `Qwen2.5-3B-Instruct`.
- **Servidor:** **LM Studio** expõe uma API compatível com OpenAI em
  `http://127.0.0.1:1234/v1`. Use **127.0.0.1** (no Windows, "localhost" pode resolver para
  IPv6 e falhar).

---

## 3. Configuração (`.env`)

O `.env` **não é commitado** (está no `.gitignore`). Copie de `.env.example`:

| Variável | Default | Descrição |
|---|---|---|
| `LLM_ENABLED` | `0` | Liga (`1`) / desliga (`0`) o fallback LLM |
| `LLM_BASE_URL` | `http://127.0.0.1:1234/v1` | Endpoint do LM Studio |
| `LLM_MODEL` | `qwen2.5-7b-instruct` | Model Identifier do LM Studio |
| `LLM_TIMEOUT` | `30` | Timeout (s) por requisição |
| `LLM_MAX_TOKENS` | `350` | Limite de tokens da resposta |
| `LLM_TEMPERATURE` | `0.5` | Criatividade controlada |
| `LLM_METRICS_FILE` | `llm_metrics.json` | Arquivo de métricas |

> **Os testes forçam `LLM_ENABLED=0`** antes de importar o `app` (determinismo). Por isso
> `run_tests.py` nunca depende do LM Studio.

---

## 4. Roteamento (onde o LLM é acionado)

```
Mensagem
 ├─ Off-topic por regra (blocklist / conhecimento geral)  → BLOQUEIA  (Camada 1, sem LLM)
 ├─ Gibberish                                             → BLOQUEIA  (sem LLM)
 ├─ Contexto ativo + sem sinal de tênis → is_on_topic()   → "não"? BLOQUEIA  (Camada 3, Qwen)
 ├─ Base resolve (árvore / motor / intents)               → resposta da BASE   [resolved_by_base]
 ├─ "quantos … slam/torneio"                              → LLM  (Fix B, roteador de contagem)
 └─ Fallback final (base não resolveu)                    → LLM  (try_llm_fallback)
        ├─ LLM responde tênis                             → resposta do LLM    [resolved_by_llm]
        ├─ LLM devolve sentinela FORA_DO_TEMA             → BLOQUEIA (era off-topic)
        └─ LLM indisponível/desligado                     → resposta canned    [unresolved]
```

### Três camadas de filtro off-topic
1. **Camada 1 (regras):** `OFF_TOPIC_KEYWORDS` (60+) + `looks_like_general_knowledge()` —
   bloqueio instantâneo, sem custo de LLM.
2. **Gibberish:** texto sem sentido — bloqueado (não faz sentido gastar o LLM).
3. **Camada 3 (Qwen autoritativo):** quando há **contexto ativo** (a árvore "sequestraria" a
   resposta) e a frase **não tem sinal de tênis**, `is_on_topic()` pergunta ao Qwen "é sobre
   tênis? sim/não". Só um **"não" confiante** bloqueia. Com LLM off, retorna `None` e o fluxo
   segue idêntico (testes determinísticos).

---

## 5. Anti-alucinação: *grounding* leve (RAG simplificado)

Antes de chamar o LLM, `app.py: build_grounding(msg_lower)` injeta **contexto factual** no
system prompt (quando relevante):
- **(a)** Ficha do jogador citado (se estiver no `player_details`).
- **(b)** Top 5 ATP/WTA atual (se a pergunta for sobre ranking/melhor do mundo).
- **(c)** Lendas reais (para "melhor de todos os tempos", "maior brasileiro" → Guga, Bia
  Haddad, Maria Esther Bueno) — evita nomes inventados.

O *grounding* foi decisivo: sem ele, o modelo alucinava tenistas brasileiros inexistentes;
com ele, responde **Guga** corretamente.

---

## 6. Anti *code-switching* (Qwen "vazando" para chinês)

Modelos pequenos às vezes misturam CJK. Mitigações em `llm_client.py`:
1. **Lembrete de idioma por recência**: a instrução de "responder em PT-BR" é anexada à
   própria pergunta (texto mais recente que o modelo vê).
2. **Não enviar histórico** ao modelo (`history=None` no fallback): o contexto de tênis
   confundia o modelo e disparava a troca. Follow-ups de tênis já são resolvidos pela base.
3. **Retry limpo**: se a resposta contém CJK (`_CJK_RE`), re-tenta com prompt mínimo
   (persona + grounding + pergunta), temperatura 0.2.
4. **Sanitização** (`_strip_cjk`): corta a partir do 1º caractere CJK remanescente.
5. **Escolha do modelo padrão `Instruct`** (não `-1M`), bem mais estável em português.

---

## 7. Persona e sentinela (`SYSTEM_PROMPT`)

O system prompt fixa o assistente **exclusivamente em tênis** (ATP/WTA), exige **PT-BR**,
respostas curtas e diretas (1–2 frases) e honestidade quando incerto. Se a pergunta **não**
for de tênis, o modelo deve responder **só** a palavra `FORA_DO_TEMA` — o `app.py` detecta a
sentinela e bloqueia (`block_off_topic`).

---

## 8. Métricas (`/metrics` e `llm_metrics.json`)

`llm_client.record()` acumula: `resolved_by_base`, `resolved_by_llm`, `llm_failures`,
`unresolved`, latência total/contagem. `metrics_snapshot()` calcula percentuais e
`tempo_medio_llm_s`. Quando `LLM_ENABLED=0`, `record()` é no-op (não polui métricas nos testes).

**Snapshot representativo** (15 perguntas, Qwen2.5-7B-Instruct): ~60% base, ~33% LLM,
~7% bloqueadas; tempo médio do LLM ~2,65 s (~19–20 tok/s em GPU modesta).

---

## 9. Degradação graciosa

Tudo na camada LLM é **opcional**. Sem o LM Studio (ou `LLM_ENABLED=0`), todas as funções
retornam `None` silenciosamente e o `app.py` recai nas respostas da base/canned. É isso que
mantém os **312 testes** verdes sem depender do LM Studio.

---

## 10. Arquivos-chave

| Arquivo | Papel |
|---|---|
| [`llm_client.py`](../llm_client.py) | Cliente LLM: `query_llm`, `is_on_topic`, `record`, `metrics_snapshot`, sanitização CJK |
| [`app.py`](../app.py) | `build_grounding`, `try_llm_fallback`, `block_off_topic`, roteador de contagem, `/metrics` |
| [`.env.example`](../.env.example) | Configuração de exemplo |
| [`COMO_RODAR.md`](../COMO_RODAR.md) | Passo a passo do LM Studio + modelo |
