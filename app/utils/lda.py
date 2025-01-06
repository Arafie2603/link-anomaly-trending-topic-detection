import random
from collections import Counter
import nltk
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import re
class LDAModel:
    def __init__(self, n_topics, max_iterations, alpha=0.1, beta=0.1):
        """
        Inisialisasi model LDA.

        Parameters:
        - n_topics (int): Jumlah topik yang akan dihasilkan
        - max_iterations (int): Jumlah iterasi maksimum
        - alpha (float): Parameter Dirichlet untuk distribusi topik-dokumen
        - beta (float): Parameter Dirichlet untuk distribusi kata-topik
        """
        self.K = n_topics
        self.max_iterations = max_iterations
        self.alpha = alpha
        self.beta = beta
        random.seed(28347429)
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        # Initialize stopwords
        self.stop_words = set(stopwords.words('indonesian'))
        
        # Add custom stopwords
        custom_stopwords = {
            'lah', 'kah', 'pun', 'amp', 'yg', 'dgn', 'nya', 'utk',
            'jd', 'trs', 'gw', 'gue', 'lu', 'klo', 'kl', 'si',
            'dm', 'rt', 'dr', 'ny', 'nan', 'amp', 'gak', 'nga',
            'udah', 'udh', 'aja', 'doang', 'banget', 'bgt', 'ya',
            'sih', 'deh', 'tuh', 'kan', 'kok', 'dong', 'dah','giat'
        }
        self.stop_words.update(custom_stopwords)
        
        # Initialize containers
        self.topic_word_counts = None
        self.document_topic_counts = None
        self.document_lengths = None
        self.topic_counts = None
        self.W = None
        self.document_topics = None
        
        # Compile regex patterns
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.number_pattern = re.compile(r'\d+')
        self.emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)

    def clean_text(self, text):
        """
        Membersihkan teks dari noise dan karakter yang tidak diinginkan.
        """
        # Lowercase
        text = text.lower()
        
        # Remove URLs
        text = self.url_pattern.sub('', text)
        
        # Remove mentions
        text = self.mention_pattern.sub('', text)
        
        # Remove hashtags
        text = self.hashtag_pattern.sub('', text)
        
        # Remove numbers
        text = self.number_pattern.sub('', text)
        
        # Remove emojis
        text = self.emoji_pattern.sub('', text)
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def is_valid_word(self, word):
        """
        Memvalidasi apakah sebuah kata valid untuk diproses.
        """
        # Check minimum length
        if len(word) < 3:
            return False
            
        # Check if word contains only letters
        if not word.isalpha():
            return False
            
        # Check if word is not in stopwords
        if word in self.stop_words:
            return False
            
        # Additional validation rules
        if (word.startswith(('xix', 'xx', 'yy', 'zz')) or  # Common spam patterns
            word.endswith(('nya', 'lah', 'kah', 'tah', 'pun')) or  # Common suffixes
            len(set(word)) == 1):  # Repeated characters
            return False
            
        return True

    def tokenize_data(self, data):
        """
        Tokenisasi dan pembersihan data teks.
        """
        tokens_list = []
        for text in data:
            # Clean the text
            cleaned_text = self.clean_text(text)
            
            # Tokenize
            tokens = word_tokenize(cleaned_text)
            
            # Filter valid words
            valid_tokens = [word for word in tokens if self.is_valid_word(word)]
            
            # Only add documents with valid tokens
            if valid_tokens:
                tokens_list.append(valid_tokens)
        
        return tokens_list

    def _sample_from_weights(self, weights):
        """
        Memilih indeks berdasarkan distribusi bobot yang diberikan.
        """
        total = sum(weights)
        rnd = total * random.random()
        for i, w in enumerate(weights):
            rnd -= w
            if rnd <= 0:
                return i

    def _p_topic_given_document(self, topic, d):
        """
        Menghitung probabilitas topik tertentu diberikan sebuah dokumen.
        """
        return ((self.document_topic_counts[d][topic] + self.alpha) /
                (self.document_lengths[d] + self.K * self.alpha))

    def _p_word_given_topic(self, word, topic):
        """
        Menghitung probabilitas kata diberikan topik.
        """
        return ((self.topic_word_counts[topic][word] + self.beta) /
                (self.topic_counts[topic] + self.W * self.beta))

    def _topic_weight(self, d, word, topic):
        """
        Menghitung bobot topik untuk kata dalam dokumen.
        """
        return (self._p_word_given_topic(word, topic) * 
                self._p_topic_given_document(topic, d))

    def _choose_new_topic(self, d, word):
        """
        Memilih topik baru untuk kata dalam dokumen menggunakan distribusi probabilitas.
        """
        weights = []
        for k in range(self.K):
            weight = self._topic_weight(d, word, k)
            weights.append(weight)
        return self._sample_from_weights(weights)

    def _gibbs_sample(self, documents):
        """
        Melakukan sampling Gibbs untuk inferensi LDA.
        """
        D = len(documents)
        for _ in range(self.max_iterations):
            for d in range(D):
                for i, (word, topic) in enumerate(zip(documents[d], self.document_topics[d])):
                    # Decrease counts
                    self.document_topic_counts[d][topic] -= 1
                    self.topic_word_counts[topic][word] -= 1
                    self.topic_counts[topic] -= 1
                    self.document_lengths[d] -= 1

                    # Sample new topic
                    new_topic = self._choose_new_topic(d, word)
                    
                    # Increase counts
                    self.document_topics[d][i] = new_topic
                    self.document_topic_counts[d][new_topic] += 1
                    self.topic_word_counts[new_topic][word] += 1
                    self.topic_counts[new_topic] += 1
                    self.document_lengths[d] += 1

    def fit(self, documents):
        """
        Melatih model LDA pada dokumen yang diberikan.
        """
        D = len(documents)
        
        # Initialize counters and lists
        self.document_topic_counts = [Counter() for _ in documents]
        self.topic_word_counts = [Counter() for _ in range(self.K)]
        self.topic_counts = [0 for _ in range(self.K)]
        self.document_lengths = [len(d) for d in documents]
        distinct_words = set(word for document in documents for word in document)
        self.W = len(distinct_words)

        # Initialize random topics
        self.document_topics = []
        for document in documents:
            topics = []
            for _ in document:
                topics.append(random.randrange(self.K))
            self.document_topics.append(topics)

        # Initialize counts
        for d in range(D):
            for word, topic in zip(documents[d], self.document_topics[d]):
                self.document_topic_counts[d][topic] += 1
                self.topic_word_counts[topic][word] += 1
                self.topic_counts[topic] += 1

        # Run Gibbs sampling
        self._gibbs_sample(documents)

    def get_topic_words(self, min_weight=0.0002):
        """
        Mendapatkan list kata per topik dengan bobotnya.
        """
        topic_word_list = {}
        for topic in range(self.K):
            data = []
            for word, count in self.topic_word_counts[topic].most_common():
                if count > 1:
                    weight = (self._p_word_given_topic(word, topic) * 
                            (self.topic_word_counts[topic][word] / self.topic_counts[topic]))
                    if weight > min_weight:
                        data.append((word, weight))
            topic_word_list[f"Topik {topic+1}"] = data
        return topic_word_list


