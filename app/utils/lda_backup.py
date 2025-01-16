import random
from collections import Counter
import nltk
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import re

def initialize_nltk():
    """
    Initialize NLTK resources and stopwords.
    """
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')

def get_stopwords():
    """
    Get combined stopwords from NLTK and custom list.
    """
    stop_words = set(stopwords.words('indonesian'))
    custom_stopwords = {
        'lah', 'kah', 'pun', 'amp', 'yg', 'dgn', 'nya', 'utk',
        'jd', 'trs', 'gw', 'gue', 'lu', 'klo', 'kl', 'si',
        'dm', 'rt', 'dr', 'ny', 'nan', 'amp', 'gak', 'nga',
        'udah', 'udh', 'aja', 'doang', 'banget', 'bgt', 'ya',
        'sih', 'deh', 'tuh', 'kan', 'kok', 'dong', 'dah','giat',
        'nyata', 'main', 'masuk', 'orang', 'bawa', 'ayo','coba', 'mesti',
        'bos', 'kayak', 'biar', 'ketemu'
    }
    stop_words.update(custom_stopwords)
    return stop_words

def clean_text(text):
    """
    Clean text by removing unwanted characters and patterns.
    """
    # Compile regex patterns
    patterns = {
        'url': re.compile(r'https?://\S+|www\.\S+'),
        'mention': re.compile(r'@\w+'),
        'hashtag': re.compile(r'#\w+'),
        'number': re.compile(r'\d+'),
        'emoji': re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
    }
    
    # Lowercase
    text = text.lower()
    
    # Apply all cleaning patterns
    for pattern in patterns.values():
        text = pattern.sub('', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove extra whitespace
    return ' '.join(text.split())

def is_valid_word(word, stop_words):
    """
    Validate if a word should be included in analysis.
    """
    # Check minimum length
    if len(word) < 3:
        return False
        
    # Check if word contains only letters
    if not word.isalpha():
        return False
        
    # Check if word is not in stopwords
    if word in stop_words:
        return False
        
    # Additional validation rules
    if (word.startswith(('xix', 'xx', 'yy', 'zz')) or  # Common spam patterns
        word.endswith(('nya', 'lah', 'kah', 'tah', 'pun')) or  # Common suffixes
        len(set(word)) == 1):  # Repeated characters
        return False
        
    return True

def tokenize_data(data):
    """
    Tokenize and clean text data.
    """
    initialize_nltk()
    stop_words = get_stopwords()
    tokens_list = []
    
    print("Starting preprocessing...")
    original_count = len(data)
    
    for text in data:
        # Clean the text
        cleaned_text = clean_text(text)
        
        # Tokenize
        tokens = word_tokenize(cleaned_text)
        
        # Filter valid words
        valid_tokens = [word for word in tokens if is_valid_word(word, stop_words)]
        
        # Only add documents with valid tokens
        if valid_tokens:
            tokens_list.append(valid_tokens)
    
    processed_count = len(tokens_list)
    print(f"Preprocessing complete:")
    print(f"- Original documents: {original_count}")
    print(f"- Processed documents: {processed_count}")
    print(f"- Removed documents: {original_count - processed_count}")
    
    return tokens_list

# [Previous functions remain the same]
def sample_from_weights(weights):
    """Memilih indeks berdasarkan distribusi bobot yang diberikan."""
    total = sum(weights)
    rnd = total * random.random()
    for i, w in enumerate(weights):
        rnd -= w
        if rnd <= 0:
            return i

def p_topic_given_document(topic, d, document_topic_counts, document_lengths, K, alpha=0.1):
    """Menghitung probabilitas topik tertentu diberikan sebuah dokumen."""
    return ((document_topic_counts[d][topic] + alpha) /
            (document_lengths[d] + K * alpha))

def p_word_given_topic(word, topic, topic_word_counts, topic_counts, W, beta=0.1):
    """Menghitung probabilitas kata diberikan topik."""
    return ((topic_word_counts[topic][word] + beta) /
            (topic_counts[topic] + W * beta))

def topic_weight(d, word, topic, document_topic_counts, document_lengths, topic_word_counts, topic_counts, K, W, alpha=0.1, beta=0.1):
    """Menghitung bobot topik untuk kata dalam dokumen."""
    return p_word_given_topic(word, topic, topic_word_counts, topic_counts, W, beta) * \
           p_topic_given_document(topic, d, document_topic_counts, document_lengths, K, alpha)

def choose_new_topic(d, word, K, document_topic_counts, document_lengths, topic_word_counts, topic_counts, W):
    """Memilih topik baru untuk kata dalam dokumen."""
    weights = []
    for k in range(K):
        weight = topic_weight(d, word, k, document_topic_counts,
                            document_lengths, topic_word_counts, topic_counts, K, W)
        weights.append(weight)
    return sample_from_weights(weights)

def gibbs_sample(documents, K, max_iteration, document_topic_counts, topic_word_counts, topic_counts, document_lengths, document_topics, W):
    """Melakukan sampling Gibbs untuk inferensi LDA."""
    D = len(documents)
    for iteration in range(max_iteration):
        if (iteration + 1) % 500 == 0:
            print(f"Iteration {iteration + 1}/{max_iteration}")
        for d in range(D):
            for i, (word, topic) in enumerate(zip(documents[d], document_topics[d])):
                # Decrease counts
                document_topic_counts[d][topic] -= 1
                topic_word_counts[topic][word] -= 1
                topic_counts[topic] -= 1
                document_lengths[d] -= 1

                # Choose new topic
                new_topic = choose_new_topic(d, word, K, document_topic_counts,
                                          document_lengths, topic_word_counts, topic_counts, W)
                
                # Increase counts
                document_topics[d][i] = new_topic
                document_topic_counts[d][new_topic] += 1
                topic_word_counts[new_topic][word] += 1
                topic_counts[new_topic] += 1
                document_lengths[d] += 1
            # Di dalam fungsi gibbs_sample, setelah bagian increase counts
    print(f"\nPenambahan kata '{word}' ke topik {new_topic}")
    print(f"Document topic counts untuk dok-{d}: {document_topic_counts[d]}")
    print(f"Topic word counts untuk kata '{word}' di topik {new_topic}: {topic_word_counts[new_topic][word]}")
    print(f"Topic counts untuk topik {new_topic}: {topic_counts[new_topic]}")

def run_lda(documents, K, max_iteration):
    """Menjalankan algoritma LDA."""
    print(f"\nInitializing LDA with {K} topics...")
    random.seed(28347429)
    D = len(documents)
    
    # Initialize counters
    document_topic_counts = [Counter() for _ in documents]
    topic_word_counts = [Counter() for _ in range(K)]
    topic_counts = [0 for _ in range(K)]
    document_lengths = [len(d) for d in documents]
    distinct_words = set(word for document in documents for word in document)
    W = len(distinct_words)
    
    print(f"Vocabulary size: {W} unique words")
    print(f"Number of documents: {D}")

    # Initialize random topics
    document_topics = []
    for document in documents:
        topics = [random.randrange(K) for _ in document]
        document_topics.append(topics)
    print(f"topic count = {document_topics}\n")

    # Initialize counts
    for d in range(D):
        for word, topic in zip(documents[d], document_topics[d]):
            document_topic_counts[d][topic] += 1
            topic_word_counts[topic][word] += 1
            topic_counts[topic] += 1

    print("\nStarting Gibbs sampling...")
    gibbs_sample(documents, K, max_iteration, document_topic_counts,
                topic_word_counts, topic_counts, document_lengths, document_topics, W)

    return topic_word_counts, document_topic_counts, document_lengths, topic_counts, W, document_topics  # Added document_topics

def get_topic_word_list(topic_word_counts, document_topic_counts, document_lengths, topic_counts, K, W, min_weight=0.0002):
    """Mendapatkan list kata per topik dengan bobotnya."""
    print("\nExtracting top words for each topic...")
    topic_word_list = {}
    for topic in range(K):
        data = []
        for word, count in topic_word_counts[topic].most_common():
            if count > 1:
                weight = p_word_given_topic(word, topic, topic_word_counts, topic_counts, W) * \
                    (topic_word_counts[topic][word] / topic_counts[topic])
                if weight > min_weight:
                    data.append((word, weight))
        topic_word_list[f"Topik {topic+1}"] = data
    return topic_word_list
def print_document_topic_counts(document_topic_counts):
    print("\nDistribusi topik pada setiap dokumen:")
    for doc_idx, counts in enumerate(document_topic_counts):
        print(f"Dokumen {doc_idx+1}:")
        for topic, count in counts.items():
            print(f"Topik {topic}: {count}")
def print_topic_word_counts(document_topic_counts, topic_word_counts, document_topics, K):
    """
    Print topic word counts for specific words in document index 2.
    """
    doc_index = 2
    target_words = {
        'pilkada', 'integritas', 'julid', 'bicara',
        'rendah', 'konyol', 'cari', 'perhati'
    }
    
    if doc_index < len(document_topic_counts):
        print(f"\nAnalysis for specific words in Document {doc_index + 1}:")
        
        # Get document's topic distribution
        topic_dist = document_topic_counts[doc_index]
        print("\nTopic Distribution in Document:")
        for topic in range(K):
            count = topic_dist.get(topic, 0)
            print(f"Topic {topic + 1}: {count} words")
            
            # Print words from this topic
            print("Words in this topic:")
            for word in target_words:
                if topic_word_counts[topic].get(word, 0) > 0:
                    print(f"  - {word}: {topic_word_counts[topic][word]}")
        
    else:
        print("Error: Document index 2 is out of range!")
def main():
    # Load and process data
    print("Loading data...")
    # with open('C:\\Users\\arraf\\OneDrive\\Dokumen\\Kuliah\\Skripsi\\link-anomaly\\link-anomaly-trending-topic-detection\\hasil_twitt_trending.json', 'r') as file:
    #     hasil_twitt_trending = json.load(file)
    with open('C:\\Users\\arraf\\OneDrive\\Dokumen\\Kuliah\\Skripsi\\link-anomaly\\hasil_twitt_trending_diskrit23.json', 'r') as file:
        hasil_twitt_trending = json.load(file)
    # with open('C:\\Users\\arraf\\OneDrive\\Dokumen\\Kuliah\\Skripsi\\link-anomaly\\link-anomaly-trending-topic-detection\\hasil_ground_truth.json', 'r') as file:
    #     hasil_twitt_trending = json.load(file)

    dat_transform = [item[0] for item in hasil_twitt_trending]
    
    # Preprocess and tokenize
    tokenized_data = tokenize_data(dat_transform)
    # print(tokenized_data)
    # from gensim.models import Phrases
    # bigram = Phrases(tokenized_data, min_count=5, threshold=10)
    # trigram = Phrases(bigram[tokenized_data], threshold=10)
    # tokenized_data = [trigram[bigram[doc]] for doc in tokenized_data]

    
    if len(tokenized_data) < 2:
        print("Not enough valid documents after preprocessing!")
        return
    
    # Run LDA
    K = 5
    max_iteration = 900

    topic_word_counts, document_topic_counts, document_lengths, topic_counts, W, document_topics = run_lda(
        tokenized_data, K, max_iteration)  
    # print_document_topic_counts(document_topic_counts)

    # In your main() function, replace this line:
    print_topic_word_counts(document_topic_counts, topic_word_counts, document_topics, K)


    # Get and print results
    topic_word_list = get_topic_word_list(topic_word_counts, document_topic_counts,
                                         document_lengths, topic_counts, K, W)

    print("\nFinal Topics:")
    for topic, words in topic_word_list.items():
        formatted_words = [f"{word}: {weight:.4f}" for word, weight in words]
        print(f"\n{topic}:")
        print(', '.join(formatted_words))
    



if __name__ == '__main__':
    main()