import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import pytz
from datetime import datetime
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.db_connection import create_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

load_dotenv()
class TwitterDataProcessor:

    def create_table(self, connection):
        cursor = connection.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_twitter (
                    conversation_id_str VARCHAR(255),
                    created_at DATETIME,
                    favorite_count INT,
                    full_text TEXT,
                    id_str VARCHAR(255),
                    image_url TEXT,
                    in_reply_to_screen_name VARCHAR(255),
                    lang VARCHAR(10),
                    location VARCHAR(255),
                    quote_count INT,
                    reply_count INT,
                    retweet_count INT,
                    tweet_url TEXT,
                    user_id_str VARCHAR(255),
                    username VARCHAR(255)
                );
            """)
            connection.commit()
            logger.info("Tabel 'data_twitter' sudah siap digunakan.")
        except mysql.connector.Error as err:
            logger.error(f"Error saat membuat tabel: {err}")
        finally:
            cursor.close()

    def insert_data(self, connection, df: pd.DataFrame):
        cursor = connection.cursor()
        try:
            df = df.where(pd.notnull(df), None)

            # Tentukan format waktu yang sesuai dengan format di CSV
            # Misalnya, jika data memiliki format 'Mon Oct 11 08:00:00 +0000 2024'
            df['created_at'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
            
            utc_timezone = pytz.timezone('UTC')
            wib_timezone = pytz.timezone('Asia/Jakarta')
            
            df = df.dropna(subset=['created_at'])
            
            # Lakukan konversi waktu
            df['created_at'] = df['created_at'].dt.tz_convert(wib_timezone)

            # Memastikan kolom-kolom yang akan disisipkan sesuai dengan yang ada di database
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO data_twitter (conversation_id_str, created_at, favorite_count, full_text, id_str,
                    image_url, in_reply_to_screen_name, lang, location, quote_count, reply_count, retweet_count, tweet_url, 
                    user_id_str, username) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['conversation_id_str'],
                    row['created_at'],
                    row['favorite_count'],
                    row['full_text'],
                    row['id_str'],
                    row['image_url'],
                    row['in_reply_to_screen_name'],
                    row['lang'],
                    row['location'],
                    row['quote_count'],
                    row['reply_count'],
                    row['retweet_count'],
                    row['tweet_url'],
                    row['user_id_str'],
                    row['username']
                ))
            connection.commit()
            logger.info(f"Berhasil menyisipkan {len(df)} tweet ke dalam database.")
        except mysql.connector.Error as err:
            logger.error(f"Error saat menyisipkan data: {err}")
        finally:
            cursor.close()


def main():
    connection = create_connection()  

    filename = "C:\\Users\\arraf\\OneDrive\\Dokumen\\Kuliah\\Skripsi\\link-anomaly\\tweets-data\\gabungan_tweets_10okt_8nov.csv"
    if os.path.exists(filename):
        logger.info(f"Membaca data dari {filename}")
        df = pd.read_csv(filename)
    else:
        logger.error(f"File {filename} tidak ditemukan.")
        return

    try:
        processor = TwitterDataProcessor()

        processor.create_table(connection)
        processor.insert_data(connection, df)
    except Exception as e:
        logger.error(f"Terjadi kesalahan: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            logger.info("Koneksi ke database ditutup.")


if __name__ == "__main__":
    main()
