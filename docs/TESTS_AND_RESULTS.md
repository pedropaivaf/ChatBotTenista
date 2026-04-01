# Testes e Resultados

Bateria automatizada com 98 testes em 7 cenarios, executada 3x consecutivas com 100% de aprovacao.

---

## Resultado Geral: 98/98 (ZERO FALHAS, 3 execucoes consecutivas)

---

## Bateria 1: Ranking + Contexto de Jogador (20 turnos)

Fluxo completo: ranking → jogador → pais → estilo → troca de jogador → torneio → pais filtrado → WTA → typos → curiosidade.

| # | Input | Esperado | Resultado |
|---|-------|----------|-----------|
| 1.01 | ranking atp | Top 10 com Alcaraz, Sinner, Zverev | OK |
| 1.02 | Sinner | Ficha Jannik Sinner + Italia | OK |
| 1.03 | qual o pais dele | Sinner + Italia (focus_player) | OK |
| 1.04 | e o estilo de jogo dele? | Re-mostra Sinner | OK |
| 1.05 | Alcaraz | Ficha Carlos Alcaraz + Espanha | OK |
| 1.06 | qual o pais dele | Alcaraz + Espanha (focus atualizado) | OK |
| 1.07 | gosto de roland garros | Campeoes RG (torneio prioridade > jogador) | OK |
| 1.08 | e wimbledon? | Campeoes Wimbledon | OK |
| 1.09 | melhor jogador do brasil atualmente | Fonseca + Brasil | OK |
| 1.10 | Fonseca | Ficha Joao Fonseca | OK |
| 1.11 | qual o pais dele | Fonseca + Brasil | OK |
| 1.12 | ranking wta | Top 10 WTA com Sabalenka | OK |
| 1.13 | Sabalenka | Ficha Aryna Sabalenka | OK |
| 1.14 | qual o pais dela | Sabalenka + Bielorrussia | OK |
| 1.15 | Medevedev (typo) | Daniil Medvedev via fuzzy | OK |
| 1.16 | Tsitipas (typo) | Stefanos Tsitsipas via fuzzy | OK |
| 1.17 | me conta uma curiosidade | Curiosidade (sem falso positivo) | OK |
| 1.18 | gosto do us open | Campeoes US Open | OK |
| 1.19 | melhor tenista espanhol | Melhores da Espanha + Alcaraz | OK |
| 1.20 | quem ganhou o australian open | Campeoes Australian Open | OK |

---

## Bateria 2: Trivia + Contexto Aberto (20 turnos)

Fluxo conversacional: saudacao → superficies → cor da bolinha → regras → curiosidade → torneio → jogador → pais → WTA.

| # | Input | Esperado | Resultado |
|---|-------|----------|-----------|
| 2.01 | oi | Saudacao sobre Tenis | OK |
| 2.02 | quais os tipos de quadra? | Saibro, Grama, Piso Duro | OK |
| 2.03 | qual a cor da bolinha | Amarelo optico (sem Coria/Coric) | OK |
| 2.04 | quais as regras do tenis? | 15, 30, 40, Deuce | OK |
| 2.05 | me conta uma curiosidade | Curiosidade (sem falso positivo) | OK |
| 2.06 | roland garros | Campeoes RG (open_topic resolve) | OK |
| 2.07 | prefiro saibro | Resposta sobre saibro | OK |
| 2.08 | quem e o Djokovic? | Ficha Djokovic | OK |
| 2.09 | e o Nadal? | Ficha Nadal | OK |
| 2.10 | tenistas brasileiros | Fonseca + Haddad (sem Shapovalov) | OK |
| 2.11 | Fonseca | Ficha Joao Fonseca | OK |
| 2.12 | qual a idade dele | Re-mostra ficha Fonseca (idade) | OK |
| 2.13 | como funciona o ranking da atp? | Historia da ATP 1972 | OK |
| 2.14 | obrigado | Despedida | OK |
| 2.15 | oi de novo | Nova saudacao | OK |
| 2.16 | ranking wta | Top 10 WTA | OK |
| 2.17 | Swiatek | Ficha Iga Swiatek + Polonia | OK |
| 2.18 | qual o pais dela | Swiatek + Polonia | OK |
| 2.19 | quem ganhou wimbledon | Campeoes Wimbledon | OK |
| 2.20 | como o tenis surgiu? | Historia do tenis + Inglaterra | OK |

---

## Bateria 3: Typos, Edge Cases e Filtragem por Pais (12 testes)

| # | Input | Esperado | Resultado |
|---|-------|----------|-----------|
| 3.01 | Danill Medevedev | Daniil Medvedev (fuzzy) | OK |
| 3.02 | Tsitipas | Stefanos Tsitsipas (fuzzy) | OK |
| 3.03 | Alcaras | Carlos Alcaraz (fuzzy) | OK |
| 3.04 | jogadores brasileiros | Fonseca + Brasil (sem Shapovalov) | OK |
| 3.05 | melhor jogador da italia | Italia + Sinner | OK |
| 3.06 | melhor jogador americano | EUA | OK |
| 3.07 | futebol | Bloqueado (off-topic) | OK |
| 3.08 | qual a melhor raquete | Resposta sobre raquetes | OK |
| 3.09 | o que e um Grand Slam? | 4 torneios | OK |
| 3.10 | quem e Roger Federer? | Federer + 20 titulos | OK |
| 3.11 | quem e Carlos Alcaraz? | Alcaraz | OK |
| 3.12 | receita de bolo | Bloqueado (off-topic) | OK |

