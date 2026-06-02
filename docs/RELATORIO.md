# Chatbot Híbrido de Tênis (NLTK + LLM) — Relatório do Trabalho Final

> **Métricas reais já preenchidas** (seção 5). Falta só completar os campos `⟨...⟩` abaixo
> (autores/RA, disciplina, professor, link do vídeo) e ajustar a formatação às normas
> exigidas (ex.: ABNT).

**Autor(es):** Pedro Paiva Ferreira · Bernardo Ladeira Leal de Medeiros · João Hugo Martins Botelho · Mateus Silva Xavier
**Disciplina:** ⟨disciplina⟩ — **Professor:** ⟨professor⟩
**Repositório:** https://github.com/pedropaivaf/ChatBotTenista
**Vídeo de demonstração:** ⟨link⟩

---

## 1. Introdução

### Objetivo do trabalho
Este trabalho implementa um **chatbot conversacional sobre tênis (ATP/WTA), em português**,
com **arquitetura híbrida**: uma **base de conhecimento estruturada** responde primeiro e,
quando ela não tem informação suficiente, um **Modelo de Linguagem (LLM)** atua como
**fallback**. O objetivo é demonstrar como a combinação de técnicas clássicas de PLN
(tokenização, stemming, *bag-of-words*, casamento de intenções) com um LLM moderno melhora a
interação humano-computador: a base garante **controle e confiabilidade** nas respostas do
domínio, enquanto o LLM amplia a **cobertura** para perguntas que fogem do roteiro.

### Contexto
Os chatbots evoluíram de sistemas **baseados em regras** (ELIZA, 1966; padrões fixos) para
abordagens de **recuperação de informação** (*retrieval*, casamento de intenções sobre uma
base) e, mais recentemente, para a **geração por LLMs** baseados em *Transformers*. Hoje é
comum a arquitetura **híbrida (RAG / retrieval-augmented)**, que ancora a geração do LLM em
dados confiáveis. Plataformas como o **Hugging Face Hub** popularizaram modelos *open-source*
(Llama, Mistral, Qwen, Gemma), e ferramentas como o **LM Studio** permitem executá-los
localmente, sem custo de API e sem enviar dados a terceiros.

### Justificativa
- **Papel da base de conhecimento:** no domínio de tênis, fatos como rankings, campeões de
  Grand Slam e perfis de jogadores precisam ser **corretos e versionáveis**. A base
  (`knowledge_base.json` + `tennis_data.json`) dá esse controle e evita alucinação no núcleo do
  domínio.
- **LLM como mecanismo complementar:** perguntas subjetivas ("melhor de todos os tempos?"),
  contextuais ("e o melhor brasileiro atual?") ou **fora do tema** não cabem numa base finita.
  O LLM cobre essa cauda longa — "joga para o modelo e retorna".
- **Escolha do modelo:** optou-se por **Qwen2.5-7B-Instruct** (ver Metodologia) por seu forte
  desempenho em **português**, por ser *instruction-tuned* e **não-gated** (download livre no
  Hugging Face), rodando localmente via **LM Studio**.

---

## 2. Fundamentação Teórica

### Definição de Chatbots
Programas que conversam em linguagem natural. Três grandes arquiteturas:
- **Baseada em regras:** gatilhos/padrões fixos → respostas pré-definidas. Previsível, mas rígida.
- **Recuperação (*retrieval*):** dada a mensagem, busca a melhor resposta numa base (por
  similaridade). É o coração da etapa de **intenções** deste projeto.
- **Geração por LLM:** um modelo *Transformer* gera a resposta token a token. Flexível, porém
  sujeito a **alucinação**.
Este trabalho combina **recuperação (base)** + **geração (LLM no fallback)**.

### Inteligência Artificial
IA é a área que constrói sistemas capazes de tarefas que exigiriam inteligência humana
(percepção, raciocínio, linguagem). Em chatbots, técnicas de IA simbólica (regras, árvores de
decisão) convivem com IA conexionista (redes neurais/LLMs). Este projeto usa **árvore de
decisão contextual** (`decision_tree.py`) e **casamento de intenções** sobre PLN clássico,
mais um **LLM neural** no fallback.

