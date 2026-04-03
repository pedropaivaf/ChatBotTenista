# Testes e Resultados

Bateria automatizada com **170 testes em 12 baterias**, executada 3x consecutivas com 100% de aprovacao.

**Resultado: 170/170 — ZERO FALHAS (3 execucoes, 510 testes totais)**

---

## Baterias de Teste

### Bateria 1: Ranking ATP + Contexto Completo (20 turnos)
Fluxo: ranking → jogador → pais → estilo → troca jogador → torneio → pais filtrado → WTA → typos → curiosidade.

| # | Input | Resultado |
|---|-------|-----------|
| 1.01 | ranking atp | OK — Top 10 ATP |
| 1.02 | Sinner | OK — Ficha Jannik Sinner (contexto ranking) |
| 1.03 | qual o pais dele | OK — Italia (focus=Sinner) |
| 1.04 | e o estilo de jogo dele? | OK — Re-mostra Sinner |
| 1.05 | Alcaraz | OK — Ficha Alcaraz (troca de foco) |
| 1.06 | qual o pais dele | OK — Espanha (focus=Alcaraz) |
| 1.07 | gosto de roland garros | OK — Campeoes RG |
| 1.08 | e wimbledon? | OK — Campeoes Wimbledon |
| 1.09 | melhor jogador do brasil atualmente | OK — Fonseca + Haddad |
| 1.10 | Fonseca | OK — Ficha Joao Fonseca |
| 1.11 | qual o pais dele | OK — Brasil |
| 1.12 | ranking wta | OK — Top 10 WTA |
| 1.13 | Sabalenka | OK — Ficha Sabalenka |
| 1.14 | qual o pais dela | OK — Bielorrussia |
| 1.15 | Medevedev (typo) | OK — Daniil Medvedev (fuzzy) |
| 1.16 | Tsitipas (typo) | OK — Stefanos Tsitsipas (fuzzy) |
| 1.17 | me conta uma curiosidade | OK — Sem falso positivo |
| 1.18 | gosto do us open | OK — Campeoes US Open |
| 1.19 | melhor tenista espanhol | OK — Espanha + Alcaraz |
| 1.20 | quem ganhou o australian open | OK — Campeoes AO |

### Bateria 2: Trivia + Contexto Aberto (20 turnos)
Fluxo conversacional: saudacao → superficies → cor bolinha → regras → curiosidade → torneio → saibro → jogadores → pais → WTA.

| # | Input | Resultado |
|---|-------|-----------|
| 2.01–2.20 | 20 interacoes | **20/20 OK** |

Destaques: "cor da bolinha" → amarelo (sem Coria), "roland garros" apos trivia → campeoes RG, "qual a idade dele" → ficha jogador em foco.

### Bateria 3: Typos e Fuzzy Matching (12 testes)

| Input com Typo | Resultado |
|---------------|-----------|
| Danill Medevedev | OK — Daniil Medvedev |
| Tsitipas | OK — Stefanos Tsitsipas |
| Alcaras | OK — Carlos Alcaraz |
| jogadores brasileiros | OK — Fonseca (sem Shapovalov) |
| melhor jogador da italia | OK — Sinner |
| futebol | OK — Bloqueado |
| receita de bolo | OK — Bloqueado |

### Bateria 4: Queries Diretas sem Contexto (8 testes)
Todas sessoes independentes: ranking atp, ranking wta, Sinner, US Open, Brasil, cor bolinha, regras, curiosidade. **8/8 OK.**

### Bateria 5: Fluxo WTA Completo (20 turnos)
WTA ranking → Gauff → pais → Swiatek → pais → Wimbledon → AO → Brasil → regras → grama → ATP → Djokovic → pais → Zverev → pais → curiosidade → US Open → Sinner → idade → despedida. **20/20 OK.**

### Bateria 6: Jogador em Foco — Detalhes e Troca (10 testes)
Alcaraz → idade → pais → estilo → ranking → Djokovic → idade → pais → RG → US Open. **10/10 OK.**

### Bateria 7: Perguntas Genericas (8 testes)
Ace, origem, ATP, piso duro, grama, numero 1 mundo, Franca, Argentina. **8/8 OK.**

### Bateria 8: Reacoes Empaticas a Atributos Tecnicos (15 testes)

