import json
import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Intervalo mínimo entre refreshes (24 horas em segundos)
CACHE_TTL = 86400

# Headers padrão para simular navegador real
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Mapeamento de nomes de países em inglês (tennisexplorer) para português (tennis_data.json)
COUNTRY_EN_TO_PT = {
    "Argentina": "Argentina", "Australia": "Austrália", "Austria": "Áustria",
    "Belarus": "Bielorrússia", "Belgium": "Bélgica", "Bolivia": "Bolívia",
    "Bosnia and Herzeg.": "Bósnia", "Brazil": "Brasil", "Bulgaria": "Bulgária",
    "Canada": "Canadá", "Chile": "Chile", "China": "China", "Colombia": "Colômbia",
    "Croatia": "Croácia", "Czech Republic": "Rep. Tcheca", "Denmark": "Dinamarca",
    "Dominican Rep.": "Rep. Dominicana", "Ecuador": "Equador", "Egypt": "Egito",
    "Finland": "Finlândia", "France": "França", "Georgia": "Geórgia",
    "Germany": "Alemanha", "Great Britain": "Reino Unido", "Greece": "Grécia",
    "Hungary": "Hungria", "India": "Índia", "Indonesia": "Indonésia",
    "Israel": "Israel", "Italy": "Itália", "Japan": "Japão",
    "Kazakhstan": "Cazaquistão", "Latvia": "Letônia", "Lithuania": "Lituânia",
    "Luxembourg": "Luxemburgo", "Mexico": "México", "Monaco": "Mônaco",
    "Montenegro": "Montenegro", "Morocco": "Marrocos", "Netherlands": "Holanda",
    "New Zealand": "Nova Zelândia", "Norway": "Noruega", "Paraguay": "Paraguai",
    "Peru": "Peru", "Philippines": "Filipinas", "Poland": "Polônia",
    "Portugal": "Portugal", "Romania": "Romênia", "Russia": "Rússia",
    "Serbia": "Sérvia", "Slovakia": "Eslováquia", "Slovenia": "Eslovênia",
    "South Africa": "África do Sul", "South Korea": "Coreia do Sul",
    "Spain": "Espanha", "Sweden": "Suécia", "Switzerland": "Suíça",
    "Taiwan": "Taiwan", "Thailand": "Tailândia", "Tunisia": "Tunísia",
    "Turkey": "Turquia", "USA": "EUA", "Ukraine": "Ucrânia",
    "Uruguay": "Uruguai", "Uzbekistan": "Uzbequistão", "Venezuela": "Venezuela",
}

# Mapeamento de código de país ISO-3 (WTA API) para português
COUNTRY_CODE_TO_PT = {
    "ARG": "Argentina", "AUS": "Austrália", "AUT": "Áustria", "BLR": "Bielorrússia",
    "BEL": "Bélgica", "BIH": "Bósnia", "BRA": "Brasil", "BUL": "Bulgária",
    "CAN": "Canadá", "CHI": "Chile", "CHN": "China", "COL": "Colômbia",
    "CRO": "Croácia", "CZE": "Rep. Tcheca", "DEN": "Dinamarca", "ECU": "Equador",
    "EGY": "Egito", "ESP": "Espanha", "EST": "Estônia", "FIN": "Finlândia",
    "FRA": "França", "GBR": "Reino Unido", "GEO": "Geórgia", "GER": "Alemanha",
    "GRE": "Grécia", "HUN": "Hungria", "INA": "Indonésia", "IND": "Índia",
    "ISR": "Israel", "ITA": "Itália", "JPN": "Japão", "KAZ": "Cazaquistão",
    "KOR": "Coreia do Sul", "LAT": "Letônia", "LTU": "Lituânia", "LUX": "Luxemburgo",
    "MAR": "Marrocos", "MEX": "México", "MNE": "Montenegro", "MON": "Mônaco",
    "NED": "Holanda", "NOR": "Noruega", "NZL": "Nova Zelândia", "PAR": "Paraguai",
    "PER": "Peru", "PHI": "Filipinas", "POL": "Polônia", "POR": "Portugal",
    "ROU": "Romênia", "RSA": "África do Sul", "RUS": "Rússia", "SLO": "Eslovênia",
    "SRB": "Sérvia", "SUI": "Suíça", "SVK": "Eslováquia", "SWE": "Suécia",
    "THA": "Tailândia", "TPE": "Taiwan", "TUN": "Tunísia", "TUR": "Turquia",
    "UKR": "Ucrânia", "URU": "Uruguai", "USA": "EUA", "UZB": "Uzbequistão",
    "VEN": "Venezuela",
}


