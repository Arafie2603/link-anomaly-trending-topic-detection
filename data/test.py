# import logging
# from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
# from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
# import re

# # Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# class TextPreprocessor:
#     def __init__(self):
#         # Initialize stopwords
#         stop_factory = StopWordRemoverFactory()
#         self.stopwords = set(word.lower() for word in stop_factory.get_stop_words())
        
#         # Add custom stopwords
#         additional_stopwords = {
#             'pak', 'moga', 'kalau', 'nya', 'baik', 'lewat', 
#             'apa', 'iya', 'ikut', 'jadi', 'yang', 'untuk',
#             'pada', 'ke', 'para', 'namun', 'menurut', 'antara',
#             'dia', 'dua', 'ia', 'seperti', 'jika', 'sehingga',
#             'bisa', 'saat', 'karena', 'yaitu', 'yakni', 'daripada',
#             'sih', 'dong', 'deh', 'loh', 'kok', 'kan',
#             'kek', 'gitu', 'gini', 'mah', 'teh', 'nah',
#             'yah', 'sih', 'nih', 'lah', 'nya', 'kah',
#             'pun', 'loh', 'kok'
#         }
#         self.stopwords.update(additional_stopwords)
        
#         # Initialize slangwords
#         self.slangwords = {
#             'milu': 'pemilu',
#             'tdk': 'tidak',
#             'gk': 'tidak',
#             'ga': 'tidak',
#             'gak': 'tidak',
#             'krn': 'karena',
#             'dgn': 'dengan',
#             'utk': 'untuk',
#             'spy': 'supaya',
#             'yg': 'yang',
#             'skrg': 'sekarang',
#             'hrs': 'harus',
#             'dr': 'dari',
#             'dll': 'dan lain lain',
#             'dkk': 'dan kawan kawan',
#             'sy': 'saya',
#             'lg': 'lagi',
#             'klo': 'kalau',
#             'trs': 'terus',
#             'bs': 'bisa',
#             'byk': 'banyak'
#         }
        
#         # Initialize stemmer
#         stemmer_factory = StemmerFactory()
#         self.stemmer = stemmer_factory.create_stemmer()
        
#         # Protected words (words that shouldn't be stemmed)
#         self.protected_words = {
#             'pemilu', 'pilpres', 'pileg', 'pilkada',
#             'presiden', 'wakil', 'calon', 'kandidat',
#             'partai', 'koalisi', 'kampanye'
#         }
        
#         logger.info(f"Initialized with {len(self.stopwords)} stopwords")
#         logger.debug(f"Sample stopwords: {list(self.stopwords)[:10]}")
    
#     def case_folding(self, text):
#         """Convert text to lowercase"""
#         return text.lower()
    
#     def cleansing(self, text):
#         """Clean text from unwanted characters and patterns"""
#         # Remove URLs
#         text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
#         # Remove mentions and hashtags
#         text = re.sub(r'@\w+|#\w+', '', text)
        
#         # Remove numbers and special characters
#         text = re.sub(r'[^a-zA-Z\s]', '', text)
        
#         # Remove extra whitespace
#         text = re.sub(r'\s+', ' ', text)
        
#         return text.strip()
    
#     def replace_slangwords(self, text):
#         """Replace slang words with their proper form"""
#         words = text.split()
#         replaced_words = []
        
#         for word in words:
#             word = word.lower().strip()
#             if word in self.slangwords:
#                 replaced_word = self.slangwords[word]
#                 logger.debug(f"Replaced slangword: {word} -> {replaced_word}")
#                 replaced_words.append(replaced_word)
#             else:
#                 replaced_words.append(word)
        
#         return ' '.join(replaced_words)
    
#     def remove_stopwords(self, text):
#         """Remove stopwords from text"""
#         words = text.split()
#         filtered_words = []
        
#         for word in words:
#             word = word.lower().strip()
#             if word and word not in self.stopwords:
#                 filtered_words.append(word)
#             else:
#                 logger.debug(f"Removed stopword: {word}")
        
#         return ' '.join(filtered_words)
    
#     def stemming(self, text):
#         """Apply stemming to text while protecting certain words"""
#         words = text.split()
#         stemmed_words = []
        
#         for word in words:
#             word = word.lower().strip()
#             if word in self.protected_words:
#                 stemmed_words.append(word)
#                 logger.debug(f"Protected word (not stemmed): {word}")
#             else:
#                 stemmed = self.stemmer.stem(word)
#                 stemmed_words.append(stemmed)
#                 if stemmed != word:
#                     logger.debug(f"Stemmed word: {word} -> {stemmed}")
        
#         return ' '.join(stemmed_words)
    
#     def preprocess(self, text):
#         """Main preprocessing function"""
#         logger.debug(f"Original text: '{text}'")
        
#         # Case folding
#         text = self.case_folding(text)
#         logger.debug(f"After case folding: '{text}'")
        
#         # Cleansing
#         text = self.cleansing(text)
#         logger.debug(f"After cleansing: '{text}'")
        
#         # Replace slangwords
#         text = self.replace_slangwords(text)
#         logger.debug(f"After slangwords replacement: '{text}'")
        
#         # Remove stopwords
#         text = self.remove_stopwords(text)
#         logger.debug(f"After stopwords removal: '{text}'")
        
#         # Stemming
#         text = self.stemming(text)
#         logger.debug(f"After stemming: '{text}'")
        
#         return text.strip()

# # Test data
# test_data = [
#     "@user saya gak setuju dgn hasil pemilu yg kemarin sih baik iya nya deh",
#     "milu hrs lebih baik deh dlm mengawasi pemilu tahun ini",
#     "pemilu skrg byk yg ga setuju krn prosesnya tdk transparan"
# ]

# def main():
#     preprocessor = TextPreprocessor()
    
#     print("\nProcessing test data:")
#     print("-" * 50)
    
#     for i, text in enumerate(test_data, 1):
#         print(f"\nText {i}:")
#         print(f"Original  : {text}")
#         processed = preprocessor.preprocess(text)
#         print(f"Processed : {processed}")
#         print("-" * 50)

# if __name__ == "__main__":
#     main()




from preprocessing import Preprocessor  # Sesuaikan dengan path file Preprocessor Anda
from socketio import Server  # Import library socketio jika diperlukan

def main():
    socketio = Server()  # Inisialisasi Server socketio
    preprocessor = Preprocessor(socketio=socketio)
    result = preprocessor.run_preprocessing()

    if "error" in result:
        print("Error:", result["error"])
    else:
        print("Success:", result["success"])
        for item in result["data"]:
            print(item)

if __name__ == "__main__":
    main()
