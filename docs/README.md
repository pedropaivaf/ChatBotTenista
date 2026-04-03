# AI Tennis ChatBot 🎾

Um ChatBot de Inteligencia Artificial nichado em Tenis, construido com **Python**, **Flask**, **NLTK** e uma **Arvore de Decisao contextual** com memoria de ate 20 interacoes.

**170 testes automatizados | 12 baterias | 100% de aprovacao**

---

## Funcionalidades

- **Rankings em tempo real**: Top 100 ATP e WTA atualizados automaticamente via scraping/API a cada 24h.
- **Ficha completa de jogadores**: Rank, pais, idade, estilo, titulos e curiosidade para ~50 jogadores.
- **Grand Slams**: Historico de campeoes 2024-2026 (Australian Open, Roland Garros, Wimbledon, US Open).
- **Contexto de 20 turnos**: Mantem memoria de conversa — "Alcaraz" apos ranking resolve como Carlos Alcaraz, "qual o pais dele" retorna Espanha.
- **Fuzzy matching**: Tolera typos como "Medevedev" → Medvedev, "Tsitipas" → Tsitsipas.
- **Filtragem por pais**: "melhor jogador do brasil" → Joao Fonseca, "jogadoras brasileiras" → Beatriz Haddad.
- **Reacoes empaticas**: "o forehand dele e incrivel" gera reacao contextual com pronomes corretos (ele/ela).
- **Elogios genericos**: "um dos melhores", "lenda", "goat" reconhecidos como feedback positivo.
- **Filtro off-topic**: 60+ palavras bloqueadas (futebol, bitcoin, politica, receita...).
- **Deteccao de gibberish**: Identifica texto sem sentido via analise de vogais, consoantes e bigramas.
- **Pipeline visual**: Painel tecnico lateral mostra cada etapa do processamento em tempo real.
- **Interface premium**: Design Glassmorphism com modo escuro.

---

## Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Backend | Flask (Python 3.13) |
| NLP | NLTK (Tokenizacao, Stemming, Entidades) |
| Dados | JSON local + Scraping (tennisexplorer.com) + API (wtatennis.com) |
| Contexto | Arvore de Decisao + Session Manager (UUID, TTL 30min) |
| Frontend | HTML5, CSS3 (Glassmorphism), JavaScript ES6 (Vanilla) |

---

## Como Instalar e Rodar

1. Clone o repositorio:
```bash
git clone https://github.com/pedropaivaf/ChatBotTenista.git
```

2. Instale as dependencias:
```bash
pip install -r requirements.txt
```

3. Execute o servidor:
```bash
python app.py
```

4. Acesse no navegador:
```
http://127.0.0.1:5000
```

---

## Estrutura do Projeto

```
ChatBotTenista/
├── app.py                  # Servidor Flask — cerebro do pipeline (415 linhas)
├── decision_tree.py        # Arvore de decisao contextual (506 linhas)
├── engine.py               # Motor de dados tecnico (266 linhas)
├── query_parser.py         # Parser inteligente de queries (203 linhas)
├── session_manager.py      # Gerenciador de sessoes in-memory (153 linhas)
├── api_client.py           # Scraping ATP + API WTA (377 linhas)
├── nltk_utils.py           # Tokenizacao, stemming, entidades (78 linhas)
├── run_tests.py            # 170 testes automatizados, 12 baterias (349 linhas)
├── tennis_data.json        # Rankings Top 100 + Grand Slams + biografias
├── knowledge_base.json     # Intents conversacionais (15+ intents)
├── templates/index.html    # Interface HTML do chat
├── static/css/style.css    # Design Glassmorphism premium
├── static/js/script.js     # Frontend JS com pipeline visual
└── docs/                   # Documentacao completa do projeto
    ├── README.md           # Este arquivo
    ├── CLAUDE.md           # Guia para treino e aperfeicoamento da IA
    ├── ARCHITECTURE.md     # Arquitetura e fluxo de processamento
    ├── PROJECT_GUIDE.md    # Guia detalhado de cada modulo
    ├── QUICK_START.md      # Inicio rapido e banco de dados
    ├── AI_HANDOFF.md       # Handoff para outros devs/IAs
    ├── CODING_STANDARDS.md # Regras de codificacao
    ├── DATABASE_AND_SCRAPING.md # Detalhes do scraping e API
    ├── TESTS_AND_RESULTS.md    # 170 testes documentados
    └── TODO_GRAND_SLAMS.md     # Melhorias futuras
```

**Total: ~2.350 linhas de codigo Python**

---

## Diferenciais

1. **IA Nichada**: Especializada exclusivamente em tenis — rejeita qualquer assunto fora do dominio.
2. **Contexto Profundo**: 20 turnos de conversa com resolucao de entidades, foco em jogador e follow-ups abertos.
3. **Dados Reais**: Rankings atualizados automaticamente de fontes oficiais (ATP e WTA).
4. **Tolerancia a Erros**: Fuzzy matching inteligente com filtro de stop words para evitar falsos positivos.
5. **Reacoes Humanas**: Bot reage a opiniones do usuario sobre atributos tecnicos dos jogadores.
6. **Interface Profissional**: Glassmorphism + console tecnico com trace visual da arvore de decisao.
7. **Testado Exaustivamente**: 170 testes em 12 baterias, executados 3x (510 testes totais), zero falhas.