# Correção de nomes conhecidos que perdem acentos ou formatação no scraping
NAME_CORRECTIONS = {
    "Joao Fonseca": "João Fonseca",
    "Joao Sousa": "João Sousa",
    "Thiago Seyboth Wild": "Thiago Seyboth Wild",
    # Acentos perdidos no scraping
    "Joao Fonseca": "João Fonseca",
    "Joao Sousa": "João Sousa",
    "Felix Auger Aliassime": "Félix Auger-Aliassime",
    "Jiri Lehecka": "Jiří Lehečka",
    "Gael Monfils": "Gaël Monfils",
    "Holger Vansen Rune": "Holger Rune",
    # Nomes compostos invertidos pelo tennisexplorer (Sobrenome Nome1 Nome2)
    # O _flip_name gera "Nome2 Sobrenome Nome1" — corrigimos aqui
    "Martin Etcheverry Tomas": "Tomás Martin Etcheverry",
    "Manuel Cerundolo Juan": "Juan Manuel Cerundolo",
    "Andres Burruchaga Roman": "Roman Andrés Burruchaga",
    "Agustin Tirante Thiago": "Thiago Agustín Tirante",
    # WTA — espaço duplo no nome que vem da API
    "Jaqueline  Cristian": "Jaqueline Cristian",
}


def _flip_name(name_raw):
    """
    Inverte nome do formato 'Sobrenome Nome' (tennisexplorer) para 'Nome Sobrenome'.
    Trata nomes compostos como 'De Minaur Alex' → 'Alex De Minaur'.
    Aplica correções de acentos para nomes conhecidos.
    """
    parts = name_raw.strip().split()
    if len(parts) <= 1:
        return name_raw.strip()
    # O último token é geralmente o primeiro nome
    first_name = parts[-1]
    last_name = " ".join(parts[:-1])
    full_name = f"{first_name} {last_name}"
    # Aplica correção se disponível
    return NAME_CORRECTIONS.get(full_name, full_name)


def _clean_name(name):
    """Remove espaços duplos e normaliza espaços em branco."""
    return " ".join(name.split())


def _translate_country_en(country_en):
    """Traduz nome de país do inglês para português."""
    return COUNTRY_EN_TO_PT.get(country_en, country_en)


def _translate_country_code(code):
    """Traduz código ISO-3 de país para nome em português."""
    return COUNTRY_CODE_TO_PT.get(code, code)


