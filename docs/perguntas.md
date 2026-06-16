# Perguntas de Demonstração — Pipeline do ChatBot Tenista

Lista de perguntas (1 por situação) para demonstrar **cada caminho** que uma mensagem
pode percorrer no pipeline (ver [CLAUDE.md](CLAUDE.md) e [LLM_HYBRID.md](LLM_HYBRID.md)).
Cada pergunta foi **testada** via `app.test_client()` e a coluna "Caminho verificado"
mostra a etapa/ação que ela aciona no painel de pipeline.

> ⚙️ **Pré-requisitos por bloco**
> - **Blocos 1, 2 e 6** funcionam **sempre** (base local) — não dependem de serviços externos.
> - **Blocos 3, 4 e 5** só produzem a **resposta da IA** com o **LM Studio ligado**
>   (`LLM_ENABLED=1`). Sem ele, o roteamento acontece igual (visível no painel), mas a
>   resposta degrada para uma mensagem *canned*.
> - O **Bloco 4** (pesquisa web) exige ainda `WEB_SEARCH_ENABLED=1` e internet.

---

## 🎾 Bloco 1 — Base local / Dados técnicos (resolve direto, sem IA)

Batem na base e respondem na hora. Funcionam mesmo sem o LM Studio.

| # | Situação | Pergunta de demonstração | Caminho verificado (ação) |
|---|----------|--------------------------|---------------------------|
| 1 | **Ficha técnica do jogador** | `Quem é o Jannik Sinner?` | Motor de Dados → `showed_player_info` (ficha completa) |
| 2 | **Campo específico (país)** | `qual o país do Alcaraz?` | `showed_player_country` (só a nacionalidade) |
| 3 | **Campo específico (altura)** | `qual a altura do Sinner?` | `showed_player_info` (campo pedido) |
| 4 | **Ranking Top 10** | `me mostra o ranking atp` | Query Parser + Motor → `showed_ranking` |
| 5 | **Posição específica** | `quem é o número 10 do mundo?` | `showed_player_info` (jogador na posição #10) |
| 6 | **Melhor de um país** | `qual o melhor jogador do brasil?` | `showed_country_best` |
| 7 | **Campeões de torneio** | `quem ganhou Wimbledon?` | `showed_champions` (histórico) |
| 8 | **Ficha de torneio** | `me fala sobre Roland Garros` | `showed_slam_details` (local/superfície/história) |
| 9 | **Recordes históricos** | `quem tem mais Grand Slams na história?` | Motor → `showed_trivia` (recordes) |

## 📚 Bloco 2 — Base de conhecimento (intents conversacionais)

Não é dado técnico, mas casa um intent do `knowledge_base.json` (≥ 50%).

| # | Situação | Pergunta de demonstração | Caminho verificado |
|---|----------|--------------------------|--------------------|
| 10 | **Intent — regras** | `quais são as regras do tênis?` | Base de Conhecimento → `showed_trivia` |
| 11 | **Intent — termo técnico** | `o que é um tiebreak?` | Base de Conhecimento → `showed_trivia` |
| 12 | **Intent — curiosidade aleatória** | `me conta uma curiosidade` | Base de Conhecimento → `showed_trivia` |

## 🤖 Bloco 3 — Joga na IA (tênis fora da base) · requer LM Studio

A base não cobre, mas é tênis → roteia para o LLM (passo `Jogador → IA` / `Pergunta geral → IA` + `LLM · LM Studio`).

| # | Situação | Pergunta de demonstração | Caminho verificado |
|---|----------|--------------------------|--------------------|
| 13 | **Jogador, atributo fora da base** | `qual a raquete do Alcaraz?` | `Jogador → IA` (grounding com perfil local) |
| 14 | **Head-to-head** | `quem ganha mais entre Alcaraz e Sinner?` | `Jogador → IA` |
| 15 | **Lista geral** | `cite 5 jogadores canhotos` | `Pergunta geral → IA` |
| 16 | **Contagem sobre slam** | `quantos Grand Slams o Djokovic conquistou?` | `Jogador → IA` (roteador de contagem) |

## 🔎 Bloco 4 — IA pesquisa na web (RAG Wikipedia) · requer LM Studio + `WEB_SEARCH_ENABLED=1`

| # | Situação | Pergunta de demonstração | Caminho verificado |
|---|----------|--------------------------|--------------------|
| 17 | **Curiosidade sobre jogador** | `me conta uma curiosidade sobre o João Fonseca` | `Jogador → IA` com `force_web=True` → passo `🔎 Pesquisa na web` |

A pesquisa só dispara quando há **jogador-alvo** (rota de curiosidade/atributo usa `force_web`).
O `web_search.py` busca na **Wikipedia** (intro + infobox) com **DuckDuckGo** como fallback,
e injeta o texto recuperado no *grounding* — o LLM responde **ancorado na fonte**, sem inventar.

## ⛔ Bloco 5 — Fallback final (tênis, mas nada resolve) · roteia ao LLM

| # | Situação | Pergunta de demonstração | Caminho verificado |
|---|----------|--------------------------|--------------------|
| 18 | **Fallback** | `qual a sua opinião sobre o saque no tênis moderno?` | Motor `skipped` → Base `skipped` → `Fallback (fail)` → LLM |

## 🚫 Bloco 6 — Filtro de bloqueio (off-topic / gibberish)

Bloqueio instantâneo na Camada 1, **sem custo de LLM**.

| # | Situação | Pergunta de demonstração | Caminho verificado |
|---|----------|--------------------------|--------------------|
| 19 | **Off-topic — outro esporte** | `quem ganhou a copa do mundo de futebol?` | `Filtro Off-Topic (fail)` → mensagem canned |
| 20 | **Off-topic — conhecimento geral** | `qual o prédio mais alto do mundo?` | `Filtro Off-Topic (fail)` |
| 21 | **Gibberish** | `asdfghjkl qwertzxcv` | `Filtro Off-Topic (fail)` → "não entendi" |

---

### Observações de roteamento (úteis na demonstração)

- **"quem é o treinador do Sinner?" NÃO vai para a IA** — cai na ficha. Motivo: `is_ficha_request()`
  captura "quem é" e `player_question_beyond_base()` retorna `False`. Para demonstrar a IA com
  treinador use `qual o treinador do Sinner?` (sem "quem é"). Por isso o exemplo 13 usa `raquete`.
- **IA × IA-com-web** é uma diferença interna: ambas passam pelo `Jogador → IA`. A pesquisa web só
  é forçada quando há **jogador-alvo**; listas/gerais não forçam web (evita ruído).
- Os blocos 1, 2 e 6 são **determinísticos** (independem do LM Studio) — ideais para abrir a demo.
