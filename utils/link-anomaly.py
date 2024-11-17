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
            "probabilitas_mention": iterasi,
            "mentions": tweet['jumlah_mention']
        })
    
    return hasil_perhitungan

hasil_mention = hitung_probabilitas_mention(tweets_data)

# Cetak hasil probabilitas mention untuk ID 1-100
# for hasil in hasil_mention[:300]:
#     print(f"ID: {hasil['id']}, Waktu: {hasil['created_at']}, Probabilitas Mention: {hasil['probabilitas_mention']}, jumlah_mention: {hasil['mentions']}")

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

print('---------- Hitung Skor Agregasi ----------')
def hitung_skor_agregasi(hasil_skor):
    waktu_awal_string = hasil_skor[0]['created_at']
    waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")

    window_r = timedelta(hours=4)  
    jumlah_diskrit = 152  

    waktu_akhir = waktu_awal + window_r

    diskrit_anomaly = [[] for _ in range(jumlah_diskrit)]

    for index in range(jumlah_diskrit):
        jml_skor_anomaly = 0  
        jumlah_mention_agregasi = 0 
        
        for data in hasil_skor:
            temp_waktu = data['created_at']
            tweet_waktu = datetime.strptime(temp_waktu, "%Y-%m-%d %H:%M:%S")

            if waktu_awal <= tweet_waktu < waktu_akhir:
                jml_skor_anomaly += data['skor_anomaly']
                jumlah_mention_agregasi += data['mentions'] 
                diskrit_anomaly[index].append(data)  

        s_x = (1 / window_r.total_seconds() / 3600) * jml_skor_anomaly  
        
        hasil_agregasi.append({
            "diskrit": index + 1, 
            "waktu_awal": waktu_awal.strftime('%Y-%m-%d %H:%M:%S'), 
            "waktu_akhir": waktu_akhir.strftime('%Y-%m-%d %H:%M:%S'), 
            "s_x": s_x,
            "jumlah_mention_agregasi": jumlah_mention_agregasi
        })
        
        # Update waktu_awal dan waktu_akhir untuk iterasi berikutnya
        waktu_awal = waktu_akhir
        waktu_akhir += window_r

    return hasil_agregasi

hasil_skor_agregasi = hitung_skor_agregasi(hasil_perhitungan)
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

# Inisialisasi variabel
r = 0.005
weights = np.array([r * (1 - r) ** i for i in range(len(hasil_agregasi))])
aggregation_scores = np.array([entry["s_x"] for entry in hasil_agregasi])

print("----- Agregation_score reshape ------")
print(aggregation_scores)

print("----- weights -----")
print(weights)

def hitung_V_t(weights, aggregation_scores):
    outer_product = np.outer(aggregation_scores, aggregation_scores)
    V_t = sum(w * outer_product for w in weights)
    return V_t

def hitung_x_chi_t(weights, aggregation_scores):
    """
    Menghitung chi_t berdasarkan bobot dan skor agregasi sesuai dengan rumus Takahashi et al.

    Parameter:
    weights (array-like): Bobot diskon untuk setiap elemen x_j.
    aggregation_scores (array-like): Skor agregasi untuk setiap diskrit waktu.

    Mengembalikan:
    chi_t (numpy array): Vektor chi_t yang dihitung berdasarkan bobot dan x_j.
    """# Inisialisasi chi_t sebagai vektor dengan panjang yang sesuai dengan fitur agregasi

    # Menghitung chi_t sesuai dengan rumus yang benar
    x_chi_t = 0
    for i in range(len(hasil_agregasi)):
        temp_xt = weights[i] * aggregation_scores[i] * aggregation_scores[i]
        x_chi_t += temp_xt 
    
    return x_chi_t


V_t_list = hitung_V_t(weights, aggregation_scores)
x_chi_t = hitung_x_chi_t(weights, aggregation_scores)
print("----- VT -----")
print(V_t_list)

print("----- Xt -----")
print(x_chi_t)

# def hitung_invers(matrix):
#     matrix = np.array(matrix)
#     if matrix.ndim == 1:
#         matrix = matrix.reshape(-1, 1)
    
#     try:
#         return np.linalg.inv(matrix)
#     except np.linalg.LinAlgError:
#         return np.linalg.pinv(matrix)
    