### Machine Learning
- **Supervisionado:** aprende de pares entrada→saída rotulados.
- **Não supervisionado:** encontra estrutura sem rótulos.
- **Por reforço:** aprende por recompensa/punição.

No **componente clássico** deste chatbot **não há treinamento de modelo próprio**: usamos
**recuperação por similaridade** com *features* de PLN (stems) e limiares — uma abordagem
**heurística/baseada em regras**, não um classificador treinado. Já o **LLM (Qwen2.5)** é fruto
de **aprendizado auto-supervisionado** (pré-treino prevendo o próximo token) seguido de
**ajuste por instrução** e **RLHF** (*Reinforcement Learning from Human Feedback*). Ou seja, o
paradigma de ML relevante aqui é o **auto-supervisionado + reforço**, encapsulado no modelo
*open-source* que reutilizamos.

### Processamento de Linguagem Natural (PLN)
Técnicas efetivamente usadas no código:
- **Tokenização** (`nltk_utils.py: tokenize`): quebra a frase em tokens.
- **Stemming** (`stem`): reduz palavras ao radical (ex.: "jogadores" → "jogador"), tolerando
  variações morfológicas do português.
- **Bag-of-words / casamento de intenções** (`app.py`): compara os radicais da mensagem com os
  padrões de cada intenção e calcula um **score de similaridade** (% de stems coincidentes),
  com **limiar de 50%** (65% quando há contexto ativo).
- **Fuzzy matching** (`decision_tree.py: _fuzzy_match_player`, limiar 0.75): tolera *typos* em
  nomes de jogadores.
- **Modelos de linguagem (Transformers):** o LLM de fallback é baseado na arquitetura
  *Transformer* (mecanismo de **atenção**, Vaswani et al., 2017).

---

## 3. Estado da Arte

### Revisão de Literatura
A tendência atual em chatbots é a arquitetura **híbrida / RAG**, em que um LLM é **ancorado**
por uma base de conhecimento para reduzir alucinação e manter atualidade factual. Assistentes
comerciais (ChatGPT, Gemini, Claude) usam LLMs de centenas de bilhões de parâmetros com
ferramentas e recuperação. Comparado ao **estado da arte**, este projeto:
- Usa um LLM **muito menor** (7B) e **local**, priorizando custo zero e privacidade;
- Aplica uma forma **simplificada de RAG** (injeção de contexto factual do `tennis_data.json`
  no *prompt* do modelo — *grounding* leve) em vez de busca vetorial densa;
- Mantém **controle total** do núcleo de respostas via base estruturada, o que assistentes
  generalistas não oferecem por padrão.

### Tecnologias utilizadas no trabalho
- **Backend:** Python 3.12+, Flask, Flask-CORS.
- **PLN clássico:** NLTK (tokenização, stemming, *bag-of-words*).
- **LLM:** Qwen2.5-7B-Instruct (GGUF) servido pelo **LM Studio** (API compatível com OpenAI).
- **Integração:** `requests` para o endpoint local `/v1/chat/completions`; `python-dotenv` para
  configuração.
- **Frontend:** HTML/CSS/JS *vanilla* com painel de *pipeline* que evidencia cada etapa
  (inclusive quando o LLM é acionado).

### Desafios e Limitações
- **Alucinações:** o LLM pode inventar fatos. Mitigamos com (i) *system prompt* que pede
  honestidade e foco, (ii) **grounding** com dados reais e (iii) **prioridade da base** no
  núcleo do domínio.
- **Troca de idioma (*code-switching*):** modelos pequenos — em especial a variante
  *Qwen2.5-7B-Instruct-**1M*** (contexto longo) — ocasionalmente "vazavam" para o **chinês** no
  meio da resposta. Mitigado com: (i) instrução de idioma reforçada por **recência** no prompt,
  (ii) **sanitização** da saída (remoção de caracteres CJK), (iii) **não enviar histórico** ao
  modelo (contexto irrelevante disparava a troca) e, principalmente, (iv) a escolha do modelo
  **padrão `Qwen2.5-7B-Instruct`** (não-`1M`), bem mais estável em português.
