# =============================================================================
# web_search.py — Camada de PESQUISA (retrieval) em fonte confiável
# -----------------------------------------------------------------------------
# "Modo pesquisa" do ChatBot Tenista: quando a base local (tennis_data.json /
# knowledge_base.json) NÃO cobre a pergunta, este módulo busca o fato numa fonte
# confiável (WIKIPEDIA) e devolve um trecho curto. Esse trecho é injetado como
# "grounding" no prompt do LLM (ver app.build_grounding) — assim o modelo responde
# A PARTIR DA FONTE, e não da memória (que alucina em jogadores/fatos específicos).
#
# Fonte ÚNICA: Wikipedia (grátis, sem API key, ótima cobertura de tênis em PT).
#   - MediaWiki Search API : acha o título mais provável da página.
#   - REST Summary API     : devolve o resumo (extrato) factual da página.
#
# IMPORTANTE — Degradação graciosa (igual ao llm_client/api_client):
#   Tudo aqui é OPCIONAL. Se WEB_SEARCH_ENABLED != "1" ou a rede/Wikipedia estiver
#   fora, TODAS as funções retornam None silenciosamente. Os testes (run_tests.py)
#   forçam WEB_SEARCH_ENABLED=0 → nenhuma chamada de rede no CI (determinismo).
# =============================================================================

import os        # Leitura de variáveis de ambiente (configuração via .env)
import re        # Detecção de "sinal de tênis" no resumo (desambiguação)
import requests  # Cliente HTTP para falar com a API da Wikipedia

# Carrega o .env (sem sobrescrever variáveis já no ambiente — deixa o run_tests.py
# forçar WEB_SEARCH_ENABLED=0 antes de importar o app).
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass  # Sem python-dotenv? Seguimos lendo direto de os.environ.

# -----------------------------------------------------------------------------
# Configuração (lida do ambiente / .env)
# -----------------------------------------------------------------------------
WEB_SEARCH_LANG    = os.getenv("WEB_SEARCH_LANG", "pt").strip()      # idioma primário
WEB_SEARCH_TIMEOUT = float(os.getenv("WEB_SEARCH_TIMEOUT", "8"))     # timeout (s) por requisição
_MAX_EXTRACT_CHARS = 1300                                            # corta o extrato p/ caber no prompt

# User-Agent descritivo (a Wikipedia recomenda identificar a aplicação).
_HEADERS = {"User-Agent": "ChatBotTenista/1.0 (projeto educacional; contato: local)"}

# "Sinal de tênis": só aceitamos um resumo da Wikipedia se ele parecer ser sobre
# tênis. Isso evita ancorar na ENTIDADE ERRADA (ex.: um homônimo que não é tenista)
# e mantém a honestidade — sem sinal de tênis, tratamos como "não encontrado".
_TENNIS_SIGNAL_RE = re.compile(
    r'\b(t[êe]nis|tennis|tenist[ao]|atp|wta|grand\s*slam|roland\s*garros|wimbledon|'
    r'us\s*open|australian\s*open|raquete|saibro|simples|duplas|torneio)\b',
    re.IGNORECASE,
)

# Cache em memória: evita refazer a mesma busca na Wikipedia dentro do processo.
_CACHE = {}


def enabled():
    """A camada de pesquisa só age quando WEB_SEARCH_ENABLED == '1'. Padrão: ligado.
    Os testes forçam '0' para rodar sem rede (determinismo)."""
    return os.getenv("WEB_SEARCH_ENABLED", "1").strip() == "1"


def _dbg(msg):
    """Print de debug À PROVA DE FALHAS. No Windows o console é cp1252 e não encoda
    '→'/emoji; sem isto, um print de debug lançava UnicodeEncodeError que era engolido
    por build_grounding e DESATIVAVA a pesquisa web (a IA caía na memória e alucinava).
    Aqui o print nunca derruba a pesquisa: cai para ASCII e, no pior caso, falha calado."""
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def _wiki_search_title(query, lang):
    """Acha o título da página mais provável para `query` na Wikipedia (idioma `lang`).
    Retorna o título (str) ou None."""
    try:
        r = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query", "list": "search", "srsearch": query,
                "format": "json", "srlimit": 1,
            },
            headers=_HEADERS, timeout=WEB_SEARCH_TIMEOUT,
        )
        r.raise_for_status()
        hits = r.json().get("query", {}).get("search", [])
        return hits[0]["title"] if hits else None
    except Exception:
        return None  # Rede/HTTP/JSON falhou → sem título.


