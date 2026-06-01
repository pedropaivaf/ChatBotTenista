# 🎾 Como rodar o ChatBot Tenista (no seu notebook)

Guia completo para rodar o chatbot híbrido (**base de conhecimento NLTK + LLM Qwen 2.5 via LM Studio**) numa máquina nova.

---

## ✅ Requisitos
- **Python 3.12+**
- **Git**
- **LM Studio** (para o LLM) — https://lmstudio.ai
- **~8 GB de RAM livre** (o modelo Qwen 7B quantizado ocupa ~4,7 GB)
- Internet **na primeira execução** (baixa o `punkt` do NLTK automaticamente)

---

## 1) Clonar o projeto
```bash
git clone https://github.com/pedropaivaf/ChatBotTenista.git
cd ChatBotTenista
```

## 2) Ambiente Python + dependências
```bash
# (opcional, recomendado) ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
```
> O `punkt` do NLTK é baixado **automaticamente** na 1ª execução (não precisa de comando manual).

## 3) LM Studio + o modelo
1. Instale e abra o **LM Studio**.
2. Na busca (🔎), procure **`Qwen2.5 7B Instruct 1M`** e baixe a versão **GGUF `Q4_K_M`** (~4,7 GB).
   - *Notebook com pouca RAM?* Use **`Qwen2.5 7B Instruct`** (padrão) ou **`Qwen2.5 3B Instruct`** e ajuste o `LLM_MODEL` no `.env` (passo 4).
3. Aba **Developer / Local Server** → **carregue** o modelo → **Start Server** (porta **1234**).
4. Confira em *API Usage* que o **Model Identifier** é `qwen2.5-7b-instruct-1m` e o servidor está em `http://127.0.0.1:1234`.

## 4) Configurar o `.env`
O `.env` **não vem no repositório** (é ignorado). Crie a partir do exemplo:
```bash
# Windows:
copy .env.example .env
# Linux/Mac:
# cp .env.example .env
```
O conteúdo já vem pronto:
```
LLM_ENABLED=1
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=qwen2.5-7b-instruct-1m
LLM_TIMEOUT=30
LLM_MAX_TOKENS=350
LLM_TEMPERATURE=0.5
```
> Se baixou outro modelo no LM Studio, troque o `LLM_MODEL` pelo **Model Identifier** mostrado lá.

## 5) Rodar
```bash
python app.py
```
Acesse: **http://localhost:5000**

---

## 🧪 Testar se está tudo certo
| Pergunta | Esperado |
|---|---|
| `ranking atp` / `quem é o Sinner` | 📚 responde pela **base** (sem badge) |
| `o que é fotossíntese?` | 🤖 **LLM** em português (badge "Gerado por IA") |
| `melhor brasileiro de todos os tempos` | 🤖 LLM → **Guga** |
| `asdfgh qwerty` | 🚫 bloqueado |

No canto superior direito, o botão da **bolinha verde** abre o **pipeline** — numa resposta de IA, expanda **"📤 Requisição enviada"** para ver requisição, resposta e métricas do LM Studio (latência, tokens, tok/s).

## 🤖 Sem o LM Studio ligado?
O app **não quebra**: responde tênis normalmente pela base; perguntas fora do tema voltam à mensagem padrão ("respiro apenas Tênis"). Basta ligar o LM Studio para o fallback de IA voltar a funcionar (**degradação graciosa**).

## ✅ Rodar os testes automatizados
```bash
python run_tests.py
```
Esperado: **300/300** (os testes rodam com o LLM desligado, então **não** precisam do LM Studio).

---

## 🆘 Problemas comuns
| Sintoma | Solução |
|---|---|
| `Servidor acessível? False` / IA não responde | LM Studio não está com **Start Server** ligado, ou porta ≠ 1234 |
| Respostas de IA muito lentas | Normal em CPU (~3–6 s). Modelo menor (3B) acelera |
| Erro de memória ao carregar o modelo | Use `Qwen2.5 3B Instruct` (mais leve) e ajuste o `LLM_MODEL` |
| Porta 5000 ocupada | Feche o processo anterior ou rode em outra porta |
| Modelo "not found" na API | `LLM_MODEL` do `.env` ≠ Model Identifier do LM Studio |
