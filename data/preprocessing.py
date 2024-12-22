import mysql.connector
import os
import re
from dotenv import load_dotenv
import logging
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "127.0.0.1")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "db_tugas_akhir")
    
    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info("Berhasil terhubung ke database.")
            return connection
        except mysql.connector.Error as err:
            logger.error(f"Gagal terhubung ke database: {err}")
            raise

def load_slangwords(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT kata_tidak_baku, kata_baku FROM slangwords;")
    slangwords = {row['kata_tidak_baku'].strip(): row['kata_baku'].strip() for row in cursor.fetchall()}
    cursor.close()
    logger.info(f"Loaded {len(slangwords)} slangwords.")
    return slangwords

def case_folding(text):
    return text.lower()

def cleansing(text):
    text = re.sub(r'http\S+|www\S+|https\S+|@\w+|#\w+|[^a-zA-Z\s]', ' ', text) 
    return re.sub(r'\s+', ' ', text).strip()  

def replace_slangwords(text, slangwords_dict):
    original_text = text
    sorted_slangs = sorted(slangwords_dict.keys(), key=lambda x: len(x), reverse=True)
    for slang in sorted_slangs:
        replacement = slangwords_dict[slang]
        escaped_slang = re.escape(slang)
        text = re.sub(rf'\b{escaped_slang}\b', replacement, text, flags=re.IGNORECASE)
    if original_text != text:
        logger.info(f"Original: {original_text}")
        logger.info(f"Replaced: {text}")
    return text

def remove_stopwords(text, stopwords):
    words = text.split()
    removed_words = [word for word in words if word in stopwords]
    logger.info(f"Removed stopwords: {removed_words}")
    return ' '.join([word for word in words if word not in stopwords])

def stemming(text, stemmer):
    words = text.split()
    return ' '.join([stemmer.stem(word) for word in words])

def run_preprocessing(text, connection):
    # Inisialisasi database connection
    db_config = DatabaseConfig()
    connection = db_config.get_connection()

    try:
        # Muat slangwords dari database
        slangwords_dict = load_slangwords(connection)
        
        # Inisialisasi StopWordRemover dan Stemmer dari Sastrawi
        stop_factory = StopWordRemoverFactory()
        stopwords = stop_factory.get_stop_words()
        stopwords.update(['pak', 'moga'])

        stemmer_factory = StemmerFactory()
        stemmer = stemmer_factory.create_stemmer()

        # Proses teks dengan seluruh tahapan preprocessing
        text = case_folding(text)
        text = cleansing(text)
        text = replace_slangwords(text, slangwords_dict)
        text = remove_stopwords(text, stopwords)
        text = stemming(text, stemmer)

        logger.info(f"Teks setelah preprocessing: {text}")
        return text

    except Exception as e:
        logger.error(f"Terjadi kesalahan: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()
            logger.info("Koneksi ke database ditutup.")

