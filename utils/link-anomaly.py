import sys
import os
import json
import math
import numpy as np
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
    k_sigma = 0
    # Set untuk menyimpan username unik, kenapa make set? karena set cocok untuk memecahkan masalah kita
    # Masalahnya apa? kita perlu menghitung k_sigma di tiap iterasi, di mana k_sigma ini dihitung dari penyebutan mention di tiap iterasi
    # di mana k_sigma dihitung dari field usn twitter, di mana jika ada usn dengan nilai yang sama tidak dihitung double, ini cocok menggunakan set
    # di mana set ini melarang penggunaan id yang sama, atau set ini tipe data yang key nya harus unique 
    unique_usernames = set() 

    for i in range(len(tweets)):
        iterasi = 1.0
        k = tweets[i]['jumlah_mention']  
        temp_m = tweets[i]['jumlah_mention'] 
        m += temp_m
        n = i + 1
        print(f"ID Tweet: {n}")

        # username digunain untuk menangkap username yang disebutin pada tiap iterasi
        # tujuannya nanti buat menentukan nilai k_sigma, pada setiap iterasi
        username = tweets[i]['username']
        if username not in unique_usernames:
            unique_usernames.add(username) 
            k_sigma += 1 

        # Perhitungan iterasi
        for j in range(k_sigma):
            if j == 0:
                iterasi *= (n + alpha) / (m + k + beta)
            iterasi *= (m + beta + j) / (n + m + alpha + beta + j)

        waktu_str = tweets[i]['time'].strftime("%Y-%m-%d %H:%M:%S")

        print(f"Iterasi untuk ID Tweet {tweets[i]['id']}: {iterasi}")
        hasil_perhitungan.append({
            "id": tweets[i]['id'],
            "time": waktu_str,
            "probabilitas_mention": iterasi
        })
    
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
skor_agregasi = []

def hitung_skor_agregasi(hasil_skor):
    # Ambil waktu awal dari hasil perhitungan
    waktu_awal_string = hasil_perhitungan[0]['time']
    waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")

    # Tentukan interval waktu untuk diskrit
    window_r = timedelta(minutes=6)
    jumlah_diskrit = 5

    # Tentukan waktu awal dan akhir
    waktu_akhir = waktu_awal + window_r

    # Buat list untuk menyimpan skor anomaly yang masuk ke setiap diskrit
    # catatan: var diskrit_anomaly hanya buat pengecekan aja, jadi kalau udah fix, nanti ingetin untuk dihapus
    diskrit_anomaly = [[] for _ in range(jumlah_diskrit)]

    for index in range(jumlah_diskrit):
        # Reset jumlah skor anomaly untuk setiap diskrit
        jml_skor_anomaly = 0  
        for data in hasil_skor:
            temp_waktu = data['time']
            tweet_waktu = datetime.strptime(temp_waktu, "%Y-%m-%d %H:%M:%S")

            if waktu_awal <= tweet_waktu < waktu_akhir:
                jml_skor_anomaly += data['skor_anomaly']
                # Simpan skor anomaly yang memenuhi syarat ke dalam list diskrit
                diskrit_anomaly[index].append(data)  
        # Hitung s_x
        # Kenapa 1/6? karena studi case saat ini window r nya = 
        s_x = (1/6) * jml_skor_anomaly  
        hasil_agregasi.append({
            "diskrit": index + 1, 
            "waktu_awal": waktu_awal.strftime('%Y-%m-%d %H:%M:%S'), 
            "waktu_akhir": waktu_akhir.strftime('%Y-%m-%d %H:%M:%S'), 
            "s_x": round(s_x, 2),
            "anomalies": diskrit_anomaly[index] 
        })
        skor_agregasi.append(round(s_x, 2))

        waktu_awal = waktu_akhir
        waktu_akhir += window_r

    return hasil_agregasi

hasil_agregasi = hitung_skor_agregasi(hasil_perhitungan)
print(json.dumps(hasil_agregasi, indent=4))




# ========================== IMPLEMENTASI SDNML ==========================

"""
Langkah 1: First Layering Learning
Langkah - langkahnya :
    1. Mencari nilai Koefisien AR
        a. Mencari nilai Vt dan Xt
        b. Mencari nilai invers Vt
        c. Menghitung metode Sherman-Morisson-Woodburry
        d. Implementasi perhitungan koefisien AR 
"""
"""
V_t_list = list untuk menampung hasil perhitungan dari Vt 
weights = hasil dari perhitungan nilai bobot
X_t_list = list untuk menampung hasil perhitungan dari Xt
hitung_inverse = fungsi yang digunakan untuk menghitung inverse dan akan menghitung inverse menggunakan pseudo-inverse jika matriks Vt merupakan singular
Ct_list = list yang menampung perhitungan dari nilai Ct
inverse_matrix = variabel yang digunakan untuk menyimpan hasil perhitungan invers dari matriks
"""
# Mencari nilai bobot wj
r = 0.9
weights = np.array([round(r * (1 - r) ** i, 5) for i in range(len(hasil_agregasi))])  
aggregation_scores = np.array(skor_agregasi)

# a. Menghitung matriks V_t dan r untuk setiap bobot di r

V_t_list = []
for weight in weights:
    V_t = weight * np.outer(skor_agregasi, skor_agregasi)  
    V_t_list.append(V_t)

X_t_list = []
for i, weight in enumerate(weights):
    temp_xt = weight * aggregation_scores[i] * aggregation_scores[i]
    X_t_list.append(round(temp_xt, 4))
print(f"hasil dari xt = {X_t_list}")
    

# Fungsi untuk menghitung invers dengan pendekatan pseudo-inverse jika matriks singular
def hitung_invers(matrix):
    try:
        return np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(matrix)

# b. Menghitung nilai Ct untuk setiap matriks Vt dan x (agregation_score)
Ct_list = []
for i, matrix in enumerate(V_t_list):
    inverse_matrix = hitung_invers(matrix)
    Ct_temp = weights[i] * np.dot(aggregation_scores.T, np.dot(inverse_matrix, aggregation_scores))
    Ct_list.append(Ct_temp)
    print(f"Invers dari Vt{i+1} (menggunakan pseudo-inverse jika singular):")
    # print(inverse_matrix)
    print(f"Nilai C_t untuk Vt{i+1}: {Ct_temp:.5f}")
    print()



# c. Menghitung metode Sherman-Morrison-Woodbury
inverse_matrix = [hitung_invers(vt) for vt in V_t_list]  

# Hasil perhitungan Sherman-Morrison-Woodbury
for i in range(len(weights)):
    r = weights[i]
    inv_vt = inverse_matrix[i]
    x = aggregation_scores
    Ct = Ct_list[i]
    
    term1 = (1 / (1 - r)) * inv_vt
    term2 = (r / (1 - r)) * np.dot(inv_vt, np.dot(x.reshape(-1, 1), x.reshape(1, -1))).dot(inv_vt) / (1 - r + Ct)
    
    # Hasil invers baru Vt setelah perhitungan punya Sherman
    Vt_new_inv = term1 - term2

    print(f"Hasil invers Vt baru untuk indeks {i+1}:")
    print(Vt_new_inv)
    print()


# d. Implementasi perhitungan koefisien AR 
a_t_list = [] 
for i in range(len(weights)):
    inv_vt = inverse_matrix[i]
    chi_t = X_t_list[i] 

    # Menghitung ât
    a_t_temp = np.dot(inv_vt, chi_t)
    a_t_list.append(a_t_temp)

    print(f"Hasil ât untuk indeks {i+1}: {a_t_temp}")


# print("Hasil ât list:", a_t_list)