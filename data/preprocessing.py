import mysql.connector
import os
import re
from dotenv import load_dotenv
import logging
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Database configuration class
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

# Fungsi untuk memuat kamus slangwords dari database
def load_slangwords(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT kata_tidak_baku, kata_baku FROM slangwords;")
    slangwords = {row['kata_tidak_baku']: row['kata_baku'] for row in cursor.fetchall()}
    cursor.close()
    return slangwords

# 1. Fungsi Case Folding
def case_folding(text):
    return text.lower()

# 2. Fungsi Cleansing (gabungkan semua langkah regex untuk efisiensi)
def cleansing(text):
    text = re.sub(r'http\S+|www\S+|https\S+|@\w+|#\w+|[^a-zA-Z\s]', ' ', text)  # Hapus URL, mention, hashtag, dan non-alfabet
    return re.sub(r'\s+', ' ', text).strip()  # Hapus spasi berlebih

# 3. Fungsi Slangwords Replacement
def replace_slangwords(text, slangwords_dict):
    words = text.split()
    return ' '.join([slangwords_dict.get(word, word) for word in words])

# 4. Fungsi Stopword Removal
def remove_stopwords(text, stopwords):
    words = text.split()
    return ' '.join([word for word in words if word not in stopwords])

# 5. Fungsi Stemming
def stemming(text, stemmer):
    words = text.split()
    return ' '.join([stemmer.stem(word) for word in words])

# Fungsi untuk menjalankan seluruh tahapan preprocessing
def preprocess_text(full_text, slangwords_dict, stopwords, stemmer):
    full_text = case_folding(full_text)
    full_text = cleansing(full_text)
    full_text = replace_slangwords(full_text, slangwords_dict)
    full_text = remove_stopwords(full_text, stopwords)
    full_text = stemming(full_text, stemmer)
    return full_text

# Fungsi utama untuk preprocessing data batch dan menyimpannya dalam satu commit
def process_data_batch(connection, slangwords_dict, stopwords, stemmer):
    cursor = connection.cursor(dictionary=True)

    try:
        # Ambil semua data yang ingin dibersihkan sekaligus
        cursor.execute("SELECT created_at, username, full_text FROM data_preprocessed;")
        rows = cursor.fetchall()

        # Proses setiap baris di memori
        updated_data = []
        for row in rows:
            full_text = row['full_text']
            processed_text = preprocess_text(full_text, slangwords_dict, stopwords, stemmer)
            updated_data.append((processed_text, row['created_at'], row['username']))

        # Update database dalam satu batch
        cursor.executemany("""
            UPDATE data_preprocessed
            SET full_text = %s
            WHERE created_at = %s AND username = %s
        """, updated_data)

        connection.commit()
        logger.info("Preprocessing dan update batch berhasil dilakukan pada kolom full_text.")
    except mysql.connector.Error as err:
        logger.error(f"Error saat melakukan preprocessing: {err}")
    finally:
        cursor.close()

# Fungsi utama untuk menjalankan proses
def main():
    db_config = DatabaseConfig()
    try:
        connection = db_config.get_connection()

        # Muat kamus slangwords
        slangwords_dict = load_slangwords(connection)
        
        # Inisialisasi StopWordRemover dan Stemmer dari Sastrawi
        stop_factory = StopWordRemoverFactory()
        stopwords = stop_factory.get_stop_words()

        stemmer_factory = StemmerFactory()
        stemmer = stemmer_factory.create_stemmer()
        
        # Jalankan proses preprocessing dalam batch
        process_data_batch(connection, slangwords_dict, stopwords, stemmer)

    except Exception as e:
        logger.error(f"Terjadi kesalahan: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            logger.info("Koneksi ke database ditutup.")

if __name__ == "__main__":
    main()
