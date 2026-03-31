# Testes e Resultados

Documento com todos os testes realizados no chatbot, cenarios cobertos e resultados obtidos.

---

## Teste de Maratona: 20 Interacoes com Contexto

Teste principal que valida a manutencao de contexto ao longo de 20 turnos consecutivos na mesma sessao, cobrindo ranking, jogadores, torneios, typos e trocas de topico.

| Turno | Input do Usuario | Resposta Esperada | Resultado |
|-------|-----------------|-------------------|-----------|
| 1 | ranking atp | Top 10 ATP com Alcaraz #1 | OK |
| 2 | Sinner | Ficha completa do Jannik Sinner (contexto do ranking) | OK |
| 3 | qual o pais dele | Italia (focus_player = Sinner) | OK |
| 4 | e o estilo de jogo dele? | Re-mostra ficha do Sinner com estilo | OK |
| 5 | Alcaraz | Ficha completa do Carlos Alcaraz (troca de jogador) | OK |
| 6 | qual o pais dele | Espanha (focus_player atualizado para Alcaraz) | OK |
| 7 | gosto de roland garros | Campeoes de Roland Garros (torneio tem prioridade) | OK |
| 8 | e wimbledon? | Campeoes de Wimbledon (contexto de torneio) | OK |
| 9 | qual o melhor jogador do brasil atualmente | Joao Fonseca #40 ATP + Bia Haddad #70 WTA | OK |
| 10 | Fonseca | Ficha completa do Joao Fonseca (contexto do pais) | OK |
| 11 | qual o pais dele | Brasil (focus_player = Fonseca) | OK |
| 12 | ranking wta | Top 10 WTA com Sabalenka #1 | OK |
| 13 | Sabalenka | Ficha completa da Aryna Sabalenka (contexto WTA) | OK |
| 14 | qual o pais dela | Bielorrussia (focus_player = Sabalenka) | OK |
| 15 | Medevedev | Ficha do Daniil Medvedev (typo corrigido via fuzzy) | OK |
| 16 | Tsitipas | Ficha do Stefanos Tsitsipas (typo corrigido via fuzzy) | OK |
| 17 | me conta uma curiosidade | Curiosidade aleatoria sobre tenis | OK |
| 18 | gosto do us open | Campeoes do US Open (open_topic -> torneio) | OK |
| 19 | melhor tenista espanhol | Melhores jogadores da Espanha (query parser) | OK |
| 20 | quem ganhou o australian open | Campeoes do Australian Open | OK |

**Estado final da sessao**: 20 turnos, 40 entries no historico, 22 jogadores mencionados.

---

## Teste de Fuzzy Matching (Tolerancia a Typos)

Validacao do `_fuzzy_match_player` com `difflib.SequenceMatcher` e threshold de 0.65 (contexto) / 0.75 (global).

| Input com Typo | Jogador Esperado | Ratio | Resultado |
|---------------|-----------------|-------|-----------|
| Medevedev | Daniil Medvedev | 0.82 | OK |
| Tsitipas | Stefanos Tsitsipas | 0.88 | OK |
| Danill Medevedev | Daniil Medvedev | 0.77 | OK |
| Alcaras | Carlos Alcaraz | 0.86 | OK |

### Falsos Positivos Corrigidos (Stop Words)

Palavras comuns do portugues que geravam falsos positivos antes da correcao:

| Palavra | Falso Match | Ratio | Status |
|---------|-----------|-------|--------|
| "dela" | "Elena" Rybakina | 0.67 | Bloqueado (stop word) |
| "dela" | "Elina" Svitolina | 0.67 | Bloqueado (stop word) |
| "conta" | "Constant" Lestienne | 0.77 | Bloqueado (stop word) |
| "gosto" | - | - | Bloqueado (stop word) |
| "curiosidade" | - | - | Bloqueado (stop word) |

A lista de stop words contem 80+ palavras comuns em portugues filtradas antes do fuzzy.

---

## Teste do Query Parser (Pais/Temporal/Superlativo)

Validacao do `parse_query()` com string matching direto (sem stems).

| Input | country_filter | wants_best | is_current | Resultado |
|-------|---------------|-----------|-----------|-----------|
| qual o melhor jogador do brasil atualmente | Brasil | True | True | OK |
| melhor tenista brasileiro | Brasil | True | False | OK |
| ranking atp brasileiro | Brasil | False | False | OK |
| melhor tenista espanhol | Espanha | True | False | OK |
| ranking wta | None | False | False | OK |
| jogadores da italia | Italia | False | False | OK |

