# =============================================================================
# llm_client.py — Cliente do LLM de fallback (Arquitetura Híbrida)
# -----------------------------------------------------------------------------
# A base de conhecimento (knowledge_base.json + tennis_data.json) responde
# PRIMEIRO. Quando ela não tem informação suficiente, este módulo consulta um
# Modelo de Linguagem (LLM) como FALLBACK.
#
# O modelo roda LOCALMENTE no LM Studio, que expõe um servidor compatível com a
# API da OpenAI em http://localhost:1234/v1. O LM Studio baixa os modelos
# diretamente do Hugging Face Hub (formato GGUF), cumprindo o requisito de usar
# um "modelo disponível em huggingface.co/models". Modelo recomendado:
# Qwen/Qwen2.5-7B-Instruct (forte em português, instruction-tuned, não-gated).
#
# IMPORTANTE — Degradação graciosa:
#   Tudo aqui é OPCIONAL. Se LLM_ENABLED != "1" (padrão) ou o LM Studio estiver
#   desligado/indisponível, todas as funções retornam None silenciosamente e o
#   app.py recai nas respostas canned originais. É isso que mantém os 170 testes
#   verdes (eles rodam com LLM_ENABLED=0).
# =============================================================================

import os        # Leitura de variáveis de ambiente (configuração via .env)
import json      # Leitura/escrita do arquivo de métricas
import time      # Medição da latência (tempo médio de resposta) do LLM
import re        # Detecção de caracteres CJK (chinês/japonês/coreano) na resposta
import requests  # Cliente HTTP para falar com o servidor local do LM Studio
from datetime import datetime  # Carimbo de data/hora nas métricas

# Qwen ocasionalmente "vaza" para o chinês. Este regex detecta CJK para forçarmos
# português (re-tentativa + sanitização da resposta).
_CJK_RE = re.compile(r'[぀-ヿ㐀-鿿가-힯ｦ-ﾟ]')


def _strip_cjk(text):
    """Se sobrar chinês/japonês/coreano, corta a partir do 1º caractere CJK e
    limpa conectores/pontuação pendurados no fim."""
    if not text:
        return text
    m = _CJK_RE.search(text)
    if not m:
        return text
    head = text[:m.start()].rstrip()
    head = re.sub(r'[\s,;:\-–—(]+$', '', head)  # remove pontuação solta no fim
    return head.strip()

# Carrega variáveis do arquivo .env, se existir. O python-dotenv NÃO sobrescreve
# variáveis já definidas no ambiente (override=False por padrão) — é justamente
# isso que permite o run_tests.py forçar LLM_ENABLED=0 antes de importar o app.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass  # Sem dotenv instalado? Seguimos lendo direto de os.environ.

# -----------------------------------------------------------------------------
# Configuração (lida do ambiente / .env)
# -----------------------------------------------------------------------------
LLM_BASE_URL    = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
LLM_MODEL       = os.getenv("LLM_MODEL", "qwen2.5-7b-instruct")
LLM_TIMEOUT     = float(os.getenv("LLM_TIMEOUT", "30"))      # segundos por requisição
LLM_MAX_TOKENS  = int(os.getenv("LLM_MAX_TOKENS", "350"))    # limite de saída
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.5")) # criatividade controlada
METRICS_FILE    = os.getenv("LLM_METRICS_FILE", "llm_metrics.json")

# Persona do assistente. Mantém o foco em tênis, mas permite responder perguntas
# gerais (é o que o fallback universal exige), pedindo honestidade para reduzir
# alucinação.
# O bot é FECHADO no tema tênis. O LLM só entra para perguntas de TÊNIS que a base
# local não cobre (ex.: jogador fora do Top 100, fato histórico). Se a pergunta NÃO
# for de tênis, o modelo devolve a sentinela FORA_DO_TEMA e o app bloqueia (avisa).
# Prompt curto de propósito: cada token pesa no tempo de resposta em CPU.
OFF_TOPIC_SENTINEL = "FORA_DO_TEMA"
SYSTEM_PROMPT = (
    "Você é o assistente do 'ChatBot Tenista', especializado EXCLUSIVAMENTE em tênis "
    "(ATP/WTA: jogadores, torneios, regras, história, estatísticas). "
    "Responda SEMPRE em português do Brasil (nunca em chinês, inglês ou outro idioma). "
    "Se a pergunta FOR sobre tênis, responda o fato de forma correta e MUITO direta "
    "(1 a 2 frases); se não tiver certeza, admita. "
    "Se a pergunta NÃO for sobre tênis, responda EXCLUSIVAMENTE com esta palavra, sem "
    "mais nada: " + OFF_TOPIC_SENTINEL + "."
)


