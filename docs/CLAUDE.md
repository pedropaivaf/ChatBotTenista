# Guia de Treino e Aperfeicoamento da IA — ChatBot Tenista

Este documento e o manual definitivo para continuar treinando, testando e aperfeicoando
o ChatBot de Tenis. Ele descreve **todos os comportamentos esperados**, as regras da arvore
de decisao, o sistema de reacoes empaticas, o pipeline de processamento e como adicionar
novas funcionalidades sem quebrar o que ja funciona.

**Antes de qualquer mudanca, rode `python run_tests.py` e garanta 170/170.**

---

## 1. Visao Geral do Pipeline

Cada mensagem do usuario passa por estas etapas, nesta ordem exata:

```
[1] Tokenizacao + Stemming (NLTK)
[2] Filtro Off-Topic (60+ keywords)
[3] Deteccao de Gibberish (vogais, consoantes, bigramas)
[4] Arvore de Decisao (contexto, follow-ups, reacoes)
[5] Query Parser (pais, temporal, superlativo, circuito)
[6] Dados Tecnicos (ranking, jogadores, campeoes)
[7] Deteccao de Torneio direto
[8] Intent Matching (knowledge_base.json, 50% threshold)
[9] Fallback (log em unrecognized_queries.json)
[10] Enrich (adiciona follow-up aberto + atualiza sessao)
```

**Regra de ouro**: Se uma etapa resolve a mensagem, as seguintes sao puladas.
A arvore de decisao (etapa 4) tem prioridade sobre tudo exceto off-topic/gibberish.

---

## 2. Arvore de Decisao — Branches e Prioridades

A arvore esta em `decision_tree.py`, metodo `try_contextual_response()`.
Branches sao avaliadas nesta ordem:

### Branch 1: Torneio no Contexto
- **Condicao**: Ha `pending_follow_up` e a mensagem contem nomes de torneios.
- **Comportamento**: Retorna campeoes do torneio detectado.
- **Exemplo**: Apos ranking, usuario diz "gosto de roland garros" → campeoes RG.

### Branch 2: Jogador do Contexto
- **Condicao**: Ha `pending_follow_up` de tipo ranking, country ou open_topic.
- **Comportamento**: Tenta resolver o nome do jogador via:
  1. Match exato contra `mentioned_entities.players`
  2. Fuzzy matching contra todos os jogadores conhecidos
- **Exemplo**: Apos "ranking atp", usuario diz "Alcaraz" → ficha Carlos Alcaraz.

### Branch 3: Detalhe do Jogador em Foco
- **Condicao**: Ha `pending_follow_up == "player_detail"` e `focus_player` definido.
- **Sub-branches** (em ordem):
  1. **Comparacao**: "comparar com Djokovic" → ficha do outro jogador.
  2. **Pais**: "qual o pais dele" → nacionalidade + bandeira.
  3. **Estilo**: "qual o estilo dele" → re-mostra ficha.
  4. **Reacao empatica**: "o forehand dele e incrivel" → reacao + ficha.
  5. **Elogio generico**: "um dos melhores" → reacao positiva.
  6. **Info**: "qual a idade dele" → re-mostra ficha.

### Branch 4: Topico Aberto
- **Condicao**: `pending_follow_up == "open_topic"` (apos trivia).
- **Comportamento**: Aceita tanto jogador quanto torneio como resposta.

### Trace Visual
Cada branch gera um node no trace:
```python
{"branch": "Torneio no Contexto", "matched": True/False, "icon": "🏆", "detail": "..."}
```
O trace e enviado ao frontend para visualizacao no painel lateral.

---

## 3. Sistema de Reacoes Empaticas

Quando o usuario expressa opiniao sobre um atributo tecnico de um jogador em foco,
o bot responde com uma reacao empatica antes de mostrar dados.

### Atributos Reconhecidos (REACTION_KEYWORDS)