class TennisAPIClient:
    """
    Cliente que atualiza rankings ATP e WTA de fontes externas reais.

    Fontes:
    - ATP: Scraping de tennisexplorer.com (HTML server-rendered, sem Cloudflare)
    - WTA: API JSON oficial (api.wtatennis.com, pública e sem autenticação)

    Estratégia: cache-based refresh — atualiza no máximo 1x por dia.
    Fallback: se qualquer erro ocorrer, mantém os dados estáticos existentes.
    """

    def __init__(self, data_path='tennis_data.json'):
        self.data_path = data_path

    def _load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_data(self, data):
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def should_refresh(self):
        """Verifica se os dados estão desatualizados (mais de CACHE_TTL segundos)."""
        data = self._load_data()
        last_updated = data.get("last_updated")
        if not last_updated:
            return True
        try:
            last_dt = datetime.fromisoformat(last_updated)
            elapsed = (datetime.now() - last_dt).total_seconds()
            return elapsed > CACHE_TTL
        except (ValueError, TypeError):
            return True

    # ============================================================
    # ATP — Scraping via tennisexplorer.com
    # ============================================================

    def _fetch_atp_ranking(self):
        """
        Busca o ranking ATP Top 100 via scraping de tennisexplorer.com.
        Página 1 = posições 1-50, Página 2 = posições 51-100.
        Retorna lista no formato do tennis_data.json ou None se falhar.
        """
        print("[API_CLIENT] Buscando ranking ATP via tennisexplorer.com...")
        all_players = []

        for page in [1, 2]:
            url = f"https://www.tennisexplorer.com/ranking/atp-men/?page={page}"
            try:
                response = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
                if response.status_code != 200:
                    print(f"[API_CLIENT] ATP page {page}: HTTP {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                # A tabela de ranking é a primeira <table class='result'> com mais de 10 linhas
                for table in soup.find_all("table", class_="result"):
                    rows = table.find_all("tr")
                    if len(rows) < 10:
                        continue

                    for row in rows[1:]:  # Pula o header
                        cells = row.find_all("td")
                        if len(cells) < 5:
                            continue

                        rank_text = cells[0].get_text(strip=True).rstrip(".")
                        name_raw = cells[2].get_text(strip=True)
                        country_en = cells[3].get_text(strip=True)
                        points_text = cells[4].get_text(strip=True)

                        # Valida que é uma linha de ranking válida
                        if not rank_text.isdigit():
                            continue

                        all_players.append({
                            "position": int(rank_text),
                            "name": _flip_name(name_raw),
                            "country": _translate_country_en(country_en),
                            "points": points_text,
                        })
                    break  # Só processa a primeira tabela grande

            except requests.RequestException as e:
                print(f"[API_CLIENT] ATP page {page} erro de rede: {e}")
                continue

        if len(all_players) >= 50:
            print(f"[API_CLIENT] ATP: {len(all_players)} jogadores obtidos com sucesso.")
            return all_players
        elif all_players:
            print(f"[API_CLIENT] ATP: apenas {len(all_players)} jogadores (parcial).")
            return all_players

        print("[API_CLIENT] ATP: falha ao obter dados.")
        return None

    # ============================================================
    # WTA — API JSON oficial (api.wtatennis.com)
    # ============================================================

    def _fetch_wta_ranking(self):
        """
        Busca o ranking WTA Top 100 via API JSON pública da WTA.
        Endpoint: api.wtatennis.com/tennis/players/ranked
        Retorna lista no formato do tennis_data.json ou None se falhar.
        """
        print("[API_CLIENT] Buscando ranking WTA via api.wtatennis.com...")
        all_players = []

        url = "https://api.wtatennis.com/tennis/players/ranked"
        params = {
            "metric": "SINGLES",
            "type": "rankSingles",
            "sort": "asc",
            "pageSize": 100,
            "page": 0,
        }
        wta_headers = {
            "User-Agent": BROWSER_HEADERS["User-Agent"],
            "Accept": "application/json",
            "account": "wta",
            "referer": "https://www.wtatennis.com/",
        }

        try:
            response = requests.get(url, params=params, headers=wta_headers, timeout=15)
            if response.status_code != 200:
                print(f"[API_CLIENT] WTA API: HTTP {response.status_code}")
                # Fallback: tenta via tennisexplorer
                return self._fetch_wta_ranking_fallback()

            data = response.json()
            if not isinstance(data, list):
                print("[API_CLIENT] WTA API: resposta inesperada.")
                return self._fetch_wta_ranking_fallback()

            for entry in data:
                player = entry.get("player", {})
                country_code = player.get("countryCode", "")
                all_players.append({
                    "position": entry.get("ranking", 0),
                    "name": _clean_name(NAME_CORRECTIONS.get(player.get("fullName", ""), player.get("fullName", ""))),
                    "country": _translate_country_code(country_code),
                    "points": str(entry.get("points", "0")),
                })

        except requests.RequestException as e:
            print(f"[API_CLIENT] WTA API erro de rede: {e}")
            return self._fetch_wta_ranking_fallback()

        if all_players:
            print(f"[API_CLIENT] WTA: {len(all_players)} jogadoras obtidas com sucesso.")
            return all_players

        print("[API_CLIENT] WTA: falha ao obter dados.")
        return None

    def _fetch_wta_ranking_fallback(self):
        """Fallback: busca ranking WTA via tennisexplorer.com caso a API falhe."""
        print("[API_CLIENT] WTA fallback: tentando tennisexplorer.com...")
        all_players = []

        for page in [1, 2]:
            url = f"https://www.tennisexplorer.com/ranking/wta-women/?page={page}"
            try:
                response = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                for table in soup.find_all("table", class_="result"):
                    rows = table.find_all("tr")
                    if len(rows) < 10:
                        continue

                    for row in rows[1:]:
                        cells = row.find_all("td")
                        if len(cells) < 5:
                            continue

                        rank_text = cells[0].get_text(strip=True).rstrip(".")
                        name_raw = cells[2].get_text(strip=True)
                        country_en = cells[3].get_text(strip=True)
                        points_text = cells[4].get_text(strip=True)

                        if not rank_text.isdigit():
                            continue

                        all_players.append({
                            "position": int(rank_text),
                            "name": _flip_name(name_raw),
                            "country": _translate_country_en(country_en),
                            "points": points_text,
                        })
                    break

            except requests.RequestException:
                continue

        if all_players:
            print(f"[API_CLIENT] WTA fallback: {len(all_players)} jogadoras obtidas.")
            return all_players
        return None

    # ============================================================
    # Refresh principal
    # ============================================================

    def refresh_rankings(self):
        """
        Atualiza rankings ATP e WTA a partir das fontes externas.
        ATP: scraping tennisexplorer.com
        WTA: API JSON wtatennis.com (fallback: tennisexplorer)
        Retorna True se atualizou pelo menos um circuito.
        """
        print("[API_CLIENT] Iniciando refresh de rankings...")
        data = self._load_data()
        updated = False

        try:
            atp_ranking = self._fetch_atp_ranking()
            if atp_ranking:
                data["ranking_atp"] = atp_ranking
                updated = True

            wta_ranking = self._fetch_wta_ranking()
            if wta_ranking:
                data["ranking_wta"] = wta_ranking
                updated = True

        except Exception as e:
            print(f"[API_CLIENT] Erro inesperado no refresh: {e}")

        # Atualiza timestamp independente de sucesso (evita retry imediato)
        data["last_updated"] = datetime.now().isoformat()
        self._save_data(data)

        if updated:
            print("[API_CLIENT] Rankings atualizados e salvos com sucesso!")
        else:
            print("[API_CLIENT] Nenhum ranking atualizado. Mantendo dados existentes.")

        return updated

    def refresh_if_needed(self):
        """Verifica e atualiza os dados se necessário. Chamado no startup do servidor."""
        if self.should_refresh():
            print("[API_CLIENT] Dados desatualizados. Iniciando refresh...")
            return self.refresh_rankings()
        else:
            print("[API_CLIENT] Dados atualizados. Nenhum refresh necessário.")
            return False
