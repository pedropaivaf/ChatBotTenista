import json # Biblioteca para ler e escrever arquivos de texto no formato JSON (nossa base de dados)
import os # Biblioteca para interagir com o sistema de arquivos (verificar se arquivos existem)

class TennisEngine: # Classe que representa o nosso motor de consulta técnica
    def __init__(self, data_path='tennis_data.json'): # Método inicializador da classe
        self.data_path = data_path # Salva o caminho do arquivo de dados numa variável interna
        self.data = self._load_data() # Chama a função interna para carregar os dados ao iniciar

    def _load_data(self): # Função que carrega os dados do arquivo JSON para a memória
        if os.path.exists(self.data_path): # Verifica se o arquivo 'tennis_data.json' realmente existe
            with open(self.data_path, 'r', encoding='utf-8') as f: # Abre o arquivo para leitura
                return json.load(f) # Transforma o texto do JSON em um objeto (dicionário) do Python
        return {} # Se o arquivo não existir, retorna um dicionário vazio para não quebrar o código

    def get_ranking_summary(self): # Função que cria o texto com o resumo do ranking ATP
        rankings = self.data.get("ranking_atp", []) # Tenta pegar a lista de ranking do banco de dados
        if not rankings: # Se a lista estiver vazia ou não existir
            return "Desculpe, os dados do ranking não estão disponíveis no momento." # Resposta de erro
        
        result = "🏆 **Ranking ATP Oficial (Atualizado 2024/2025):**\n" # Título da resposta com negrito e emoji
        for p in rankings[:5]: # Percorre os 5 primeiros jogadores da lista
            result += f"{p['position']}º. {p['name']} ({p['country']}) - {p['points']} pts\n" # Monta a linha do jogador
        result += "\nQuer saber mais sobre algum desses jogadores?" # Adiciona a pergunta de acompanhamento
        return result # Retorna o texto formatado final

    def get_last_champions(self): # Função que busca os campeões dos torneios mais importantes
        slams = self.data.get("grand_slams", {}).get("2024", {}) # Busca os vencedores específicos do ano de 2024
        if not slams: # Se não encontrar os dados de 2024
            return "Não encontrei os campeões de 2024." # Mensagem de erro
        
        result = "🎾 **Campeões de Grand Slam em 2024:**\n" # Título formatado
        for tourney, winner in slams.items(): # Percorre cada torneio e seu respectivo campeão
            result += f"• {tourney}: {winner}\n" # Monta a linha com o nome do torneio e vencedor
        result += "\nAcha que 2025 terá os mesmos dominadores?" # Pergunta de acompanhamento
        return result # Retorna a lista completa para o usuário

    def get_player_info(self, name): # Função que busca detalhes biográficos de um jogador específico
        players = self.data.get("player_details", {}) # Carrega os detalhes dos jogadores da base
        for p_name, details in players.items(): # Percorre cada jogador cadastrado nos detalhes
            if name.lower() in p_name.lower(): # Se o nome pesquisado for parecido com o nome do cadastro
                # Retorna um texto detalhado com idade, estilo, títulos e curiosidade
                return f"**{p_name}** ({details['age']} anos):\nEstilo: {details['style']}\nTítulos: {details['titles']}\nCuriosidade: {details['fact']}\n\nO que mais você gostaria de saber sobre ele?"
        return None # Caso não encontre nenhum jogador com esse nome na base técnica