| Palavra-chave | Exemplo de Reacao |
|---------------|-------------------|
| resistencia | "A resistencia {dele_dela} e realmente absurda! 🎾" |
| forehand | "O forehand {dele_dela} e uma arma mortal! 🔥" |
| backhand | "O backhand {dele_dela} e de outro nivel! 💪" |
| saque | "O saque {dele_dela} e devastador! ⚡" |
| mental | "A forca mental {dele_dela} e impressionante! 🧠" |
| velocidade | "A velocidade {dele_dela} na quadra e incrivel! 💨" |
| movimentacao | "A movimentacao {dele_dela} e fantastica!" |
| agressivo | "O jogo agressivo {dele_dela} e eletrizante! 🔥" |
| defesa | "A defesa {dele_dela} e incrivel!" |
| voleio | "O voleio {dele_dela} e preciso!" |
| rapidez | "A rapidez {dele_dela} na quadra e incrivel! 💨" |
| rapido | "A velocidade {dele_dela} e impressionante! 💨" |
| potencia | "A potencia {dele_dela} e absurda! 💥" |
| consistencia | "A consistencia {dele_dela} e impressionante!" |
| inteligencia | "A inteligencia tatica {dele_dela} e de outro nivel! 🧠" |
| tatica | "A tatica {dele_dela} e brilhante! 🧠" |

### Pronomes Genero-Corretos
- **ATP** (masculino): ele/dele
- **WTA** (feminino): ela/dela
- Determinado por: ranking WTA + lista `wta_legends` em `_get_pronoun()`.

### Regras para Reacoes
1. So reage quando ha `focus_player` definido.
2. So reage quando a mensagem contem uma keyword de REACTION_KEYWORDS.
3. Reacao e seguida de ficha completa do jogador.
4. Sem focus_player, NAO gera reacao (evita reacao a perguntas genericas).

### Como Adicionar Novo Atributo
1. Adicione a keyword e reacoes em `REACTION_KEYWORDS` no `decision_tree.py`.
2. Use placeholders `{dele_dela}`, `{ele_ela}`, `{Ele_Ela}` para pronomes.
3. Rode os testes para garantir que nao ha falso positivo.

---

## 4. Elogios Genericos (GENERIC_PRAISE)

Quando o usuario faz um elogio generico ao jogador em foco, o bot reconhece
como feedback positivo ao inves de cair no fallback.

### Expressoes Reconhecidas
```
melhores, o melhor, o maior, um dos maiores, um dos melhores,
incrivel, sensacional, fantastico, lenda, lendario, goat,
fera, monstro, demais, muito bom, espetacular, fenomenal,
genial, absurdo, impressionante, fora de serie
```

### Comportamento Esperado
- **Input**: "um dos melhores" (apos ficha do Federer)
- **Output**: Reacao positiva ("Concordo! Ele e realmente especial! 🎾") + follow-up aberto.
- **NAO deve**: Cair no fallback ou mostrar "nao entendi".

### Como Adicionar Novo Elogio
1. Adicione a expressao na lista `GENERIC_PRAISE` em `decision_tree.py`.
2. Use sempre minusculo, sem acentos se necessario (o match e case-insensitive).
3. Rode testes para verificar.

---

## 5. Follow-ups — Regras e Padroes

### Principios
1. **Sempre 1 pergunta por resposta** — nunca 2+ perguntas.
2. **Sempre abre para outro tema** — nunca repete o mesmo assunto.
3. **Nunca sim/nao** — perguntas abertas que convidam exploracao.

### Mapa de Follow-ups (FOLLOW_UPS)

| Topico + Acao | Follow-up |
|---------------|-----------|
| ranking + showed_ranking | "Sobre qual desses jogadores voce quer saber mais?" |
| ranking + showed_country_ranking | "Quer ver a ficha de algum deles ou explorar outro tema?" |
| player + showed_player_info | "Quer explorar algum torneio, ver o ranking ou saber sobre outro jogador?" |
| player + showed_player_from_context | "Quer ver algum Grand Slam ou saber sobre outro jogador?" |
| player + showed_player_country | "Posso te contar sobre torneios, ranking ou outros jogadores!" |
| player + showed_country_best | "Quer ver a ficha de algum desses ou explorar outro tema?" |
| tournament + showed_champions | "Quer saber sobre algum desses jogadores ou ver outro torneio?" |
| surface + showed_surface_info | "Quer saber sobre algum jogador ou torneio?" |
| trivia + showed_trivia | "Sobre o que mais quer conversar? Jogadores, torneios, curiosidades..." |

### Como Adicionar Follow-up
1. Identifique a tupla `(topico, bot_action)`.
2. Adicione em `FOLLOW_UPS` no `decision_tree.py`.
3. A pergunta deve **mudar de tema** (jogador → torneio, torneio → ranking, etc.).

---

## 6. Fuzzy Matching — Tolerancia a Typos

### Configuracao
- **Algoritmo**: `difflib.SequenceMatcher`
- **Threshold**: 0.75 (75% de similaridade)
- **Stem minimo**: 4 caracteres (evita matches curtos como "mai" → "Mai Hontama")

