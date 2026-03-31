# Banco de Dados e Fluxo de Atualizacao (Scraping/API)

Este documento detalha como o chatbot obtem, armazena e atualiza os dados de rankings de tenis.

---

## Estrutura do Banco de Dados (`tennis_data.json`)

O projeto utiliza um arquivo JSON como banco de dados local. Nao ha banco relacional (MySQL, PostgreSQL) — toda a informacao fica em memoria apos o carregamento.

### Campos Principais

```json
{
  "last_updated": "2026-03-30T23:07:32",
  "ranking_atp": [ ... ],
  "ranking_wta": [ ... ],
  "grand_slams": { ... },
  "player_details": { ... }
}
```

### ranking_atp / ranking_wta (Top 100)

Cada entrada representa um jogador no ranking:

```json
{
  "position": 1,
  "name": "Carlos Alcaraz",
  "country": "Espanha",
  "points": "13590"
}
```

- **100 jogadores ATP** + **100 jogadoras WTA**.
- Posicoes sequenciais de 1 a 100, sem duplicatas.
- Paises traduzidos para portugues brasileiro.
- Nomes corrigidos com acentos (ex: Joao -> Joao Fonseca).

### grand_slams (Historico 2024-2026)

```json
{
  "2026": {
    "Australian Open": {
      "Masculino": {"campeao": "Jannik Sinner", "vice": "Carlos Alcaraz"},
      "Feminino": {"campeao": "Aryna Sabalenka", "vice": "Iga Swiatek"}
    }
  }
}
```

### player_details (~50 jogadores)

```json
{
  "Jannik Sinner": {
    "age": 24,
    "style": "Destro",
    "titles": "AO 2024/2025, US Open 2024",
    "country": "Italia",
    "fact": "Primeiro italiano #1."
  }
}
```

---

## Fontes de Dados Externas

### ATP — tennisexplorer.com (Scraping HTML)

O site oficial da ATP (`atptour.com`) utiliza Cloudflare e bloqueia requisicoes diretas (retorna 403). Por isso, utilizamos o tennisexplorer.com como fonte alternativa.

**URL**: `https://www.tennisexplorer.com/ranking/atp-men/`

**Estrategia**:
- Pagina 1 (`?page=1`): Posicoes 1-50
- Pagina 2 (`?page=2`): Posicoes 51-100
- Parsing via BeautifulSoup: tabela HTML `<table class="result">`

**Formato dos dados no site**:
```
Posicao | Movimento | Nome (Sobrenome Primeiro) | Pais (Ingles) | Pontos
  1.    |     -     | Alcaraz Carlos            | Spain         | 13590
```

**Transformacoes aplicadas**:
1. **Inversao de nome**: "Alcaraz Carlos" -> "Carlos Alcaraz" (funcao `_flip_name`)
2. **Traducao de pais**: "Spain" -> "Espanha" (dicionario `COUNTRY_EN_TO_PT` com 50+ paises)
3. **Correcao de acentos**: "Joao Fonseca" -> "Joao Fonseca" (dicionario `NAME_CORRECTIONS`)
4. **Nomes compostos**: "Etcheverry Tomas Martin" -> "Tomas Martin Etcheverry" (correcao manual)

**Headers HTTP**:
```python
{
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Accept": "text/html,application/xhtml+xml",
}
```

---

### WTA — api.wtatennis.com (API JSON Oficial)

A WTA disponibiliza uma API REST publica que retorna JSON limpo, sem necessidade de autenticacao ou API key.

**Endpoint**:
```
GET https://api.wtatennis.com/tennis/players/ranked
    ?metric=SINGLES
    &type=rankSingles
    &sort=asc
    &pageSize=100
    &page=0
```

**Headers obrigatorios**:
```python
{
    "account": "wta",
    "referer": "https://www.wtatennis.com/"
}
```

**Resposta JSON** (array de objetos):
```json
[
  {
    "player": {
      "fullName": "Aryna Sabalenka",
      "countryCode": "BLR",
      "dateOfBirth": "1998-05-05"
    },
    "ranking": 1,
    "points": 11025,
    "tournamentsPlayed": 20,
    "movement": 0
  }
]
```

**Transformacoes aplicadas**:
1. **Traducao de codigo de pais**: "BLR" -> "Bielorrussia" (dicionario `COUNTRY_CODE_TO_PT` com 60+ codigos ISO-3)
2. **Limpeza de espacos duplos** nos nomes (funcao `_clean_name`)

**Fallback**: Se a API WTA estiver fora do ar, o sistema automaticamente tenta scraping via tennisexplorer.com (`/ranking/wta-women/`).

---

## Fluxo de Atualizacao

```
[Startup do Servidor (app.py)]
         |
  api_client.refresh_if_needed()
         |
  Verifica campo "last_updated" no tennis_data.json
         |
    Mais de 24h?
    /         \
  NAO         SIM
   |           |
  Pula      Inicia refresh
   |           |
   |     [ATP] Scraping tennisexplorer.com (2 paginas)
   |           |
   |     [WTA] API JSON wtatennis.com (1 request)
   |           |   \-- fallback: tennisexplorer.com
   |           |
   |     Traduz paises, inverte nomes, corrige acentos
   |           |
   |     Salva em tennis_data.json + atualiza last_updated
   |           |
  TennisEngine carrega dados atualizados
         |
  Servidor pronto para receber requisicoes
```

### Detalhes do Cache

| Parametro | Valor |
|-----------|-------|
| TTL do cache | 24 horas (86400 segundos) |
| Campo de controle | `last_updated` (ISO 8601) |
| Fallback se falhar | Mantem dados existentes, marca timestamp |
| Re-tentativa | So no proximo startup apos 24h |

### Tratamento de Erros

- **Rede indisponivel**: O scraping/API falha silenciosamente, mantendo dados estaticos.
- **Site mudou estrutura**: BeautifulSoup nao encontra tabela -> retorna None -> fallback.
- **API WTA fora**: Tenta automaticamente via tennisexplorer como fallback.
- **JSON corrompido**: `_load_data()` retorna `{}`, bot funciona sem rankings.

---

## Dependencias

| Biblioteca | Uso |
|-----------|-----|
| `requests` | Requisicoes HTTP para scraping e API |
| `beautifulsoup4` | Parsing de HTML do tennisexplorer |
| `json` (stdlib) | Leitura/escrita do banco de dados JSON |

Instalacao:
```bash
pip install requests beautifulsoup4
```

---

## Resumo dos Dicionarios de Traducao

### COUNTRY_EN_TO_PT (Ingles -> Portugues)
Usado para traduzir paises do tennisexplorer.
```
"Spain" -> "Espanha", "Italy" -> "Italia", "Germany" -> "Alemanha",
"Brazil" -> "Brasil", "USA" -> "EUA", "Great Britain" -> "Reino Unido", ...
```
Total: 50+ paises.

### COUNTRY_CODE_TO_PT (ISO-3 -> Portugues)
Usado para traduzir codigos da API WTA.
```
"ESP" -> "Espanha", "ITA" -> "Italia", "GER" -> "Alemanha",
"BRA" -> "Brasil", "USA" -> "EUA", "GBR" -> "Reino Unido", ...
```
Total: 60+ codigos.

### NAME_CORRECTIONS (Nome Scrapeado -> Nome Correto)
Corrige acentos e nomes compostos invertidos.
```
"Joao Fonseca" -> "Joao Fonseca"
"Felix Auger Aliassime" -> "Felix Auger-Aliassime"
"Manuel Cerundolo Juan" -> "Juan Manuel Cerundolo"
```
Total: ~15 correcoes.
