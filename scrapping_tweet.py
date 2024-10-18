import pandas as pd
import os
import mysql.connector
import re

filename = 'fransiskus.csv'
search_keyword = 'pilkada since:2024-10-10 until:2024-10-10 lang:id'
limit = 20
print(os.getcwd())

readcsv = './tweets-data/pilkada.csv'

if os.path.exists(readcsv):
    df = pd.read_csv(readcsv)
    print(df.head())
else:
    print(f"File {readcsv} tidak ditemukan.")

print(df.columns)

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
        created_at DATETIME,
        mentions TEXT
    )
    """)

def extract_mentions(text):
    return re.findall(r'(@\w+)', text)  

with connection.cursor() as cursor:
    for _, row in df.iterrows():
        mentions = ', '.join(extract_mentions(row['full_text'])) 
        cursor.execute("INSERT INTO tweets (tweet_text, username, created_at, mentions) VALUES (%s, %s, %s, %s)",
        (row['full_text'], row['username'], row['created_at'], mentions))

connection.commit()
connection.close()

print("Data berhasil disimpan ke MySQL.")