### Stop Words (100+)
Palavras comuns em portugues excluidas do fuzzy para evitar falsos positivos:
```
de, do, da, dos, das, o, a, os, as, um, uma, e, que, qual, como,
cor, bola, bolinha, amarelo, amarela, tipo, quadra, piso, regra, basica,
jogo, jogar, dele, dela, mais, muito, gosto...
```

### Falsos Positivos Historicos Resolvidos
| Input | Match Errado | Causa | Correcao |
|-------|-------------|-------|----------|
| "amarela" | Tamara Korpatsch (0.77) | fuzzy com threshold | Stop word: amarela |
| "cor" | Coria (0.86) | fuzzy com threshold | Stop word: cor |
| "brasileiros" | Denis Shapovalov | gentilico confundido | Stop word + filtro |
| "mai" (stem de "mais") | Mai Hontama | stem curto (3 chars) | Min 4 chars |
| "dela" | Elena Rybakina | fuzzy "dela" vs "Elena" | Stop word: dela |

### Como Resolver Novo Falso Positivo
1. Identifique a palavra que causa o match errado.
2. Adicione em `_STOP_WORDS` no `decision_tree.py`.
3. Se for stem curto (< 4 chars), ja esta protegido automaticamente.
4. Rode `python run_tests.py` para confirmar.

---

## 7. Filtro Off-Topic (60+ keywords)

### Categorias Bloqueadas
- **Esportes**: futebol, basquete, nba, f1, golf, boxe, mma, ufc, voleibol, rugby...
- **Times/Jogadores**: flamengo, corinthians, messi, neymar, lebron, jordan...
- **Outros**: bitcoin, politica, receita, filme, anime, musica, programacao, religiao...

### Resposta Padrao
"Desculpe, mas eu respiro apenas Tenis! 🎾 Pergunte sobre jogadores, rankings ou torneios!"

### Como Adicionar Nova Keyword Off-Topic
1. Adicione na lista `OFF_TOPIC_KEYWORDS` em `app.py`.
2. Use minusculo, sem acentos alternativos se necessario.
3. **Cuidado**: Nao adicione palavras que possam conflitar com tenis:
   - "volei" conflita com "voleio" → use "voleibol" em vez.
   - "jogo" e usado em tenis → NAO adicionar.
4. Rode testes (Bateria 9 cobre falsos positivos).

---

## 8. Deteccao de Gibberish

### Criterios (em `app.py`, funcao `is_gibberish`)
1. **Mensagens curtas** (< 3 caracteres apos limpar): Rejeitadas.
2. **Ratio de vogais** < 15%: "bcdfghjk" → gibberish.
3. **Consoantes consecutivas** >= 5: "asdfgh" → gibberish.
4. **Bigramas improvaveis**: Se a maioria dos bigramas nao existe em portugues.

### Bigramas Validos
Lista expandida inclui combinacoes comuns do portugues:
```
br, cr, dr, fr, gr, pr, tr, bl, cl, fl, gl, pl,
ch, lh, nh, qu, gu, rr, ss, sc, sp, st,
ei, ai, ou, ao, ão, oe, oi, ui, eu, au, io, ia, ie...
```

### Protecao contra Falsos Positivos
- "brasileiras" → Valida (bigramas br, ei, si todos validos).
- "Tsitsipas" → Valida (nome de jogador, nao passa pelo gibberish porque e resolvido antes).
- Nomes de jogadores NAO passam pelo gibberish se resolvidos na arvore de decisao.

---

## 9. Query Parser — Modificadores Estruturados

### Modificadores Detectados (`query_parser.py`)

| Modificador | Exemplos | Campo |
|-------------|----------|-------|
| Pais | "do brasil", "brasileiro", "italiana" | `country_filter` |
| Temporal | "atualmente", "hoje", "agora" | `is_current` |
| Superlativo | "melhor", "top", "numero 1", "lider" | `wants_best` |
| Circuito | "atp", "masculino", "wta", "feminino" | `circuit` |
| Limite | "top 5", "top 20" | `limit` |

### Deteccao Automatica de Genero
Palavras femininas auto-selecionam circuito WTA:
- "jogadora", "tenista" (contexto feminino), "melhor jogadora"
- "brasileiras", "espanholas", "italianas" (gentilico feminino)

