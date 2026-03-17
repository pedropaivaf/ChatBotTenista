import nltk # Importa a biblioteca NLTK (Natural Language Toolkit) para Processamento de Linguagem Natural
import numpy as np # Importa NumPy para manipulação de arrays numéricos (útil para modelos futuros)
from nltk.stem.porter import PorterStemmer # Importa o algoritmo de Porter para reduzir palavras ao radical

# Faz o download do recurso 'punkt', que é o motor para dividir frases em palavras
nltk.download('punkt')
stemmer = PorterStemmer() # Cria uma instância do stemmer (o "redutor" de palavras)

def tokenize(sentence): # Função que transforma uma frase em uma lista de palavras individuais
    """
    Divide a frase em um array de palavras/tokens.
    Exemplo: "O que é um Grand Slam?" -> ["O", "que", "é", "um", "Grand", "Slam", "?"]
    """
    return nltk.word_tokenize(sentence) # Usa a função oficial do NLTK para realizar a separação correta

def stem(word): # Função que reduz uma palavra ao seu radical (exclui sufixos e prefixos)
    """
    Stemming = encontrar a forma raiz da palavra.
    Exemplo: ["organize", "organizes", "organizing"] -> "organ"
    """
    return stemmer.stem(word.lower()) # Converte para minúsculo e aplica o algoritmo de redução

def bag_of_words(tokenized_sentence, words): # Função que cria uma representação numérica da frase (vetor)
    """
    Retorna o array bag of words:
    Coloca o número 1 para cada palavra conhecida que existe na frase, e 0 caso contrário.
    """
    # Aplica o radical (stem) em cada palavra encontrada na frase do usuário
    sentence_words = [stem(word) for word in tokenized_sentence]
    # Cria uma lista (bag) cheia de zeros com o mesmo tamanho da nossa lista de palavras conhecidas
    bag = np.zeros(len(words), dtype=np.float32)
    
    # Percorre nossa lista de palavras conhecidas
    for idx, w in enumerate(words):
        if w in sentence_words: # Se a palavra conhecida estiver na frase do usuário
            bag[idx] = 1 # Marca a posição correspondente no vetor como 1

    return bag # Retorna o vetor numérico (seria usado para treinar Redes Neurais futuramente)
