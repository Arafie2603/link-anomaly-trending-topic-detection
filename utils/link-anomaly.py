import sys
import os
import json
import math
import numpy as np
# To support import export module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import create_connection
from datetime import datetime, timedelta
from scipy.special import gamma

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

from datetime import datetime

def fetch_tweets_data():
    connection = create_connection()
    tweets_data = []

    if connection is not None:
        cursor = connection.cursor()
        cursor.execute("SELECT id, created_at, username, full_text, mentions, jumlah_mention FROM data_preprocessed")
        
        results = cursor.fetchall()
        
        for row in results:
            mentions_list = row[4].split(", ") if row[4] else []  
            
            tweet = {
                "id": row[0],
                "created_at": row[1],
                "username": row[2],
                "full_text": row[3], 
                "mentions": mentions_list,  
                "jumlah_mention": row[5]
            }
            tweets_data.append(tweet)

        cursor.close()
        connection.close()

    return tweets_data

# Fetching the tweets data
tweets_data = fetch_tweets_data()

# Pastikan 'created_at' adalah string sebelum mengonversi
for tweet in tweets_data:
    if isinstance(tweet['created_at'], str):
        tweet['created_at'] = datetime.strptime(tweet['created_at'], "%Y-%m-%d %H:%M:%S")

# Mengurutkan berdasarkan 'created_at'
tweets_data.sort(key=lambda x: x['created_at']) 

# ---------- Tahap 1: Probabilitas Mention ----------
print('---------- Hasil Probabilitas Mention (TAHAPAN PERTAMA) ----------')

hasil_perhitungan = []

def hitung_probabilitas_mention(tweets):
    alpha = 0.5
    beta = 0.5
    m = 0
    k_sigma = 0
    unique_usernames = set()

    for i, tweet in enumerate(tweets):
        iterasi = 1.0
        k = tweet['jumlah_mention']  
        temp_m = tweet['jumlah_mention'] 
        m += temp_m
        n = i + 1

        username = tweet['username']
        if username not in unique_usernames:
            unique_usernames.add(username)
            k_sigma += 1 

        for j in range(k_sigma):
            if j == 0:
                iterasi *= (n + alpha) / (m + k + beta)
            iterasi *= (m + beta + j) / (n + m + alpha + beta + j)

        waktu_str = tweet['created_at'].strftime("%Y-%m-%d %H:%M:%S")

        hasil_perhitungan.append({
            "id": tweet['id'],
            "created_at": waktu_str,
            "probabilitas_mention": iterasi
        })
    
    return hasil_perhitungan

hasil_mention = hitung_probabilitas_mention(tweets_data)
# hasil_filtered_mention = [hasil for hasil in hasil_mention if 1 <= hasil["id"] <= 100]

# # Cetak hasil probabilitas mention untuk ID 1-100
# for hasil in hasil_filtered_mention:
#     print(f"ID: {hasil['id']}, Waktu: {hasil['created_at']}, Probabilitas Mention: {hasil['probabilitas_mention']}")


# ---------- Tahap 2: Hitung Probablitas Mention User ----------
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
        for item in hasil_perhitungan:
            if item['id'] == row['id']:
                item['probabilitas_user'] = pmention

    return hasil_perhitungan

hasil_probabilitas_user = hitung_probabilitas_user(tweets_data)
hasil_filtered_user = [hasil for hasil in hasil_probabilitas_user if 1 <= hasil["id"] <= 100]

# Cetak hasil probabilitas mention user untuk ID 1-100
# for hasil in hasil_filtered_user:
#     print(f"ID: {hasil['id']}, Waktu: {hasil['created_at']}, Probabilitas Mention: {hasil['probabilitas_mention']}, Probabilitas User: {hasil['probabilitas_user']}")


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
# print(json.dumps(hasil_perhitungan, indent=4))

"""
2. Menghitung Agregasi Skor Anomaly
Program ini menggunakan diskrit time sebesar 6 jam, dan jumlah diskrit sebanyak 120
"""

hasil_agregasi = []
skor_agregasi = []

