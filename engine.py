import json # trigger reload
import os # Biblioteca para interagir com o sistema de arquivos (verificar se arquivos existem)
import requests # Para buscar dados em sites externos
import re # Para extrair informações do HTML via expressões regulares
import unicodedata # Para normalizar textos com acentos (ex: Canadá)

# Mapeamento expandido de países para emojis de bandeira para o Top 100 completo
COUNTRY_FLAGS = {
    "Sérvia": "🇷🇸", "Espanha": "🇪🇸", "Itália": "🇮🇹", "Alemanha": "🇩🇪", 
    "Rússia": "🇷🇺", "Noruega": "🇳🇴", "Polônia": "🇵🇱", "EUA": "🇺🇸", 
    "Austrália": "🇦🇺", "Bulgária": "🇧🇬", "Grécia": "🇬🇷", "Bielorrússia": "🇧🇾", 
    "Cazaquistão": "🇰🇿", "China": "🇨🇳", "Rep. Tcheca": "🇨🇿", "Brasil": "🇧🇷", 
    "Ucrânia": "🇺🇦", "Tunísia": "🇹🇳", "Croácia": "🇭🇷", "Suíça": "🇨🇭", 
    "Reino Unido": "🇬🇧", "Dinamarca": "🇩🇰", "Canadá": "🇨🇦", "Chile": "🇨🇱",
    "França": "🇫🇷", "Argentina": "🇦🇷", "Holanda": "🇳🇱", "Portugal": "🇵🇹",
    "Hungria": "🇭🇺", "Bélgica": "🇧🇪", "Japão": "🇯🇵", "Índia": "🇮🇳",
    "Egito": "🇪🇬", "Colômbia": "🇨🇴", "Eslováquia": "🇸🇰", "México": "🇲🇽",
    "Finlândia": "🇫🇮", "Áustria": "🇦🇹", "Nova Zelândia": "🇳🇿", "Romênia": "🇷🇴",
    "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
}