- **Dependência de dados:** a qualidade do núcleo depende do `tennis_data.json`/
  `knowledge_base.json`; dados desatualizados geram respostas erradas (ex.: troca de nº 1 do
  ranking).
- **Custos computacionais / tempo de resposta:** rodar um modelo 7B localmente consome RAM/CPU
  (ou GPU) e adiciona **latência** (medida em `tempo_medio_llm_s`). A base responde em
  milissegundos; o LLM, em segundos.
- **Questões éticas:** vieses do modelo, privacidade (mitigada pelo uso **local**), e
  transparência (o painel mostra quando a resposta veio do LLM e não da base).

---

## 4. Metodologia

### Justificativas
- **Tema (tênis):** continuidade do 1º trabalho; domínio rico em entidades (jogadores, torneios,
  rankings) e em perguntas subjetivas — ótimo para evidenciar a divisão **base × LLM**.
- **Modelo (Qwen2.5-7B-Instruct):** (1) **forte em português**; (2) **instruction-tuned** (bom
  para Q&A/conversa); (3) **não-gated** no Hugging Face (download livre); (4) tamanho **7B**
  equilibra qualidade e viabilidade local em quantização GGUF (`Q4_K_M`, ~4,7 GB, roda em ~8 GB
  de RAM). Avaliamos três variantes do Qwen 7B: a **`-1M`** (contexto longo) trocava de idioma
  com frequência; a **`-Coder`** é especializada em programação; a **padrão `Instruct`** foi a
  mais estável em português e a escolhida. Alternativa para máquinas modestas: **Qwen2.5-3B-Instruct**.
- **Extras:** *grounding* leve (injeção de contexto), painel de *pipeline* didático, endpoint
  `/metrics` para avaliação quantitativa, e **degradação graciosa** (o bot funciona mesmo sem o
  LLM).

### Desenvolvimento do Chatbot
- **Construção do agente:** pipeline de 10 etapas em `app.py` (tokenização → filtros →
  contexto → parser → motor de dados → intenções → fallback).
- **Lógica de decisão (base → LLM):** a base é sempre consultada primeiro. O LLM é acionado em
  dois pontos: (a) perguntas **fora do tema** e (b) o **fallback final**, quando nenhuma
  intenção atinge o limiar de confiança. **Gibberish** (texto sem sentido) permanece bloqueado
  e **não** aciona o LLM.
- **Integração (LM Studio):** módulo `llm_client.py` encapsula a chamada HTTP ao servidor local
  (`/v1/chat/completions`), monta `system prompt` + *grounding* + histórico recente e trata
  erros retornando `None` (→ resposta padrão).
- **Configuração:** variáveis em `.env` (`LLM_ENABLED`, `LLM_BASE_URL`, `LLM_MODEL`, ...). Os
  testes forçam `LLM_ENABLED=0`, garantindo determinismo.

### Arquitetura do Sistema (fluxo)
```
Mensagem
 ├─ Gibberish?  → bloqueia (mensagem padrão) — NÃO chama LLM
 ├─ Off-topic?  → LLM (fallback universal) → indisponível? mensagem padrão
 ├─ Base de conhecimento (NLTK + intenções + motor de dados + árvore de decisão)
 │     └─ resolveu? → resposta da BASE        [métrica: resolved_by_base]
 └─ Fallback final (base não resolveu)
       └─ LLM (LM Studio) → respondeu? resposta do LLM   [métrica: resolved_by_llm]
       └─ indisponível/falhou → mensagem padrão           [métrica: unresolved]
```

---

## 5. Resultados e Discussão

> Métricas reais coletadas via `GET /metrics` numa sessão representativa de 15 perguntas, com o
> LM Studio rodando o **`Qwen2.5-7B-Instruct`**. Os percentuais variam conforme o mix de perguntas.

### Avaliação de Desempenho
| Métrica | Valor |
|---|---|
| Total de perguntas avaliadas | 15 |
| Resolvidas pela **base** | 9 (**60,0%**) |
| Resolvidas pelo **LLM** | 5 (**33,3%**) |
| Não resolvidas (gibberish bloqueado) | 1 (6,7%) |
| **Tempo médio de resposta do LLM** | **2,65 s** |
| Falhas de chamada ao LLM | 0 |

