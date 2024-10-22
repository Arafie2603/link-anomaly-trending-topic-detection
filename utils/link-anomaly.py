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
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Convert results into a list of dictionaries
        for row in results:
            tweet = {
                "id": row[0],
                "tweet_text": row[1],
                "username": row[2],
                "created_at": row[3],
                "mentions": row[4],
                "jumlah_mention": row[5]
            }
            tweets_data.append(tweet)

        cursor.close()
        connection.close()

    return tweets_data

# Fetching the tweets data
tweets_data = fetch_tweets_data()
# print(twitan)
# for tweet in twitan:
#     print(f"ID: {tweet['id']}, Jumlah Mention (K): {tweet['jumlah_mention']}")


# ---------- Tahap 1: Probabilitas Mention ----------
print('---------- Hasil Probabilitas Mention (TAHAPAN PERTAMA) ----------')
hasil_prob = []
# Fungsi untuk menghitung probabilitas mention
def hitung_probabilitas_mention(tweets):
    alpha = 0.5
    beta = 0.5
    m = 0

    for i in range(len(tweets)):  
        iterasi = 1.0
        k = tweets[i]['jumlah_mention']  # Menggunakan field jumlah_mention
        temp_m = tweets[i]['jumlah_mention']  # Sama dengan k
        m += temp_m
        
        n = i + 1 
        print(f"ID Tweet: {n}")
        
        for j in range(n):
            if j == 0:
                iterasi *= (n + alpha) / (m + k + beta)
            iterasi *= (m + beta + j) / (n + m + alpha + beta + j)
        
        print(f"Iterasi untuk ID Tweet {n}: {iterasi}")
        
        # Menyimpan hasil dari setiap iterasi
        hasil_prob.append({"id": tweets[i]['id'], "skor_anomaly": iterasi})
    
    return hasil_prob
hitung_probabilitas_mention(tweets_data)

print(hasil_prob)

# ---------- Tahap 2: Hitung Probablitas Mention User ----------
print('---------- Hasil Probabilitas Mention User (TAHAPAN KEDUA) ----------')
# def hitung_probabilitas_user(v, m):
#     sum_p_mention = 0
#     y = 0.5
#     for i in range(len(tweets_data)):
#         # Jika terdapat lebih dari 1 mention
#         if len(tweets_data[i]["v"]) > 1:
#             print()
#         else :
#             p_mention = tweets_data[i]["v"]
#             if (p_mention == tweets_data[i]['V'][0]):
#                 sum_p_mention += 1
#     for i in range(len(tweets_data)):
#         sum_p_mention = 0
#         hasil_p_mention = 0
#         if len(tweets_data[i]['V']) > 1:
#             print()
#         elif tweets_data[i]['V'] != [] :
#             p_mention = tweets_data[i]['V']
#             if (p_mention == tweets_data[i]['V'][0]):
#                 sum_p_mention += 1
#             else :
#                 sum_p_mention = 1
#         hasil_p_mention = sum_p_mention / (2+0.5)
#         print(f"Hasil testingan p_mention id {tweets_data[i]['id']} : ", hasil_p_mention)


# def hitung_probabilitas_tweets(data):
#     return data

# m = 0
# for i in range (len(tweets_data)):
#     temp_m = tweets_data[i]["K"]
#     m += temp_m