# 📖 Guia do Projeto: Tennis AI ChatBot

Este documento foi criado para que você domine cada detalhe do projeto para sua apresentação. Aqui explicamos o "porquê" e o "como" de cada arquivo.

---

## 🏗️ Estrutura do Projeto

### 1. `app.py` (O Cérebro)
Este é o servidor principal. Ele utiliza o framework **Flask** para criar as rotas da web.
- **Rota `/`**: Carrega a interface visual (HTML).
- **Rota `/predict`**: O "endpoint" que recebe a mensagem do usuário via JavaScript e devolve a resposta do bot.
- **Lógica Híbrida**: Ele decide se a pergunta deve ser respondida pelo **Motor de Dados** (fatos técnicos) ou pelo **NLP** (conversa casual).

### 2. `nltk_utils.py` (O Intérprete)
Este arquivo contém as funções de Processamento de Linguagem Natural (PLN).
- **Tokenização**: Quebra a frase em palavras individuais.
- **Stemming**: Reduz as palavras ao seu radical (ex: "vencendo" e "venceu" viram a mesma raiz), permitindo que o bot entenda variações da mesma palavra.

### 3. `engine.py` (O Especialista)
É o motor de consulta que criamos para substituir APIs externas instáveis.
- Ele lê o arquivo `tennis_data.json` e sabe como filtrar os rankings, buscar campeões e detalhes de jogadores de forma ultra-rápida.

### 4. `knowledge_base.json` e `tennis_data.json` (A Memória)
- **`knowledge_base.json`**: Contém as "intenções" (intents). Define padrões de fala e respostas casuais, incluindo as perguntas de acompanhamento que tornam o bot conversacional.
- **`tennis_data.json`**: É a nossa "Bíblia do Tênis" com dados oficiais reais de 2024/2025 (Rankings, Slams, etc.).

### 5. Pasta `/templates` e `/static` (A Face)
- **`index.html`**: Estrutura semântica do chat.
- **`style.css`**: Design Premium com efeito *Glassmorphism* (vidro fosco) e modo escuro, garantindo um visual moderno.
- **`script.js`**: Faz a ponte entre o usuário e o servidor sem precisar recarregar a página (AJAX/Fetch).

---

## 🚀 Pontos Fortes para sua Apresentação

1.  **Autonomia Total**: O projeto não depende de APIs externas. Ele é rápido, 100% offline e nunca "cai".
2.  **Engajamento**: Diferente de bots simples, este faz perguntas de volta para o usuário, simulando uma conversa real sobre o esporte.
3.  **Arquitetura Híbrida**: Combina regras de dados técnicos (`engine.py`) com inteligência linguística (`NLTK`).
4.  **Design "Wow"**: A interface foi pensada para parecer uma aplicação profissional de IA de 2026.

---

## 🛠️ Como Explicar o Funcionamento
"Quando o usuário digita 'Quem é o número 1?', o `app.py` recebe isso, o `nltk_utils` limpa a frase, o `engine.py` busca no `tennis_data.json` o nome do Sinner e o bot responde com o ranking atualizado, perguntando em seguida se você quer saber sobre outro jogador."