# print(f"dimensi agregasi = {aggregation_scores.shape}")
# print(f"dimensi vt = {hitung_invers(V_t_list).shape}")



# Fungsi untuk menghitung Ct sesuai dengan rumus
def hitung_Ct(weights, aggregation_scores, V_t_list):
    Ct_list = []
    for i in range(len(weights)):
        inv_vt = V_t_list  # Matriks invers V_t (dimensi 152x152)
        r = weights[i]
        x_t = aggregation_scores[i]
        
        # Perhitungan Ct sesuai rumus: Ct = r * x_t^T * V_t^{-1} * x_t
        x_t_T = x_t.T  # x_t^T (dimensi 1, 152)
        
        # Pastikan dimensi perkalian dot sesuai
        Ct = r * np.dot(np.dot(x_t_T, inv_vt), x_t)  # Operasi dot yang benar
        
        Ct_list.append(Ct[0, 0])  # Ambil hasil skalar Ct dari hasil dot produk

    return Ct_list
Ct_list = hitung_Ct(weights, aggregation_scores, V_t_list)
print("----- Ct -----")
print(Ct_list)

Vt_new_inv_list = []
# Pastikan aggregation_scores adalah array 1D dengan panjang 152
print(f"Dimensi aggregation_scores: {aggregation_scores.shape}")

for i in range(len(weights)):
    inv_vt = np.linalg.pinv(V_t_list)
    r = weights[i]
    
    # Akses satu elemen dari aggregation_scores dan reshape menjadi (152, 1)
    x = aggregation_scores[i]  # Ambil nilai pada indeks i
    x = x.reshape(152, 1)  # reshape menjadi (152, 1) jika perlu
    
    Ct = Ct_list[i]

    print(f"Dimensi x = {x.shape}")  # Pastikan x adalah (152, 1)
    
    # Term 1
    term1 = (1 / (1 - r)) * inv_vt

    # Term 2
    a = np.dot(x, x.T)  # Hasilnya (152, 152)
    print(f"Dimensi a = {a.shape}")
    
    term2 = (r / (1 - r)) * np.dot(np.dot(inv_vt, a), inv_vt) / (1 - r + Ct)

    # Hasil invers baru Vt setelah Sherman-Morrison-Woodbury
    Vt_new_inv = term1 - term2
    Vt_new_inv_list.append(Vt_new_inv)

print("----- Sherman -----")
print(Vt_new_inv_list)





a_t_list = [np.dot(Vt_new_inv_list[i], x_chi_t) for i in range(len(weights))]

print("Hasil a_t_list:")
for i, a_t in enumerate(a_t_list):
    print(f"a_t[{i}]:\n", a_t)

t_0 = aggregation_scores[0]
def hitung_Kt(weights, Ct_list):
    K_t_list = []
    d_t_list = []
    m = 0

    for i, tweet in enumerate(hasil_agregasi):
        r = weights[i]
        c_t = Ct_list[i]
        m = tweet['jumlah_mention_agregasi']

        d_t = c_t / (1 - r + c_t)
        d_t_list.append(d_t)

        t = i + 1

        factor1 = np.sqrt(np.pi) / (1 - d_t)
        factor2 = np.sqrt((1 - r) / r)
        factor3 = (1 - r) ** (-(t - m) / 2)
        factor4 = gamma((t - t_0 - 1) / 2) / gamma((t - t_0) / 2)

        K_t = factor1 * factor2 * factor3 * factor4
        K_t_list.append(K_t)

    return K_t_list, d_t_list

K_t_list, d_t_list = hitung_Kt(weights, Ct_list)

print("----- Kt -----")
for i, K_t in enumerate(K_t_list):
    print(f"Iterasi {i+1}: K_t = {K_t}")

def hitung_e_j_kuadrat(j, aggregation_scores, a_t_list):
    x_j = aggregation_scores[j]
    a_j_transpose = a_t_list[j].T 
    x_bar_j = aggregation_scores[j]  
    e_j_kuadrat = (x_j - np.dot(a_j_transpose, x_bar_j)) ** 2
    return e_j_kuadrat

