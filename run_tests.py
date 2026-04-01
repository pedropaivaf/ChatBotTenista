"""Bateria de testes exaustivos do chatbot - 68+ cenários."""
import sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
import app as app_module
client = app_module.app.test_client()

FAILS = []
TOTAL = 0

def chat(msg, sid):
    r = client.post('/predict', json={'message': msg, 'session_id': sid})
    data = r.get_json()
    return re.sub(r'<[^>]+>', '', data['answer'])

def expect(test_id, msg, sid, must_contain=None, must_not_contain=None):
    global TOTAL, FAILS
    TOTAL += 1
    resp = chat(msg, sid)
    first_line = resp.split('\n')[0][:100]
    ok = True
    reason = ''

    if must_contain:
        for mc in must_contain:
            if mc.lower() not in resp.lower():
                ok = False
                reason = f'FALTA: "{mc}"'
                break
    if ok and must_not_contain:
        for mnc in must_not_contain:
            if mnc.lower() in resp.lower():
                ok = False
                reason = f'INDEVIDO: "{mnc}"'
                break

    status = 'OK' if ok else 'FAIL'
    print(f'  [{status}] {test_id}: "{msg}" -> {first_line}')
    if not ok:
        FAILS.append({'test': test_id, 'msg': msg, 'reason': reason, 'got': first_line})
        print(f'       ERRO: {reason}')
    return resp

# =======================================================
print('=' * 70)
print('BATERIA 1: Ranking + Contexto de Jogador (20 turnos)')
print('=' * 70)
expect('1.01', 'ranking atp', 'b1', ['Alcaraz', 'Sinner', 'Zverev'])
expect('1.02', 'Sinner', 'b1', ['Jannik Sinner', 'Itália'])
expect('1.03', 'qual o pais dele', 'b1', ['Sinner', 'Itália'])
expect('1.04', 'e o estilo de jogo dele?', 'b1', ['Sinner'])
expect('1.05', 'Alcaraz', 'b1', ['Carlos Alcaraz', 'Espanha'])
expect('1.06', 'qual o pais dele', 'b1', ['Alcaraz', 'Espanha'])
expect('1.07', 'gosto de roland garros', 'b1', ['Roland Garros', 'Vencedores'])
expect('1.08', 'e wimbledon?', 'b1', ['Wimbledon', 'Vencedores'])
expect('1.09', 'qual o melhor jogador do brasil atualmente', 'b1', ['Brasil', 'Fonseca'])
expect('1.10', 'Fonseca', 'b1', ['João Fonseca', 'Brasil'])
expect('1.11', 'qual o pais dele', 'b1', ['Fonseca', 'Brasil'])
expect('1.12', 'ranking wta', 'b1', ['Sabalenka', 'Gauff'])
expect('1.13', 'Sabalenka', 'b1', ['Aryna Sabalenka'])
expect('1.14', 'qual o pais dela', 'b1', ['Sabalenka', 'Bielorrússia'])
expect('1.15', 'Medevedev', 'b1', ['Daniil Medvedev', 'Rússia'])
expect('1.16', 'Tsitipas', 'b1', ['Tsitsipas', 'Grécia'])
expect('1.17', 'me conta uma curiosidade', 'b1', None, ['Coria', 'Coric', 'Lestienne'])
expect('1.18', 'gosto do us open', 'b1', ['US Open', 'Vencedores'])
expect('1.19', 'melhor tenista espanhol', 'b1', ['Espanha', 'Alcaraz'])
expect('1.20', 'quem ganhou o australian open', 'b1', ['Australian Open'])

