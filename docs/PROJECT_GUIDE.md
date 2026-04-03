# Guia do Projeto: Tennis AI ChatBot

Este documento explica o "porque" e o "como" de cada arquivo do projeto.

---

## Estrutura do Projeto (~2.350 linhas de Python)

### 1. `app.py` — O Cerebro (415 linhas)
Servidor principal Flask com logica hibrida de roteamento.
- **Rota `/`**: Carrega a interface visual (HTML).
- **Rota `/predict`**: Recebe a mensagem do usuario e devolve a resposta + pipeline trace.
- **Pipeline**: Off-topic → Gibberish → Contexto → Query Parser → Dados Tecnicos → Torneios → Intents → Fallback → Enrich.
- **Filtro off-topic**: 60+ keywords (futebol, bitcoin, politica, receita...).
- **Deteccao de gibberish**: Analisa ratio de vogais (< 15%), consoantes consecutivas (5+), e bigramas improvaveis para rejeitar texto sem sentido como "asdfghjk".
- **Pipeline trace**: Cada etapa gera um step (nome, status, detalhe, dados) enviado ao frontend para visualizacao.

### 2. `nltk_utils.py` — O Interprete (78 linhas)
Funcoes de Processamento de Linguagem Natural (PLN).
- **Tokenizacao**: Quebra a frase em palavras individuais.
- **Stemming**: Reduz palavras ao radical (ex: "vencendo" e "venceu" viram a mesma raiz).
- **Extracao de Entidades**: Identifica nomes de jogadores e torneios via stems, com validacao minima de 4 caracteres para evitar falsos positivos.

### 3. `engine.py` — O Especialista (266 linhas)
Motor de consulta que le `tennis_data.json` e filtra dados.
- `get_ranking_summary()`: Top 10 ATP ou WTA formatado com bandeiras emoji.
- `get_player_info()`: Ficha completa com rank, pais, idade, estilo, titulos e curiosidade.
- `get_filtered_ranking()`: Filtra ranking por pais (ex: "ranking do Brasil").
- `get_best_from_country()`: Retorna os melhores jogadores de um pais (ATP e WTA).
- `get_last_champions()`: Campeoes de Grand Slams por torneio ou todos.
- `get_player_country()`: Nacionalidade com bandeira emoji.
- `reload_data()`: Recarrega JSON sem reiniciar o servidor.

### 4. `session_manager.py` — A Memoria (153 linhas)
Gerencia sessoes de conversa para manter contexto.
- Cada aba do navegador recebe um UUID unico.
- Rastreia ate 20 turnos: topico atual, circuito (ATP/WTA), jogador em foco.
- Sessoes expiram apos 30 minutos de inatividade.
- Limpa sessoes expiradas automaticamente.

### 5. `query_parser.py` — O Detetive (203 linhas)
Analisa a mensagem para extrair modificadores estruturados.
- **Pais**: 40+ paises + 50+ gentilicos ("brasileiro", "espanhol", "italiana").
- **Temporal**: "atualmente", "hoje", "agora" → flag `is_current`.
- **Superlativo**: "melhor", "top", "lider", "numero 1" → flag `wants_best`.
- **Circuito**: "atp"/"masculino" ou "wta"/"feminino". Palavras femininas (jogadora, tenista) auto-detectam WTA.
- **Protecao**: Remove nomes de torneios antes de detectar pais (evita "Australian Open" → Australia).

### 6. `decision_tree.py` — O Contexto (506 linhas)
Arvore de decisao que gera follow-ups abertos e resolve entidades por contexto. **O modulo mais complexo.**

**Branches (em ordem de prioridade):**
1. Torneio detectado no contexto → mostra campeoes.
2. Jogador resolvido do contexto (fuzzy match) → mostra ficha.
3. Detalhe do jogador em foco:
   - Comparacao, pais, estilo de jogo.
   - **Reacao empatica** a 13 atributos tecnicos (forehand, saque, mental, velocidade...).
   - **Elogio generico** ("um dos melhores", "lenda", "goat") → reacao positiva.
4. Topico aberto (apos trivia) → aceita jogador ou torneio.

**Subsistemas:**
- **Fuzzy matching**: threshold 0.75, 100+ stop words filtradas.
- **Follow-ups abertos**: Sempre 1 pergunta que abre para outro tema do tenis (nunca sim/nao).
- **Reacoes**: Respostas empaticas com pronomes genero-corretos (ele/ela, dele/dela).
- **Trace visual**: Cada branch gera um node com icone, nome, status (matched/missed) e detalhe.

### 7. `api_client.py` — O Atualizador (377 linhas)
Busca rankings atualizados de fontes externas reais.
- **ATP**: Scraping de tennisexplorer.com (HTML, 2 paginas, Top 100).
- **WTA**: API JSON oficial da WTA (api.wtatennis.com), com fallback para tennisexplorer.
- Atualiza automaticamente no startup se dados tem mais de 24h.
- Traduz paises (50+ EN→PT, 60+ ISO-3→PT), corrige nomes com acentos (~15 correcoes).

### 8. `knowledge_base.json` e `tennis_data.json` — Os Dados
- **`knowledge_base.json`**: 15+ intents conversacionais com padroes e respostas.
- **`tennis_data.json`**: Rankings Top 100 (ATP+WTA), Grand Slams 2024-2026, biografias de ~50 jogadores.

### 9. Pasta `/templates` e `/static` — A Face
- **`index.html`**: Estrutura semantica do chat com painel lateral.
- **`style.css`**: Design Premium Glassmorphism com modo escuro.
- **`script.js`**: Comunicacao Fetch API com session_id, pipeline visual com animacoes, fluxograma da arvore de decisao.

---

## Pontos Fortes para Apresentacao

1. **Contexto de 20 Turnos**: O bot mantem contexto entre mensagens — entende "Alcaraz" apos ranking, "qual o pais dele" apos ficha de jogador, e "roland garros" apos curiosidade.
2. **Tolerancia a Erros de Digitacao**: Fuzzy matching permite que "Medevedev", "Tsitipas" e outros typos sejam resolvidos para o jogador correto.
3. **Parser Inteligente**: "Qual o melhor jogador do brasil atualmente" retorna Joao Fonseca porque reconhece "brasil" + "melhor" + "atualmente" como filtros.
4. **Dados em Tempo Real**: Rankings ATP e WTA Top 100 atualizados automaticamente via scraping/API a cada 24h.
5. **Reacoes Empaticas**: "O forehand dele e incrivel" gera uma reacao contextual — o bot concorda e complementa com dados.
6. **Filtro Off-Topic + Gibberish**: Rejeita futebol, politica, bitcoin E texto sem sentido como "asdfghjk".
7. **Pipeline Visual**: Console tecnico lateral mostra cada etapa do processamento com animacoes, incluindo trace da arvore de decisao.
8. **170 Testes**: 12 baterias cobrindo todos os cenarios, executados 3x com zero falhas.

---

## Como Explicar o Funcionamento

"Quando o usuario digita 'Qual o melhor jogador do brasil atualmente?', o `app.py` recebe a mensagem, o `query_parser.py` detecta 'brasil' como pais e 'melhor' como superlativo, o `engine.py` filtra o ranking ATP por Brasil e retorna Joao Fonseca como #40 do mundo. O bot pergunta 'Quer ver a ficha de algum deles ou explorar outro tema?'. Se o usuario responde 'Fonseca', a `decision_tree.py` resolve isso no contexto e mostra a ficha completa dele. Se o usuario diz 'o forehand dele e incrivel', o bot reage com uma resposta empatica e sugere explorar outro assunto."
