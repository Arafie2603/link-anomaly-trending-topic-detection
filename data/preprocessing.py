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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "127.0.0.1")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "db_tugas_akhir")
        
        # Initialize stopword tools
        stop_factory = StopWordRemoverFactory()
        self.stopwords = set(word.lower() for word in stop_factory.get_stop_words())
        
        # Add custom stopwords
        additional_stopwords = {
            'pak', 'moga', 'kalau', 'nya', 'baik', 'lewat', 
            'apa', 'iya', 'ikut', 'jadi', 'yang', 'untuk',
            'pada', 'ke', 'para', 'namun', 'menurut', 'antara',
            'dia', 'dua', 'ia', 'seperti', 'jika', 'sehingga',
            'bisa', 'karena', 'yaitu', 'yakni', 'daripada',
            'sih', 'dong', 'deh', 'loh', 'kok', 'kan', 'lah',
            'kek', 'gitu', 'gini', 'mah', 'teh', 'nah', 'semoga', 'giat', 'si', 'kamu'
        }
        self.stopwords.update(additional_stopwords)
        
    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info("Successfully connected to database")
            return connection
        except mysql.connector.Error as err:
            logger.error(f"Failed to connect to database: {err}")
            raise

# Global variables for multiprocessing
local_connection = None
local_slangwords_dict = None
local_stopwords = None
local_stemmer = None

def init_worker(db_config_dict, slangwords_dict, stopwords_set, stemmer_instance):
    global local_connection, local_slangwords_dict, local_stopwords, local_stemmer
    
    try:
        # Initialize database connection for worker
        local_connection = mysql.connector.connect(
            host=db_config_dict['host'],
            user=db_config_dict['user'],
            password=db_config_dict['password'],
            database=db_config_dict['database']
        )
        
        # Initialize dictionaries and sets with proper case handling
        local_slangwords_dict = {k.lower(): v.lower() for k, v in slangwords_dict.items()}
        local_stopwords = set(word.lower() for word in stopwords_set)
        local_stemmer = stemmer_instance
        
        # Verify initialization
        logger.info(f"Worker initialized with {len(local_stopwords)} stopwords")
        logger.debug(f"Sample stopwords in worker: {list(local_stopwords)[:10]}")
        logger.debug(f"'baik' in stopwords: {'baik' in local_stopwords}")
        
        verify_worker_initialization()
        
        logger.info("Worker initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize worker: {e}")
        raise


def verify_worker_initialization():
    """Verify that worker components are properly initialized"""
    if not local_stopwords:
        raise ValueError("Stopwords not initialized!")
    if not local_slangwords_dict:
        raise ValueError("Slangwords dictionary not initialized!")
    if not local_stemmer:
        raise ValueError("Stemmer not initialized!")
    
    # Verify critical stopwords
    test_words = ['baik', 'nya', 'iya', 'jadi', 'yang', 'untuk']
    missing_words = [word for word in test_words if word not in local_stopwords]
    if missing_words:
        logger.error(f"Missing stopwords: {missing_words}")
    
    logger.debug(f"Stopwords verification complete. Sample: {list(local_stopwords)[:5]}")
    logger.debug(f"Slangwords verification complete. Sample: {dict(list(local_slangwords_dict.items())[:5])}")