# =======================================================
print()
print('=' * 70)
print('BATERIA 2: Trivia + Contexto Aberto (20 turnos)')
print('=' * 70)
expect('2.01', 'oi', 'b2', ['Tênis'])
expect('2.02', 'quais os tipos de quadra?', 'b2', ['saibro', 'Grama', 'Piso'])
expect('2.03', 'qual a cor da bolinha', 'b2', ['amarelo'], ['Coria', 'Coric', 'Shapovalov'])
expect('2.04', 'quais as regras do tenis?', 'b2', ['15', '30', '40'])
expect('2.05', 'me conta uma curiosidade', 'b2', None, ['Coria', 'Lestienne', 'Shapovalov'])
expect('2.06', 'roland garros', 'b2', ['Roland Garros'])
expect('2.07', 'prefiro saibro', 'b2', ['saibro'])
expect('2.08', 'quem é o Djokovic?', 'b2', ['Djokovic'])
expect('2.09', 'e o Nadal?', 'b2', ['Nadal'])
expect('2.10', 'tenistas brasileiros', 'b2', ['Brasil'], ['Shapovalov', 'Coric'])
expect('2.11', 'Fonseca', 'b2', ['João Fonseca'])
expect('2.12', 'qual a idade dele', 'b2', None, ['fugiu da minha quadra'])
expect('2.13', 'como funciona o ranking da atp?', 'b2', ['ATP'])
expect('2.14', 'obrigado', 'b2', None, [])
expect('2.15', 'oi de novo', 'b2', None, [])
expect('2.16', 'ranking wta', 'b2', ['Sabalenka'])
expect('2.17', 'Swiatek', 'b2', ['Iga Swiatek', 'Polônia'])
expect('2.18', 'qual o pais dela', 'b2', ['Swiatek', 'Polônia'])
expect('2.19', 'quem ganhou wimbledon', 'b2', ['Wimbledon'])
expect('2.20', 'como o tenis surgiu?', 'b2', ['Inglaterra'])

# =======================================================
print()
print('=' * 70)
print('BATERIA 3: Typos, Edge Cases e Filtragem por País')
print('=' * 70)
expect('3.01', 'Danill Medevedev', 'b3', ['Medvedev'], ['fugiu'])
expect('3.02', 'Tsitipas', 'b3b', ['Tsitsipas'])
expect('3.03', 'Alcaras', 'b3c', ['Alcaraz'])
expect('3.04', 'jogadores brasileiros', 'b3d', ['Fonseca', 'Brasil'], ['Shapovalov', 'Denis'])
expect('3.05', 'melhor jogador da italia', 'b3e', ['Itália', 'Sinner'])
expect('3.06', 'qual o melhor jogador americano', 'b3f', ['EUA'])
expect('3.07', 'futebol', 'b3g', ['Tênis'], [])
expect('3.08', 'qual a melhor raquete', 'b3h', ['raquete'])
expect('3.09', 'o que é um Grand Slam?', 'b3i', ['Grand Slam', 'quatro'])
expect('3.10', 'quem é Roger Federer?', 'b3j', ['Federer', '20'])
expect('3.11', 'quem é Carlos Alcaraz?', 'b3k', ['Alcaraz'])
expect('3.12', 'receita de bolo', 'b3l', ['Tênis'], [])

# =======================================================
print()
print('=' * 70)
print('BATERIA 4: Queries Diretas (sessões independentes)')
print('=' * 70)
expect('4.01', 'ranking atp', 'b4a', ['1', 'Alcaraz'])
expect('4.02', 'ranking wta', 'b4b', ['1', 'Sabalenka'])
expect('4.03', 'quem é Jannik Sinner?', 'b4c', ['Sinner', 'Itália'])
expect('4.04', 'quem ganhou o us open', 'b4d', ['US Open'])
expect('4.05', 'melhor jogador do brasil', 'b4e', ['Fonseca', 'Brasil'])
expect('4.06', 'qual a cor da bolinha de tenis', 'b4f', ['amarelo'], ['Coria'])
expect('4.07', 'quais as regras basicas', 'b4g', ['15', '30', '40'])
expect('4.08', 'me conta uma curiosidade', 'b4h', None, ['Coria', 'Lestienne'])

