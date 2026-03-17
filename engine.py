import json # Biblioteca para ler e escrever arquivos de texto no formato JSON (nossa base de dados)
import os # Biblioteca para interagir com o sistema de arquivos (verificar se arquivos existem)

class TennisEngine: # Classe que representa o nosso motor de consulta técnica
    def __init__(self, data_path='tennis_data.json'): # Método inicializador da classe que roda ao criarmos o objeto
        self.data_path = data_path # Salva o caminho do arquivo de dados numa variável interna (atributo)
        self.data = self._load_data() # Chama a função interna para carregar os dados reais na memória

    def _load_data(self): # Função "privada" (interna) para carregar o conteúdo do JSON
        if os.path.exists(self.data_path): # Verifica se o arquivo físico (ex: tennis_data.json) existe no disco
            with open(self.data_path, 'r', encoding='utf-8') as f: # Abre o arquivo para leitura com acentuação correta
                return json.load(f) # Decodifica o texto JSON e transforma em um dicionário Python
        return {} # Se o arquivo não for encontrado, retorna um dicionário vazio para evitar travamentos

    def get_ranking_summary(self): # Função que cria o texto resumo do Ranking Mundial ATP
        rankings = self.data.get("ranking_atp", []) # Tenta extrair a lista de rankings; se não houver, usa lista vazia
        if not rankings: # Se a lista estiver vazia (sem dados no JSON)
            return "Desculpe, os dados do ranking não estão disponíveis no momento." # Retorna mensagem amigável
        
        # Inicia a construção da string de resposta com um título estilizado (HTML para o frontend brilhar)
        result = "🏆 <span class='msg-highlight'>Ranking ATP Oficial (Atualizado: Março de 2026):</span>\n"
        for p in rankings[:5]: # Percorre apenas os 5 primeiros jogadores (o "Top 5")
            # Adiciona uma linha para cada jogador com posição, nome, país e pontos
            result += f"{p['position']}º. {p['name']} ({p['country']}) - {p['points']} pts\n"
        result += "\nQuer saber mais sobre algum desses jogadores?" # Pergunta final para engajar o usuário
        return result # Retorna o bloco de texto completo pronto para o chat

    def get_last_champions(self, tournament=None): # Função para buscar os grandes campeões históricos
        grand_slams = self.data.get("grand_slams", {}) # Carrega o dicionário de Slams do motor
        
        if tournament: # Se o usuário perguntou sobre um torneio específico (ex: "US Open")
            found_winners = [] # Lista para acumular os resultados encontrados
            # Ordena os anos de forma decrescente (do mais novo para o mais antigo)
            sorted_years = sorted(grand_slams.keys(), reverse=True)
            for year in sorted_years: # Percorre cada ano da nossa base histórica
                tournaments = grand_slams[year] # Pega a lista de torneios daquele ano
                for t_name, winner in tournaments.items(): # Verifica cada torneio e seu vencedor
                    if tournament.lower() in t_name.lower(): # Se o nome bater com o que o usuário pediu
                        found_winners.append(f"{year}: {winner}") # Guarda o ano e o nome do campeão
            
            if not found_winners: # Se rodou tudo e não achou nada parecido
                return f"Não encontrei dados de vencedores para '{tournament}' na minha base técnica."
            
            # Monta a resposta com os títulos encontrados (historio de US Open, etc)
            result = f"🏆 <span class='msg-highlight'>Vencedores de {tournament} (Histórico Recente):</span>\n"
            for entry in found_winners: # Adiciona cada campeão em uma lista com marcadores (bullets)
                result += f"• {entry}\n"
            result += "\nAlgum desses títulos te surpreende?" # Pergunta de acompanhamento
            return result

        # Se o usuário perguntou de forma geral, pegamos os dados do ano mais recente disponível
        if not grand_slams: # Se não houver dados de Slams
            return "Não encontrei os campeões no momento."
            
        latest_year = max(grand_slams.keys()) # Descobre qual é o ano mais alto cadastrado (ex: 2025)
        slams = grand_slams.get(latest_year, {}) # Pega os torneios desse ano específico
        
        # Cria a resposta resumida do ano atual
        result = f"🎾 <span class='msg-highlight'>Campeões de Grand Slam em {latest_year}:</span>\n"
        for tourney, winner in slams.items(): # Lista todos os torneios e seus vencedores daquele ano
            result += f"• {tourney}: {winner}\n"
        result += "\nAcha que teremos novos dominadores no próximo ano?" # Encerra com uma curiosidade
        return result

    def get_player_info(self, name): # Função que busca a "ficha técnica" biográfica de um tenista
        players = self.data.get("player_details", {}) # Carrega a base de detalhes dos jogadores
        for p_name, details in players.items(): # Percorre os nomes cadastrados (ex: Carlos Alcaraz)
            if name.lower() in p_name.lower(): # Se encontrar um match (mesmo parcial) no nome
                # Retorna a resposta completa usando as tags CSS de destaque que criamos no style.css
                return f"<span class='msg-highlight'>{p_name}</span> ({details['age']} anos):\nEstilo: {details['style']}\nTítulos: {details['titles']}\nCuriosidade: {details['fact']}\n\nO que mais você gostaria de saber sobre ele?"
        return None # Retorna vazio se o jogador não estiver na nossa "biblioteca" técnica

    def get_player_country(self, name): # Nova função para buscar especificamente a nacionalidade
        players = self.data.get("player_details", {}) # Carrega os detalhes dos jogadores
        for p_name, details in players.items(): # Procura pelo nome solicitado
            if name.lower() in p_name.lower(): # Match de nome (mesmo em minúsculo)
                # Retorna uma frase formatada com a bandeira/país usando a cor de destaque
                return f"🎾 O jogador <span class='msg-highlight'>{p_name}</span> é da <span class='msg-highlight'>{details.get('country', 'Nacionalidade não cadastrada')}</span>."
        return f"Ainda não tenho a nacionalidade de '{name}' no meu banco de dados técnico."
