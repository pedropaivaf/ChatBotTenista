import nltk
import numpy as np
from nltk.stem.porter import PorterStemmer

# Download necessário para o NLTK
nltk.download('punkt')
stemmer = PorterStemmer()

def tokenize(sentence):
    """
    Divide a frase em um array de palavras/tokens.
    Exemplo: "O que é um Grand Slam?" -> ["O", "que", "é", "um", "Grand", "Slam", "?"]
    """
    return nltk.word_tokenize(sentence)

def stem(word):
    """
    Stemming = encontrar a forma raiz da palavra.
    Exemplo: ["organize", "organizes", "organizing"] -> "organ"
    """
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, words):
    """
    Retorna o array bag of words:
    1 para cada palavra conhecida que existe na frase, 0 caso contrário.
    """
    # Realiza o stemming de cada palavra
    sentence_words = [stem(word) for word in tokenized_sentence]
    # Inicializa a bag com 0 para cada palavra
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, w in enumerate(words):
        if w in sentence_words: 
            bag[idx] = 1

    return bag