def hitung_tau_t(weights, aggregation_scores, a_t_list):
    tau_t_list = [] 
    
    for t in range(1, len(aggregation_scores)):
        tau_t = 0.0 
        for j in range(t):
            weight = weights[j]
            e_j_kuadrat = hitung_e_j_kuadrat(j, aggregation_scores, a_t_list)
            tau_t += weight * e_j_kuadrat
        tau_t_list.append(tau_t)
    return tau_t_list

tau_t_values = hitung_tau_t(weights, aggregation_scores, a_t_list)
print("----- tau sub t -----")
for idx, tau_t in enumerate(tau_t_values):
    tau_t_bulat = np.round(tau_t, 2)
    print(f"τ̂ₜ pada diskrit waktu {idx + 1}: {tau_t_bulat}")


def hitung_density_sdnml(tau_t_values, K_t_list, t_0):
    sdnml_density_values = []
    
    n = min(len(tau_t_values), len(K_t_list), len(hasil_agregasi))
    
    for t in range(n):
        tau_t = tau_t_values[t]
        tau_t_minus_1 = tau_t_values[t - 1] if t - 1 >= 0 else tau_t_values[0]
        
        K_t = K_t_list[t]
        K_t = np.maximum(K_t, 1e-10)
        tau_t = np.maximum(tau_t, 1e-10)
        tau_t_minus_1 = np.maximum(tau_t_minus_1, 1e-10)
        
        exponent_t_tau_t = (t - t_0) / 2
        exponent_t_tau_t_minus_1 = (t - t_0 - 1) / 2
        
        density_sdnml = (1 / K_t) * (tau_t ** (-exponent_t_tau_t)) / (tau_t_minus_1 ** (-exponent_t_tau_t_minus_1))
        sdnml_density_values.append(density_sdnml)
    
    return sdnml_density_values


sdnml_density_values = hitung_density_sdnml(tau_t_values, K_t_list, t_0)

print("----- first layer learning -----")
for t, density in enumerate(sdnml_density_values, start=1):
    print(f"Densitas SDNML pada diskrit waktu {t + 1}: {density}")

k = 15  
def hitung_first_layer_scoring(sdnml_density_values, k):
    y_scores = []

    for j in range(k, len(sdnml_density_values) + 1):
        log_density_values = np.log(sdnml_density_values[j - k:j])
        y_j = (1 / k) * np.sum(log_density_values)
        y_scores.append(y_j)

    return y_scores

y_scores = hitung_first_layer_scoring(sdnml_density_values, k)

print("----- first layer scoring -----")
for idx, y_score in enumerate(y_scores, start=k):
    print(f"Skor perubahan titik awal y_{idx}: {y_score}")
# Menggunakan kembali parameter smoothing untuk SDNML
# t_0 = y_scores[0] 

# Fungsi untuk menghitung density SDNML pada lapisan kedua (second-layer learning)
# def hitung_second_layer_density(y_scores, weights, t_0):
#     tau_y_values = []
#     K_y_list = []
#     for j in range(1, len(y_scores)):
#         tau_y = 0.0
#         for i in range(j):
#             weight = weights[i]
#             y_i = y_scores[i]
#             tau_y += weight * (y_i - y_scores[j]) ** 2

#         tau_y_values.append(tau_y)

#         d_t = tau_y / (1 - weights[j] + tau_y)
#         factor1 = np.sqrt(np.pi) / (1 - d_t)
#         factor2 = np.sqrt((1 - weights[j]) / weights[j])
#         factor3 = (1 - weights[j]) ** (-(j - t_0) / 2)
#         factor4 = gamma((j - t_0 - 1) / 2) / gamma((j - t_0) / 2)

#         K_y = factor1 * factor2 * factor3 * factor4
#         K_y_list.append(K_y)

#     return tau_y_values, K_y_list

# # Hitung density function untuk lapisan kedua
# tau_y_values, K_y_list = hitung_second_layer_density(y_scores, weights, t_0)

# # Cetak hasil tau_y_values dan K_y_list
# for j, (tau_y, K_y) in enumerate(zip(tau_y_values, K_y_list), start=2):
#     print(f"Density SDNML untuk lapisan kedua pada skor y_{j}: τ̂_y = {tau_y}, K_y = {K_y}")
