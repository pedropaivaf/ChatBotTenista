# AI Handoff: ChatBot Tenista

Este documento serve como guia de contexto para outros modelos de IA ou desenvolvedores que assumirem o projeto.

---

## Estado Atual (v2.0)

O projeto possui um backend hibrido maduro com 7 modulos Python (~2.350 linhas) e 170 testes automatizados:

1. **NLP Local**: NLTK para tokenizacao, stemming e extracao de entidades.
2. **Arvore de Decisao**: Maquina de estados contextual com 20 turnos de memoria, follow-ups abertos e resolucao de entidades.
3. **Dados em Tempo Real**: Scraping de tennisexplorer.com (ATP) e API oficial wtatennis.com (WTA) com cache de 24h.
4. **Fuzzy Matching**: difflib.SequenceMatcher com threshold 0.75 e filtro de stop words (100+) para evitar falsos positivos.
5. **Reacoes Empaticas**: 13 atributos tecnicos (forehand, saque, mental, etc.) com respostas contextuais e pronomes genero-corretos.
6. **Filtro Off-Topic**: 60+ palavras bloqueadas + deteccao de gibberish (analise de vogais, consoantes consecutivas, bigramas).

---

## Arquitetura de Processamento

```
Mensagem → Tokenize/Stem → Filtro Off-Topic/Gibberish → Arvore de Decisao
→ Query Parser → Dados Tecnicos → Torneios → Intents → Fallback → Enrich
```

Cada etapa gera um trace visual exibido no painel lateral do frontend.

---

## Modulos e Responsabilidades

| Modulo | Responsabilidade |
|--------|-----------------|
| `app.py` (415 linhas) | Pipeline principal, filtros, integracao de todos os modulos |
| `decision_tree.py` (506 linhas) | Contexto conversacional, follow-ups, reacoes empaticas, fuzzy matching |
| `engine.py` (266 linhas) | Consultas ao banco de dados JSON (rankings, jogadores, torneios) |
| `query_parser.py` (203 linhas) | Extracao de pais, temporal, superlativo, circuito |
| `session_manager.py` (153 linhas) | Sessoes in-memory com UUID, TTL 30min, 20 turnos |
| `api_client.py` (377 linhas) | Scraping ATP + API WTA com cache 24h |
| `nltk_utils.py` (78 linhas) | Tokenizacao, stemming, bag of words |

---

## Constantes Criticas (nao remover sem entender o impacto)

- `OFF_TOPIC_KEYWORDS` em app.py — 60+ palavras que bloqueiam assuntos fora de tenis
- `FOLLOW_UPS` em decision_tree.py — mapa de follow-ups por (topico, acao)
- `REACTION_KEYWORDS` em decision_tree.py — 13 atributos tecnicos com reacoes empaticas
- `GENERIC_PRAISE` em decision_tree.py — elogios genericos reconhecidos como feedback positivo
- `_STOP_WORDS` em decision_tree.py — 100+ palavras excluidas do fuzzy matching
- `COUNTRY_MAP` / `DEMONYM_MAP` em query_parser.py — 80+ mapeamentos de pais/gentilico

---

## Pontos de Atencao

1. **Fuzzy matching**: O threshold de 0.75 foi calibrado para equilibrar deteccao de typos vs falsos positivos. Ajustar com cuidado.
2. **Stop words**: Cada falso positivo historico foi resolvido adicionando a palavra a `_STOP_WORDS`. Manter essa lista.
3. **Prioridade torneio > jogador**: A arvore de decisao detecta torneios ANTES de tentar resolver como nome de jogador. Isso evita confusoes como "Roland Garros" → match com algum jogador.
4. **Stems minimos**: Stems com menos de 4 caracteres sao ignorados na extracao de entidades para evitar falsos positivos (ex: stem "mai" → Mai Hontama).
5. **Nomes de torneios**: Removidos da deteccao de pais no query_parser (ex: "Australian Open" nao deve disparar filtro de Australia).

---

## Sugestoes de Melhoria (Roadmap)

1. **Detalhes de Grand Slams**: Adicionar localizacao, superficie, premiacao, maior campeao e historia para cada Grand Slam (ver `TODO_GRAND_SLAMS.md`).
2. **Calendario ATP**: Masters 1000, ATP 250/500, Finals — com datas e locais.
3. **Modelo Neural**: Migrar classificacao de intents para PyTorch/TensorFlow para melhor generalizacao.
4. **Base de Dados Externa**: Migrar de JSON para SQLite ou MongoDB para facilitar expansao.
5. **Noticias em Tempo Real**: Scraping de sites de noticias de tenis.
6. **Historico de Confrontos**: Head-to-head entre jogadores.
7. **Estatisticas Detalhadas**: Aces, duplas faltas, % primeiro servico por jogador.

---

## Variaveis de Ambiente

Nenhuma variavel de ambiente sensivel e necessaria. O projeto funciona 100% standalone.

---

## Como Executar Testes

```bash
python run_tests.py
```

170 testes, 12 baterias, ~30 segundos. Resultado esperado: **170/170 ZERO FALHAS**.