def _wiki_extract(title, lang):
    """Extrato factual da página `title`. Tenta a INTRO COMPLETA (mais rica — traz
    títulos, marcos, nascimento, etc., via MediaWiki `prop=extracts`) e cai para o
    resumo curto (REST Summary) se preciso. Retorna o texto (str) ou None."""
    # 1) Intro COMPLETA (prose) — bem mais informativa que a 1ª frase do resumo.
    try:
        r = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query", "prop": "extracts", "exintro": 1,
                "explaintext": 1, "redirects": 1, "format": "json", "titles": title,
            },
            headers=_HEADERS, timeout=WEB_SEARCH_TIMEOUT,
        )
        r.raise_for_status()
        for p in r.json().get("query", {}).get("pages", {}).values():
            ex = (p.get("extract") or "").strip()
            if ex and len(ex) > 60:
                return ex
    except Exception:
        pass
    # 2) Fallback: resumo curto (REST Summary API).
    try:
        r = requests.get(
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}",
            headers=_HEADERS, timeout=WEB_SEARCH_TIMEOUT,
        )
        if r.status_code == 200:
            return (r.json().get("extract") or "").strip()
    except Exception:
        pass
    return None


# Campos ÚTEIS do infobox (dados estruturados que a intro em prosa NÃO traz): mão
# (destro/canhoto), treinador, altura, etc. Mapeia variações de chave → rótulo limpo.
_INFOBOX_KEYS = {
    "mao": "mão", "mão": "mão", "plays": "mão",
    "treinador": "treinador", "treinadora": "treinador", "técnico": "treinador",
    "tecnico": "treinador", "coach": "treinador",
    "altura": "altura", "height": "altura",
    "profissional": "profissional desde", "profissionalização": "profissional desde",
    "profissionalizacao": "profissional desde", "turnedpro": "profissional desde",
    "prizemoney": "prize money", "prize money": "prize money", "money": "prize money",
    "residência": "residência", "residencia": "residência",
}


def _clean_wiki(v):
    """Remove marcação wiki (refs, templates, links, html) de um valor do infobox."""
    v = re.sub(r'<ref[^>]*>.*?</ref>', '', v, flags=re.S)   # <ref>...</ref>
    v = re.sub(r'<ref[^>]*/>', '', v)                       # <ref .../>
    v = re.sub(r'\{\{[^{}]*\}\}', ' ', v)                   # {{templates}}
    v = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', v) # [[a|b]] → b
    v = v.replace("'''", "").replace("''", "")
    v = re.sub(r'<[^>]+>', '', v)                           # html
    return re.sub(r'\s+', ' ', v).strip(" .;,|")


def _wiki_infobox(title, lang):
    """Lê o INFOBOX (seção 0, wikitext) e devolve um resumo dos campos úteis (mão,
    treinador, altura…) — onde vivem fatos que a intro em prosa não menciona.
    Retorna string curta ou None."""
    try:
        r = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query", "prop": "revisions", "rvprop": "content",
                "rvslots": "main", "rvsection": 0, "redirects": 1,
                "format": "json", "titles": title,
            },
            headers=_HEADERS, timeout=WEB_SEARCH_TIMEOUT,
        )
        r.raise_for_status()
        wt = ""
        for p in r.json().get("query", {}).get("pages", {}).values():
            revs = p.get("revisions")
            if revs:
                wt = revs[0].get("slots", {}).get("main", {}).get("*", "")
                break
        if not wt:
            return None
        found = {}
        for line in wt.splitlines():
            m = re.match(r'\s*\|\s*([\wÀ-ÿ ]+?)\s*=\s*(.+)', line)
            if not m:
                continue
            key = m.group(1).strip().lower()
            label = _INFOBOX_KEYS.get(key)
            if label and label not in found:
                val = _clean_wiki(m.group(2))
                if val and len(val) < 90:
                    found[label] = val
        if not found:
            return None
        return "Dados (Wikipedia infobox): " + "; ".join(f"{k}: {v}" for k, v in found.items()) + "."
    except Exception:
        return None


# -----------------------------------------------------------------------------
# DuckDuckGo (busca web geral) — FALLBACK grátis e SEM API key. Complementa a
# Wikipedia com fatos específicos/ATUAIS que a enciclopédia não traz (ex.: a marca
# da raquete, patrocínios, notícias recentes).
# -----------------------------------------------------------------------------
_DDG_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _ddg_enabled():
    return os.getenv("WEB_DDG_ENABLED", "1").strip() == "1"


