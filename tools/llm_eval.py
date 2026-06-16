# =============================================================================
# tools/llm_eval.py — Avaliação AO VIVO do "modo pesquisa" (LLM + Wikipedia)
# -----------------------------------------------------------------------------
# Diferente do run_tests.py (determinístico, LLM/WEB_SEARCH DESLIGADOS), este
# harness LIGA o LLM (LM Studio) e a PESQUISA (Wikipedia) e roda uma bateria de
# cenários REAIS pelo pipeline completo (app.test_client → /predict). Serve para
# ITERAR a qualidade das respostas sem ninguém precisar colar o pipeline:
#   - imprime a resposta de cada cenário (revisão factual a olho), e
#   - aplica checagens ESTRUTURAIS de PASS/FAIL (roteou certo? não despejou a
#     ficha? bloqueou off-topic? acionou a pesquisa quando devia?).
#
# Uso:   python tools/llm_eval.py
# Requer: LM Studio no ar (porta 1234) com o modelo carregado + internet.
#         Sem servidor/rede, ele AVISA e sai (não é um teste de CI).
# =============================================================================

import os, sys, re

# Sobe um nível para importar o app a partir da raiz do projeto.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")  # evita mojibake no console Windows
except Exception:
    pass

# LIGA o LLM e a pesquisa ANTES de importar o app (o dotenv não sobrescreve isto).
os.environ["LLM_ENABLED"] = "1"
os.environ["WEB_SEARCH_ENABLED"] = "1"

import llm_client            # health-check do LM Studio
import app as app_module     # pipeline completo
client = app_module.app.test_client()

PASS, FAIL = 0, 0


def ask(msg, sid):
    """Envia uma mensagem ao /predict e devolve (texto_limpo, nomes_das_etapas)."""
    r = client.post("/predict", json={"message": msg, "session_id": sid})
    data = r.get_json()
    text = re.sub(r"<[^>]+>", "", data.get("answer", ""))
    steps = [s.get("name", "") for s in data.get("pipeline", [])]
    return text, steps


def check(label, msg, sid, *, must=None, forbid=None, any_of=None, want_search=False, setup=None):
    """Roda um cenário e aplica checagens estruturais; sempre imprime a resposta.
    must:   todas as substrings precisam aparecer. forbid: nenhuma pode aparecer.
    any_of: PELO MENOS UMA precisa aparecer (verifica que citou um fato específico)."""
    global PASS, FAIL
    if setup:
        for s in setup:
            ask(s, sid)
    resp, steps = ask(msg, sid)
    reasons = []
    low = resp.lower()
    for m in (must or []):
        if m.lower() not in low:
            reasons.append(f'faltou "{m}"')
    for f in (forbid or []):
        if f.lower() in low:
            reasons.append(f'apareceu "{f}" (parece ficha/indevido)')
    if any_of and not any(a.lower() in low for a in any_of):
        reasons.append(f'nenhum fato específico de {any_of}')
    if want_search and not any("Pesquisa" in s for s in steps):
        reasons.append("não acionou a etapa de Pesquisa (Wikipedia)")
    ok = not reasons
    PASS, FAIL = PASS + (1 if ok else 0), FAIL + (0 if ok else 1)
    print(f'\n[{"PASS" if ok else "FAIL"}] {label}')
    print(f'   Q: {msg}')
    print(f'   R: {resp[:300]}')
    if not ok:
        print(f'   ↳ {"; ".join(reasons)}')


NOT_FICHA = ["Rank Atual"]          # marcador EXCLUSIVO da ficha completa (a prosa da web pode citar "ATP")
BLOCK = "respiro apenas Tênis"      # mensagem de off-topic