def main():
    # Load data
    with open('C:\\Users\\arraf\\OneDrive\\Dokumen\\Kuliah\\Skripsi\\link-anomaly\\link-anomaly-trending-topic-detection\\hasil_twitt_trending.json', 'r') as file:
        hasil_twitt_trending = json.load(file)

    # Transform data
    dat_transform = [item[0] for item in hasil_twitt_trending]
    
    # Initialize and fit LDA model
    lda_model = LDAModel(n_topics=5, max_iterations=3000)
    
    # Preprocess and tokenize data
    tokenized_data = lda_model.tokenize_data(dat_transform)
    
    # Print preprocessing statistics
    print(f"Original documents: {len(dat_transform)}")
    print(f"Processed documents: {len(tokenized_data)}")
    
    # Only proceed if we have enough valid documents
    if len(tokenized_data) < 2:
        print("Not enough valid documents after preprocessing!")
        return
        
    # Fit the model
    lda_model.fit(tokenized_data)
    
    # Get and print results
    topic_word_list = lda_model.get_topic_words()
    for topic, words in topic_word_list.items():
        formatted_words = [f"{word}: {weight:.4f}" for word, weight in words]
        print(f"\n{topic}:")
        print(', '.join(formatted_words))


if __name__ == '__main__':
    main()