def _enabled():
    """O fallback LLM só age quando LLM_ENABLED == '1'. Padrão: desligado."""
    return os.getenv("LLM_ENABLED", "0").strip() == "1"


# -----------------------------------------------------------------------------
# Métricas (alimentam a seção "Resultados e Discussão" do relatório)
# -----------------------------------------------------------------------------
# Acumulamos em llm_metrics.json: quantas perguntas a BASE resolveu, quantas o
# LLM resolveu, falhas do LLM, não resolvidas e a latência somada do LLM (para
# calcular o tempo médio de resposta).
_METRIC_KEYS = ("resolved_by_base", "resolved_by_llm", "llm_failures", "unresolved")


def _load_metrics():
    """Lê o arquivo de métricas (ou devolve a estrutura zerada)."""
    base = {k: 0 for k in _METRIC_KEYS}
    base["llm_total_latency"] = 0.0  # soma das latências (segundos)
    base["llm_latency_count"] = 0    # nº de respostas do LLM medidas
    base["updated_at"] = None
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                base.update(json.load(f))
        except Exception:
            pass  # Arquivo corrompido/vazio? Recomeça do zero.
    return base


def record(kind, latency=None):
    """Registra um desfecho de resposta. No-op quando o LLM está desligado
    (assim os testes não geram/poluem o arquivo de métricas).

    kind: 'resolved_by_base' | 'resolved_by_llm' | 'llm_failures' | 'unresolved'
    latency: tempo (s) da chamada ao LLM, quando aplicável.
    """
    if not _enabled():
        return
    m = _load_metrics()
    if kind in _METRIC_KEYS:
        m[kind] = m.get(kind, 0) + 1
    if latency is not None:
        m["llm_total_latency"] = m.get("llm_total_latency", 0.0) + float(latency)
        m["llm_latency_count"] = m.get("llm_latency_count", 0) + 1
    m["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def metrics_snapshot():
    """Resumo legível das métricas (percentuais + latência média)."""
    m = _load_metrics()
    total = m["resolved_by_base"] + m["resolved_by_llm"] + m["unresolved"]
    avg_latency = (m["llm_total_latency"] / m["llm_latency_count"]) if m["llm_latency_count"] else 0.0
    pct = lambda n: round(100 * n / total, 1) if total else 0.0
    return {
        "total_perguntas": total,
        "resolvidas_pela_base": m["resolved_by_base"],
        "resolvidas_pelo_llm": m["resolved_by_llm"],
        "nao_resolvidas": m["unresolved"],
        "falhas_llm": m["llm_failures"],
        "pct_base": pct(m["resolved_by_base"]),
        "pct_llm": pct(m["resolved_by_llm"]),
        "pct_nao_resolvidas": pct(m["unresolved"]),
        "tempo_medio_llm_s": round(avg_latency, 2),
        "atualizado_em": m["updated_at"],
    }


# -----------------------------------------------------------------------------
# Comunicação com o LM Studio
# -----------------------------------------------------------------------------
def is_available():
    """Health-check rápido: o servidor do LM Studio está no ar?
    Retorna False imediatamente se o fallback estiver desligado."""
    if not _enabled():
        return False
    try:
        r = requests.get(f"{LLM_BASE_URL}/models", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def is_on_topic(user_text):
    """Validador AUTORITATIVO de tópico via Qwen (Camada 3 do roteamento off-topic).

    A blocklist nunca cobre todos os assuntos fora de tênis; quando as regras não
    decidem e há contexto ativo sem sinal de tênis, é ESTE classificador que diz,
    "de fato", se a pergunta é sobre tênis. Mantém-se rápido: prompt mínimo e
    saída de 1 token.

    Retorna:
        True  → o modelo respondeu um "sim" (é sobre tênis).
        False → o modelo respondeu um "não" CONFIANTE (fora de tênis). Direção
                segura: só tira da base com um "não" claro.
        None  → LLM desligado, servidor fora, timeout ou resposta inconclusiva.
                Nunca lança exceção.
    """
    if not _enabled():
        return None

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": (
                "Você é um classificador de tópico. Responda APENAS com uma única "
                "palavra: 'sim' ou 'não'. A pergunta do usuário é sobre TÊNIS "
                "(jogadores, torneios, regras, ATP/WTA, história ou estatísticas do "
                "tênis)? Se for sobre qualquer outro assunto, responda 'não'."
            )},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.0,
        "max_tokens": 2,
        "stream": False,
    }

    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            json=payload,
            timeout=min(LLM_TIMEOUT, 8.0),  # checagem precisa ser rápida
        )
        resp.raise_for_status()
        data = resp.json()
        answer = (data["choices"][0]["message"]["content"] or "").strip().lower()
    except Exception:
        return None  # Indisponível → não bloqueia o fluxo normal.

    # Normaliza acentos/pontuação e olha só o começo da resposta.
    answer = answer.replace("ã", "a").replace("á", "a").lstrip("\"'` ")
    if answer.startswith(("nao", "no")):
        return False
    if answer.startswith(("sim", "yes", "y")):
        return True
    return None  # Resposta inconclusiva → trata como indisponível.


