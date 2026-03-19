import nltk # Biblioteca principal de Processamento de Linguagem Natural (NLP)
import numpy as np # Biblioteca para cálculos matemáticos e manipulação de vetores numéricos
from nltk.stem.porter import PorterStemmer # Algoritmo de Porter para reduzir palavras ao seu "radical" (stem)

# Criamos uma instância global do Stemmer que vai podar as palavras (ex: "vencedores" -> "venc")
stemmer = PorterStemmer() # Inicializa o objeto responsável pela extração do radical

def tokenize(sentence): # Define a função que fatia uma frase em pedaços menores
    """
    Função que fatia uma frase (string) em uma lista de palavras individuais (tokens).
    Exemplo: "Olá, como vai?" -> ["Olá", "como", "vai", "?"]
    """
    # Usamos o word_tokenize do NLTK que lida de forma inteligente com pontuações
    return nltk.word_tokenize(sentence) # Retorna a lista de palavras/tokens

def stem(word): # Define a função que simplifica cada palavra à sua raiz
    """
    Função que reduz uma palavra ao seu radical (raiz).
    Exemplo: "vencedores" -> "venc", "ganhando" -> "ganh"
    Vantagem: O robô entende que "jogou", "jogando" e "jogador" referem-se à mesma ideia ("jog").
    """
    # Converte tudo para minúsculo antes de aplicar a "poda" do radical pelo algoritmo de Porter
    return stemmer.stem(word.lower()) # Retorna a palavra simplificada

def bag_of_words(tokenized_sentence, words): # Função avançada para converter texto em números
    """
    Função que transforma uma frase em um vetor de 'Bag of Words' (Saco de Palavras).
    Gera uma lista de 0s e 1s que representa quais palavras do vocabulário estão na frase.
    """
    # Primeiro, aplicamos o stem (radical) em cada palavra da frase enviada pelo usuário
    sentence_words = [stem(word) for word in tokenized_sentence] # Gera a lista de radicais da frase
    # Criamos um array preenchido com zeros, do tamanho exato da nossa base de palavras conhecidas
    bag = np.zeros(len(words), dtype=np.float32) # Inicializa o vetor numérico zerado
    
    # Percorre o vocabulário conhecido e compara com a frase do usuário
    for idx, w in enumerate(words): # 'idx' é a posição e 'w' é a palavra do vocabulário
        if w in sentence_words: # Se o radical da palavra do vocabulário estiver na frase do usuário...
            bag[idx] = 1 # Marcamos essa posição como 1 para indicar que a ideia foi encontrada

    return bag # Retorna o vetor numérico (o que o robô 'enxerga')

def extract_entities(sentence_tokens, candidates): # Função para detecção inteligente de jogadores/torneios
    """
    Função que busca Identificar 'Entidades' (nomes próprios) no meio de uma frase.
    Refinada para evitar colisões (ex: 'Taylor Fritz' vs 'Taylor Townsend') usando pontuação.
    """
    best_candidate = None # Armazena o melhor resultado encontrado
    max_matches = 0 # Armazena o maior número de palavras coincidentes
    
    # Percorre cada nome de candidato (ex: todos os jogadores do banco de dados)
    for candidate in candidates:
        # Tokeniza e gera os radicais de cada parte do nome do candidato
        candidate_tokens = [stem(w) for w in tokenize(candidate)]
        
        # Filtra tokens muito curtos do candidato (ex: "de", "da") para evitar falsos positivos
        important_candidate_tokens = [t for t in candidate_tokens if len(t) > 2]
        
        # Conta quantas palavras importantes do candidato estão na frase do usuário
        matches = sum(1 for token in important_candidate_tokens if token in sentence_tokens)
        
        # LÓGICA DE PONTUAÇÃO:
        # 1. Se o número de matches atual for maior que o recorde anterior...
        if matches > max_matches:
            max_matches = matches
            best_candidate = candidate
        # 2. Se houver empate no número de matches...
        elif matches > 0 and matches == max_matches:
            # Pegamos o candidato que tem o maior percentual de cobertura da frase
            # Isso ajuda a diferenciar "Taylor Fritz" de "Taylor Townsend" se o usuário digitou "fritz"
            current_best_tokens = [stem(w) for w in tokenize(best_candidate)]
            important_best = [t for t in current_best_tokens if len(t) > 2]
            
            # Se o novo candidato for um "match perfeito" (todas as palavras batem), ele assume a liderança
            if len(important_candidate_tokens) == matches:
                best_candidate = candidate

    # Retorna o melhor candidato apenas se houver pelo menos um match significativo
    return best_candidate if max_matches > 0 else None
