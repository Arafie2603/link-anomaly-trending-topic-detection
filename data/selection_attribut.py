import pandas as pd
import re
import mysql.connector
from dotenv import load_dotenv
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv("DB_HOST", "127.0.0.1"),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD", ""),
    'database': os.getenv("DB_NAME", "db_ta")
}

# Function to load data from the database
def load_data():
    connection = mysql.connector.connect(**db_config)
    query = "SELECT created_at, username, full_text FROM data_twitter"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

# Function to extract mentions and count them
def process_mentions(df):
    # Menambahkan kolom `mentions` dan `jumlah_mention`
    df['mentions'] = df['full_text'].apply(lambda x: ','.join(re.findall(r'@\w+', x)))
    df['jumlah_mention'] = df['mentions'].apply(lambda x: len(x.split(',')) if x else 0)
    
    # Filter hanya tweet yang memiliki mention
    df = df[df['jumlah_mention'] > 0]
    
    return df

# Function to save the processed data to the new table
def save_to_database(df):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Membuat tabel `data_preprocessed` jika belum ada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_preprocessed (
            id INT AUTO_INCREMENT PRIMARY KEY,
            created_at DATETIME,
            username VARCHAR(255),
            full_text TEXT,
            mentions TEXT,
            jumlah_mention INT
        );
    """)
    connection.commit()

    # Menyisipkan data ke tabel `data_preprocessed`
    rows_inserted = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO data_preprocessed (created_at, username, full_text, mentions, jumlah_mention)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            row['created_at'],
            row['username'],
            row['full_text'],
            row['mentions'],
            row['jumlah_mention']
        ))
        rows_inserted += 1

    connection.commit()
    cursor.close()
    connection.close()
    logger.info(f"Berhasil menyimpan {rows_inserted} tweet ke tabel data_preprocessed.")

# Main function
def main():
    # Step 1: Load data from `data_twitter`
    df = load_data()

    # Step 2: Process mentions and count them
    df = process_mentions(df)

    # Step 3: Save processed data to `data_preprocessed`
    if not df.empty:  # Only save to DB if the dataframe is not empty
        save_to_database(df)
    else:
        logger.info("Tidak ada tweet dengan mention yang valid untuk dimasukkan ke database.")

if __name__ == "__main__":
    main()