def _parse_ddg_html(html, max_results=3):
    """Extrai [{title, url, snippet}] do HTML do DuckDuckGo. Função PURA (sem rede) p/ ser
    testável. ROBUSTEZ: o link primário vem pela classe `result__a`; se o DDG mudar a classe,
    cai no fallback ESTRUTURAL (qualquer âncora com o redirect `uddg=`). O snippet é OPCIONAL
    — um resultado entra com título+url mesmo sem snippet (antes, se a classe `result__snippet`
    mudasse, TODOS os resultados eram descartados pela exigência de snippet)."""
    from urllib.parse import unquote
    links = re.findall(r'result__a"[^>]*href="(.*?)"[^>]*>(.*?)</a>', html, re.S)
    if not links:  # fallback: âncoras com o redirect uddg= (independe do nome da classe CSS)
        links = re.findall(r'href="([^"]*uddg=[^"]*)"[^>]*>(.*?)</a>', html, re.S)
    snips = re.findall(r'result__snippet[^>]*>(.*?)</a>', html, re.S)
    out = []
    for i, (href, title) in enumerate(links[:max_results]):
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', title)).strip()
        s = ""
        if i < len(snips):
            s = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', snips[i])).strip()
        url = href
        mu = re.search(r'uddg=([^&]+)', href)   # DDG usa redirect: extrai o URL real
        if mu:
            url = unquote(mu.group(1))
        if t:   # título basta; snippet pode faltar se o DDG mudar a classe (degrada melhor)
            out.append({"title": t, "url": url, "snippet": s[:280]})
    return out


def _ddg_search(query, max_results=3):
    """Busca web no DuckDuckGo (HTML) → lista [{title, url, snippet}]. [] em falha/sem rede."""
    try:
        r = requests.post("https://html.duckduckgo.com/html/", data={"q": query},
                          headers=_DDG_HEADERS, timeout=WEB_SEARCH_TIMEOUT)
        r.raise_for_status()
        return _parse_ddg_html(r.text, max_results)
    except Exception:
        return []


# -----------------------------------------------------------------------------
# Busca DIRECIONADA por CONTEXTO. A pergunta crua faz o DuckDuckGo devolver "raquete"
# para quase todo equipamento (raquete domina a indexação desses jogadores e "tênis" é
# a palavra do ESPORTE). Quando reconhecemos o contexto com confiança, montamos uma
# busca ancorada no jogador: "{jogador} {termos do contexto}". Sem reconhecimento →
# devolvemos a query crua (preserva os contextos que já funcionam: namorada, lesão,
# treinador, curiosidade, confronto…). Regex com \b evita falsos positivos por substring
# (ex.: "concorda"/"recorda" NÃO casam "corda").
# -----------------------------------------------------------------------------

# "tênis" = CALÇADO (e não o esporte) quando vem como objeto possuído ("o tênis do X",
# "que tênis ele usa") OU quando há palavra explícita de calçado.
_FOOTWEAR_RE = re.compile(
    r'\b(cal[çc]ados?|sapatos?|sapat[êe]nis|chuteiras?|sapatilhas?)\b'
    r'|\b(o|os|que|qual|um|seu)\s+t[êe]nis\b'
    r'|t[êe]nis\s+(que|d[oae]|usad|nike|adidas|asics|nos\s+p[ée]s)',
    re.IGNORECASE)

# Regras de EQUIPAMENTO: (regex, rótulo p/ exibir, termo canônico, template de busca).
# ORDEM IMPORTA — mais específico primeiro. 'raqueteira' antes de 'raquete' (uma contém a
# outra como substring; o \b já protege, mas a ordem reforça). O rótulo é mostrado no
# painel ("contexto entendido"); o termo canônico é usado ao COMBINAR vários equipamentos.
_EQUIP_RULES = [
    (_FOOTWEAR_RE, "calçado", "tênis calçado", "tênis calçado que usa nos jogos"),
    (re.compile(r'\b(raqueteiras?|mochilas?|bolsas?|bag|malas?)\b', re.IGNORECASE),
     "raqueteira", "raqueteira", "raqueteira bag mochila"),
    (re.compile(r'\b(cordas?|encordoamento|strings?)\b', re.IGNORECASE),
     "cordas", "cordas", "cordas encordoamento tensão"),
    (re.compile(r'\b(raquetes?)\b', re.IGNORECASE),
     "raquete", "raquete", "raquete que usa"),
    (re.compile(r'\b(roupas?|vestu[áa]rio|camisas?|camisetas?|uniforme|outfit|'
                r'patroc[íi]nio|patrocinador(?:es)?|patrocinad[ao]s?|patrocina|bon[ée])\b',
                re.IGNORECASE),
     "roupa/patrocínio", "roupa patrocínio", "roupa vestuário patrocínio"),
]


