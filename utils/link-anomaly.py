import sys
import os
import json
import math
# To support import export module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import create_connection
from datetime import datetime, timedelta

"""
1. Perhitungan Skor Anomaly
- Perhitungan probabilitas mention menggunakan persamaan (3.10)
- Perhitungan probabilitas user menggunakan persamaan (3.11)

"""

"""
Penjelasan tiap variabel di bagian perhitungan skor anomaly tahap pertama:
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
            # Menggunakan split untuk mengubah string menjadi list
            mentions_list = row[4].split(", ") if row[4] else []  
            
            tweet = {
                "id": row[0],
                "tweet_text": row[1],
                "username": row[2],
                "time": row[3], 
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

hasil_perhitungan = []
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
        
        waktu_str = tweets[i]['time'].strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Iterasi untuk ID Tweet {tweets[i]['id']}: {iterasi}")
        hasil_perhitungan.append({"id": tweets[i]['id'],"time": waktu_str ,"probabilitas_mention": iterasi})
    
    return hasil_perhitungan

hitung_probabilitas_mention(tweets_data)

# ---------- Tahap 2: Hitung Probablitas Mention User ----------
"""
Penjelasan tiap variabel di bagian perhitungan skor anomaly tahap pertama:
temp_mentions = digunakan untuk menyimpan mentions tiap iterasi, karena akan dilakukan perhitungan mundur apakah mention disebutkan
                dalam data sebelumnya
y = nilai konstan referensi dari penelitian Takahashi
m = fungsinya masih sama seperti tahapan pertama
pmention = variabel yang digunakan untuk menghitung skor probabilitas mention user
"""
print('---------- Hasil Probabilitas Mention User (TAHAPAN KEDUA) ----------')
def hitung_mention_tiap_id(target_id, tweets_data):
    temp_mentions = []
    m = 0
    y = 0.5
    pmention = 0

    for tweet in tweets_data:
        mentions = tweet['mentions']
        temp_m = tweet['jumlah_mention']
        m += temp_m

        if isinstance(mentions, str):  
            mentions_list = mentions.split(', ')  
        else:
            mentions_list = mentions  
        temp_mentions.extend(mentions_list)

        if tweet['id'] == target_id:
            if tweet['jumlah_mention'] > 1:
                for i in mentions_list:  
                    mu = temp_mentions.count(i)
                    pmention += mu / (m + y)
            else:
                mention_string = ', '.join(mentions_list)
                mu = temp_mentions.count(mention_string)
                pmention += mu / (m + y)
    
    return pmention  
def hitung_probabilitas_user(tweets):
    for row in tweets:
        pmention = hitung_mention_tiap_id(row['id'], tweets)  
        print(f"ID Tweet: {row['id']}, pmention: {pmention}") 
        for item in hasil_perhitungan:
            if item['id'] == row['id']:
                item['probabilitas_user'] = pmention
                
    return hasil_perhitungan

hitung_probabilitas_user(tweets_data)

print('---------- Hitung Skor Anomaly ----------')
# print(json.dumps(hasil_perhitungan, indent=4))
def hitung_skor_anomaly(hasil):
    for skor in hasil:
        nilai_mention = skor['probabilitas_mention']
        nilai_user = skor['probabilitas_user']

        for item in hasil_perhitungan:
            if item['id'] == skor['id']:
                skor_anomaly = -math.log10(nilai_mention) - math.log10(nilai_user)
                item['skor_anomaly'] = skor_anomaly

hitung_skor_anomaly(hasil_perhitungan)
print(json.dumps(hasil_perhitungan, indent=4))

"""
2. Menghitung Agregasi Skor Anomaly
Program test ini menggunakan diskrit time sebesar 6 menit, dan jumlah diksrit sebanyak 5
"""


hasil_agregasi = []
def hitung_skor_agregasi(hasil_skor):
    # Ambil waktu awal dari hasil perhitungan
    waktu_awal_string = hasil_perhitungan[0]['time']
    waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")

    # Tentukan interval waktu untuk diskrit
    window_r = timedelta(minutes=6)
    jumlah_diskrit = 5

    # Tentukan waktu awal dan akhir
    waktu_akhir = waktu_awal + window_r

    for index in range(jumlah_diskrit):
        # Reset jumlah skor anomaly untuk setiap diskrit
        jml_skor_anomaly = 0  
        for data in hasil_skor:
            temp_waktu = data['time']
            tweet_waktu = datetime.strptime(temp_waktu, "%Y-%m-%d %H:%M:%S")

            if waktu_awal <= tweet_waktu < waktu_akhir:
                jml_skor_anomaly += data['skor_anomaly']  
        s_x = (1/4) * jml_skor_anomaly  # Hitung s_x
        print(s_x)
        hasil_agregasi.append({"diskrit": index + 1, "waktu_awal": waktu_awal.strftime('%Y-%m-%d %H:%M:%S'), "waktu_akhir": waktu_akhir.strftime('%Y-%m-%d %H:%M:%S'), "s_x": s_x})

        waktu_awal = waktu_akhir
        waktu_akhir += window_r

    return hasil_agregasi

hasil_agregasi = hitung_skor_agregasi(hasil_perhitungan)
print(json.dumps(hasil_agregasi, indent=4))




