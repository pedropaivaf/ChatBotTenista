# 🤖 AI Handoff: ChatBot Tenista

Este documento serve como guia de contexto para outros modelos de IA ou desenvolvedores que assumirem o projeto.

## Estado Atual
O projeto possui um backend híbrido: 
1. **NLP Local**: NLTK para perguntas gerais e históricas.
2. **API em Tempo Real**: Integração pronta com a **API-Sports** para rankings e placares.

## Como Usar a API
1. Obtenha uma chave em [API-Sports](https://dashboard.api-sports.io/).
2. Crie um arquivo `.env` (use o `.env.example` como base).
3. Adicione sua chave em `API_SPORTS_KEY`.

## Arquitetura de NLP
- **NLTK**: Utilizado para normalizar as entradas do usuário.
- **Matching**: O bot utiliza uma comparação de tokens (stemmed) entre a entrada do usuário e os padrões definidos no JSON.
- **Vulnerabilidade**: Atualmente não possui um modelo de Deep Learning treinado, dependendo de correspondência de palavras-chave/tokens.

## Sugestões de Melhoria (Roadmap)
1. **Modelo de Redes Neurais**: Implementar um `PyTorch` ou `TensorFlow` para classificação de intenções em vez de matching manual.
2. **Base de Dados Externa**: Migrar o `knowledge_base.json` para um banco de dados SQL ou NoSQL para facilitar a expansão.
3. **Web Scraping**: Adicionar um módulo para buscar notícias de tênis em tempo real (ex: API da ATP ou sites de notícias).
4. **Memória de Curto Prazo**: Implementar sessões no Flask para que o bot lembre do contexto da conversa anterior.

## Variáveis de Ambiente
Atualmente não são necessárias variáveis de ambiente sensíveis.

## Contatos e Handoff
- **Status**: Versão 1.0 (MVP) concluída.
- **Foco**: Manter a estética premium e a simplicidade do processamento NLTK.
