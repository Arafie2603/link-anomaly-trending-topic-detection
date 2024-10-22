import pandas as pd
import os
import mysql.connector
import re
import pytz

filename = 'fransiskus.csv'
search_keyword = 'pilkada since:2024-10-10 until:2024-10-10 lang:id'
limit = 40
print("Current working directory:", os.getcwd())

# Menggunakan jalur yang sesuai
readcsv = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tweets-data', 'pilkada.csv')
print(f"Checking for file: {readcsv}")

if os.path.exists(readcsv):
    try:
        df = pd.read_csv(readcsv)

        # Konversi kolom 'created_at' dari string ke datetime
        df['created_at'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y')

        # Konversi waktu dari UTC ke WIB
        utc_timezone = pytz.timezone('UTC')
        wib_timezone = pytz.timezone('Asia/Jakarta')
        df['created_at'] = df['created_at'].dt.tz_convert(utc_timezone).dt.tz_convert(wib_timezone)

        # Mengurutkan DataFrame berdasarkan 'created_at' dari yang terawal ke yang terbaru
        df = df.sort_values(by='created_at', ascending=True)

        print(df.head())
    except Exception as e:
        print(f"Error reading {readcsv}: {e}")
        df = None  # Set df to None if reading fails
else:
    print(f"File {readcsv} tidak ditemukan.")
    df = None  # Set df to None if file doesn't exist

# Jika df tidak ada, hentikan eksekusi lebih lanjut
if df is None:
    print("Data tidak tersedia. Hentikan eksekusi.")
    exit()

print(df.columns)

# Koneksi ke database
host = '127.0.0.1'  
user = 'root'  
password = ''  
database = 'db_ta'  

connection = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

with connection.cursor() as cursor:
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS tweets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tweet_text TEXT,
        username VARCHAR(255),
        time DATETIME,
        mentions TEXT,
        jumlah_mention INT DEFAULT 0  -- Kolom baru untuk jumlah mention
    )
    """)

def extract_mentions(text):
    return re.findall(r'(@\w+)', text)

with connection.cursor() as cursor:
    for _, row in df.iterrows():
        mentions_list = extract_mentions(row['full_text'])
        mentions = ', '.join(mentions_list)
        jumlah_mention = len(mentions_list)
        # Menyimpan waktu yang telah dikonversi ke dalam database
        cursor.execute("""
        INSERT INTO tweets (tweet_text, username, time, mentions, jumlah_mention) 
        VALUES (%s, %s, %s, %s, %s)
        """, (row['full_text'], row['username'], row['created_at'], mentions, jumlah_mention))

connection.commit()
connection.close()

print("Data berhasil disimpan ke MySQL.")