print('---------- Hitung Skor Agregasi ----------')
def hitung_skor_agregasi(hasil_skor):
    # Ambil waktu awal dari hasil perhitungan
    waktu_awal_string = hasil_skor[0]['created_at']
    waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")

    # Tentukan interval waktu untuk diskrit
    # Ubah ke 1 jam
    # Ubah ke 648
    window_r = timedelta(hours=1)  
    jumlah_diskrit = 648  

    # Tentukan waktu awal dan akhir
    waktu_akhir = waktu_awal + window_r

    # Buat list untuk menyimpan skor anomaly yang masuk ke setiap diskrit
    diskrit_anomaly = [[] for _ in range(jumlah_diskrit)]

    for index in range(jumlah_diskrit):
        # Reset jumlah skor anomaly untuk setiap diskrit
        jml_skor_anomaly = 0  
        for data in hasil_skor:
            temp_waktu = data['created_at']
            tweet_waktu = datetime.strptime(temp_waktu, "%Y-%m-%d %H:%M:%S")

            if waktu_awal <= tweet_waktu < waktu_akhir:
                jml_skor_anomaly += data['skor_anomaly']
                # Simpan skor anomaly yang memenuhi syarat ke dalam list diskrit
                diskrit_anomaly[index].append(data)  
        
        # Hitung s_x
        # Faktor 1/6 tetap, karena masih sesuai studi kasus
        s_x = (1 / window_r.total_seconds() / 3600) * jml_skor_anomaly  
        hasil_agregasi.append({
            "diskrit": index + 1, 
            "waktu_awal": waktu_awal.strftime('%Y-%m-%d %H:%M:%S'), 
            "waktu_akhir": waktu_akhir.strftime('%Y-%m-%d %H:%M:%S'), 
            "s_x": s_x,
            "anomalies": diskrit_anomaly[index] 
        })
        skor_agregasi.append(s_x)

        waktu_awal = waktu_akhir
        waktu_akhir += window_r

    return hasil_agregasi

hasil_agregasi = hitung_skor_agregasi(hasil_perhitungan)
# print(json.dumps(hasil_agregasi, indent=4))
# print(hasil_agregasi)



# ========================== IMPLEMENTASI SDNML ==========================

"""
Langkah 1: First Layering Learning
Langkah - langkahnya :
    1. Mencari nilai Koefisien AR
        a. Mencari nilai Vt dan Xt
        b. Mencari nilai invers Vt
        c. Menghitung metode Sherman-Morisson-Woodburry
        d. Implementasi perhitungan koefisien AR 
        e. menghitung faktor normalisasi Kt(xt-1)
        f. menghitung fungsi densitas SDNML 

informasi penggunaan variabel : 
V_t_list = list untuk menampung hasil perhitungan dari Vt 
weights = hasil dari perhitungan nilai bobot
X_t_list = list untuk menampung hasil perhitungan dari Xt
hitung_inverse = fungsi yang digunakan untuk menghitung inverse dan akan menghitung inverse menggunakan pseudo-inverse jika matriks Vt merupakan singular
Ct_list = list yang menampung perhitungan dari nilai Ct
inverse_matrix = variabel yang digunakan untuk menyimpan hasil perhitungan invers dari matriks
"""

r = 0.005
jumlah_diskrit = 648  
weights = np.array([r * (1 - r) ** i for i in range(len(hasil_agregasi))])  
aggregation_scores = np.array(skor_agregasi)  

# Menghitung matriks V_t untuk setiap bobot
V_t_list = []
for weight in weights:
    V_t = weight * np.outer(aggregation_scores, aggregation_scores)  
    V_t_list.append(V_t)

# Menghitung nilai X_t untuk setiap bobot
x_chi_t = 0
for i in range(len(hasil_agregasi)):
    temp_xt = weights[i] * aggregation_scores[i] * aggregation_scores[i]
    x_chi_t += temp_xt 

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

# d. Implementasi perhitungan koefisien AR 
a_t_list = [] 
for i in range(len(weights)):
    inv_vt = inverse_matrix[i]

    # Menghitung ât
    a_t_temp = np.dot(inv_vt, x_chi_t)
    a_t_list.append(a_t_temp)

    # print(f"Hasil ât untuk indeks {i+1}: {a_t_temp}")
# print("Hasil ât list:", a_t_list)

# e. Menghitung faktor normalisasi Kt(xt-1)
def hitung_Kt(weights, Ct_list, tweets):
    K_t_list = []
    d_t_list = []
    m = 0

    for i in range(len(weights)):
        r = weights[i]
        c_t = Ct_list[i]
        
        tweet = tweets[i] 
        k = tweet['jumlah_mention'] 
        m += k  

        d_t = c_t / (1 - r + c_t)
        d_t_list.append(d_t)

        t = i + 1
        t_0 = 0

        factor1 = np.sqrt(np.pi) / (1 - d_t)
        factor2 = np.sqrt((1 - r) / r)
        factor3 = (1 - r) ** (-(t - m) / 2)
        factor4 = gamma((t - t_0 - 1) / 2) / gamma((t - t_0) / 2)

        K_t = factor1 * factor2 * factor3 * factor4
        K_t_list.append(K_t)

    return K_t_list, d_t_list
K_t_list, d_t_list = hitung_Kt(aggregation_scores, weights, Ct_list, tweets_data)
print("Nilai K_t untuk setiap iterasi:")
for i, K_t in enumerate(K_t_list):
    print(f"Iterasi {i+1}: K_t = {K_t}")