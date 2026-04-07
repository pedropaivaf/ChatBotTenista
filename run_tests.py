"""
Bateria EXAUSTIVA de testes do chatbot Tennis AI.
297 cenários em 21 baterias cobrindo: contexto, fuzzy, reações, trivia, Grand Slams, Masters 1000,
ATP 500, último ganhador, países, edge cases, WTA, off-topic, typos, fluxos de 20 turnos,
campos específicos (altura/títulos/idade), listagem de torneios, recordes, GOAT, lendas,
posição no ranking, next gen, regras detalhadas.
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
import app as app_module
client = app_module.app.test_client()

FAILS = []
TOTAL = 0

def chat(msg, sid):
    r = client.post('/predict', json={'message': msg, 'session_id': sid})
    return re.sub(r'<[^>]+>', '', r.get_json()['answer'])

def expect(tid, msg, sid, yes=None, no=None):
    global TOTAL, FAILS
    TOTAL += 1
    resp = chat(msg, sid)
    line = resp.split('\n')[0][:100]
    ok, reason = True, ''
    if yes:
        for y in yes:
            if y.lower() not in resp.lower():
                ok, reason = False, f'FALTA: "{y}"'; break
    if ok and no:
        for n in no:
            if n.lower() in resp.lower():
                ok, reason = False, f'INDEVIDO: "{n}"'; break
    s = 'OK' if ok else 'FAIL'
    print(f'  [{s}] {tid}: "{msg}" -> {line}')
    if not ok:
        FAILS.append({'t': tid, 'm': msg, 'r': reason, 'g': line})
        print(f'       {reason}')
    return resp


# =====================================================================
print('='*70)
print('BATERIA 1: Ranking ATP + Contexto Completo (20 turnos)')
print('='*70)
expect('1.01', 'ranking atp', 'b1', ['Alcaraz', 'Sinner'])
expect('1.02', 'Sinner', 'b1', ['Jannik Sinner', 'Itália'])
expect('1.03', 'qual o pais dele', 'b1', ['Sinner', 'Itália'])
expect('1.04', 'e o estilo de jogo dele?', 'b1', ['Sinner'])
expect('1.05', 'Alcaraz', 'b1', ['Carlos Alcaraz', 'Espanha'])
expect('1.06', 'qual o pais dele', 'b1', ['Alcaraz', 'Espanha'])
expect('1.07', 'gosto de roland garros', 'b1', ['Roland Garros', 'Vencedores'])
expect('1.08', 'e wimbledon?', 'b1', ['Wimbledon', 'Vencedores'])
expect('1.09', 'qual o melhor jogador do brasil atualmente', 'b1', ['Brasil', 'Fonseca'])
expect('1.10', 'Fonseca', 'b1', ['João Fonseca'])
expect('1.11', 'qual o pais dele', 'b1', ['Fonseca', 'Brasil'])
expect('1.12', 'ranking wta', 'b1', ['Sabalenka', 'Gauff'])
expect('1.13', 'Sabalenka', 'b1', ['Aryna Sabalenka'])
expect('1.14', 'qual o pais dela', 'b1', ['Sabalenka', 'Bielorrússia'])
expect('1.15', 'Medevedev', 'b1', ['Daniil Medvedev', 'Rússia'])
expect('1.16', 'Tsitipas', 'b1', ['Tsitsipas', 'Grécia'])
expect('1.17', 'me conta uma curiosidade', 'b1', None, ['Coria', 'Lestienne'])
expect('1.18', 'gosto do us open', 'b1', ['US Open', 'Vencedores'])
expect('1.19', 'melhor tenista espanhol', 'b1', ['Espanha', 'Alcaraz'])
expect('1.20', 'quem ganhou o australian open', 'b1', ['Australian Open'])


# =====================================================================
print()
print('='*70)
print('BATERIA 2: Trivia + Contexto Aberto (20 turnos)')
print('='*70)
expect('2.01', 'oi', 'b2', ['Tênis'])
expect('2.02', 'quais os tipos de quadra?', 'b2', ['saibro', 'Grama', 'Piso'])
expect('2.03', 'qual a cor da bolinha', 'b2', ['amarelo'], ['Coria', 'Coric'])
expect('2.04', 'quais as regras do tenis?', 'b2', ['15', '30', '40'])
expect('2.05', 'me conta uma curiosidade', 'b2', None, ['Coria', 'Lestienne'])
expect('2.06', 'roland garros', 'b2', ['Roland Garros'])
expect('2.07', 'prefiro saibro', 'b2', ['saibro'])
expect('2.08', 'quem é o Djokovic?', 'b2', ['Djokovic'])
expect('2.09', 'e o Nadal?', 'b2', ['Nadal'])
expect('2.10', 'tenistas brasileiros', 'b2', ['Brasil'], ['Shapovalov'])
expect('2.11', 'Fonseca', 'b2', ['João Fonseca'])
expect('2.12', 'qual a idade dele', 'b2', None, ['fugiu da minha quadra'])
expect('2.13', 'como funciona o ranking da atp?', 'b2', ['ATP'])
expect('2.14', 'obrigado', 'b2', None)
expect('2.15', 'oi de novo', 'b2', None)
expect('2.16', 'ranking wta', 'b2', ['Sabalenka'])
expect('2.17', 'Swiatek', 'b2', ['Iga Swiatek', 'Polônia'])
expect('2.18', 'qual o pais dela', 'b2', ['Swiatek', 'Polônia'])
expect('2.19', 'quem ganhou wimbledon', 'b2', ['Wimbledon'])
expect('2.20', 'como o tenis surgiu?', 'b2', ['Inglaterra'])


# =====================================================================
print()
print('='*70)
print('BATERIA 3: Typos e Fuzzy Matching (12 testes)')
print('='*70)
expect('3.01', 'Danill Medevedev', 'b3a', ['Medvedev'], ['fugiu'])
expect('3.02', 'Tsitipas', 'b3b', ['Tsitsipas'])
expect('3.03', 'Alcaras', 'b3c', ['Alcaraz'])
expect('3.04', 'jogadores brasileiros', 'b3d', ['Fonseca', 'Brasil'], ['Shapovalov'])
expect('3.05', 'melhor jogador da italia', 'b3e', ['Itália', 'Sinner'])
expect('3.06', 'qual o melhor jogador americano', 'b3f', ['EUA'])
expect('3.07', 'futebol', 'b3g', ['Tênis'])
expect('3.08', 'qual a melhor raquete', 'b3h', ['raquete'], ['Alcaraz'])
expect('3.09', 'o que é um Grand Slam?', 'b3i', ['Grand Slam', 'quatro'])
expect('3.10', 'quem é Roger Federer?', 'b3j', ['Federer'])
expect('3.11', 'quem é Carlos Alcaraz?', 'b3k', ['Alcaraz'])
expect('3.12', 'receita de bolo', 'b3l', ['Tênis'])


# =====================================================================
print()
print('='*70)
print('BATERIA 4: Queries Diretas sem Contexto (8 testes)')
print('='*70)
expect('4.01', 'ranking atp', 'b4a', ['Alcaraz'])
expect('4.02', 'ranking wta', 'b4b', ['Sabalenka'])
expect('4.03', 'quem é Jannik Sinner?', 'b4c', ['Sinner', 'Itália'])
expect('4.04', 'quem ganhou o us open', 'b4d', ['US Open'])
expect('4.05', 'melhor jogador do brasil', 'b4e', ['Fonseca', 'Brasil'])
expect('4.06', 'qual a cor da bolinha de tenis', 'b4f', ['amarelo'], ['Coria'])
expect('4.07', 'quais as regras basicas', 'b4g', ['15', '30', '40'])
expect('4.08', 'me conta uma curiosidade', 'b4h', None, ['Coria', 'Lestienne'])


# =====================================================================
print()
print('='*70)
print('BATERIA 5: Fluxo WTA Completo (20 turnos)')
print('='*70)
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
expect('5.20', 'obrigado', 'b5', None)


# =====================================================================
print()
print('='*70)
print('BATERIA 6: Jogador em Foco — Detalhes e Troca (10 testes)')
print('='*70)
expect('6.01', 'quem é o Alcaraz?', 'b6', ['Carlos Alcaraz'])
expect('6.02', 'qual a idade dele', 'b6', ['Alcaraz', '22'])
expect('6.03', 'qual o pais dele', 'b6', ['Alcaraz', 'Espanha'])
expect('6.04', 'qual o estilo dele', 'b6', ['Alcaraz'])
expect('6.05', 'ranking atp', 'b6', ['Ranking ATP', 'Alcaraz'])
expect('6.06', 'Djokovic', 'b6', ['Novak Djokovic'])
expect('6.07', 'qual a idade dele', 'b6', ['Djokovic'])
expect('6.08', 'qual o pais dele', 'b6', ['Djokovic', 'Sérvia'])
expect('6.09', 'quem ganhou roland garros', 'b6', ['Roland Garros'])
expect('6.10', 'e o us open?', 'b6', ['US Open'])


# =====================================================================
print()
print('='*70)
print('BATERIA 7: Perguntas Genéricas sobre Tênis (8 testes)')
print('='*70)
expect('7.01', 'o que é um ace no tenis?', 'b7a', ['15', '30'])
expect('7.02', 'qual a origem do tenis?', 'b7b', ['Inglaterra'])
expect('7.03', 'o que é a ATP?', 'b7c', ['ATP', '1972'])
expect('7.04', 'piso duro', 'b7d', ['piso'])
expect('7.05', 'grama', 'b7e', ['grama'])
expect('7.06', 'quem é o numero 1 do mundo', 'b7f', ['Alcaraz'])
expect('7.07', 'melhor jogador da franca', 'b7g', ['França'])
expect('7.08', 'melhor jogador da argentina', 'b7h', ['Argentina'])


# =====================================================================
print()
print('='*70)
print('BATERIA 8: REAÇÕES EMPÁTICAS a Atributos Técnicos (15 testes)')
print('='*70)
# Resistência (reação pode usar frase alternativa, validar jogador + não fugiu)
chat('quem é o Djokovic?', 'r1')
expect('8.01', 'o que mais me impressiona é a resistencia dele', 'r1',
       ['Djokovic'], ['fugiu', 'Coria'])
# Forehand
chat('quem é o Alcaraz?', 'r2')
expect('8.02', 'adoro o forehand dele', 'r2',
       ['Alcaraz'], ['fugiu', 'Coria'])
# Backhand
chat('quem é o Djokovic?', 'r3')
expect('8.03', 'o backhand dele é incrível', 'r3',
       ['Djokovic'], ['fugiu', 'Coria'])
# Saque (WTA)
chat('ranking wta', 'r4'); chat('Sabalenka', 'r4')
expect('8.04', 'o saque dela é incrível', 'r4',
       ['Sabalenka'], ['fugiu', 'Coria'])
# Mental
chat('quem é o Sinner?', 'r5')
expect('8.05', 'a força mental dele impressiona', 'r5',
       ['Sinner'], ['fugiu', 'Coria'])
# Velocidade
chat('quem é o Alcaraz?', 'r6')
expect('8.06', 'a velocidade dele na quadra é absurda', 'r6',
       ['Alcaraz'], ['fugiu', 'Coria'])
# Agressivo
chat('quem é o Medvedev?', 'r7')
expect('8.07', 'jogo agressivo demais', 'r7',
       ['Medvedev'], ['fugiu', 'Coria'])
# Defesa
chat('quem é o Djokovic?', 'r8')
expect('8.08', 'a defesa dele é incrível', 'r8',
       ['Djokovic'], ['fugiu', 'Coria'])
# Voleio
chat('quem é o Federer?', 'r9')
expect('8.09', 'o voleio dele era perfeito', 'r9',
       ['Federer'], ['fugiu', 'Coria'])
# País + reação juntos
chat('quem é o Sinner?', 'r10')
expect('8.10', 'qual o pais dele, o saque dele é muito bom', 'r10',
       ['Itália'], ['fugiu', 'Coria'])
# Resistência + info
chat('quem é o Nadal?', 'r11')
expect('8.11', 'a resistencia dele no saibro é lendária', 'r11',
       ['Nadal'], ['fugiu', 'Coria'])
# Sem reação quando sem opinião
chat('quem é o Alcaraz?', 'r12')
expect('8.12', 'qual o pais dele', 'r12',
       ['Espanha'], ['resistência', 'forehand', 'saque'])
# Sem reação no ranking
expect('8.13', 'ranking atp', 'r13', ['Alcaraz'], ['resistência', 'forehand'])
# Sem reação na curiosidade
expect('8.14', 'me conta uma curiosidade', 'r14', None, ['resistência', 'forehand', 'Coria'])
# Sem reação em trivia genérica
expect('8.15', 'quais as regras do tenis', 'r15', ['15', '30'], ['resistência'])


# =====================================================================
print()
print('='*70)
print('BATERIA 9: Falsos Positivos — Garantir que NÃO confunde (15 testes)')
print('='*70)
expect('9.01', 'qual a cor da bolinha', 'f1', ['amarelo'], ['Coria', 'Coric'])
expect('9.02', 'bola de tenis amarela', 'f2', ['amarelo'], ['Coria'])
expect('9.03', 'como funciona a pontuação', 'f3', ['15', '30'], ['Coria', 'Shapovalov'])
expect('9.04', 'tipo de quadra', 'f4', ['saibro'], ['Shapovalov', 'Coria'])
expect('9.05', 'regras basicas do tenis', 'f5', ['15'], ['Coria', 'Shapovalov'])
expect('9.06', 'jogadores brasileiros', 'f6', ['Fonseca'], ['Shapovalov', 'Denis'])
expect('9.07', 'jogadoras brasileiras', 'f7', ['Haddad'], ['Shapovalov'])
expect('9.08', 'tenistas do brasil', 'f8', ['Brasil'], ['Shapovalov', 'Coric'])
expect('9.09', 'quem ganhou o torneio', 'f9', None, ['Coria', 'Shapovalov'])
expect('9.10', 'o que é set no tenis', 'f10', None, ['Coria', 'Shapovalov'])
expect('9.11', 'qual a melhor raquete', 'f11', ['raquete'], ['Alcaraz', 'Coria'])
expect('9.12', 'politica', 'f12', ['Tênis'])
expect('9.13', 'basquete nba', 'f13', ['Tênis'])
expect('9.14', 'copa do mundo', 'f14', ['Tênis'])
expect('9.15', 'receita de bolo de chocolate', 'f15', ['Tênis'])


# =====================================================================
print()
print('='*70)
print('BATERIA 10: Filtragem por País — Todos os cenários (12 testes)')
print('='*70)
expect('10.01', 'melhor jogador do brasil', 'p1', ['Fonseca', 'Brasil'])
expect('10.02', 'melhor jogador da espanha', 'p2', ['Espanha', 'Alcaraz'])
expect('10.03', 'melhor jogador da italia', 'p3', ['Itália', 'Sinner'])
expect('10.04', 'melhor jogador americano', 'p4', ['EUA'])
expect('10.05', 'melhor jogador da argentina', 'p5', ['Argentina'])
expect('10.06', 'melhor jogador da franca', 'p6', ['França'])
expect('10.07', 'melhor jogador da russia', 'p7', ['Rússia'])
expect('10.08', 'melhor jogador da alemanha', 'p8', ['Alemanha', 'Zverev'])
expect('10.09', 'melhor jogador da servia', 'p9', ['Sérvia', 'Djokovic'])
expect('10.10', 'melhor jogadora da polonia', 'p10', ['Polônia', 'Swiatek'])
expect('10.11', 'quem é o numero 1 do mundo', 'p11', ['Alcaraz'])
expect('10.12', 'melhor jogadora do mundo', 'p12', ['Sabalenka'])


# =====================================================================
print()
print('='*70)
print('BATERIA 11: Torneios — Detecção Direta (10 testes)')
print('='*70)
expect('11.01', 'quem ganhou o australian open', 't1', ['Australian Open'])
expect('11.02', 'quem ganhou roland garros', 't2', ['Roland Garros'])
expect('11.03', 'quem ganhou wimbledon', 't3', ['Wimbledon'])
expect('11.04', 'quem ganhou o us open', 't4', ['US Open'])
expect('11.05', 'campeões de roland garros', 't5', ['Roland Garros'])
expect('11.06', 'vencedor de wimbledon', 't6', ['Wimbledon'])
# Torneio após contexto de jogador
chat('quem é o Sinner?', 't7')
expect('11.07', 'gosto de roland garros', 't7', ['Roland Garros', 'Vencedores'])
chat('quem é o Alcaraz?', 't8')
expect('11.08', 'e wimbledon?', 't8', ['Wimbledon', 'Vencedores'])
# Torneio após trivia
chat('me conta uma curiosidade', 't9')
expect('11.09', 'us open', 't9', ['US Open'])
chat('quais os tipos de quadra', 't10')
expect('11.10', 'australian open', 't10', ['Australian Open'])


# =====================================================================
print()
print('='*70)
print('BATERIA 12: Stress Test — Fluxo de 20 turnos misturando TUDO')
print('='*70)
expect('12.01', 'oi', 'stress', ['Tênis'])
expect('12.02', 'ranking atp', 'stress', ['Alcaraz'])
expect('12.03', 'Sinner', 'stress', ['Jannik Sinner'])
expect('12.04', 'o forehand dele é incrível', 'stress', ['forehand', 'Sinner'])
expect('12.05', 'qual o pais dele', 'stress', ['Sinner', 'Itália'])
expect('12.06', 'roland garros', 'stress', ['Roland Garros'])
expect('12.07', 'melhor jogador do brasil', 'stress', ['Fonseca'])
expect('12.08', 'Fonseca', 'stress', ['João Fonseca'])
expect('12.09', 'a velocidade dele é absurda', 'stress', ['Fonseca'], ['fugiu', 'Coria'])
expect('12.10', 'ranking wta', 'stress', ['Sabalenka'])
expect('12.11', 'Sabalenka', 'stress', ['Aryna Sabalenka'])
expect('12.12', 'o saque dela é devastador', 'stress', ['Sabalenka'], ['fugiu', 'Coria'])
expect('12.13', 'qual o pais dela', 'stress', ['Sabalenka', 'Bielorrússia'])
expect('12.14', 'Medevedev', 'stress', ['Daniil Medvedev'])
expect('12.15', 'a defesa dele impressiona', 'stress', ['Medvedev'], ['fugiu', 'Coria'])
expect('12.16', 'quais as regras do tenis', 'stress', ['15', '30', '40'])
expect('12.17', 'qual a cor da bolinha', 'stress', ['amarelo'], ['Coria'])
expect('12.18', 'quem é o numero 1 do mundo', 'stress', ['Alcaraz'])
expect('12.19', 'futebol', 'stress', ['Tênis'])
expect('12.20', 'obrigado', 'stress', None)


# =====================================================================
# BATERIA 13: Detalhes dos Grand Slams (15 testes)
# =====================================================================
print('\n--- BATERIA 13: Detalhes dos Grand Slams ---')

# Queries diretas de detalhes (sem contexto)
expect('13.01', 'me fala sobre roland garros', 'gs1', ['Roland Garros', 'Paris', 'Saibro', 'Nadal'])
expect('13.02', 'detalhes do wimbledon', 'gs2', ['Wimbledon', 'Grama', 'Londres'])
expect('13.03', 'o que é o australian open', 'gs3', ['Australian Open', 'Melbourne', 'Piso Duro'])
expect('13.04', 'como é o us open', 'gs4', ['US Open', 'Nova York', 'Piso Duro'])
expect('13.05', 'história do roland garros', 'gs5', ['Roland Garros', 'Fundado', '1891'])

# Queries de campeões continuam funcionando (NÃO mostram detalhes)
expect('13.06', 'quem ganhou wimbledon', 'gs6', ['Wimbledon'], ['Grama', 'Fundado'])
expect('13.07', 'campeões de roland garros', 'gs7', ['Roland Garros'], ['Saibro', 'Paris'])

# Torneio bare (sem keywords de detalhe) → campeões
expect('13.08', 'wimbledon', 'gs8', ['Wimbledon', 'Vencedores'])

# Keywords específicas de detalhe
expect('13.09', 'qual a premiação do us open', 'gs9', ['US Open', 'milhões'])
expect('13.10', 'qual o piso do australian open', 'gs10', ['Australian Open', 'Piso Duro'])

# Fluxo contextual: ranking → detalhes de slam
chat('ranking atp', 'gs11')
expect('13.11', 'me fala sobre roland garros', 'gs11', ['Roland Garros', 'Saibro', 'Nadal'])

# Fluxo: após detalhes → "quem ganhou" → campeões
chat('sobre o wimbledon', 'gs12')
expect('13.12', 'quem ganhou wimbledon', 'gs12', ['Wimbledon'], ['Grama'])

# Fluxo: após detalhes RG → "e wimbledon?" (sem detail keywords) → campeões
chat('sobre roland garros', 'gs13')
expect('13.13', 'e wimbledon?', 'gs13', ['Wimbledon'])

# Fluxo: após detalhes RG → "detalhes do wimbledon" → detalhes Wimbledon
chat('detalhes do roland garros', 'gs14')
expect('13.14', 'detalhes do wimbledon', 'gs14', ['Wimbledon', 'Grama', 'Londres'])

# Maior campeã aparece nos detalhes
expect('13.15', 'me fala sobre o australian open', 'gs15', ['Australian Open', 'Margaret Court'])


# =====================================================================
# BATERIA 14: Fluxo de 20 turnos com Grand Slams (20 testes)
# =====================================================================
print('\n--- BATERIA 14: Fluxo 20 turnos com Grand Slams ---')
expect('14.01', 'oi', 'slam20', ['tênis'])
expect('14.02', 'ranking atp', 'slam20', ['Ranking', 'ATP'])
expect('14.03', 'Sinner', 'slam20', ['Sinner'])
expect('14.04', 'o forehand dele é incrível', 'slam20', ['forehand', 'Sinner'])
expect('14.05', 'me fala sobre roland garros', 'slam20', ['Roland Garros', 'Saibro', 'Nadal'])
expect('14.06', 'quem ganhou roland garros', 'slam20', ['Roland Garros'])
expect('14.07', 'e wimbledon?', 'slam20', ['Wimbledon'])
expect('14.08', 'detalhes do wimbledon', 'slam20', ['Wimbledon', 'Grama', 'Londres'])
expect('14.09', 'Djokovic', 'slam20', ['Djokovic'])
expect('14.10', 'qual o país dele', 'slam20', ['Sérvia', 'Djokovic'])
expect('14.11', 'ranking wta', 'slam20', ['Ranking', 'WTA'])
expect('14.12', 'Sabalenka', 'slam20', ['Sabalenka'])
expect('14.13', 'o saque dela é devastador', 'slam20', ['saque', 'Sabalenka'])
expect('14.14', 'sobre o australian open', 'slam20', ['Australian Open', 'Melbourne', 'Piso Duro'])
expect('14.15', 'quem ganhou australian open', 'slam20', ['Australian Open'])
expect('14.16', 'melhor jogador do brasil', 'slam20', ['Brasil'])
expect('14.17', 'me conta sobre o us open', 'slam20', ['US Open', 'Nova York'])
expect('14.18', 'quais as regras do tenis', 'slam20', ['15', '30', '40'])
expect('14.19', 'uma curiosidade', 'slam20', None)
expect('14.20', 'obrigado', 'slam20', None)


# =====================================================================
# BATERIA 15: Torneios ATP 1000 (15 testes)
# =====================================================================
print('\n--- BATERIA 15: Torneios ATP Masters 1000 ---')

# Detecção direta de Masters 1000
expect('15.01', 'indian wells', 'atp1k_1', ['Indian Wells', 'Masters 1000', 'Califórnia'])
expect('15.02', 'miami open', 'atp1k_2', ['Miami Open', 'Masters 1000'])
expect('15.03', 'monte carlo', 'atp1k_3', ['Monte Carlo', 'Saibro', 'Masters 1000'])
expect('15.04', 'madrid open', 'atp1k_4', ['Madrid Open', 'Masters 1000', 'Saibro'])
expect('15.05', 'me fala sobre roma', 'atp1k_5', ['Roma', 'Masters 1000', 'Saibro'])
expect('15.06', 'cincinnati', 'atp1k_6', ['Cincinnati', 'Masters 1000'])
expect('15.07', 'shanghai', 'atp1k_7', ['Shanghai', 'Masters 1000'])
expect('15.08', 'paris masters', 'atp1k_8', ['Paris Masters', 'Masters 1000', 'Indoor'])
expect('15.09', 'atp finals', 'atp1k_9', ['ATP Finals', 'Turim'])

# Masters em contexto (após ranking)
chat('ranking atp', 'atp1k_10')
expect('15.10', 'indian wells', 'atp1k_10', ['Indian Wells', 'Masters 1000'])

# Masters após detalhes de slam
chat('sobre roland garros', 'atp1k_11')
expect('15.11', 'monte carlo', 'atp1k_11', ['Monte Carlo', 'Masters 1000'])

# Campeões recentes aparecem
expect('15.12', 'detalhes do miami open', 'atp1k_12', ['Miami Open', 'Sinner'])

# Ranking NÃO é confundido com torneio
expect('15.13', 'ranking atp', 'atp1k_13', ['Ranking', 'ATP'], ['ATP Finals'])

# Masters Canadá
expect('15.14', 'masters canadá', 'atp1k_14', ['Masters 1000', 'Montreal'])

# Premiação
expect('15.15', 'premiação do indian wells', 'atp1k_15', ['Indian Wells', 'milhões'])


# =====================================================================
# BATERIA 16: Torneios ATP 500 + Fonseca (15 testes)
# =====================================================================
print('\n--- BATERIA 16: Torneios ATP 500 + João Fonseca ---')

# ATP 500 direto
expect('16.01', 'rio open', 'atp500_1', ['Rio Open', 'ATP 500', 'Brasil'])
expect('16.02', 'barcelona open', 'atp500_2', ['Barcelona', 'ATP 500', 'Saibro'])
expect('16.03', 'halle', 'atp500_3', ['Halle', 'ATP 500', 'Grama'])
expect('16.04', 'dubai', 'atp500_4', ['Dubai', 'ATP 500'])
expect('16.05', 'acapulco', 'atp500_5', ['Acapulco', 'ATP 500', 'México'])

# Rio Open com Fonseca nos campeões
expect('16.06', 'quem ganhou o rio open', 'atp500_6', ['Rio Open', 'Fonseca'])

# Ficha atualizada do Fonseca
expect('16.07', 'João Fonseca', 'atp500_7', ['Fonseca', 'Rio Open'])

# Fluxo: jogador → torneio ATP 500
chat('ranking atp', 'atp500_8')
chat('Fonseca', 'atp500_8')
expect('16.08', 'rio open', 'atp500_8', ['Rio Open', 'ATP 500'])

# Fluxo: ATP 500 em open_topic
chat('uma curiosidade', 'atp500_9')
expect('16.09', 'rio open', 'atp500_9', ['Rio Open', 'ATP 500'])

# Basileia e Viena
expect('16.10', 'basileia', 'atp500_10', ['Basileia', 'ATP 500', 'Federer'])
expect('16.11', 'viena', 'atp500_11', ['Viena', 'ATP 500'])

# Queen's
expect('16.12', "queen's", 'atp500_12', ["Queen's", 'ATP 500', 'Grama'])

# Fluxo de 20 turnos misturando Masters e 500
expect('16.13', 'oi', 'mix20', ['tênis'])
expect('16.14', 'indian wells', 'mix20', ['Indian Wells', 'Masters 1000'])
expect('16.15', 'rio open', 'mix20', ['Rio Open', 'ATP 500', 'Fonseca'])


# =====================================================================
# BATERIA 17: "Quem foi o último ganhador?" com torneio no contexto (10 testes)
# =====================================================================
print('\n--- BATERIA 17: Último ganhador via contexto ---')

# Após detalhes de ATP 500 → quem ganhou?
chat('rio open', 'win1')
expect('17.01', 'quem foi o último ganhador?', 'win1', ['Rio Open', 'Fonseca'])

# Após detalhes de Masters 1000 → quem ganhou?
chat('indian wells', 'win2')
expect('17.02', 'quem foi o último campeão?', 'win2', ['Indian Wells', 'Alcaraz'])

# Após detalhes de Grand Slam → quem ganhou?
chat('sobre roland garros', 'win3')
expect('17.03', 'quem ganhou?', 'win3', ['Roland Garros'])

# Após detalhes do Miami Open → quem venceu?
chat('miami open', 'win4')
expect('17.04', 'quem venceu?', 'win4', ['Miami', 'Sinner'])

# Após ATP Finals → último ganhador
chat('atp finals', 'win5')
expect('17.05', 'quem foi o campeão?', 'win5', ['ATP Finals', 'Sinner'])

# Fluxo: torneio → último ganhador → outro torneio → último ganhador
chat('monte carlo', 'win6')
expect('17.06', 'quem ganhou?', 'win6', ['Monte Carlo', 'Sinner'])
chat('madrid open', 'win6')
expect('17.07', 'quem foi o último ganhador?', 'win6', ['Madrid', 'Zverev'])

# Após Barcelona Open
chat('barcelona open', 'win8')
expect('17.08', 'quem foi o ganhador?', 'win8', ['Barcelona', 'Alcaraz'])

# Variação: "último vencedor"
chat('dubai', 'win9')
expect('17.09', 'último vencedor?', 'win9', ['Dubai', 'Sinner'])

# Após Wimbledon (Grand Slam) via detalhes
chat('detalhes do wimbledon', 'win10')
expect('17.10', 'quem ganhou?', 'win10', ['Wimbledon'])


# =====================================================================
# BATERIA 18: Listagem de torneios (8 testes)
# =====================================================================
print('\n--- BATERIA 18: Listagem de torneios ---')

# Sem contexto — pipeline direto
expect('18.01', 'quais são os torneios de tênis?', 'list1', ['Grand Slams', 'Masters 1000', 'ATP 500'])
expect('18.02', 'listar torneios', 'list2', ['Grand Slams', 'Masters 1000', 'ATP 500'])
expect('18.03', 'todos os torneios', 'list3', ['Grand Slams', 'Masters 1000'])

# Em contexto player_detail
chat('João Fonseca', 'list4')
expect('18.04', 'quais são os torneios?', 'list4', ['Grand Slams', 'Masters 1000'])

# Em contexto open_topic
chat('uma curiosidade', 'list5')
expect('18.05', 'quais os campeonatos de tenis?', 'list5', ['Grand Slams', 'Masters 1000'])

# Fluxo: lista → escolher torneio → detalhes
expect('18.06', 'quais são os torneios?', 'list6', ['Grand Slams', 'Masters 1000'])
expect('18.07', 'rio open', 'list6', ['Rio Open', 'ATP 500', 'Fonseca'])

# "quem ganhou" NÃO mostra lista (preserva comportamento de campeões)
expect('18.08', 'quem ganhou os torneios', 'list8', ['Campeões'], ['Calendário'])


# =====================================================================
# BATERIA 19: Respostas específicas por campo (altura, títulos, idade) (12 testes)
# =====================================================================
print('\n--- BATERIA 19: Respostas específicas por campo ---')

# Altura no contexto player_detail
chat('Carlos Alcaraz', 'field1')
expect('19.01', 'qual a altura dele?', 'field1', ['1,83m', 'Alcaraz'], ['Estilo', 'Curiosidade'])

chat('Sabalenka', 'field2')
expect('19.02', 'qual a altura dela?', 'field2', ['1,82m', 'Sabalenka'], ['Estilo'])

# Idade específica
chat('João Fonseca', 'field3')
expect('19.03', 'quantos anos ele tem?', 'field3', ['19 anos', 'Fonseca'], ['Estilo'])

# Títulos específicos
chat('Djokovic', 'field4')
expect('19.04', 'quantos títulos ele tem?', 'field4', ['99', 'Djokovic'], ['Estilo'])

# Altura sem pronome (direto no contexto)
chat('Sinner', 'field5')
expect('19.05', 'altura', 'field5', ['1,92m', 'Sinner'], ['Estilo'])

# Ficha completa mostra altura
expect('19.06', 'Medvedev', 'field6', ['1,98m', 'Medvedev', 'Altura'])

# Fluxo: jogador → altura → títulos → outro jogador
chat('Alcaraz', 'field7')
expect('19.07', 'qual a altura?', 'field7', ['1,83m'])
expect('19.08', 'quantos títulos?', 'field7', ['16'])

# Jogador WTA
chat('Iga Swiatek', 'field9')
expect('19.09', 'qual a altura dela?', 'field9', ['1,76m', 'Swiatek'])
expect('19.10', 'quantos títulos?', 'field9', ['22'])

# Sem contexto: "qual a altura do Federer" NÃO funciona (não está no ranking)
# Teste com jogador no ranking
expect('19.11', 'qual a altura do Hubert Hurkacz', 'field11', ['1,96m', 'Hurkacz'])

# Idade via pronome
chat('Ben Shelton', 'field12')
expect('19.12', 'idade dele', 'field12', ['Shelton'])


# =====================================================================
# BATERIA 20: Recordes, GOAT, Lendas, Regras, WTA (20 testes)
# =====================================================================
print('\n--- BATERIA 20: Cobertura ampliada de conhecimento ---')

# Recordes (usando patterns que não colidem com winner_stems)
expect('20.01', 'recordes de títulos do tênis', 'kb1', ['Djokovic', 'Navratilova'])
expect('20.02', 'quem é o recordista de slams', 'kb2', ['Djokovic', '24'])
expect('20.03', 'recordes do tênis', 'kb3', ['Djokovic', 'Grand Slams'])
expect('20.04', 'partida mais longa da história', 'kb4', ['Isner', 'Mahut', '11'])
expect('20.05', 'recorde de velocidade de saque', 'kb5', ['263'])

# GOAT debate
expect('20.06', 'quem é o goat do tênis', 'kb6', ['Djokovic', 'Nadal', 'Federer'])
expect('20.07', 'debate goat', 'kb7', ['Djokovic', 'Nadal', 'Federer'])
expect('20.08', 'quem é o melhor de todos os tempos', 'kb8', ['Djokovic', 'Nadal', 'Federer'])

# Lendas
expect('20.09', 'Roger Federer', 'kb9', ['Federer', '1,85m'])
expect('20.10', 'Serena Williams', 'kb10', ['Serena', '23'])
expect('20.11', 'lendas do tênis', 'kb11', ['Djokovic', 'Nadal', 'Federer', 'Serena'])

# Regras e termos
expect('20.12', 'o que é tiebreak', 'kb12', ['tiebreak', '7 pontos'])
expect('20.13', 'termos do tênis', 'kb13', ['Ace', 'Deuce', 'Break'])
expect('20.14', 'o que é golden slam', 'kb14', ['Steffi Graf', '1988'])

# WTA e ATP
expect('20.15', 'o que é WTA', 'kb15', ['WTA', 'feminino'])
expect('20.16', 'como funciona o ranking ATP', 'kb16', ['ATP', 'pontos'])

# Next Gen
expect('20.17', 'next gen', 'kb17', ['Alcaraz', 'Sinner', 'Fonseca'])

# Superfícies e especialistas
expect('20.18', 'especialistas por superfície', 'kb18', ['Nadal', 'Saibro'])

# Dicas
expect('20.19', 'como começar a jogar tênis', 'kb19', ['raquete'])

# Fluxo: recordes → lenda → detalhes
expect('20.20', 'recordes históricos do tênis', 'kb20', ['Djokovic'])


# =====================================================================
# BATERIA 21: Posição ranking + recordes de títulos (12 testes)
# =====================================================================
print('\n--- BATERIA 21: Posição no ranking + recordes ---')

# Posição específica sem contexto
expect('21.01', 'quem é o número 20 do mundo', 'pos1', ['20º'])
expect('21.02', 'quem é o top 5 do ranking', 'pos2', ['5º'])
expect('21.03', 'atual número 1 do mundo', 'pos3', ['1º', 'Alcaraz'])

# Posição WTA
expect('21.04', 'quem é a número 1 do wta', 'pos4', ['1º', 'WTA', 'Sabalenka'])

# Posição em contexto (após ver jogador)
chat('João Fonseca', 'pos5')
expect('21.05', 'quem é o atual 20 do mundo', 'pos5', ['20º'])

# Recordes NÃO caem no bloco de campeões
expect('21.06', 'quem ganhou mais títulos no tênis', 'pos6', ['Djokovic', 'Navratilova'])
expect('21.07', 'qual jogador tem mais títulos', 'pos7', ['Djokovic', 'Navratilova'])

# Títulos no contexto de jogador (campo específico preservado)
chat('Alcaraz', 'pos8')
expect('21.08', 'quantos títulos ele tem', 'pos8', ['16', 'Alcaraz'])

# Posição em contexto player_detail NÃO responde sobre o foco
chat('Sinner', 'pos9')
expect('21.09', 'quem é o número 50 do ranking', 'pos9', ['50º'])

# Top com circuit
expect('21.10', 'número 3 do ranking wta', 'pos10', ['3º', 'WTA'])

# Recorde "mais grand slams" não cai em campeões
expect('21.11', 'quem tem mais grand slams', 'pos11', ['Djokovic', '24'])

# Posição alta
expect('21.12', 'quem é o número 100 do ranking atp', 'pos12', ['100º'])


# =====================================================================
print()
print('='*70)
total_pass = TOTAL - len(FAILS)
print(f'RESULTADO FINAL: {total_pass}/{TOTAL} passaram ({len(FAILS)} falhas)')
if FAILS:
    print()
    for f in FAILS:
        print(f'  FAIL {f["t"]}: "{f["m"]}" -> {f["r"]} (got: {f["g"]})')
else:
    print('ZERO FALHAS!')
print('='*70)
