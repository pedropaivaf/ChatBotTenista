# 🚀 Início Rápido e Banco de Dados

Este guia rápido explica como colocar o seu ChatBot para funcionar e como os dados estão organizados.

---

### 📂 Estrutura de Dados (Banco de Dados)

O projeto utiliza uma arquitetura **NoSQL baseada em JSON**. Não é necessário instalar nenhum servidor de banco de dados externo (como MySQL ou MongoDB).

- **Onde ficam os dados?**
  - `tennis_data.json`: Contém os dados técnicos oficiais (Ranking ATP, Campeões de Grand Slam, Detalhes de Jogadores).
  - `knowledge_base.json`: Contém a inteligência de conversação (intenções, padrões de fala e respostas).

- **Vantagens:**
  - **Portabilidade:** Funciona em qualquer lugar apenas copiando os arquivos.
  - **Velocidade:** O bot lê os dados instantaneamente da memória.
  - **Facilidade:** Você pode atualizar o ranking ou adicionar novos fatos editando os arquivos de texto diretamente.

---

### 🏃 Como Executar o Projeto

Siga estes passos simples no seu terminal:

1.  **Entrar na pasta do projeto:**
    ```bash
    cd ChatBotTenista
    ```

2.  **Instalar dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Rodar o servidor Python:**
    ```bash
    python app.py
    ```

4.  **Acessar o ChatBot:**
    Abra o seu navegador e acesse: `http://127.0.0.1:5000`

---

### 🎙️ Dicas para a Apresentação

- **Demonstração técnica:** Mostre o arquivo `tennis_data.json` para explicar que o bot tem uma "memória oficial".
- **Interatividade:** Mostre como o bot sempre faz uma pergunta de volta para manter o papo fluindo.
- **Efeito Visual:** Chame a atenção para o design *Glassmorphism* (efeito de vidro) da interface, que é uma tendência moderna em design de UI.