def main():
    print("=" * 70)
    print("AVALIAÇÃO AO VIVO — LLM (LM Studio) + Pesquisa (Wikipedia)")
    print("=" * 70)
    if not llm_client.is_available():
        print("\n[ABORTADO] LM Studio indisponível em", llm_client.LLM_BASE_URL)
        print("Ligue o servidor (Start Server, porta 1234) e rode de novo.")
        print("Este harness NÃO faz parte do CI — run_tests.py roda com tudo desligado.")
        return

    # 1) Curiosidade de jogador NA BASE → responde a curiosidade, SEM a ficha.
    #    (não exigimos o nome na resposta — o modelo costuma responder direto; o que
    #    importa é não ser a ficha nem o fallback genérico. Correção factual: a olho.)
    NOFB = NOT_FICHA + ["não entendi"]
    check("In-base · Alcaraz (curiosidade, sem ficha)",
          "me conta uma curiosidade sobre o Carlos Alcaraz", "e1", forbid=NOFB,
          any_of=["jovem", "mais novo", "número 1", "#1", "n1"])
    check("In-base · Sinner (curiosidade, sem ficha)",
          "qual a curiosidade do Sinner?", "e2", forbid=NOFB,
          any_of=["italiano", "primeiro", "número 1", "#1"])

    # 2) Curiosidade via CONTEXTO (pronome) após a ficha → sem re-exibir a ficha.
    check("Contexto · ficha do Alcaraz → 'curiosidade sobre ele'",
          "me conta uma curiosidade sobre ele", "e3",
          setup=["quem é o Alcaraz?"], forbid=NOT_FICHA)

    # 3) Jogador FORA da base → PESQUISA Wikipedia e responde correto (revisão a olho).
    check("Fora da base · Seyboth Wild (pesquisa Wikipedia, fato específico)",
          "me conta uma curiosidade sobre o Thiago Seyboth Wild", "e4",
          forbid=NOT_FICHA + ["buscando", "consolidou"], want_search=True,
          any_of=["2018", "juvenil", "junior", "júnior", "us open", "58",
                  "santiago", "2020", "casper", "ruud", "título"])
    check("Discernimento · 'melhor ranking do João Fonseca' (é sobre ELE, não o #1)",
          "qual o melhor ranking do João Fonseca?", "e5",
          must=["fonseca"], forbid=["jannik sinner"])

    # 3b) WTA na base (pronome feminino correto) e typo via fuzzy.
    check("In-base WTA · Sabalenka (curiosidade, sem ficha)",
          "me conta uma curiosidade sobre a Sabalenka", "e4b", forbid=NOT_FICHA,
          any_of=["bielorr", "belarus", "número", "primeira", "australian open", "2023", "2024",
                  "rybakina", "grand slam", "wta", "saque", "seis", "pai", "tigresa", "anos"])
    check("Typo · 'curiosidade sobre o Medevedev' → Medvedev",
          "me conta uma curiosidade sobre o Medevedev", "e4c", forbid=NOT_FICHA,
          any_of=["russo", "rússia", "us open", "2021", "2022", "número", "grand slam", "masters", "djokovic"])

    # 3c) Discernimento base × IA: blocos que NÃO devem disparar (vão à IA).
    NO_BASE = NOT_FICHA + ["Campeões de Grand Slam", "Vencedores de", "Melhores jogadores"]
    check("Discernimento · head-to-head (Sinner x Alcaraz) → IA, não ficha",
          "o Sinner já jogou contra o Alcaraz?", "e9", forbid=NO_BASE)
    check("Discernimento · 'mais rico do brasil' → IA, não 'melhores ranqueados'",
          "tenista mais rico do brasil", "e10", forbid=NO_BASE)
    check("Discernimento · 'ingresso de Wimbledon' → IA, não campeões",
          "quanto custa um ingresso para Wimbledon?", "e11", forbid=NO_BASE)
    # Não-regressão: o que a base cobre continua na base.
    check("Base · 'melhor jogador do brasil' → base (não IA)",
          "melhor jogador do brasil", "e12", must=["Melhores jogadores"])

    # 3d) Fallback DuckDuckGo: fato específico/atual que NÃO está na Wikipedia (raquete).
    check("Web (DuckDuckGo) · raquete do João Fonseca → fonte web",
          "qual raquete o João Fonseca usa?", "e13", forbid=NOT_FICHA, want_search=True,
          any_of=["yonex", "vcore", "babolat", "wilson", "head", "raquete"])
    check("Infobox Wikipedia · treinador do João Fonseca",
          "quem treina o João Fonseca?", "e14", forbid=NOT_FICHA,
          any_of=["guilherme", "teixeira", "treinador"])

    # 4) Honestidade: jogador INVENTADO → não pode fabricar (deve admitir).
    check("Honestidade · jogador inexistente (não inventar)",
          "me conta uma curiosidade sobre o tenista Joaozinho Inventadasilva", "e6",
          forbid=NOT_FICHA)

    # 5) Off-topic → bloqueado (bot fechado em tênis).
    check("Off-topic · fotossíntese → bloqueia",
          "o que é fotossíntese?", "e7", must=[BLOCK])

    # 6) Curiosidade GENÉRICA (sem jogador) → base (não vira pesquisa nem ficha).
    check("Genérica · 'me conta uma curiosidade' → base",
          "me conta uma curiosidade", "e8", forbid=["respiro apenas"])

    print("\n" + "=" * 70)
    print(f"RESULTADO: {PASS} PASS / {FAIL} FAIL  (revise as respostas acima para a qualidade factual)")
    print("=" * 70)


if __name__ == "__main__":
    main()