---

## Teste de Contexto: focus_player

Validacao de que `focus_player` rastreia o ultimo jogador discutido em detalhe, nao o ultimo mencionado na lista.

| Acao | focus_player | Correto |
|------|-------------|---------|
| Apos ranking atp (10 jogadores listados) | None | OK |
| Apos "Sinner" (ficha mostrada) | Jannik Sinner | OK |
| Apos "qual o pais dele" (pais mostrado) | Jannik Sinner | OK |
| Apos "Alcaraz" (nova ficha) | Carlos Alcaraz | OK |
| Apos "Fonseca" (ficha apos query Brasil) | Joao Fonseca | OK |
| Apos "Sabalenka" (ficha WTA) | Aryna Sabalenka | OK |

---

## Teste de Prioridade: Torneio vs Jogador

Validacao de que nomes de torneio tem prioridade sobre fuzzy match de jogador na arvore de decisao.

| Contexto Anterior | Input | Esperado | Resultado |
|------------------|-------|----------|-----------|
| Ficha do Alcaraz (player_detail) | gosto de roland garros | Campeoes RG | OK |
| Ficha do Sinner (player_detail) | e wimbledon? | Campeoes Wimbledon | OK |
| Curiosidade (open_topic) | gosto do us open | Campeoes US Open | OK |
| Campeoes RG (player_from_ranking) | e wimbledon? | Campeoes Wimbledon | OK |

Antes da correcao, "garros" fazia fuzzy match com "carlos" (ratio 0.67) e mostrava Alcaraz ao inves dos campeoes. Agora torneio e detectado primeiro.

---

## Teste de Scraping: Dados ATP e WTA

Validacao da integridade dos dados obtidos via scraping/API.

| Verificacao | ATP | WTA |
|------------|-----|-----|
| Total de jogadores | 100 | 100 |
| Posicoes sequenciais 1-100 | OK | OK |
| Zero duplicatas | OK | OK |
| Todos paises traduzidos para PT-BR | OK | OK |
| Nomes com acentos corrigidos | OK | OK |
| Pontos em ordem decrescente | OK | OK |

### Fontes de Dados
- **ATP**: tennisexplorer.com/ranking/atp-men/ (2 paginas, HTML scraping)
- **WTA**: api.wtatennis.com/tennis/players/ranked (API JSON oficial)
- **Fallback WTA**: tennisexplorer.com/ranking/wta-women/ (se API falhar)

### Nomes Corrigidos pelo Scraper

| Nome no Site | Nome Corrigido |
|-------------|---------------|
| Fonseca Joao | Joao Fonseca |
| Auger Aliassime Felix | Felix Auger-Aliassime |
| Lehecka Jiri | Jiri Lehecka |
| Etcheverry Tomas Martin | Tomas Martin Etcheverry |
| Cerundolo Juan Manuel | Juan Manuel Cerundolo |

---

## Teste de Sessao: Expiracao e Limites

| Cenario | Resultado |
|---------|-----------|
| Nova aba gera novo session_id | OK (crypto.randomUUID + sessionStorage) |
| Sessao persiste entre mensagens | OK (mesmo session_id enviado) |
| Historico limitado a 40 entries (20 turnos x2) | OK |
| turn_count incrementa a cada mensagem do usuario | OK |
| Sessoes expiram apos 30min de inatividade | OK (cleanup_expired) |

---

## Teste Off-Topic

| Input | Resultado |
|-------|-----------|
| quem ganhou a copa do mundo | Bloqueado ("copa" + "futebol" detectados) |
| resultado do basquete | Bloqueado ("basquete" detectado) |
| receita de bolo | Bloqueado ("receita" detectado) |
| ranking atp | Permitido (tenis) |

---

## Como Executar os Testes

Os testes sao executados via test client do Flask sem precisar do navegador:

```python
import app as app_module
client = app_module.app.test_client()

# Enviar mensagem
response = client.post('/predict', json={
    'message': 'ranking atp',
    'session_id': 'test-session'
})
data = response.get_json()
print(data['answer'])  # Resposta do bot
print(data['logs'])    # Logs tecnicos
```

Para testar no navegador, inicie o servidor e acesse http://127.0.0.1:5000/:

```bash
python app.py
```