class TennisEngine: # Classe que representa o nosso motor de consulta técnica
    def __init__(self, data_path='tennis_data.json'): # Método inicializador que roda ao criarmos o objeto
        self.data_path = data_path # Salva o caminho do arquivo de dados numa variável interna (atributo)
        self.data = self._load_data() # Chama a função interna para carregar os dados reais na memória

    def _load_data(self): # Função "privada" (interna) para carregar o conteúdo do JSON
        if os.path.exists(self.data_path): # Verifica se o arquivo físico (ex: tennis_data.json) existe no disco
            with open(self.data_path, 'r', encoding='utf-8') as f: # Abre o arquivo para leitura com acentuação correta
                return json.load(f) # Decodifica o texto JSON e transforma em um dicionário Python
        return {} # Se o arquivo não for encontrado, retorna um dicionário vazio para evitar travamentos

    def _get_flag(self, country_name): 
        # Normaliza o nome do país para evitar erros com acentos (ex: NFC vs NFD)
        if not country_name or country_name == 'N/A': return "🌍"
        normalized_name = unicodedata.normalize('NFC', country_name.strip())
        flag = COUNTRY_FLAGS.get(normalized_name, "🌍")
        try:
            print(f"[DEBUG_FLAG] Pais: '{country_name}' -> Normalizado: '{normalized_name}' -> Flag: '{flag}'")
        except UnicodeEncodeError:
            print(f"[DEBUG_FLAG] Pais: '{country_name}' -> Normalizado: '{normalized_name}' -> Flag: (emoji)")
        return flag

    # --- Lógica de Rankings (Dinâmica para ATP e WTA) ---
    def get_ranking_summary(self, circuit='ATP'): 
        circuit = circuit.upper()
        ranking_key = "ranking_atp" if circuit == 'ATP' else "ranking_wta"
        rankings = self.data.get(ranking_key, [])
        
        if not rankings:
            return f"Desculpe, os dados do ranking {circuit} não estão disponíveis no momento."
        
        result = f"🏆 <span class='msg-highlight'>Ranking {circuit} Oficial (Atualizado: Março de 2026):</span>\n\n"
        for p in rankings[:10]: 
            flag = self._get_flag(p.get('country', ''))
            result += f"<span class='msg-highlight'>{p['position']}º</span>. {p['name']} ({flag} {p['country']}) - <span class='msg-highlight'>{p['points']} pts</span>\n"
        
        if circuit.lower() == "wta":
            result += f"\nQuer saber mais sobre alguma dessas jogadoras da {circuit}?"
        else:
            result += f"\nQuer saber mais sobre algum desses jogadores da {circuit}?"
        return result 

    # --- Lógica de Torneios e Campeões ---
    def get_last_champions(self, tournament=None): 
        grand_slams = self.data.get("grand_slams", {})
        if tournament:
            found_winners = []
            sorted_years = sorted(grand_slams.keys(), reverse=True)
            for year in sorted_years:
                tournaments = grand_slams[year]
                for t_name, info in tournaments.items():
                    if tournament.lower() in t_name.lower():
                        if isinstance(info, dict):
                            parts = []
                            if "Masculino" in info:
                                m = info["Masculino"]
                                parts.append(f"Masc: {m['campeao']} (Vice: {m.get('vice', 'N/A')})")
                            if "Feminino" in info:
                                f = info["Feminino"]
                                parts.append(f"Fem: {f['campeao']} (Vice: {f.get('vice', 'N/A')})")
                            found_winners.append(f"{year}: {' | '.join(parts)}")
                        else:
                            found_winners.append(f"{year}: {info}")
            if not found_winners:
                return f"Não encontrei dados de vencedores para '{tournament}' na minha base técnica."
            result = f"🏆 <span class='msg-highlight'>Vencedores de {tournament} (Histórico Detalhado):</span>\n\n"
            for entry in found_winners:
                result += f"• {entry}\n"
            result += "\nAlgum desses títulos te surpreende?"
            return result

        if not grand_slams: return "Não encontrei os campeões no momento."
        latest_year = max(grand_slams.keys())
        slams = grand_slams.get(latest_year, {})
        result = f"🎾 <span class='msg-highlight'>Campeões de Grand Slam em {latest_year}:</span>\n\n"
        for tourney, info in slams.items():
            if isinstance(info, dict):
                m = info.get("Masculino", {}).get("campeao", "")
                f = info.get("Feminino", {}).get("campeao", "")
                camp_p = f"{m} (M)" if m else ""
                if f: camp_p += f" / {f} (F)" if camp_p else f"{f} (F)"
                result += f"• {tourney}: {camp_p}\n"
            else: result += f"• {tourney}: {info}\n"
        result += "\nAcha que teremos novos dominadores no próximo ano?"
        return result

    def get_last_winner(self, tournament):
        """Retorna o último campeão de um torneio (Grand Slam ou ATP 1000/500)."""
        # Para Grand Slams: busca no histórico de campeões (percorre anos do mais recente ao mais antigo)
        grand_slams = self.data.get("grand_slams", {})
        if grand_slams:
            for year in sorted(grand_slams.keys(), reverse=True):
                slams = grand_slams[year]
                for t_name, info in slams.items():
                    if tournament.lower() in t_name.lower():
                        if isinstance(info, dict):
                            parts = []
                            if "Masculino" in info:
                                parts.append(f"Masc: {info['Masculino']['campeao']}")
                            if "Feminino" in info:
                                parts.append(f"Fem: {info['Feminino']['campeao']}")
                            return f"🏆 <span class='msg-highlight'>Último campeão de {t_name} ({year}):</span>\n\n{'  |  '.join(parts)}"
        # Para ATP 1000/500/Finals: busca nos recent_champions
        t_details = self.data.get("tournament_details", {})
        for t_name, info in t_details.items():
            if tournament.lower() in t_name.lower() or t_name.lower() in tournament.lower():
                champions = info.get("recent_champions", [])
                if champions:
                    return f"🏆 <span class='msg-highlight'>Último campeão de {t_name}:</span>\n\n• {champions[0]}"
        return None

    def get_all_tournament_names(self):
        """Retorna lista de todos os nomes de torneios conhecidos (Grand Slams + Masters + ATP 500 + Finals)."""
        names = []
        for source in ("grand_slam_details", "tournament_details"):
            names.extend(self.data.get(source, {}).keys())
        return names

    def get_grand_slam_details(self, tournament):
        """Busca detalhes em grand_slam_details e tournament_details (unificado)."""
        return self._get_tournament_details(tournament)

    def _get_tournament_details(self, tournament):
        """Retorna ficha completa de qualquer torneio (Grand Slam, Masters 1000, ATP 500, Finals)."""
        # Busca em grand_slam_details primeiro (têm estrutura com greatest_male/female)
        gs_details = self.data.get("grand_slam_details", {})
        for t_name, info in gs_details.items():
            if tournament.lower() in t_name.lower():
                male = info.get("greatest_male", {})
                female = info.get("greatest_female", {})
                flag = self._get_flag(info["location"].split(", ")[-1]) if ", " in info["location"] else ""
                result = (
                    f"🏟️ <span class='msg-highlight'>{t_name} — Ficha Completa:</span>\n\n"
                    f"📍 <span class='attr-label'>Local:</span> {flag} {info['location']}\n"
                    f"🎾 <span class='attr-label'>Superfície:</span> {info['surface']}\n"
                    f"📅 <span class='attr-label'>Fundado em:</span> {info['founded']}\n"
                    f"🎯 <span class='attr-label'>Pontos (Campeão):</span> {info['points']} pts\n"
                    f"💰 <span class='attr-label'>Premiação:</span> {info['prize_money']}\n\n"
                    f"👑 <span class='msg-highlight'>Maior Campeão:</span> "
                    f"{male['name']} — {male['titles']}x títulos"
                    f" ({male.get('nickname', '')})\n"
                    f"👑 <span class='msg-highlight'>Maior Campeã:</span> "
                    f"{female['name']} — {female['titles']}x títulos"
                    f" ({female.get('nickname', '')})\n\n"
                    f"📖 <span class='attr-label'>História:</span> {info['history']}"
                )
                return result

        # Busca em tournament_details (Masters 1000, ATP 500, ATP Finals)
        t_details = self.data.get("tournament_details", {})
        for t_name, info in t_details.items():
            if tournament.lower() in t_name.lower() or t_name.lower() in tournament.lower():
                flag = self._get_flag(info["location"].split(", ")[-1]) if ", " in info["location"] else ""
                champions_text = "\n".join(f"  • {c}" for c in info.get("recent_champions", []))
                result = (
                    f"🏟️ <span class='msg-highlight'>{t_name} ({info['category']}) — Ficha Completa:</span>\n\n"
                    f"📍 <span class='attr-label'>Local:</span> {flag} {info['location']}\n"
                    f"🎾 <span class='attr-label'>Superfície:</span> {info['surface']}\n"
                    f"📅 <span class='attr-label'>Fundado em:</span> {info['founded']}\n"
                    f"🎯 <span class='attr-label'>Pontos (Campeão):</span> {info['points']} pts\n"
                    f"💰 <span class='attr-label'>Premiação:</span> {info['prize_money']}\n\n"
                    f"🏆 <span class='msg-highlight'>Campeões Recentes:</span>\n{champions_text}\n\n"
                    f"📖 <span class='attr-label'>História:</span> {info['history']}"
                )
                return result
        return None

    # --- Lógica Biográfica de Jogadores ---
    def get_player_info(self, name): 
        players = self.data.get("player_details", {})
        ranking_atp = self.data.get("ranking_atp", [])
        ranking_wta = self.data.get("ranking_wta", [])

        # Variáveis globais de controle de dados
        found_player_name = None
        player_data = None
        is_full_bio = False

        # 1. Tenta biografia completa
        for p_name, details in players.items():
            if name.lower() in p_name.lower():
                found_player_name = p_name
                player_data = details
                is_full_bio = True
                break
        
        # 2. Se não achou biografia, tenta apenas o ranking
        if not found_player_name:
            for circuit in ['atp', 'wta']:
                for r in self.data.get(f"ranking_{circuit}", []):
                    if name.lower() in r['name'].lower():
                        found_player_name = r['name']
                        player_data = r
                        is_full_bio = False
                        break
                if found_player_name: break

        if not found_player_name: return None

        # --- CONSTRUÇÃO DA RESPOSTA COM DESIGN PREMIUM ---
        
        # Rank Info e Pontos
        rank_label = "N/A"
        player_points = "N/A"
        
        # Busca no ranking ATP
        for r in ranking_atp:
            if found_player_name.lower() in r['name'].lower() or r['name'].lower() in found_player_name.lower():
                rank_label = f"{r['position']}º (ATP)"
                player_points = r.get('points', 'N/A')
                break
        
        # Se não achou na ATP, busca na WTA
        if rank_label == "N/A":
            for r in ranking_wta:
                if found_player_name.lower() in r['name'].lower() or r['name'].lower() in found_player_name.lower():
                    rank_label = f"{r['position']}º (WTA)"
                    player_points = r.get('points', 'N/A')
                    break

        country_name = player_data.get('country', 'N/A')
        # Busca a bandeira emoji normalizada
        flag = self._get_flag(country_name)

        # Dados estruturados com fallbacks para garantir que todos tenham os mesmos campos
        age = player_data.get('age', 'N/A')
        if age != 'N/A' and isinstance(age, (int, float)): age = f"{age} anos"
        
        style = player_data.get('style', 'N/A')
        titles = player_data.get('titles', 'N/A')
        fact = player_data.get('fact', 'N/A')

        # Cabeçalho da Ficha - Estrutura unificada e robusta
        result = (f"🎾 <span class='player-name'>{found_player_name}</span>\n"
                  f"📊 <span class='attr-label attr-rank'>Rank Atual:</span> {rank_label}\n"
                  f"<span class='flag-emoji'>{flag}</span> <span class='attr-label attr-country'>País:</span> {country_name}\n"
                  f"🎂 <span class='attr-label attr-age'>Idade:</span> {age}\n"
                  f"🎾 <span class='attr-label attr-style'>Estilo:</span> {style}\n"
                  f"🏆 <span class='attr-label attr-titles'>Títulos:</span> {titles}\n"
                  f"💡 <span class='attr-label attr-fact'>Curiosidade:</span> {fact}\n"
                  f"🎯 <span class='attr-label'>Pontos:</span> {player_points}\n\n")


        # Definindo pronome baseado no circuito (WTA/Feminino ou ATP/Masculino)
        pronome = "ele"
        wta_legends = ["Haddad Maia", "Swiatek", "Sabalenka", "Williams", "Sharapova", "Bueno", "Jabeur", "Krejcikova", "Gauff", "Rybakina", "Paolini", "Zheng", "Pegula"]
        if "(WTA)" in rank_label or any(w in found_player_name for w in wta_legends):
            pronome = "ela"

        if is_full_bio:
            result += f"O que mais você gostaria de saber sobre {pronome}?"
        else:
            # Mensagem auxiliar para jogadores que só tem dados básicos no ranking
            result += (f"Eu detectei que <span class='msg-highlight'>{found_player_name}</span> faz parte do Top 100, mas ainda não tenho sua biografia detalhada.\n"
                       f"O que mais você gostaria de saber sobre {pronome}?")

        return result

    def get_player_country(self, name): 
        players = self.data.get("player_details", {})
        for p_name, details in players.items():
            if name.lower() in p_name.lower():
                country_name = details.get('country', 'Nacionalidade não cadastrada')
                flag = self._get_flag(country_name)
                return f"🎾 O jogador <span class='msg-highlight'>{p_name}</span> é da <span class='flag-emoji'>{flag}</span> <span class='msg-highlight'>{country_name}</span>."
        
        for circuit in ['atp', 'wta']:
            for p in self.data.get(f"ranking_{circuit}", []):
                if name.lower() in p['name'].lower():
                    flag = self._get_flag(p['country'])
                    return f"🎾 O jogador <span class='msg-highlight'>{p['name']}</span> representa <span class='flag-emoji'>{flag}</span> <span class='msg-highlight'>{p['country']}</span>."
        return f"Ainda não tenho a nacionalidade de '{name}' no meu banco de dados técnico."

    def get_all_player_names(self):
        details_names = list(self.data.get("player_details", {}).keys())
        atp_names = [p['name'] for p in self.data.get("ranking_atp", [])]
        wta_names = [p['name'] for p in self.data.get("ranking_wta", [])]
        all_names = list(set(details_names + atp_names + wta_names))
        return all_names

    # --- Métodos de Filtragem por País ---

    def _normalize(self, text):
        """Normaliza texto removendo acentos para comparação case/accent-insensitive."""
        if not text:
            return ""
        nfkd = unicodedata.normalize('NFKD', text.lower().strip())
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    def get_filtered_ranking(self, circuit='ATP', country=None, limit=10):
        """Retorna o ranking filtrado por país e/ou limitado a N resultados."""
        ranking_key = f"ranking_{circuit.lower()}"
        rankings = self.data.get(ranking_key, [])

        if country:
            country_norm = self._normalize(country)
            rankings = [p for p in rankings if self._normalize(p.get('country', '')) == country_norm]

        return rankings[:limit]

    def get_best_from_country(self, country):
        """Retorna os melhores jogadores de um país (ATP e WTA)."""
        atp_best = self.get_filtered_ranking('ATP', country=country, limit=3)
        wta_best = self.get_filtered_ranking('WTA', country=country, limit=3)

        if not atp_best and not wta_best:
            return f"Não encontrei jogadores representando <span class='msg-highlight'>{country}</span> no ranking atual."

        flag = self._get_flag(country)
        result = f"🎾 <span class='msg-highlight'>Melhores jogadores {flag} {country}:</span>\n\n"

        if atp_best:
            result += "<span class='msg-highlight'>ATP (Masculino):</span>\n"
            for p in atp_best:
                result += f"  {p['position']}º. {p['name']} — {p['points']} pts\n"
            result += "\n"

        if wta_best:
            result += "<span class='msg-highlight'>WTA (Feminino):</span>\n"
            for p in wta_best:
                result += f"  {p['position']}º. {p['name']} — {p['points']} pts\n"

        return result.strip()

    def reload_data(self):
        """Recarrega os dados do JSON sem reiniciar o servidor."""
        self.data = self._load_data()
