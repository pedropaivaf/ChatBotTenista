import json
import os
import re
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Intervalo mínimo entre refreshes (24 horas em segundos)
CACHE_TTL = 86400

# Configuração de requisições HTTP com retry (garante ranking completo no startup)
REQUEST_TIMEOUT = 20        # timeout por tentativa (segundos)
MAX_RETRIES = 3             # número de tentativas por requisição
RETRY_BACKOFF = 2          # base de espera entre tentativas (segundos, cresce a cada retry)

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


def _age_from_dob(dob):
    """Calcula a idade (anos completos) a partir de uma data de nascimento ISO
    ('YYYY-MM-DD', como a API da WTA retorna em dateOfBirth). Retorna int ou None."""
    if not isinstance(dob, str) or len(dob) < 10:
        return None
    try:
        d = datetime.strptime(dob[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None
    today = datetime.now()
    age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    return age if 14 <= age <= 60 else None  # sanidade (descarta datas absurdas)


def _http_get(url, headers, params=None, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES, label=""):
    """
    GET HTTP com retry automático em timeout/erro de rede.
    Espera incremental (RETRY_BACKOFF * tentativa) entre tentativas.
    Retorna o Response em caso de sucesso, ou None se todas as tentativas falharem.
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return requests.get(url, headers=headers, params=params, timeout=timeout)
        except requests.RequestException as e:
            last_error = e
            if attempt < max_retries:
                wait = RETRY_BACKOFF * attempt
                print(f"[API_CLIENT] {label} tentativa {attempt}/{max_retries} falhou ({e}). Retry em {wait}s...")
                time.sleep(wait)
    print(f"[API_CLIENT] {label} falhou após {max_retries} tentativas: {last_error}")
    return None


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
            response = _http_get(url, BROWSER_HEADERS, label=f"ATP page {page}")
            if response is None:
                continue
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

                    # Link da página do jogador (usado p/ enriquecer a idade via dateOfBirth)
                    link = cells[2].find("a")
                    player_url = link.get("href") if link else None

                    all_players.append({
                        "position": int(rank_text),
                        "name": _flip_name(name_raw),
                        "country": _translate_country_en(country_en),
                        "points": points_text,
                        "_url": player_url,  # temporário — removido após o enriquecimento
                    })
                break  # Só processa a primeira tabela grande

        if len(all_players) >= 100:
            print(f"[API_CLIENT] ATP: {len(all_players)} jogadores obtidos com sucesso (completo).")
            return all_players
        elif all_players:
            print(f"[API_CLIENT] ATP: apenas {len(all_players)} jogadores (parcial — top 100 incompleto).")
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

        response = _http_get(url, wta_headers, params=params, label="WTA API")
        if response is None:
            return self._fetch_wta_ranking_fallback()
        if response.status_code != 200:
            print(f"[API_CLIENT] WTA API: HTTP {response.status_code}")
            # Fallback: tenta via tennisexplorer
            return self._fetch_wta_ranking_fallback()

        try:
            data = response.json()
        except ValueError:
            print("[API_CLIENT] WTA API: resposta não é JSON válido.")
            return self._fetch_wta_ranking_fallback()

        if not isinstance(data, list):
            print("[API_CLIENT] WTA API: resposta inesperada.")
            return self._fetch_wta_ranking_fallback()

        for entry in data:
            player = entry.get("player", {})
            country_code = player.get("countryCode", "")
            rec = {
                "position": entry.get("ranking", 0),
                "name": _clean_name(NAME_CORRECTIONS.get(player.get("fullName", ""), player.get("fullName", ""))),
                "country": _translate_country_code(country_code),
                "points": str(entry.get("points", "0")),
            }
            # Idade real a partir da data de nascimento (vários nomes possíveis na API)
            age = _age_from_dob(player.get("dateOfBirth") or player.get("birthDate") or player.get("dob"))
            if age:
                rec["age"] = age
            all_players.append(rec)

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
            response = _http_get(url, BROWSER_HEADERS, label=f"WTA fallback page {page}")
            if response is None or response.status_code != 200:
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
        complete = True  # vira False se algum circuito vier incompleto/falhar

        try:
            atp_ranking = self._fetch_atp_ranking()
            if atp_ranking:
                data["ranking_atp"] = atp_ranking
                updated = True
                if len(atp_ranking) < 100:
                    complete = False
                # Enriquece player_details com a idade REAL (data de nascimento das
                # páginas do tennisexplorer). Só busca quem não tem idade numérica.
                self._enrich_ages_from_atp(data, atp_ranking)
            else:
                complete = False

            wta_ranking = self._fetch_wta_ranking()
            if wta_ranking:
                data["ranking_wta"] = wta_ranking
                updated = True
                if len(wta_ranking) < 100:
                    complete = False
                # Enriquece player_details com a idade REAL (dateOfBirth da API WTA)
                self._enrich_ages_from_wta(data, wta_ranking)
            else:
                complete = False

        except Exception as e:
            print(f"[API_CLIENT] Erro inesperado no refresh: {e}")
            complete = False

        # Só grava o cache de 24h quando os rankings vierem COMPLETOS (top 100).
        # Se vier parcial, mantém os dados desatualizados para forçar novo
        # refresh no próximo start (em vez de travar dados incompletos por 24h).
        if complete:
            data["last_updated"] = datetime.now().isoformat()
        else:
            data["last_updated"] = ""
            print("[API_CLIENT] Dados incompletos — será feito novo refresh no próximo start.")
        # Limpeza defensiva: nunca persistir a chave temporária '_url' no ranking ATP.
        for p in data.get("ranking_atp", []):
            p.pop("_url", None)
        self._save_data(data)

        if updated and complete:
            print("[API_CLIENT] Rankings atualizados e salvos com sucesso (completo)!")
        elif updated:
            print("[API_CLIENT] Rankings atualizados parcialmente. Mantendo o que veio.")
        else:
            print("[API_CLIENT] Nenhum ranking atualizado. Mantendo dados existentes.")

        return updated

    def _enrich_ages_from_wta(self, data, wta_ranking):
        """Preenche player_details[nome]['age'] com a idade REAL vinda da API WTA
        (dateOfBirth). Só preenche quando a idade atual NÃO é numérica (ou seja,
        'N/A' ou placeholder como '25 anos (Est.)') — assim correções manuais com
        um número de verdade no JSON são PRESERVADAS em refreshes futuros."""
        details = data.get("player_details", {})
        filled = 0
        for p in wta_ranking:
            name = p.get("name")
            pd_age = details.get(name, {}).get("age")
            if isinstance(pd_age, (int, float)):
                p["age"] = pd_age  # espelha a idade da bio (fonte do display) no ranking
                continue
            age = p.get("age")  # idade calculada do dateOfBirth
            if age and name in details:
                details[name]["age"] = age
                filled += 1
        if filled:
            print(f"[API_CLIENT] Idades WTA enriquecidas via dateOfBirth: {filled} jogadoras.")

    def _fetch_player_age_te(self, player_url):
        """Busca a idade de um jogador na página dele no tennisexplorer.
        Procura 'Age: NN (DD. M. YYYY)' e calcula a idade pela data de nascimento
        (estável). Retorna int ou None."""
        if not player_url:
            return None
        full = player_url if player_url.startswith("http") else "https://www.tennisexplorer.com" + player_url
        resp = _http_get(full, BROWSER_HEADERS, timeout=12, max_retries=1, label="ATP idade")
        if resp is None or resp.status_code != 200:
            return None
        txt = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
        m = re.search(r'Age:\s*\d{1,2}\s*\(\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})\s*\)', txt)
        if m:
            day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return _age_from_dob(f"{year:04d}-{month:02d}-{day:02d}")
        m2 = re.search(r'Age:\s*(\d{1,2})\b', txt)
        if m2:
            a = int(m2.group(1))
            return a if 14 <= a <= 60 else None
        return None

    def _enrich_ages_from_atp(self, data, atp_ranking):
        """Preenche player_details[nome]['age'] com a idade REAL (data de nascimento
        da página do tennisexplorer) para jogadores ATP sem idade numérica. Preserva
        correções manuais (só preenche quando a idade NÃO é um número). Consome a
        chave temporária '_url' das entradas do ranking."""
        details = data.get("player_details", {})
        filled = 0
        fetched = 0
        for p in atp_ranking:
            name = p.get("name")
            url = p.pop("_url", None)  # consome a chave temporária (não persiste no JSON)
            # Já tem idade numérica na bio (real ou corrigida à mão)? Espelha no ranking
            # e não busca de novo (preserva correções manuais).
            pd_age = details.get(name, {}).get("age")
            if isinstance(pd_age, (int, float)):
                p["age"] = pd_age
                continue
            if not url:
                continue
            age = self._fetch_player_age_te(url)
            fetched += 1
            if not age:
                continue
            if name in details:
                details[name]["age"] = age
            p["age"] = age  # grava também na entrada do ranking (consistência/fallback)
            filled += 1
        if fetched:
            print(f"[API_CLIENT] Idades ATP enriquecidas (tennisexplorer): {filled}/{fetched} buscadas.")

    def refresh_if_needed(self):
        """Verifica e atualiza os dados se necessário. Chamado no startup do servidor."""
        if self.should_refresh():
            print("[API_CLIENT] Dados desatualizados. Iniciando refresh...")
            return self.refresh_rankings()
        else:
            print("[API_CLIENT] Dados atualizados. Nenhum refresh necessário.")
            return False
