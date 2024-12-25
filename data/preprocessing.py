import os
import re
import time
import logging
import mysql.connector
import pytz
from multiprocessing import Pool, Manager
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from datetime import datetime
logger = logging.getLogger(__name__)

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

local_connection = None
local_slangwords_dict = None
local_stopwords = None
local_stemmer = None

def init_worker(db_config_dict, slangwords_dict, stopwords_set, stemmer_instance):
    global local_connection, local_slangwords_dict, local_stopwords, local_stemmer

    local_connection = mysql.connector.connect(
        host=db_config_dict['host'],
        user=db_config_dict['user'],
        password=db_config_dict['password'],
        database=db_config_dict['database']
    )
    
    local_slangwords_dict = slangwords_dict
    local_stopwords = stopwords_set
    local_stemmer = stemmer_instance
    
    logger.info("Worker initialized successfully")

def load_slangwords(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT kata_tidak_baku, kata_baku FROM slangwords;")
    slangwords = {row['kata_tidak_baku'].strip(): row['kata_baku'].strip() for row in cursor.fetchall()}
    cursor.close()
    logger.info(f"Loaded {len(slangwords)} slangwords.")
    return slangwords

def convert_to_localtime(utc_time):
    if isinstance(utc_time, str):
        utc_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
    utc_tz = pytz.timezone("UTC")
    jakarta_tz = pytz.timezone("Asia/Jakarta")
    utc_dt = utc_tz.localize(utc_time) if utc_time.tzinfo is None else utc_time
    jakarta_dt = utc_dt.astimezone(jakarta_tz)  
    return jakarta_dt.strftime("%Y-%m-%d %H:%M:%S")


def process_row(args):
    try:
        row, progress = args
        created_at, username, full_text = row
        created_at_jakarta = convert_to_localtime(created_at)
        mentions, jumlah_mention = process_mentions(full_text)
        processed_text = preprocess_text(full_text)
        progress.value += 1

        return (created_at_jakarta, username, processed_text, mentions, jumlah_mention)
    except Exception as e:
        logger.error(f"Error in process_row: {str(e)}")
        raise

def preprocess_text(text):
    text = case_folding(text)
    text = cleansing(text)
    text = replace_slangwords(text)
    text = remove_stopwords(text)
    text = stemming(text)
    return text

def case_folding(text):
    return text.lower()

def cleansing(text):
    text = re.sub(r'http\S+|www\S+|https\S+|@\w+|#\w+|[^a-zA-Z\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def process_mentions(full_text):
    mentions = ','.join(re.findall(r'@\w+', full_text))
    jumlah_mention = len(mentions.split(',')) if mentions else 0
    return mentions, jumlah_mention

def replace_slangwords(text):
    if not local_slangwords_dict:
        logger.warning("Slangwords dictionary is not initialized")
        return text
        
    sorted_slangs = sorted(local_slangwords_dict.keys(), key=lambda x: len(x), reverse=True)
    for slang in sorted_slangs:
        replacement = local_slangwords_dict[slang]
        escaped_slang = re.escape(slang)
        text = re.sub(rf'\b{escaped_slang}\b', replacement, text, flags=re.IGNORECASE)
    return text

def remove_stopwords(text):
    if not local_stopwords:
        logger.warning("Stopwords set is not initialized")
        return text
        
    words = text.split()
    return ' '.join([word for word in words if word not in local_stopwords])

def stemming(text):
    if not local_stemmer:
        logger.warning("Stemmer is not initialized")
        return text
        
    words = text.split()
    return ' '.join([local_stemmer.stem(word) for word in words])

class Preprocessor:
    def __init__(self, socketio):
        self.db_config = DatabaseConfig()
        self.connection = self.db_config.get_connection()
        self.socketio = socketio
        
        # Initialize tools
        stop_factory = StopWordRemoverFactory()
        stemmer_factory = StemmerFactory()
        
        # Load resources
        self.slangwords_dict = load_slangwords(self.connection)
        self.stopwords = set(stop_factory.get_stop_words())
        self.stopwords.update(['pak', 'moga'])
        self.stemmer = stemmer_factory.create_stemmer()

    def save_to_database(self, processed_data):
        cursor = self.connection.cursor()
        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS data_preprocessed (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_at DATETIME,
                    username VARCHAR(255),
                    full_text TEXT,
                    mentions TEXT,
                    jumlah_mention INT
                );""")
            self.connection.commit()

            filtered_data = [
                row for row in processed_data 
                if row[3] and row[3].strip() and row[4] > 0 
            ]

            for row in filtered_data:
                cursor.execute("""
                    INSERT INTO data_preprocessed (created_at, username, full_text, mentions, jumlah_mention)
                    VALUES (%s, %s, %s, %s, %s)
                """, row)
            
            self.connection.commit()
            logger.info(f"Berhasil menyimpan {len(filtered_data)} tweet dengan mentions ke tabel data_preprocessed.")
            logger.info(f"Sebanyak {len(processed_data) - len(filtered_data)} tweet tanpa mentions dilewati.")
        finally:
            cursor.close()

    def run_preprocessing(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("""SELECT created_at, username, full_text FROM data_twitter""")
            data = cursor.fetchall()
            
            if not data:
                logger.warning("No data found in data_twitter table")
                return {"error": "No data found to process"}

            db_config_dict = {
                'host': self.db_config.host,
                'user': self.db_config.user,
                'password': self.db_config.password,
                'database': self.db_config.database
            }

            with Manager() as manager:
                progress = manager.Value('i', 0)
                total_items = len(data)
                start_time = time.time()
                with Pool(
                    processes=4,
                    initializer=init_worker,
                    initargs=(
                        db_config_dict,
                        self.slangwords_dict,
                        self.stopwords,
                        self.stemmer
                    )
                ) as pool:
                    
                    processed_data = []
                    for result in pool.imap_unordered(process_row, [(row, progress) for row in data]):
                        processed_data.append(result)
                        current_progress = progress.value
                        self.send_progress_update(current_progress, total_items, start_time)

                    if processed_data:
                        self.save_to_database(processed_data)
                        self.socketio.emit('progress_complete', {})
                    else:
                        logger.info("Tidak ada tweet yang valid untuk diproses.")

                    return {"success": "Data processed and stored successfully", "count": len(processed_data)}

        except Exception as e:
            logger.error(f"Terjadi kesalahan dalam run_preprocessing: {str(e)}")
            self.socketio.emit('progress_error', {'error': str(e)})
            return {"error": f"Failed to process data: {str(e)}"}

        finally:
            cursor.close()
            self.close_connection()

    def close_connection(self):
        if hasattr(self, 'connection') and self.connection.is_connected():
            self.connection.close()
            logger.info("Koneksi ke database ditutup.")

    def send_progress_update(self, current, total, start_time):
        if current > 0:
            elapsed_time = time.time() - start_time
            eta = (elapsed_time / current) * (total - current)
            eta_formatted = time.strftime("%H:%M:%S", time.gmtime(eta))
        else:
            eta_formatted = "--:--:--"
            
        self.socketio.emit('progress_cleansing_stemming', {
            'current': current,
            'total': total,
            'eta': eta_formatted
        })