"""
1. Perhitungan Skor Anomaly
- Perhitungan probabilitas mention menggunakan persamaan (3.10)
- Perhitungan probabilitas user menggunakan persamaan (3.11)

"""
import sys
import os
# To support import export module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import create_connection

"""
Penjelasan tiap variabel di bagian perhitungan skor anomaly
m = Jumlah mention dalam rentang waktu perhitungan
n = Indeks tweet pada rentang waktu perhitungan 
k = Jumlah mention pada tweet
alpha, beta = nilai konstan, merujuk pada penelitian Takahashi
hasil_prob = variabel sementara untuk menghitung hasil perhitungan probabilitas mention pada tahap pertama
iterasi = variabel yang menampung perhitungan pada setiap tweets
"""

def fetch_tweets_data():
    connection = create_connection()
    tweets_data = []

    if connection is not None:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tweets")
        
        results = cursor.fetchall()
        
        for row in results:
            mentions_list = row[4].split(", ") if row[4] else []  # Menggunakan split untuk mengubah string menjadi list
            
            tweet = {
                "id": row[0],
                "tweet_text": row[1],
                "username": row[2],
                "created_at": row[3],
                "mentions": mentions_list,  
                "jumlah_mention": row[5]
            }
            tweets_data.append(tweet)

        cursor.close()
        connection.close()

    return tweets_data

tweets_data = fetch_tweets_data()


for tweet in tweets_data:
    print(tweet)

# ---------- Tahap 1: Probabilitas Mention ----------
print('---------- Hasil Probabilitas Mention (TAHAPAN PERTAMA) ----------')

hasil_probabilitas_mention = []
def hitung_probabilitas_mention(tweets):
    alpha = 0.5
    beta = 0.5
    m = 0

    for i in range(len(tweets)):  
        iterasi = 1.0
        k = tweets[i]['jumlah_mention']  
        temp_m = tweets[i]['jumlah_mention'] 
        m += temp_m
        
        n = i + 1 
        print(f"ID Tweet: {n}")
        
        for j in range(n):
            if j == 0:
                iterasi *= (n + alpha) / (m + k + beta)
            iterasi *= (m + beta + j) / (n + m + alpha + beta + j)
        
        print(f"Iterasi untuk ID Tweet {n}: {iterasi}")
        
        hasil_probabilitas_mention.append({"id": tweets[i]['id'], "skor_anomaly": iterasi})
    
    return hasil_probabilitas_mention

hitung_probabilitas_mention(tweets_data)
print(hasil_probabilitas_mention)

# ---------- Tahap 2: Hitung Probablitas Mention User ----------
print('---------- Hasil Probabilitas Mention User (TAHAPAN KEDUA) ----------')
hasil_probabilitas_user = []
def hitung_probabilitas_user(tweets):
    y = 0.5
    m = 0
    temp_mentions = []
    for row in tweets:
        temp_m = row['jumlah_mention']
        m += temp_m
        mentions = row['mentions']
        # print(f"jumlah mention {row['id']} : {len(row['mentions'])}")

        if isinstance(mentions, str):  # Pastikan mentions adalah string
            mentions_list = mentions.split(', ')  # Misalkan mentions dipisahkan oleh koma
        else:
            mentions_list = mentions  # Jika sudah dalam format list

        temp_mentions.extend(mentions_list)  

        mu = 0
        if len(mentions) > 1:
            for index, i in enumerate(mentions):
                
                print('----debugging----')
                # print(f"nilai temp_mention = {temp_mentions}")
                # print(f"hasil dari mu {row['id']} : {temp_mentions.count(i)}")
                # print(f"jumlah mentions dari {row['id']} = {mu}")
                mu = temp_mentions.count(i)
                print(f"Nilai mu pada id {row['id']} = {mu}")
                
        else :
            print("ini yang sama dengan 1 dan dibawahnya")
            # print(mu)
    # print((temp_mentions))
                


hitung_probabilitas_user(tweets_data)