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
    Ela permite encontrar nomes compostos como 'Roger Federer' mesmo no meio de outras palavras.
    """
    # Percorre cada nome de candidato (ex: nomes de todos os jogadores do banco de dados)
    for candidate in candidates:
        # Tokeniza e gera os radicais de cada parte do nome do candidato
        # Isso garante que "Novak Djokovic" seja encontrado mesmo se o usuário escrever "novak"
        candidate_tokens = [stem(w) for w in tokenize(candidate)]
        
        # LÓGICA DE DETECÇÃO: Verifica se TODOS os pedaços do nome candidato estão na frase
        # Usamos 'all()' para garantir que para 'Joao Fonseca', ambos 'joao' e 'fonsec' sejam achados
        if all(token in sentence_tokens for token in candidate_tokens):
            return candidate # Se achou tudo, retorna o nome oficial (formatado) do cadastro
            
    return None # Se percorreu todos os candidatos e não achou nenhum match completo, retorna nada