def query_llm(user_text, grounding=None, history=None):
    """Consulta o LLM (LM Studio) como fallback.

    user_text: a pergunta do usuário.
    grounding: contexto factual opcional (ex.: dados de um jogador) injetado no
               system prompt para reduzir alucinação.
    history:   lista opcional de mensagens anteriores [{"role","content"}, ...].

    Retorna {"answer": str, "latency": float} em caso de sucesso, ou None em
    QUALQUER falha (desligado, servidor fora, timeout, resposta vazia) — deixando
    o app.py recair na resposta canned.
    """
    if not _enabled():
        return None

    system_content = SYSTEM_PROMPT
    if grounding:
        system_content += (
            "\n\nContexto factual do sistema (use se for relevante, ignore se não for):\n"
            + grounding
        )

    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history)
    # Lembrete de idioma anexado à PRÓPRIA pergunta (recência máxima): é o texto que
    # o modelo responde diretamente, então trava melhor o português em modelos pequenos
    # (Qwen tende a "vazar" para chinês/inglês quando a instrução fica longe).
    messages.append({
        "role": "user",
        "content": user_text + "\n\n(Importante: escreva a resposta INTEIRA em português do Brasil, "
                                "sem nenhuma palavra em chinês, japonês ou inglês.)",
    })

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "stream": False,
    }

    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            json=payload,
            timeout=LLM_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = (data["choices"][0]["message"]["content"] or "").strip()

        # Qwen às vezes mistura chinês: re-tenta com prompt LIMPO e, no fim, sanitiza.
        if answer and _CJK_RE.search(answer):
            try:
                # Retry LIMPO: descarta o histórico (principal gatilho da confusão);
                # mantém só persona + grounding + a pergunta, com idioma reforçado.
                retry = dict(payload)
                retry["temperature"] = 0.2
                retry["messages"] = [
                    {"role": "system", "content": system_content +
                        "\n\nRESPONDA EXCLUSIVAMENTE EM PORTUGUÊS DO BRASIL. É proibido escrever "
                        "qualquer palavra em chinês, japonês, coreano ou inglês."},
                    {"role": "user", "content": user_text + "\n\n(Responda em português do Brasil.)"},
                ]
                r2 = requests.post(f"{LLM_BASE_URL}/chat/completions", json=retry, timeout=LLM_TIMEOUT)
                r2.raise_for_status()
                d2 = r2.json()
                a2 = (d2["choices"][0]["message"]["content"] or "").strip()
                if a2:
                    answer, data = a2, d2
            except Exception:
                pass
            answer = _strip_cjk(answer)

        latency = time.perf_counter() - start

        if not answer:
            record("llm_failures")
            return None

        record("resolved_by_llm", latency=latency)
        usage = data.get("usage") or {}
        return {
            "answer": answer,
            "latency": latency,
            # Detalhes da chamada — alimentam o "inspetor de API" no pipeline visual
            "request": {
                "method": "POST",
                "endpoint": f"{LLM_BASE_URL}/chat/completions",
                "model": LLM_MODEL,
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "messages": messages,
            },
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
            "finish_reason": (data["choices"][0] or {}).get("finish_reason"),
        }
    except Exception:
        record("llm_failures")
        return None