# =======================================================
print()
print('=' * 70)
print('BATERIA 5: Fluxo Longo WTA (20 turnos)')
print('=' * 70)
expect('5.01', 'ranking wta', 'b5', ['Sabalenka'])
expect('5.02', 'Gauff', 'b5', ['Coco Gauff'])
expect('5.03', 'qual o pais dela', 'b5', ['Gauff', 'EUA'])
expect('5.04', 'Swiatek', 'b5', ['Iga Swiatek'])
expect('5.05', 'qual o pais dela', 'b5', ['Swiatek', 'Polônia'])
expect('5.06', 'gosto de wimbledon', 'b5', ['Wimbledon', 'Vencedores'])
expect('5.07', 'e o australian open?', 'b5', ['Australian Open'])
expect('5.08', 'melhor jogadora do brasil', 'b5', ['Haddad', 'Brasil'])
expect('5.09', 'quais as regras do tenis', 'b5', ['15', '30', '40'])
expect('5.10', 'prefiro grama', 'b5', ['grama'])
expect('5.11', 'ranking atp', 'b5', ['Alcaraz'])
expect('5.12', 'Djokovic', 'b5', ['Djokovic', 'Sérvia'])
expect('5.13', 'qual o pais dele', 'b5', ['Djokovic', 'Sérvia'])
expect('5.14', 'Zverev', 'b5', ['Zverev', 'Alemanha'])
expect('5.15', 'qual o pais dele', 'b5', ['Zverev', 'Alemanha'])
expect('5.16', 'me conta uma curiosidade', 'b5', None, ['Coria'])
expect('5.17', 'us open', 'b5', ['US Open'])
expect('5.18', 'quem é o Sinner', 'b5', ['Sinner'])
expect('5.19', 'qual a idade dele', 'b5', None, ['fugiu'])
expect('5.20', 'obrigado', 'b5', None, [])

# =======================================================
print()
print('=' * 70)
print('BATERIA 6: Perguntas sobre jogador em foco (detalhes)')
print('=' * 70)
expect('6.01', 'quem é o Alcaraz?', 'b6', ['Carlos Alcaraz'])
expect('6.02', 'qual a idade dele', 'b6', ['Alcaraz', '22'])
expect('6.03', 'qual o pais dele', 'b6', ['Alcaraz', 'Espanha'])
expect('6.04', 'qual o estilo dele', 'b6', ['Alcaraz'])
expect('6.05', 'ranking atp', 'b6', ['Ranking ATP', 'Alcaraz'])
expect('6.06', 'Djokovic', 'b6', ['Novak Djokovic'])
expect('6.07', 'qual a idade dele', 'b6', ['Djokovic'])
expect('6.08', 'qual o pais dele', 'b6', ['Djokovic', 'Sérvia'])
expect('6.09', 'quem ganhou roland garros', 'b6', ['Roland Garros', 'Vencedores'])
expect('6.10', 'e o us open?', 'b6', ['US Open'])

# =======================================================
print()
print('=' * 70)
print('BATERIA 7: Perguntas genéricas sobre tênis')
print('=' * 70)
expect('7.01', 'o que é um ace no tenis?', 'b7a', ['15', '30'])
expect('7.02', 'qual a origem do tenis?', 'b7b', ['Inglaterra'])
expect('7.03', 'o que é a ATP?', 'b7c', ['ATP', '1972'])
expect('7.04', 'piso duro', 'b7d', ['piso'])
expect('7.05', 'grama', 'b7e', ['grama'])
expect('7.06', 'quem é o numero 1 do mundo', 'b7f', ['Alcaraz'])
expect('7.07', 'melhor jogador da franca', 'b7g', ['França'])
expect('7.08', 'melhor jogador da argentina', 'b7h', ['Argentina'])

# =======================================================
print()
print('=' * 70)
total_pass = TOTAL - len(FAILS)
print(f'RESULTADO FINAL: {total_pass}/{TOTAL} passaram ({len(FAILS)} falhas)')
if FAILS:
    print()
    for f in FAILS:
        print(f'  FAIL {f["test"]}: "{f["msg"]}" -> {f["reason"]} (got: {f["got"]})')
else:
    print('ZERO FALHAS!')
print('=' * 70)
