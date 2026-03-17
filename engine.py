import json
import os

class TennisEngine:
    def __init__(self, data_path='tennis_data.json'):
        self.data_path = data_path
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_ranking_summary(self):
        rankings = self.data.get("ranking_atp", [])
        if not rankings:
            return "Desculpe, os dados do ranking não estão disponíveis no momento."
        
        result = "🏆 **Ranking ATP Oficial (Atualizado 2024/2025):**\n"
        for p in rankings[:5]:
            result += f"{p['position']}º. {p['name']} ({p['country']}) - {p['points']} pts\n"
        result += "\nQuer saber mais sobre algum desses jogadores?"
        return result

    def get_last_champions(self):
        slams = self.data.get("grand_slams", {}).get("2024", {})
        if not slams:
            return "Não encontrei os campeões de 2024."
        
        result = "🎾 **Campeões de Grand Slam em 2024:**\n"
        for tourney, winner in slams.items():
            result += f"• {tourney}: {winner}\n"
        result += "\nAcha que 2025 terá os mesmos dominadores?"
        return result

    def get_player_info(self, name):
        players = self.data.get("player_details", {})
        for p_name, details in players.items():
            if name.lower() in p_name.lower():
                return f"**{p_name}** ({details['age']} anos):\nEstilo: {details['style']}\nTítulos: {details['titles']}\nCuriosidade: {details['fact']}\n\nO que mais você gostaria de saber sobre ele?"
        return None
