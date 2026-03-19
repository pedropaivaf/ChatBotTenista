import json # Biblioteca para ler e escrever arquivos de texto no formato JSON (nossa base de dados)
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
    "Finlândia": "🇫🇮", "Áustria": "🇦🇹", "Nova Zelândia": "🇳🇿", "Romênia": "🇷🇴"
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
        print(f"[DEBUG_FLAG] Pais: '{country_name}' -> Normalizado: '{normalized_name}' -> Flag: '{flag}'")
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
        
        result += f"\nQuer saber mais sobre algum(a) desses(as) jogadores de {circuit}?"
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
                  f"💰 <span class='attr-label'>Pontos:</span> {player_points}\n\n")

        if is_full_bio:
            result += f"O que mais você gostaria de saber sobre ele(a)?"
        else:
            # Mensagem auxiliar para jogadores que só tem dados básicos no ranking
            result += (f"Eu detectei que <span class='msg-highlight'>{found_player_name}</span> faz parte do Top 100, mas ainda não tenho sua biografia detalhada.\n"
                       f"Você pode perguntar sobre o <span class='msg-highlight'>Ranking Geral</span> ou os <span class='msg-highlight'>Campeões de Grand Slam</span>!")

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