> **Custo computacional:** ~19–20 tokens/s no LM Studio (GPU NVIDIA RTX 3050 6 GB); a base
> responde em milissegundos. Com o modelo padrão, o LLM responde em **uma única chamada**
> (sem retry), tipicamente em 2–6 s.

**Suíte de testes automatizados:** `run_tests.py` → **300/300** cenários (21 baterias). *(A
integração do LLM não altera o resultado: os testes rodam com `LLM_ENABLED=0`.)*

**Robustez de contexto (20 turnos):** validado num fluxo de 20 turnos — o bot mantém o foco em
conversas longas (pronomes "dele/dela" sempre resolvem para o jogador em foco; a troca de foco
só ocorre quando um novo jogador é nomeado explicitamente), alternando entre atributos, troca de
tema e perguntas fora do tema (→ LLM), sem perder contexto.

### Qualidade das respostas (avaliação qualitativa)
- **Base (núcleo de tênis):** "ranking ATP", "quem é o Sinner", "campeão de Wimbledon", "qual a
  idade dele?" (segue o foco) — 100% confiável.
- **Base (debate curado):** "quem é o melhor de todos os tempos?" → *Big Three* (intent `goat_debate`).
- **LLM (cauda subjetiva):** "melhor brasileiro de todos os tempos?" → **"Gustavo Kuerten (Guga)"**,
  correto graças ao *grounding*.
- **LLM (fora do tema):** "o que é fotossíntese?", "qual a capital da França?" → respostas corretas.

**Discussão:** a base resolveu a maioria (**60%**) com confiabilidade total no núcleo; o LLM
cobriu a cauda (**33%**) — perguntas gerais e subjetivas. O ***grounding*** foi decisivo: em
testes sem ele, o modelo **alucinava** nomes de tenistas brasileiros inexistentes ("Vasco
Vasques", "Carlos Costa"); com a injeção das lendas reais (Guga, Bia Haddad, Maria Esther Bueno),
passou a responder **Guga** corretamente. A transparência do painel (badge "Gerado por IA")
deixa claro ao usuário quando a resposta veio do modelo — reforçando o controle sobre alucinações.

---

## 7. Conclusões e Trabalhos Futuros

**Aprendizados principais:**
- **Arquitetura híbrida (base + LLM):** une **confiabilidade** (base estruturada) e
  **cobertura** (LLM), cada um no que faz melhor.
- **Controle de respostas:** priorizar a base e tornar o acionamento do LLM **explícito** (no
  painel) aumenta a transparência e reduz risco de alucinação no núcleo.
- **Dependência do modelo:** a qualidade/latência do fallback depende do modelo e do *hardware*;
  a degradação graciosa garante que o produto **nunca quebra** sem o LLM.

**Trabalhos futuros:** RAG com busca vetorial (embeddings), expansão do `tennis_data.json`,
*head-to-head* entre jogadores, *cache* de respostas do LLM, avaliação automática de
alucinação, e atualização dos testes para os dados correntes.

---

## 8. Referências
> Ajuste à norma exigida (ABNT/IEEE). Sugestões de base:
- VASWANI, A. et al. *Attention Is All You Need*. NeurIPS, 2017.
- BIRD, S.; KLEIN, E.; LOPER, E. *Natural Language Processing with Python (NLTK Book)*. O'Reilly, 2009.
- LEWIS, P. et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS, 2020.
- QWEN TEAM. *Qwen2.5 Technical Report*. 2024/2025.
- Documentação do **Hugging Face Hub** — https://huggingface.co/models
- Documentação do **LM Studio** — https://lmstudio.ai/docs
- Documentação do **Flask** e do **NLTK**.

---

## 9. Apêndices
- **Códigos-fonte (obrigatório):** https://github.com/pedropaivaf/ChatBotTenista
- **Vídeo de demonstração:** ⟨link⟩
- **Arquivos-chave da integração:** `llm_client.py` (cliente LLM), `app.py` (lógica base→LLM,
  rota `/metrics`), `.env.example` (configuração).