| # | Cenario | Resultado |
|---|---------|-----------|
| 8.01 | resistencia do Djokovic | OK — Reacao + ficha |
| 8.02 | forehand do Alcaraz | OK — Reacao + ficha |
| 8.03 | backhand do Djokovic | OK — Reacao + ficha |
| 8.04 | saque da Sabalenka (WTA) | OK — Reacao + ficha (pronome ela) |
| 8.05 | forca mental do Sinner | OK — Reacao + ficha |
| 8.06 | velocidade do Alcaraz | OK — Reacao + ficha |
| 8.07 | jogo agressivo do Medvedev | OK — Reacao + ficha |
| 8.08 | defesa do Djokovic | OK — Reacao + ficha |
| 8.09 | voleio do Federer | OK — Reacao + ficha |
| 8.10 | pais + saque (msg composta) | OK — Reacao + pais |
| 8.11 | resistencia + saibro do Nadal | OK — Reacao + ficha |
| 8.12 | pais sem opiniao | OK — Sem reacao indevida |
| 8.13 | ranking sem opiniao | OK — Sem reacao indevida |
| 8.14 | curiosidade sem opiniao | OK — Sem reacao indevida |
| 8.15 | regras sem opiniao | OK — Sem reacao indevida |

### Bateria 9: Falsos Positivos — Garantir que NAO confunde (15 testes)

| # | Input | Resultado |
|---|-------|-----------|
| 9.01 | cor da bolinha | OK — Amarelo (sem Coria) |
| 9.02 | bola de tenis amarela | OK — Amarelo (sem Korpatsch) |
| 9.03 | como funciona a pontuacao | OK — 15/30/40 |
| 9.04 | tipo de quadra | OK — Saibro (sem Shapovalov) |
| 9.05 | regras basicas do tenis | OK — Sem falso positivo |
| 9.06 | jogadores brasileiros | OK — Fonseca (sem Denis) |
| 9.07 | jogadoras brasileiras | OK — Haddad |
| 9.08 | tenistas do brasil | OK — Brasil |
| 9.09–9.11 | torneio/set/raquete | OK — Sem falso positivo |
| 9.12–9.15 | politica/basquete/copa/receita | OK — Bloqueado |

### Bateria 10: Filtragem por Pais (12 testes)

| Pais | Resultado |
|------|-----------|
| Brasil | OK — Fonseca |
| Espanha | OK — Alcaraz |
| Italia | OK — Sinner |
| EUA | OK |
| Argentina | OK |
| Franca | OK |
| Russia | OK |
| Alemanha | OK — Zverev |
| Servia | OK — Djokovic |
| Polonia | OK — Swiatek |
| Numero 1 mundo (masc) | OK — Alcaraz |
| Melhor jogadora mundo (fem) | OK — Sabalenka |

### Bateria 11: Torneios — Deteccao Direta (10 testes)
Australian Open, Roland Garros, Wimbledon, US Open (direto e contextual). **10/10 OK.**
Destaque: "quem ganhou o australian open" nao confunde mais com pais Australia.

### Bateria 12: Stress Test — 20 turnos misturando TUDO
oi → ranking → Sinner → forehand (reacao) → pais → RG → Brasil → Fonseca → velocidade (reacao) → ranking WTA → Sabalenka → saque (reacao) → pais → Medvedev (typo) → defesa (reacao) → regras → cor bolinha → numero 1 → futebol (bloqueado) → despedida. **20/20 OK.**

---

## Bugs Corrigidos

| Bug | Causa | Correcao |
|-----|-------|----------|
| "australian open" → pais Australia | query_parser detecta "australia" no nome do torneio | Remove nomes de torneios antes de detectar pais |
| "melhor jogadora do mundo" → Alcaraz (ATP) | Feminino nao detectado no superlativo global | Palavras femininas (jogadora) selecionam WTA |
| "bola de tenis amarela" → Korpatsch | Fuzzy "amarela" vs "tamara" = 0.77 | Stop words: amarelo, amarela |
| "cor da bolinha" → Coria | Fuzzy "cor" vs "coria" = 0.86 | Stop words: cor, bola, bolinha |
| "gosto mais de jogar no saibro" → Mai Hontama | Stem "mai" (de "mais") = 3 chars matchava jogadora | Validacao minima de 4 caracteres no stem |
| "brasileiras" → gibberish | Bigramas "br", "ei", "si" nao estavam na lista | Expandir lista de bigramas validos em portugues |
| "volei" bloqueava "voleio" | Keyword "volei" no filtro off-topic | Remover "volei", manter "voleibol" e "vôlei" |
| Denis Shapovalov retornado como brasileiro | Fuzzy match "brasil" vs "Denis" | Stop words + filtro de gentilicos |
| Reacoes empaticas inexistentes | Bot ignorava opiniao do usuario | REACTION_KEYWORDS para 13 atributos tecnicos |
| Follow-ups repetitivos | Sempre a mesma pergunta | Follow-ups abertos que mudam de tema |
| Elogios genericos → fallback | "um dos melhores" nao reconhecido | GENERIC_PRAISE com 16+ expressoes |

---

## Como Executar

```bash
python run_tests.py
```

170 testes, 12 baterias, ~30 segundos de execucao.