---

## Bateria 4: Queries Diretas sem Contexto (8 testes)

| # | Input | Resultado |
|---|-------|-----------|
| 4.01 | ranking atp | OK - Top 10 ATP |
| 4.02 | ranking wta | OK - Top 10 WTA |
| 4.03 | quem e Jannik Sinner? | OK - Ficha completa |
| 4.04 | quem ganhou o us open | OK - Campeoes US Open |
| 4.05 | melhor jogador do brasil | OK - Fonseca + Haddad |
| 4.06 | qual a cor da bolinha de tenis | OK - Amarelo optico |
| 4.07 | quais as regras basicas | OK - 15, 30, 40 |
| 4.08 | me conta uma curiosidade | OK - Curiosidade |

---

## Bateria 5: Fluxo Longo WTA (20 turnos)

| # | Input | Resultado |
|---|-------|-----------|
| 5.01 | ranking wta | OK - Top 10 WTA |
| 5.02 | Gauff | OK - Coco Gauff |
| 5.03 | qual o pais dela | OK - Gauff + EUA |
| 5.04 | Swiatek | OK - Iga Swiatek |
| 5.05 | qual o pais dela | OK - Swiatek + Polonia |
| 5.06 | gosto de wimbledon | OK - Campeoes Wimbledon |
| 5.07 | e o australian open? | OK - Campeoes AO |
| 5.08 | melhor jogadora do brasil | OK - Haddad Maia |
| 5.09 | quais as regras do tenis | OK - 15, 30, 40 |
| 5.10 | prefiro grama | OK - Resposta sobre grama |
| 5.11 | ranking atp | OK - Top 10 ATP |
| 5.12 | Djokovic | OK - Novak Djokovic |
| 5.13 | qual o pais dele | OK - Djokovic + Servia |
| 5.14 | Zverev | OK - Alexander Zverev |
| 5.15 | qual o pais dele | OK - Zverev + Alemanha |
| 5.16 | me conta uma curiosidade | OK - Sem falso positivo |
| 5.17 | us open | OK - Campeoes US Open |
| 5.18 | quem e o Sinner | OK - Jannik Sinner |
| 5.19 | qual a idade dele | OK - Ficha Sinner (idade) |
| 5.20 | obrigado | OK - Despedida |

---

## Bateria 6: Detalhes do Jogador em Foco (10 testes)

| # | Input | Resultado |
|---|-------|-----------|
| 6.01 | quem e o Alcaraz? | OK - Carlos Alcaraz |
| 6.02 | qual a idade dele | OK - Alcaraz (22 anos) |
| 6.03 | qual o pais dele | OK - Alcaraz + Espanha |
| 6.04 | qual o estilo dele | OK - Alcaraz |
| 6.05 | ranking atp | OK - Top 10 (nao confunde com ficha) |
| 6.06 | Djokovic | OK - Novak Djokovic |
| 6.07 | qual a idade dele | OK - Djokovic |
| 6.08 | qual o pais dele | OK - Djokovic + Servia |
| 6.09 | quem ganhou roland garros | OK - Campeoes RG |
| 6.10 | e o us open? | OK - Campeoes US Open |

---

## Bateria 7: Perguntas Genericas sobre Tenis (8 testes)

| # | Input | Resultado |
|---|-------|-----------|
| 7.01 | o que e um ace no tenis? | OK - Regras |
| 7.02 | qual a origem do tenis? | OK - Inglaterra |
| 7.03 | o que e a ATP? | OK - ATP 1972 |
| 7.04 | piso duro | OK - Superficies |
| 7.05 | grama | OK - Grama |
| 7.06 | quem e o numero 1 do mundo | OK - Carlos Alcaraz |
| 7.07 | melhor jogador da franca | OK - Franca |
| 7.08 | melhor jogador da argentina | OK - Argentina |

---

## Bugs Corrigidos Durante os Testes

| Bug | Causa | Correcao |
|-----|-------|----------|
| "cor da bolinha" → Coria/Coric | Fuzzy match "cor" vs "coria" (0.86) | Stop words: adicionou "cor", "bola", "bolinha", etc |
| "jogadores brasileiros" → Shapovalov | Fuzzy match "tenis" vs "denis" (0.80) | Stop words: adicionou "tenis", "jogador", etc |
| "me conta curiosidade" → Lestienne | Fuzzy match "conta" vs "constant" (0.77) | Stop words: adicionou "conta", "curiosidade" |
| "dela" → Elena Rybakina | Fuzzy match "dela" vs "elena" (0.67) | Stop words: adicionou "dela", "dele", "ela", etc |
| "qual a idade dele" → nacionalidade | Intent match 60% com "Qual a nacionalidade dele?" | PLAYER_INFO_KEYWORDS detecta "idade" no contexto player_detail |
| "ranking wta" → ficha jogador | "rank" dentro de "ranking" acionava PLAYER_INFO_KEYWORDS | Removeu "rank" e "pontos" de PLAYER_INFO_KEYWORDS |
| "qual a melhor raquete" → Alcaraz | wants_best=True sem contexto de jogador | Superlativo global precisa de palavras de contexto ("jogador", "mundo") |
| open_topic fuzzy match | Fuzzy contra 200+ jogadores com threshold 0.75 | open_topic usa apenas extract_entities (match exato) |

---

## Como Executar os Testes

```bash
python run_tests.py
```

Os testes usam o test client do Flask (sem navegador) e verificam 98 cenarios em 7 baterias, validando que nenhuma regressao foi introduzida.
