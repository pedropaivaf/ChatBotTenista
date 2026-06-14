# ChatBot Tenista 🎾

ChatBot conversacional **nichado em tênis (ATP/WTA), em português**, com **arquitetura
híbrida**: base de conhecimento (Python · Flask · NLTK · árvore de decisão contextual) +
**LLM local (Qwen2.5-7B via LM Studio)** como fallback. Memória de até 20 turnos.

**312 testes automatizados | 23 baterias | 100% de aprovação**

---

## Funcionalidades

- **Rankings em tempo real**: Top 100 ATP e WTA atualizados automaticamente (scraping/API, cache 24h).
- **Ficha de jogadores**: rank, país, idade, estilo, títulos, altura e curiosidade — **290 jogadores**.
- **Grand Slams + ATP 1000/500/Finals**: campeões 2024–2026 e detalhes de 18 torneios.
- **Recordes e lendas**: 16 recordes históricos + GOAT debate.
- **Contexto de 20 turnos**: "Alcaraz" após ranking → Carlos Alcaraz; "qual o país dele" → Espanha.
- **Fuzzy matching**: tolera typos ("Medevedev" → Medvedev).
- **Filtragem por país**: "melhor jogador do brasil" → João Fonseca.
- **Reações empáticas**: "o forehand dele é incrível" → reação com pronome correto.
- **Fechado em tênis**: off-topic e gibberish bloqueados.
- **LLM de fallback**: perguntas de tênis fora da base vão ao Qwen (com *grounding* anti-alucinação).
- **Pipeline visual**: painel técnico lateral mostra cada etapa do processamento + a chamada ao LLM.

---

## Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Backend | Flask (Python 3.12+) |
| NLP clássico | NLTK (tokenização, stemming, bag-of-words) |
| LLM (fallback) | Qwen2.5-7B-Instruct via LM Studio (API compatível com OpenAI) |
| Dados | JSON local + scraping (tennisexplorer.com) + API (wtatennis.com) |
| Contexto | Árvore de decisão + Session Manager (UUID, TTL 30min) |
| Frontend | HTML5, CSS3 (Glassmorphism), JavaScript ES6 (vanilla) |

---

## Como Instalar e Rodar

```bash
git clone https://github.com/pedropaivaf/ChatBotTenista.git
cd ChatBotTenista
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```

- O `punkt` do NLTK é baixado automaticamente na 1ª execução.
- **LLM opcional**: sem o LM Studio o app funciona (degradação graciosa). Para ligar, veja
  [`COMO_RODAR.md`](../COMO_RODAR.md) e [LLM_HYBRID.md](LLM_HYBRID.md).

```bash
python run_tests.py      # 312/312 — obrigatório antes de commit
```

---

## Estrutura do Projeto

```
ChatBotTenista/
├── app.py                  # Servidor Flask — pipeline + roteamento base→LLM (860)
├── decision_tree.py        # Árvore de decisão contextual (899)
├── engine.py               # Motor de dados técnico (514)
├── llm_client.py           # Cliente do LLM (LM Studio / Qwen) (330)
├── api_client.py           # Scraping ATP + API WTA, retry + cache 24h (416)
├── query_parser.py         # Parser de queries (país/temporal/superlativo) (208)
├── session_manager.py      # Sessões in-memory (153)
├── nltk_utils.py           # Tokenização, stemming, entidades (90)
├── run_tests.py            # 312 testes, 23 baterias (765)
├── tennis_data.json        # Rankings + 290 jogadores + Grand Slams + torneios + recordes
├── knowledge_base.json     # 49 intents conversacionais
├── .env.example            # Configuração do LLM (copiar para .env)
├── templates/index.html    # Interface do chat
├── static/                 # CSS Glassmorphism + JS (pipeline visual)
├── COMO_RODAR.md           # Guia passo a passo (base + LM Studio)
└── docs/                   # Documentação completa (ver índice abaixo)
```

**Total: ~3.470 linhas de Python na aplicação (8 módulos) + 765 de testes.**

---

## Índice da Documentação (`docs/`)

| Doc | Conteúdo |
|---|---|
| [AI_HANDOFF.md](AI_HANDOFF.md) | **Comece aqui** — contexto completo para continuar em outro PC/IA |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura, módulos e fluxo de processamento |
| [LLM_HYBRID.md](LLM_HYBRID.md) | Camada LLM (Qwen/LM Studio): roteamento, grounding, métricas |
| [PROJECT_GUIDE.md](PROJECT_GUIDE.md) | Guia módulo a módulo |
| [CLAUDE.md](CLAUDE.md) | Manual de treino/aperfeiçoamento da IA |
| [DATABASE_AND_SCRAPING.md](DATABASE_AND_SCRAPING.md) | Schema dos JSON + scraping/API + retry/cache |
| [TESTS_AND_RESULTS.md](TESTS_AND_RESULTS.md) | 312 testes em 23 baterias + bugs corrigidos |
| [QUICK_START.md](QUICK_START.md) | Início rápido |
| [CODING_STANDARDS.md](CODING_STANDARDS.md) | Regras de codificação |
| [RELATORIO.md](RELATORIO.md) | Relatório acadêmico do trabalho final |
| [TODO_GRAND_SLAMS.md](TODO_GRAND_SLAMS.md) | Backlog histórico |

---

## Diferenciais

1. **Híbrido (Base + LLM)**: confiabilidade da base + cobertura do LLM, cada um no que faz melhor.
2. **Fechado em tênis**: rejeita qualquer assunto fora do domínio (3 camadas de filtro).
3. **Contexto profundo**: 20 turnos, resolução de entidades, foco em jogador, follow-ups abertos.
4. **Dados reais**: rankings atualizados de fontes oficiais (ATP/WTA) com retry e cache.
5. **Anti-alucinação**: *grounding* leve injeta fatos no prompt do LLM.
6. **Degradação graciosa**: funciona 100% mesmo sem o LM Studio.
7. **Testado exaustivamente**: 312 testes em 23 baterias, zero falhas.
