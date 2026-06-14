# Testes e Resultados

Suíte automatizada com **312 testes em 23 baterias**.

**Resultado atual: 312/312 — ZERO FALHAS.**

```bash
python run_tests.py
```

> Os testes forçam `LLM_ENABLED=0` (determinismo) — **não dependem do LM Studio**.
> **Regra de ouro:** rode e garanta 312/312 **antes de qualquer commit**.

---

## As 23 baterias

| # | Bateria | Foco |
|---|---------|------|
| 1 | Ranking ATP + Contexto Completo | Fluxo de 20 turnos: ranking → jogador → país → estilo → troca → torneio → WTA → typos |
| 2 | Trivia + Contexto Aberto | 20 turnos conversacionais (open_topic) |
| 3 | Typos e Fuzzy Matching | "Medevedev", "Tsitipas", "Alcaras" → jogador correto |
| 4 | Queries Diretas sem Contexto | Sessões independentes (ranking, jogador, torneio, regras) |
| 5 | Fluxo WTA Completo | 20 turnos no circuito feminino (pronome "dela") |
| 6 | Jogador em Foco — Detalhes e Troca | idade/país/estilo + troca de foco |
| 7 | Perguntas Genéricas sobre Tênis | Ace, ATP, superfícies, nº 1, países |
| 8 | Reações Empáticas | 13 atributos técnicos (forehand, saque, mental…) |
| 9 | Falsos Positivos | "cor da bolinha" ≠ Coria, "amarela" ≠ Korpatsch, gentílicos |
| 10 | Filtragem por País | Brasil, Espanha, Itália, EUA… + auto-feminino→WTA |
| 11 | Torneios — Detecção Direta | Grand Slams direto e contextual |
| 12 | Stress Test | 20 turnos misturando tudo |
| 13 | Detalhes dos Grand Slams | "me fala sobre wimbledon" → ficha vs "quem ganhou" → campeões |
| 14 | Fluxo 20 turnos com Grand Slams | Detalhes + campeões + troca de torneio |
| 15 | Torneios ATP Masters 1000 | Indian Wells, Monte Carlo, Madrid… (não colide com jogador) |
| 16 | Torneios ATP 500 + João Fonseca | Rio Open, Barcelona… + Fonseca nos campeões |
| 17 | Último ganhador via contexto | "quem foi o campeão?" puxa torneio do contexto |
| 18 | Listagem de torneios | "quais são os torneios?" → lista por categoria |
| 19 | Respostas específicas por campo | altura/títulos/idade isolados (via pronome) |
| 20 | Recordes, GOAT, Lendas, Regras, WTA | knowledge_base ampliada (49 intents) |
| 21 | Posição no ranking + recordes | "número 20 do mundo", "mais grand slams" → Djokovic |
| 22 | Off-topic → AVISAR E BLOQUEAR | **bot fechado em tênis**: off-topic bloqueado, nunca vai ao LLM |
| 23 | Pergunta factual/recorde mencionando torneio | NÃO vira "campeões genéricos" — segue para recordes/LLM |

---

## Bateria 22 — Off-topic (bot fechado em tênis)

Confirma o roteamento atual: perguntas fora de tênis são **bloqueadas** com aviso, sem
devolver dados do jogador em foco e **sem** acionar o LLM. Inclui não-regressões: follow-up
legítimo de altura ainda funciona; sobrenome após ranking ainda resolve jogador; "quem é o
batman?" não casa com jogador.

## Bateria 23 — Perguntas factuais que mencionam torneio

Cobre o bug em que "Quantos Grand Slams o Boris Becker conquistou?" e "Quem foi o primeiro
tenista a completar o Golden Slam?" caíam em **campeões genéricos**. Após a correção (3
camadas), seguem para LLM/recordes; pedido legítimo ("quem ganhou os grand slams") continua
mostrando campeões.

| # | Cenário | Esperado |
|---|---------|----------|
| 23.01 | "Quantos Grand Slams o Boris Becker conquistou?" (após ranking) | NÃO "Campeões de Grand Slam" |
| 23.02 | "Quem foi o primeiro tenista a completar o Golden Slam?" (após curiosidade) | NÃO campeões, NÃO #1 (Sinner) |
| 23.03 | "Quantos Grand Slams o Boris Becker conquistou?" (após ficha de jogador) | NÃO "Campeões de Grand Slam" |
| 23.04 | "quem ganhou os grand slams" (não-regressão) | mostra **Campeões** |

---

## Bugs corrigidos (histórico)

### Núcleo de PLN / contexto
| Bug | Causa | Correção |
|-----|-------|----------|
| "australian open" → país Austrália | parser detecta "australia" no nome do torneio | Remove torneios antes de detectar país |
| "melhor jogadora do mundo" → ATP | feminino não detectado no superlativo | Palavras femininas → WTA |
| "bola amarela" → Korpatsch / "cor" → Coria | fuzzy com threshold | Stop words: amarela, cor, bola, bolinha |
| "mais" → Mai Hontama | stem "mai" (3 chars) | Stem mínimo de 4 caracteres |
| "brasileiras" → gibberish | bigramas válidos faltando | Lista de bigramas expandida |
| Reações/elogios genéricos no fallback | não reconhecidos | REACTION_KEYWORDS + GENERIC_PRAISE |

### Correções recentes (v3)
| Bug | Causa | Correção |
|-----|-------|----------|
| ATP só com 50 jogadores no startup | timeout da página 2 + `>=50` contava como sucesso | `_http_get` com retry; sucesso só com 100; cache não trava parcial (`api_client.py`) |
| Factual "quantos grand slams o X" → campeões | árvore captura por "slam" | `_is_records_or_fact_question` + 3 guardas (`decision_tree.py`) |
| "primeiro a completar…" → #1 do ranking | "primeiro" lido como superlativo | guarda no atalho superlativo (`app.py`, Fix A) |
| "quantos … slam" → definição (intent 100%) | pattern curto "grand slam" | roteador de contagem → LLM (`app.py`, Fix B) |

---

## Cobertura

- **Contexto**: fluxos de 20 turnos, pronomes, troca de foco, follow-ups.
- **Robustez**: typos, falsos positivos, gibberish, off-topic.
- **Domínio**: rankings, jogadores (290), Grand Slams, Masters 1000/500/Finals, recordes, lendas.
- **Híbrido**: roteamento base × LLM validado com `LLM_ENABLED=0` (degradação graciosa).