### Protecao de Torneios
Nomes de torneios sao removidos da mensagem ANTES da deteccao de pais:
- "australian open" → remove "australian" → nao detecta Australia.
- "us open" → remove "us" → nao detecta EUA.

---

## 10. Sessao e Contexto (20 turnos)

### Estrutura da Sessao
```python
{
    "turn_count": 0-20,
    "current_topic": "ranking" | "player" | "tournament" | "trivia" | None,
    "current_circuit": "ATP" | "WTA" | None,
    "focus_player": "Carlos Alcaraz" | None,
    "pending_follow_up": "player_from_ranking" | "player_detail" | "open_topic" | None,
    "last_bot_action": "showed_ranking" | "showed_player_info" | ...,
    "mentioned_entities": {"players": [], "tournaments": [], "countries": []},
}
```

### Tipos de pending_follow_up
| Tipo | Significado | O que aceita como resposta |
|------|------------|---------------------------|
| `player_from_ranking` | Usuario viu ranking, pode mencionar jogador | Nome de jogador |
| `player_from_country_ranking` | Usuario viu ranking filtrado por pais | Nome de jogador |
| `player_detail` | Usuario viu ficha de jogador | Atributo, elogio, pais, estilo |
| `open_topic` | Pos-trivia, aceita qualquer tema | Jogador, torneio ou novo tema |

### Regras de Transicao
1. "ranking atp" → topic=ranking, pending=player_from_ranking
2. "Sinner" (apos ranking) → topic=player, focus=Sinner, pending=player_detail
3. "qual o pais dele" → topic=player, action=showed_player_country
4. "roland garros" → topic=tournament, pending=player_from_ranking
5. "uma curiosidade" → topic=trivia, pending=open_topic

---

## 11. Como Adicionar Funcionalidades

### Novo Jogador no player_details
Edite `tennis_data.json`:
```json
"Nome Completo": {
    "age": 25,
    "style": "Destro/Canhoto",
    "titles": "Torneio 2024, ...",
    "country": "Pais em Portugues",
    "fact": "Curiosidade interessante."
}
```

### Novo Intent Conversacional
Edite `knowledge_base.json`:
```json
{
    "tag": "nome_do_intent",
    "patterns": ["frase1", "frase2", "frase3"],
    "responses": ["resposta1", "resposta2"],
    "follow_up": "Pergunta de acompanhamento?"
}
```

### Nova Reacao Empatica
Em `decision_tree.py`, adicione em REACTION_KEYWORDS:
```python
"nova_keyword": ["Reacao 1 com {dele_dela}!", "Reacao 2 com {ele_ela}!"],
```

### Novo Pais/Gentilico
Em `query_parser.py`:
- `COUNTRY_MAP`: {"nome_variante": "Nome Canonico"}
- `DEMONYM_MAP`: {"gentilico": "Nome Canonico"}

Em `api_client.py` (se necessario para traducao):
- `COUNTRY_EN_TO_PT`: {"English Name": "Nome Portugues"}
- `COUNTRY_CODE_TO_PT`: {"ISO": "Nome Portugues"}

Em `engine.py`:
- `COUNTRY_FLAGS`: {"Nome Portugues": "🏳️"}

---

## 12. Checklist de Testes Antes de Qualquer Commit

1. `python run_tests.py` → **170/170 ZERO FALHAS**
2. Testar manualmente no navegador:
   - Fluxo de 20 turnos sem perder contexto
   - Typo de jogador (ex: "Medevedev")
   - Elogio generico (ex: "um dos melhores")
   - Reacao empatica (ex: "o forehand dele")
   - Filtragem por pais (ex: "melhor do brasil")
   - Off-topic (ex: "futebol")
   - Gibberish (ex: "asdfghjk")
   - Troca de genero (ex: "ranking wta" → "Sabalenka" → "qual o pais dela")
3. Verificar pipeline visual no painel lateral

---

## 13. Erros Comuns a Evitar

| Erro | Consequencia | Como Evitar |
|------|-------------|-------------|
| Adicionar keyword off-topic que conflita com tenis | Bloqueia perguntas validas | Testar com Bateria 9 |
| Threshold fuzzy < 0.70 | Muitos falsos positivos | Manter em 0.75 |
| Threshold fuzzy > 0.85 | Nao detecta typos comuns | Manter em 0.75 |
| Follow-up sim/nao | Conversa morre | Sempre perguntas abertas |
| Follow-up no mesmo tema | Usuario enjoa | Sempre mudar de tema |
| Reacao sem focus_player | Reacao a pergunta generica | Verificar if focus_player |
| Stem < 4 chars no entity matching | Falso positivo curto | Min 4 chars ja implementado |
| Pais detectado em nome de torneio | "Australian Open" → Australia | Remover torneios antes |