def load_slangwords(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT kata_tidak_baku, kata_baku FROM slangwords;")
        slangwords = {row['kata_tidak_baku'].strip().lower(): row['kata_baku'].strip().lower() 
                     for row in cursor.fetchall()}
        
        # Add additional slangwords
        additional_slangwords = {
            'milu': 'pemilu',
            'tdk': 'tidak',
            'gk': 'tidak',
            'ga': 'tidak',
            'gak': 'tidak',
            'krn': 'karena',
            'dgn': 'dengan',
            'utk': 'untuk',
            'spy': 'supaya',
            'yg': 'yang',
            'skrg': 'sekarang',
            'hrs': 'harus',
            'dr': 'dari',
            'dll': 'dan lain lain',
            'dkk': 'dan kawan kawan',
            'sy': 'saya',
            'lg': 'lagi',
            'klo': 'kalau',
            'trs': 'terus',
            'bs': 'bisa',
            'byk': 'banyak'
        }
        slangwords.update(additional_slangwords)
        
        logger.info(f"Loaded {len(slangwords)} slangwords")
        logger.debug(f"Sample slangwords: {dict(list(slangwords.items())[:5])}")
        return slangwords
    finally:
        cursor.close()

def convert_to_localtime(utc_time):
    """Convert UTC time to Asia/Jakarta timezone"""
    try:
        if isinstance(utc_time, str):
            utc_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
        
        utc_tz = pytz.timezone("UTC")
        jakarta_tz = pytz.timezone("Asia/Jakarta")
        
        # Localize the datetime if it's naive
        utc_dt = utc_tz.localize(utc_time) if utc_time.tzinfo is None else utc_time
        jakarta_dt = utc_dt.astimezone(jakarta_tz)
        
        return jakarta_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error converting time: {e}")
        return utc_time

def process_row(args):
    """Process a single row of data"""
    try:
        row, progress = args
        tweet_id_str, created_at, username, full_text = row
        
        # Convert time and process mentions
        created_at_jakarta = convert_to_localtime(created_at)
        mentions, jumlah_mention = process_mentions(full_text)
        
        # Preprocess text
        processed_text = preprocess_text(full_text)
        
        # Log processing results
        logger.debug(f"Original text: {full_text}")
        logger.debug(f"Processed text: {processed_text}")

        logger.debug(f"Checking global variables in worker:")
        logger.debug(f"local_slangwords_dict initialized: {local_slangwords_dict is not None}")
        logger.debug(f"local_stopwords initialized: {local_stopwords is not None}")
        
        # Update progress
        progress.value += 1
        
        return (tweet_id_str, created_at_jakarta, username, processed_text, mentions, jumlah_mention)
    except Exception as e:
        logger.error(f"Error processing row: {e}")
        raise


def case_folding(text):
    """Convert text to lowercase"""
    return text.lower()

def cleansing(text):
    """Clean text from unwanted characters and patterns"""
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    
    # Remove mentions and hashtags
    text = re.sub(r'@\w+|#\w+', '', text)
    
    # Remove numbers and special characters
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def process_mentions(text):
    """Extract mentions from text"""
    mentions = ','.join(re.findall(r'@\w+', text))
    jumlah_mention = len(re.findall(r'@\w+', text))
    return mentions, jumlah_mention

def replace_slangwords(text, slang_dict):
    """Replace slang words with their proper form"""
    words = text.split()
    replaced_words = []
    
    for word in words:
        word = word.lower().strip()
        if word in slang_dict:
            replaced_word = slang_dict[word]
            logger.debug(f"Replaced slangword: {word} -> {replaced_word}")
            replaced_words.append(replaced_word)
        else:
            replaced_words.append(word)
    
    return ' '.join(replaced_words)

def remove_stopwords(text, stopwords):
    """Remove stopwords from text"""
    words = text.split()
    filtered_words = []
    
    for word in words:
        word = word.lower().strip()
        if word and word not in stopwords:
            filtered_words.append(word)
        else:
            logger.debug(f"Removed stopword: {word}")
    
    return ' '.join(filtered_words)

# Menambahkan log untuk stopwords
def preprocess_text(text):
    """Main preprocessing function"""
    logger.debug(f"Starting preprocessing of text: '{text}'")
    
    # Case folding
    text = case_folding(text)
    logger.debug(f"After case folding: '{text}'")
    
    # Cleansing
    text = cleansing(text)
    logger.debug(f"After cleansing: '{text}'")
    
    # Replace slangwords
    text = replace_slangwords(text, local_slangwords_dict)
    logger.debug(f"After slangwords replacement: '{text}'")
    
    # Remove stopwords
    logger.debug(f"Stopwords being used: {local_stopwords}")
    text = remove_stopwords(text, local_stopwords)
    logger.debug(f"After stopwords removal: '{text}'")
    
    # Stemming
    text = stemming(text)
    logger.debug(f"After stemming: '{text}'")
    
    return text.strip()


def stemming(text):
    """Apply stemming to text"""
    if not local_stemmer:
        logger.warning("Stemmer not initialized")
        return text
    
    # Daftar kata yang tidak boleh di-stem
    protected_words = {
        'pemilu', 'pilpres', 'pileg', 'pilkada',
        'presiden', 'wakil', 'calon', 'kandidat',
        'partai', 'koalisi', 'kampanye'
    }
    
    words = text.split()
    stemmed_words = []
    
    for word in words:
        # Skip stemming untuk kata-kata yang dilindungi
        if word.lower() in protected_words:
            stemmed_words.append(word)
        else:
            stemmed = local_stemmer.stem(word)
            stemmed_words.append(stemmed)
            if stemmed != word:
                logger.debug(f"Stemmed word: {word} -> {stemmed}")
    
    return ' '.join(stemmed_words)

class Preprocessor:
    def __init__(self, socketio=None):
        # Initialize database config and connection
        self.db_config = DatabaseConfig()
        self.connection = self.db_config.get_connection()
        self.socketio = socketio
        
        # Initialize NLP tools
        stemmer_factory = StemmerFactory()
        self.stemmer = stemmer_factory.create_stemmer()
        self.stopwords = self.db_config.stopwords
        
        # Load slangwords
        self.slangwords_dict = self._load_slangwords()
        
        logger.info("Preprocessor initialized successfully")
    
    def _load_slangwords(self):
        """Internal method to load slangwords"""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT kata_tidak_baku, kata_baku FROM slangwords")
            slangwords = {
                row['kata_tidak_baku'].strip().lower(): row['kata_baku'].strip().lower() 
                for row in cursor.fetchall()
            }
            
            # Add additional slangwords
            additional_slangwords = {
                'milu': 'pemilu',
                'tdk': 'tidak',
                'gk': 'tidak',
                'ga': 'tidak',
                'gak': 'tidak',
                'krn': 'karena',
                'dgn': 'dengan',
                'utk': 'untuk',
                'spy': 'supaya',
                'yg': 'yang',
                'skrg': 'sekarang',
                'hrs': 'harus',
                'dr': 'dari',
                'dll': 'dan lain lain',
                'dkk': 'dan kawan kawan',
                'sy': 'saya',
                'lg': 'lagi',
                'klo': 'kalau',
                'trs': 'terus',
                'bs': 'bisa',
                'byk': 'banyak'
            }
            slangwords.update(additional_slangwords)
            logger.info(f"Loaded {len(slangwords)} slangwords")
            return slangwords
            
        except Exception as e:
            logger.error(f"Error loading slangwords: {e}")
            raise
        finally:
            cursor.close()

    def send_progress_update(self, current, total, start_time):
        if self.socketio:
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
    def save_to_database(self, processed_data):
        """Save processed data to database with relations"""
        cursor = self.connection.cursor()
        try:
            # Create table if not exists with new structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_preprocessed (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tweet_id_str VARCHAR(255),
                    created_at DATETIME,
                    username VARCHAR(255),
                    full_text TEXT,
                    mentions TEXT,
                    jumlah_mention INT,
                    FOREIGN KEY (tweet_id_str) REFERENCES data_twitter(id_str)
                );
            """)
            self.connection.commit()

            # Filter data with mentions
            filtered_data = [
                row for row in processed_data 
                if row[4] and row[4].strip() and row[5] > 0  # Adjusted indices for new data structure
            ]

            # Insert filtered data
            insert_query = """
                INSERT INTO data_preprocessed 
                (tweet_id_str, created_at, username, full_text, mentions, jumlah_mention)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_query, filtered_data)
            
            self.connection.commit()
            logger.info(f"Saved {len(filtered_data)} tweets with mentions")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def close_connection(self):
        if hasattr(self, 'connection') and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
    def run_preprocessing(self):
        cursor = self.connection.cursor()
        try:
            # Get data from database including id_str
            cursor.execute("SELECT id_str, created_at, username, full_text FROM data_twitter")
            data = cursor.fetchall()
            
            if not data:
                logger.warning("No data found in data_twitter table")
                return {"error": "No data found to process"}

            # Rest of the preprocessing logic remains the same
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
                    initargs=(db_config_dict, 
                            self.slangwords_dict,
                            self.stopwords,
                            self.stemmer)
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
                        logger.info("No valid tweets to process.")

                    return {
                        "success": "Data processed and stored successfully",
                        "count": len(processed_data)
                    }

        except Exception as e:
            logger.error(f"Error in run_preprocessing: {str(e)}")
            self.socketio.emit('progress_error', {'error': str(e)})
            return {"error": f"Failed to process data: {str(e)}"}

        finally:
            cursor.close()
            self.close_connection()