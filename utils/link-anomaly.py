import sys
import os
# To support import export module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import create_connection
from datetime import datetime

"""
1. Perhitungan Skor Anomaly
- Perhitungan probabilitas mention menggunakan persamaan (3.10)
- Perhitungan probabilitas user menggunakan persamaan (3.11)

"""

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
                "time": row[3],  # Pastikan ini adalah datetime string
                "mentions": mentions_list,  
                "jumlah_mention": row[5]
            }
            tweets_data.append(tweet)

        cursor.close()
        connection.close()

    return tweets_data

# Fetching the tweets data
tweets_data = fetch_tweets_data()

# Pastikan 'time' adalah string sebelum mengonversi
for tweet in tweets_data:
    # Cek apakah 'time' sudah berupa datetime
    if isinstance(tweet['time'], str):
        tweet['time'] = datetime.strptime(tweet['time'], "%Y-%m-%d %H:%M:%S")

# Mengurutkan berdasarkan 'time'
tweets_data.sort(key=lambda x: x['time']) 

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
        
        print(f"Iterasi untuk ID Tweet {tweets[i]['id']}: {iterasi}")
        
        hasil_probabilitas_mention.append({"id": tweets[i]['id'], "probabilitas_mention": iterasi})
    
    return hasil_probabilitas_mention

hitung_probabilitas_mention(tweets_data)
# print(hasil_probabilitas_mention)

# print(tweets_data)

# ---------- Tahap 2: Hitung Probablitas Mention User ----------
print('---------- Hasil Probabilitas Mention User (TAHAPAN KEDUA) ----------')
hasil_probabilitas_user = []

def hitung_probabilitas_user(tweets):
    for row in tweets:
        pmention = hitung_mention_tiap_id(row['id'], tweets)  
        print(f"ID Tweet: {row['id']}, pmention: {pmention}") 
        hasil_probabilitas_user.append({"id": row['id'], "probabilitas_user": pmention})
    return hasil_probabilitas_user

def hitung_mention_tiap_id(target_id, tweets_data):
    temp_mentions = []
    m = 0
    y = 0.5
    pmention = 0

    for tweet in tweets_data:
        mentions = tweet['mentions']
        temp_m = tweet['jumlah_mention']
        m += temp_m

        # Pastikan mencetak isi mentions dengan benar
        if isinstance(mentions, str):  
            mentions_list = mentions.split(', ')  
        else:
            mentions_list = mentions  
        temp_mentions.extend(mentions_list)

        if tweet['id'] == target_id:
            if tweet['jumlah_mention'] > 1:
                for i in mentions_list:  
                    mu = temp_mentions.count(i)
                    # print(f"Memeriksa {i} di temp_mentions. Count: {mu}")  # Debug output
                    pmention += mu / (m + y)
            else:
                mention_string = ', '.join(mentions_list)
                mu = temp_mentions.count(mention_string)
                pmention += mu / (m + y)
    
    return pmention  # Kembalikan nilai pmention

print("------------------------testing-------------------------")

# Misalkan tweets_data adalah data tweet yang sudah ada
hitung_probabilitas_user(tweets_data)

print("----------hasil probabilitas mention-----------")
print(hasil_probabilitas_mention)
print('----------hasil probabilitas user----------')
print(hasil_probabilitas_user)