---

## 14. Fluxos Validados de Teste (20 turnos)

### Fluxo 1: ATP Completo
```
1. "oi" → saudacao
2. "ranking atp" → Top 10 ATP
3. "Sinner" → ficha Sinner
4. "o forehand dele e incrivel" → reacao + ficha
5. "qual o pais dele" → Italia
6. "Alcaraz" → ficha Alcaraz (troca foco)
7. "um dos melhores" → elogio generico aceito
8. "gosto de roland garros" → campeoes RG
9. "e wimbledon?" → campeoes Wimbledon
10. "melhor jogador do brasil" → Fonseca
11. "Fonseca" → ficha Fonseca
12. "qual o pais dele" → Brasil
13. "ranking wta" → Top 10 WTA
14. "Sabalenka" → ficha Sabalenka
15. "o saque dela e devastador" → reacao + ficha
16. "qual o pais dela" → Bielorrussia
17. "Medevedev" → ficha Medvedev (typo corrigido)
18. "quais as regras" → regras do tenis
19. "cor da bolinha" → amarelo optico
20. "obrigado" → despedida
```

### Fluxo 2: WTA + Trivia
```
1. "boa tarde" → saudacao
2. "ranking wta" → Top 10 WTA
3. "Gauff" → ficha Gauff
4. "qual o pais dela" → EUA
5. "Swiatek" → ficha Swiatek
6. "a resistencia dela" → reacao + ficha
7. "quem ganhou wimbledon" → campeoes Wimbledon
8. "e o australian open?" → campeoes AO
9. "jogadoras brasileiras" → Haddad
10. "quais as regras do tenis" → regras
11. "o que e grama no tenis" → superficie
12. "ranking atp" → Top 10 ATP
13. "Djokovic" → ficha Djokovic
14. "a forca mental dele" → reacao + ficha
15. "Zverev" → ficha Zverev
16. "qual o pais dele" → Alemanha
17. "me conta uma curiosidade" → trivia
18. "us open" → campeoes US Open
19. "Sinner" → ficha Sinner
20. "tchau" → despedida
```

---

## 15. Arquivos-Chave e Linhas Importantes

| Arquivo | Linhas | O que contem |
|---------|--------|-------------|
| `app.py` | 38-59 | OFF_TOPIC_KEYWORDS |
| `app.py` | ~100-130 | Funcao is_gibberish |
| `app.py` | ~135-350 | Pipeline principal (predict) |
| `decision_tree.py` | 10-45 | FOLLOW_UPS |
| `decision_tree.py` | 49-59 | STYLE/TOURNAMENT/COMPARISON/COUNTRY keywords |
| `decision_tree.py` | 63-80 | REACTION_KEYWORDS |
| `decision_tree.py` | 86-92 | GENERIC_PRAISE |
| `decision_tree.py` | 96-112 | _build_reaction() |
| `decision_tree.py` | 116-133 | _get_pronoun() |
| `decision_tree.py` | ~200-450 | try_contextual_response() (arvore principal) |
| `query_parser.py` | 10-50 | COUNTRY_MAP, DEMONYM_MAP |
| `query_parser.py` | 52-70 | TEMPORAL/SUPERLATIVE/ATP/WTA markers |
| `engine.py` | 10-40 | COUNTRY_FLAGS |
| `session_manager.py` | 10-20 | SESSION_TTL, MAX_TURNS |
| `run_tests.py` | 1-349 | 170 testes em 12 baterias |

---

## 16. Proximos Passos Sugeridos

1. **Detalhes de Grand Slams**: Localizacao, superficie, premiacao, historia, maior campeao (ver `TODO_GRAND_SLAMS.md`).
2. **Calendario ATP**: Masters 1000, ATP 250/500, Finals.
3. **Head-to-Head**: Confrontos diretos entre jogadores.
4. **Estatisticas**: Aces, % primeiro servico, duplas faltas.
5. **Mais reacoes**: Adicionar reacoes para "servico", "slice", "drop shot", "lob".
6. **Mais paises**: Expandir COUNTRY_MAP e DEMONYM_MAP para paises menos comuns.
7. **Mais jogadores**: Expandir player_details com jogadores fora do Top 50.
8. **Noticias**: Scraping de sites de noticias de tenis em tempo real.
