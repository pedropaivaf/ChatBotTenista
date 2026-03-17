import nltk # Biblioteca principal de Processamento de Linguagem Natural
import numpy as np # Biblioteca para cálculos matemáticos e vetores
from nltk.stem.porter import PorterStemmer # Algoritmo para reduzir palavras ao seu "radical" (stem)

# Criamos uma instância do "Stemmer" que vai podar as palavras (ex: "jogando" -> "jog")
stemmer = PorterStemmer()

def tokenize(sentence):
    """
    Função que fatia uma frase em uma lista de palavras individuais (tokens).
    Exemplo: "Olá, como vai?" -> ["Olá", "como", "vai", "?"]
    """
    # Usamos a função padrão do NLTK para fazer essa separação inteligente
    return nltk.word_tokenize(sentence)

def stem(word):
    """
    Função que reduz uma palavra ao seu radical (raiz).
    Exemplo: "vencedores" -> "venc", "ganhando" -> "ganh"
    Isso ajuda o robô a entender variações da mesma palavra.
    """
    # Converte para minúsculo e aplica a "poda" do radical
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, words):
    """
    Função que transforma uma lista de palavras em um vetor numérico (0 ou 1).
    Isso é o que as Redes Neurais e modelos de Machine Learning usam para 'ler'.
    """
    # Primeiro, reduzimos todas as palavras da frase aos seus radicais
    sentence_words = [stem(word) for word in tokenized_sentence]
    # Criamos um array de zeros com o mesmo tamanho do nosso vocabulário conhecido
    bag = np.zeros(len(words), dtype=np.float32)
    
    # Marcamos com 1 as posições onde a palavra do vocabulário está presente na frase
    for idx, w in enumerate(words):
        if w in sentence_words: 
            bag[idx] = 1 # O robô agora 'vê' a presença daquela ideia na frase

    return bag

def extract_entities(sentence_tokens, candidates):
    """
    Função avançada para identificar 'Entidades Nomeadas' (Jogadores ou Torneios).
    Ela verifica se os radicais dos candidatos estão presentes na frase do usuário.
    """
    # Percorre cada candidato que queremos encontrar (ex: "US Open" ou "Roger Federer")
    for candidate in candidates:
        # Tokeniza e gera o radical de cada parte do candidato
        # Isso permite encontrar "US Open" mesmo que o usuário escreva "us open" ou "o us open"
        candidate_tokens = [stem(w) for w in tokenize(candidate)]
        
        # Verifica se TODOS os pedaços do nome candidato estão presentes nos tokens da frase
        # O 'all()' garante que para 'Australian Open', ambos 'australian' e 'open' devem ser achados
        if all(token in sentence_tokens for token in candidate_tokens):
            return candidate # Retorna o nome formatado bonitinho se encontrado
            
    return None # Retorna nada se não identificar uma entidade conhecida
