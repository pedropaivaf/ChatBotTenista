import json # Biblioteca para ler e escrever arquivos de texto no formato JSON (nossa base de dados)
import os # Biblioteca para interagir com o sistema de arquivos (verificar se arquivos existem)

class TennisEngine: # Classe que representa o nosso motor de consulta técnica
    def __init__(self, data_path='tennis_data.json'): # Método inicializador que roda ao criarmos o objeto
        self.data_path = data_path # Salva o caminho do arquivo de dados numa variável interna (atributo)
        self.data = self._load_data() # Chama a função interna para carregar os dados reais na memória

    def _load_data(self): # Função "privada" (interna) para carregar o conteúdo do JSON
        if os.path.exists(self.data_path): # Verifica se o arquivo físico (ex: tennis_data.json) existe no disco
            with open(self.data_path, 'r', encoding='utf-8') as f: # Abre o arquivo para leitura com acentuação correta
                return json.load(f) # Decodifica o texto JSON e transforma em um dicionário Python
        return {} # Se o arquivo não for encontrado, retorna um dicionário vazio para evitar travamentos

    # --- Lógica de Rankings (Dinâmica para ATP e WTA) ---
    def get_ranking_summary(self, circuit='ATP'): # Função que cria o texto resumo do Ranking (Masculino ou Feminino)
        circuit = circuit.upper() # Garante que a sigla esteja em maiúsculas (ex: "atp" -> "ATP")
        # Define qual chave do JSON buscar com base no circuito
        ranking_key = "ranking_atp" if circuit == 'ATP' else "ranking_wta"
        
        rankings = self.data.get(ranking_key, []) # Tenta extrair a lista de rankings da categoria selecionada
        
        if not rankings: # Caso a lista esteja vazia ou a chave não exista no JSON
            return f"Desculpe, os dados do ranking {circuit} não estão disponíveis no momento."
        
        # Inicia a construção da resposta com um título estilizado usando as classes CSS do projeto
        result = f"🏆 <span class='msg-highlight'>Ranking {circuit} Oficial (Atualizado: Março de 2026):</span>\n"
        
        # Percorre os primeiros 10 registros do ranking (Top 10)
        for p in rankings[:10]: 
            # Monta a string formatada: Posição, Nome, País e Pontuação
            result += f"{p['position']}º. {p['name']} ({p['country']}) - {p['points']} pts\n"
        
        # Adiciona uma pergunta final para incentivar o usuário a continuar a conversa
        result += f"\nQuer saber mais sobre algum@ dess@s jogadores de {circuit}?"
        return result # Retorna o bloco de texto completo pronto para o chat

    # --- Lógica de Torneios e Campeões ---
    def get_last_champions(self, tournament=None): # Função para buscar os grandes campeões históricos
        grand_slams = self.data.get("grand_slams", {}) # Carrega o dicionário de Slams do arquivo de dados
        
        if tournament: # Se o usuário perguntou sobre um torneio específico (ex: "US Open")
            found_winners = [] # Lista para acumular os resultados encontrados
            # Ordena os anos de forma decrescente (do mais novo para o mais antigo) para mostrar o recente primeiro
            sorted_years = sorted(grand_slams.keys(), reverse=True)
            for year in sorted_years: # Percorre cada ano da nossa base histórica cadastrada
                tournaments = grand_slams[year] # Pega o dicionário de torneios daquele ano específico
                for t_name, winner in tournaments.items(): # Verifica cada par Nome-Vencedor
                    if tournament.lower() in t_name.lower(): # Se o nome do torneio bater com o pedido (match de texto)
                        found_winners.append(f"{year}: {winner}") # Guarda a informação de conquista
            
            if not found_winners: # Se após rodar tudo não houver nenhum match válido
                return f"Não encontrei dados de vencedores para '{tournament}' na minha base técnica."
            
            # Monta a resposta formatada com os títulos encontrados (histórico do torneio específico)
            result = f"🏆 <span class='msg-highlight'>Vencedores de {tournament} (Histórico Recente):</span>\n"
            for entry in found_winners: # Adiciona cada campeão em uma lista com marcadores de ponto (bullets)
                result += f"• {entry}\n"
            result += "\nAlgum desses títulos te surpreende?" # Pergunta final de acompanhamento
            return result # Envia a lista de campeões

        # Se o usuário perguntou de forma geral (sem citar qual torneio), mostramos o ano mais atual
        if not grand_slams: # Proteção caso não haja nenhum Slam cadastrado
            return "Não encontrei os campeões no momento."
            
        latest_year = max(grand_slams.keys()) # Descobre qual é o ano mais recente disponível no banco de dados
        slams = grand_slams.get(latest_year, {}) # Carrega os resultados desse ano recorde
        
        # Cria a resposta resumida dos campeões do circuito no ano atual
        result = f"🎾 <span class='msg-highlight'>Campeões de Grand Slam em {latest_year}:</span>\n"
        for tourney, winner in slams.items(): # Lista todos os torneios mapeados naquele ano
            result += f"• {tourney}: {winner}\n"
        result += "\nAcha que teremos novos dominadores no próximo ano?" # Encerra com uma provocação positiva
        return result # Retorna o resumo do ano

    # --- Lógica Biográfica de Jogadores ---
    def get_player_info(self, name): # Função que busca a "ficha técnica" detalhada de um tenista
        players = self.data.get("player_details", {}) # Carrega a base de perfis biográficos (Top Players + Lendas)
        for p_name, details in players.items(): # Percorre todos os nomes dos perfis cadastrados
            if name.lower() in p_name.lower(): # Se encontrar um match no nome (ex: "sinner" encontra "Jannik Sinner")
                # Retorna os dados formatados usando as classes HTML/CSS para destaque visual no frontend
                return f"<span class='msg-highlight'>{p_name}</span> ({details['age']} anos):\nEstilo: {details['style']}\nTítulos: {details['titles']}\nCuriosidade: {details['fact']}\n\nO que mais você gostaria de saber sobre el@?"
        return None # Caso o jogador não esteja na nossa biblioteca, retorna vazio para o app saber lidar

    def get_player_country(self, name): # Função dedicada para buscar a nacionalidade de forma rápida
        players = self.data.get("player_details", {}) # Carrega os perfis biográficos
        for p_name, details in players.items(): # Procura pelo nome solicitado na base
            if name.lower() in p_name.lower(): # Match de texto para localizar o cadastro
                # Retorna uma frase formatada com o país em destaque
                return f"🎾 O jogador <span class='msg-highlight'>{p_name}</span> é da <span class='msg-highlight'>{details.get('country', 'Nacionalidade não cadastrada')}</span>."
        return f"Ainda não tenho a nacionalidade de '{name}' no meu banco de dados técnico." # Resposta para nomes desconhecidos

    # --- Lógica de Utilitário para o NLTK ---
    def get_all_player_names(self): # Função crítica que torna o bot dinâmico
        """Retorna uma lista com os nomes de todos os jogadores cadastrados para que o NLTK possa reconhecê-los."""
        # Extrai todas as chaves (os nomes reais) do dicionário player_details
        return list(self.data.get("player_details", {}).keys())