def _match_equipment(raw):
    """Equipamentos detectados na pergunta → lista de (rótulo, termo, template), na ordem
    das regras (mais específico primeiro). Vazio = nenhum contexto de equipamento."""
    return [(label, term, tmpl) for rx, label, term, tmpl in _EQUIP_RULES if rx.search(raw)]


def _detected_context(query):
    """Rótulo humano do(s) contexto(s) de equipamento detectado(s), p/ exibir no painel —
    ou None quando a pergunta não é sobre equipamento (usa a busca crua)."""
    m = _match_equipment((query or "").strip())
    return " + ".join(label for label, _, _ in m) if m else None


def _targeted_ddg_query(query, player_hint=None):
    """Monta a busca DDG direcionada ao contexto da pergunta, ancorada no jogador.
    Sem jogador OU sem equipamento reconhecido → query crua (já acerta namorada/lesão/
    treinador/curiosidade/confronto). VÁRIOS equipamentos na mesma pergunta → combina os
    termos (ex.: 'raquete e corda' → '{jogador} cordas raquete'), sem perder nenhum."""
    raw = (query or "").strip()
    if not player_hint:
        return raw
    m = _match_equipment(raw)
    if not m:
        return raw
    if len(m) == 1:
        return f"{player_hint} {m[0][2]}"                        # template rico (1 contexto)
    return f"{player_hint} " + " ".join(term for _, term, _ in m)  # combina (2+ contextos)


def search_tennis(query, player_hint=None):
    """Pesquisa um fato de TÊNIS (Wikipedia + DuckDuckGo) e devolve grounding + fontes.

    query:       a pergunta/assunto do usuário (texto livre).
    player_hint: nome do jogador, quando já resolvido (melhora a desambiguação).

    Retorna um dict:
        {"text": <grounding p/ o prompt>, "sources": [{engine,title,url,snippet}], "query": str}
        OU None (desligado / sem rede / nada confiável — nunca lança exceção).
    """
    if not enabled():
        return None

    target = (player_hint or query or "").strip()
    if not target:
        return None

    cache_key = f"{WEB_SEARCH_LANG}:{target.lower()}::{(query or '').lower()}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    parts, sources = [], []

    # (1) WIKIPEDIA — base biográfica (intro + infobox), PT→EN.
    idiomas = [WEB_SEARCH_LANG] + (["en"] if WEB_SEARCH_LANG != "en" else [])
    for lang in idiomas:
        bias = "tenista" if lang == "pt" else "tennis player"
        title = _wiki_search_title(f"{target} {bias}", lang)
        if not title:
            continue
        extract = _wiki_extract(title, lang)
        if extract and len(extract) > 40 and _TENNIS_SIGNAL_RE.search(extract):
            if len(extract) > _MAX_EXTRACT_CHARS:
                extract = extract[:_MAX_EXTRACT_CHARS].rsplit(" ", 1)[0] + "…"
            infobox = _wiki_infobox(title, lang)
            corpo = (infobox + "\n" + extract) if infobox else extract
            parts.append(f"Contexto recuperado (Wikipedia — '{title}'): {corpo}")
            sources.append({
                "engine": "Wikipedia", "title": title,
                "url": f"https://{lang}.wikipedia.org/wiki/" + requests.utils.quote(title.replace(" ", "_")),
                "snippet": ((infobox + " ") if infobox else "") + extract[:200],
            })
            _dbg(f"[WEB_SEARCH] Wikipedia ({lang}): '{title}'")  # debug no terminal
            break

    # (2) DUCKDUCKGO — fallback web p/ fatos específicos/atuais (raquete, patrocínio…).
    if _ddg_enabled():
        ddg_q = _targeted_ddg_query(query or target, player_hint)
        web = _ddg_search(ddg_q)
        if web:
            # Inclui o TÍTULO além do snippet: muitas vezes o fato decisivo vive no
            # título do resultado (ex.: "Sabalenka anunció que se casa con…") e o snippet
            # traz só contexto vago. Sem o título, o LLM dizia "não há informação".
            parts.append("Resultados da web (DuckDuckGo):\n" + "\n".join(
                (f"- {w['title']}: {w['snippet']}" if w['snippet'] else f"- {w['title']}") for w in web))
            for w in web:
                sources.append({"engine": "DuckDuckGo", **w})
            _dbg(f"[WEB_SEARCH] DuckDuckGo '{ddg_q}' → {len(web)} resultado(s)")  # debug no terminal

    if not parts:
        _dbg(f"[WEB_SEARCH] Nada confiável para '{target}'")  # debug no terminal
        return None

    result = {"text": "\n\n".join(parts), "sources": sources, "query": (query or target),
              "context": _detected_context(query or target)}
    _CACHE[cache_key] = result
    return result
