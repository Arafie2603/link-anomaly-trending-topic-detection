import sys
import os
import matplotlib.pyplot as plt
import math
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from collections import defaultdict
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

print('---------- Hasil Probabilitas Mention User (TAHAPAN KEDUA) ----------')
def hitung_mention_tiap_id(target_id, tweets_data):
    temp_mentions = []  # List untuk menyimpan semua mention yang pernah muncul
    temp_pmention = []
    m = 0  # Total mention dalam dataset
    y = 0.5  # Parameter y
    pmention = 0  # Probabilitas mention

    for tweet in tweets_data:
        mentions = tweet['mentions']
        temp_m = tweet['jumlah_mention']
        m += temp_m  # Tambahkan jumlah mention dalam tweet ke total mention

        # Pisahkan mention jika berbentuk string
        if isinstance(mentions, str):
            mentions_list = mentions.split(',')
        else:
            mentions_list = mentions

        # Jika ID tweet cocok dengan target_id, hitung probabilitasnya
        if tweet['id'] == target_id:
            if tweet['jumlah_mention']>1:
                for i in range((tweet['jumlah_mention'])):
                    mu = temp_mentions.count(i)
                    if mu == 0:
                        p = y / (m + y)
                        temp_pmention.append(p)
                    else:
                        p += mu / (m+y)
                        temp_pmention.append(p)
                # print(temp_pmention)
                pmention = sum(temp_pmention)
                temp_pmention.clear()
                print(f"pemntion {tweet['id']} = {pmention}")
            else :
                mu = temp_mentions.count(tweet['mentions'])
                if mu == 0:  # Mention pertama kali
                    pmention += y / (m + y)
                    print(f"Probabilitas {tweet['id']}: {pmention:.4f}")
                else:  # Mention sudah muncul sebelumnya
                    pmention += mu / (m + y)
                    print(f"Probabilitas {tweet['id']}: {pmention:.4f}")

        # Tambahkan mention baru ke `temp_mentions` setelah memproses tweet ini
        temp_mentions.extend(mentions_list)

    return pmention

def hitung_probabilitas_user(tweets):
    for row in tweets:
        pmention = hitung_mention_tiap_id(row['id'], tweets)  
        for item in hasil_perhitungan:
            if item['id'] == row['id']:
                item['probabilitas_user'] = pmention

    return hasil_perhitungan

hasil_probabilitas_user = hitung_probabilitas_user(tweets_data)
# hasil_filtered_user = [hasil for hasil in hasil_probabilitas_user if 1 <= hasil["id"] <= 100]

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

    window_r = timedelta(hours=24)  
    jumlah_diskrit = 120  

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
print(json.dumps(hasil_agregasi, indent=4))
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

aggregation_scores = np.array([entry["s_x"] for entry in hasil_agregasi])

# print("----- Agregation_score reshape ------")
# print(aggregation_scores)

def hitung_weights(r, n):
    """
    Menghitung bobot (weights) berdasarkan formula r * (1 - r)^i.
    
    Parameters:
    - r (float): Nilai bobot dasar (misalnya, tingkat diskon).
    - n (int): Jumlah elemen/agregasi yang ingin dihitung bobotnya.
    Returns:
    - np.array: Array berisi nilai bobot.
    """
    if r <= 0 or r >= 1:
        raise ValueError("Parameter r harus berada dalam rentang (0, 1).")
    if n <= 0:
        raise ValueError("Parameter n harus lebih besar dari 0.")
    weights = np.array([r * (1 - r) ** i for i in range(n)])
    return weights

weights = hitung_weights(r, len(hasil_agregasi))
print("----- weights -----")
print(weights)

# Pastikan aggregation_scores adalah vektor kolom dua dimensi
def hitung_V_t(weights, aggregation_scores):
    V_t_list = []
    for i in range(len(weights)):
        xj = aggregation_scores[i].reshape(-1, 1) 
        outer_product = np.outer(xj, xj.T) 
        V_t = weights[i] * outer_product
        V_t_list.append(V_t)
    return V_t_list


def hitung_x_chi_t(weights, aggregation_scores):
    chi_t = 0
    for j in range(len(aggregation_scores)):  
        x_j = aggregation_scores[j].reshape(-1, 1) 
        temp_chi_t = weights[j] * np.dot(x_j.T, x_j).item() 
        chi_t += temp_chi_t
    return chi_t

V_t_list = hitung_V_t(weights, aggregation_scores)
x_chi_t = hitung_x_chi_t(weights, aggregation_scores)

def hitung_invers(matrix):
    try:
        return np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(matrix)

# print("----- Xt -----")
# print(x_chi_t)
# Fungsi untuk menghitung Ct
def hitung_Ct(V_t_list, aggregation_scores, weights):
    Ct_list = []
    for i in range(len(aggregation_scores)):
        inverse_matrix = hitung_invers(V_t_list[i])
        xj = aggregation_scores[i].reshape(-1, 1) 
        Ct_temp = weights[i] * np.dot(xj.T, np.dot(inverse_matrix, xj)).item()
        Ct_list.append(Ct_temp)
    return Ct_list

# Contoh pemakaian fungsi hitung_Ct:
# Misalkan `weights`, `aggregation_scores`, dan `V_t_list` sudah didefinisikan

Ct_list = hitung_Ct(V_t_list, aggregation_scores, weights)
# # Menampilkan hasil
# print("----- Ct -----")
# print(Ct_list)

def sherman_morrison_woodbury(V_t_list, weights, Ct_list, aggregation_scores):
    Vt_new_inv_list = []
    inverse_matrix = [hitung_invers(vt) for vt in V_t_list]
    for i in range(len(weights)):
        r = weights[i]
        inv_vt = inverse_matrix[i]
        xj = aggregation_scores[i].reshape(-1, 1) 
        Ct = Ct_list[i]

        term1 = (1 / (1 - r)) * inv_vt
        term2 = (r / (1 - r)) * np.dot(inv_vt, np.dot(xj, xj.T)).dot(inv_vt) / (1 - r + Ct)
        Vt_new_inv = term1 - term2
        Vt_new_inv_list.append(Vt_new_inv)
    return Vt_new_inv_list


Vt_new_inv_list = sherman_morrison_woodbury(V_t_list, weights, Ct_list, aggregation_scores)
a_t_list = [np.dot(Vt_new_inv_list[i], x_chi_t) for i in range(len(weights))]

# print("Hasil a_t_list:")
# for i, a_t in enumerate(a_t_list):
#     print(f"a_t[{i}]:\n", a_t)

t_0 = aggregation_scores[0]
def hitung_Kt(weights, Ct_list, aggregation_scores, hasil_agregasi_first_layer):
    """
    Menghitung nilai Kt dan dt pada second layer learning menggunakan hasil agregasi pada first layer.

    Parameters:
    - weights (array-like): Bobot diskon untuk setiap elemen x_j.
    - Ct_list (list): Daftar nilai Ct pada setiap iterasi.
    - aggregation_scores (array-like): Skor agregasi pada setiap diskrit waktu.
    - hasil_agregasi_first_layer (list): Hasil agregasi dari first layer untuk mendapatkan nilai m.

    Returns:
    - K_t_list (list): Daftar nilai K_t untuk setiap iterasi.
    - d_t_list (list): Daftar nilai d_t untuk setiap iterasi.
    """
    K_t_list = []
    d_t_list = []

    for i, y_score in enumerate(aggregation_scores):
        r = weights[i]
        c_t = Ct_list[i]
        
        # Ambil nilai 'jumlah_mention_agregasi' dari hasil_agregasi_first_layer
        m = hasil_agregasi_first_layer[i]["jumlah_mention_agregasi"] if i < len(hasil_agregasi_first_layer) else 0

        d_t = c_t / (1 - r + c_t)
        d_t_list.append(d_t)

        t = i + 1

        # Hitung K_t sesuai dengan formula
        factor1 = np.sqrt(np.pi) / (1 - d_t)
        factor2 = np.sqrt((1 - r) / r)
        factor3 = (1 - r) ** (-(t - m) / 2)
        factor4 = gamma((t - t_0 - 1) / 2) / gamma((t - t_0) / 2)

        K_t = factor1 * factor2 * factor3 * factor4
        K_t_list.append(K_t)

    return K_t_list, d_t_list

K_t_list, d_t_list = hitung_Kt(weights, Ct_list,aggregation_scores, hasil_agregasi)

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
# for idx, tau_t in enumerate(tau_t_values):
#     print(f"τ̂ₜ pada diskrit waktu {idx + 1}: {np.array(tau_t)}")


def hitung_density_sdnml(tau_t_values, K_t_list, t_0, agregation_scores):
    sdnml_density_values = []
    n = min(len(tau_t_values), len(K_t_list), len(agregation_scores))
    for t in range(n):
        tau_t = max(tau_t_values[t], 1e-10)
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


sdnml_density_values = hitung_density_sdnml(tau_t_values, K_t_list, t_0, aggregation_scores)

# print("----- first layer learning -----")
# for t, density in enumerate(sdnml_density_values, start=1):
#     print(f"Densitas SDNML pada diskrit waktu {t + 1}: {density}")

k = 5
def hitung_first_layer_scoring(sdnml_density_values, k, hasil_agregasi):
    y_scores = []  # List untuk menyimpan skor perubahan dan detail jumlah_mention_agregasi

    for j in range(k, len(sdnml_density_values) + 1):
        log_density_values = np.log(sdnml_density_values[j - k:j])
        y_j = (1 / k) * np.sum(log_density_values)

        agregasi_info = hasil_agregasi[j-1] 


        y_scores.append({
            "y_score": y_j,
            "jumlah_mention_agregasi": agregasi_info["jumlah_mention_agregasi"]

        })

    return y_scores

y_scores = hitung_first_layer_scoring(sdnml_density_values, k, hasil_agregasi)

# Tampilkan hasil y_scores dengan detail jumlah_mention_agregasi
print("----- first layer scoring dengan jumlah_mention_agregasi -----")
for idx, y_score_info in enumerate(y_scores, start=k):
    print(f"Skor perubahan titik awal y_{idx}: {y_score_info['y_score']}, "
        f"Jumlah Mention Agregasi: {y_score_info['jumlah_mention_agregasi']}")

# Gunakan output dari first layer scoring (y_scores) sebagai input untuk second layer

def hitung_second_layer_scoring(sdnml_density_values, k):
    y_scores_second_layer = []
    
    # Mulai dari indeks dinamis berdasarkan nilai k
    start_index = 2 * k

    # Hitung skor perubahan pada second layer scoring
    for j in range(start_index, len(sdnml_density_values) + 1):
        log_density_values = np.log(sdnml_density_values[j - k:j])
        y_j = (1 / k) * np.sum(log_density_values)
        y_scores_second_layer.append({
            "y_score": y_j,
            "jumlah_mention_agregasi": hasil_agregasi[j - 1]["jumlah_mention_agregasi"]  # Mengambil data jumlah_mention dari hasil_agregasi
        })

    return y_scores_second_layer


# Menentukan aggregation_scores_second_layer dengan data hasil dari y_scores pada first layer
aggregation_scores_second_layer = np.array([entry["y_score"] for entry in y_scores])
t_0_second_layer = aggregation_scores_second_layer[0]

# 1. Hitung bobot untuk second layer
weights_second_layer = hitung_weights(r, len(aggregation_scores_second_layer))

# 2. Hitung Vt dan Xt untuk second layer
V_t_list_second_layer = hitung_V_t(weights_second_layer, aggregation_scores_second_layer)
x_chi_t_second_layer = hitung_x_chi_t(weights_second_layer, aggregation_scores_second_layer)

# 3. Hitung Ct untuk second layer
Ct_list_second_layer = hitung_Ct(V_t_list_second_layer, aggregation_scores_second_layer, weights_second_layer)

# 4. Implementasikan Sherman-Morrison-Woodbury untuk second layer
Vt_new_inv_list_second_layer = sherman_morrison_woodbury(V_t_list_second_layer, weights_second_layer, Ct_list_second_layer, aggregation_scores_second_layer)

# 5. Hitung a_t untuk second layer
a_t_list_second_layer = [np.dot(Vt_new_inv_list_second_layer[i], x_chi_t_second_layer) for i in range(len(weights_second_layer))]

# 6. Hitung tau_t untuk second layer
tau_t_values_second_layer = hitung_tau_t(weights_second_layer, aggregation_scores_second_layer, a_t_list_second_layer)

# 7. Hitung Kt untuk second layer
K_t_list_second_layer, d_t_list_second_layer = hitung_Kt(weights_second_layer, Ct_list_second_layer, y_scores, hasil_agregasi)

# 8. Hitung SDNML density untuk second layer
sdnml_density_values_second_layer = hitung_density_sdnml(tau_t_values_second_layer, K_t_list_second_layer, t_0_second_layer, aggregation_scores_second_layer)

# Membuat aggregation_scores_second_layer dengan y_scores dari second layer
aggregation_scores_second_layer = np.array([entry["y_score"] for entry in y_scores])

y_scores_second_layer = hitung_second_layer_scoring(sdnml_density_values_second_layer, k)
y_scores_second_layer_values = [entry['y_score'] for entry in y_scores_second_layer]

print((y_scores_second_layer_values))
# Cetak hasil second layer scoring
print("----- second layer scoring -----")
for idx, y_score_info in enumerate(y_scores_second_layer, start=2 * k):
    print(f"Skor perubahan titik awal y_{idx}: {y_score_info['y_score']}, "
        f"Jumlah Mention Agregasi: {y_score_info['jumlah_mention_agregasi']}")

def anomaly_detection(scores, y_scores_second_layer, hasil_agregasi, NH=20, p=0.05, lambda_h=0.01, rh=0.005):
    q = np.full(NH, 1 / NH) 
    alarms = []
    thresholds = []
    results = []

    # Tentukan rentang histogram berdasarkan skor
    a, b = np.min(scores), np.max(scores)
    bins = np.linspace(a, b, NH + 1)

    for y_data in y_scores_second_layer:
        score = y_data["y_score"]
        diskrit_y = y_data["jumlah_mention_agregasi"]  

        # Cari diskrit yang sesuai di hasil_agregasi
        agregasi_data = next((item for item in hasil_agregasi if item["jumlah_mention_agregasi"] == diskrit_y), None)

        if not agregasi_data:
            raise ValueError(f"Diskrit {diskrit_y} tidak ditemukan dalam hasil_agregasi.")

        h = np.digitize(score, bins) - 1  
        h = min(max(h, 0), NH - 1)  

        # Update histogram
        new_q = np.zeros_like(q)
        for k in range(NH):
            if k == h:
                new_q[k] = (1 - rh) * q[k] + rh
            else:
                new_q[k] = (1 - rh) * q[k]

        normalizer = np.sum(new_q + lambda_h)
        new_q = (new_q + lambda_h) / normalizer
        q = new_q

        # Threshold optimization
        cumulative_prob = np.cumsum(q)
        threshold = bins[np.argmax(cumulative_prob >= 1 - p)]
        thresholds.append(threshold)

        # Alarm output
        alarm = bool(score >= threshold)  # Pastikan tipe bool Python biasa
        alarms.append(alarm)


        # Tambahkan hasil diskrit
        results.append({
            "diskrit": agregasi_data["diskrit"],
            "waktu_awal": agregasi_data["waktu_awal"],
            "waktu_akhir": agregasi_data["waktu_akhir"],
            "jumlah_mention_agregasi": agregasi_data["jumlah_mention_agregasi"],
            "y_score": score,
            "threshold": threshold,
            "alarm": alarm
        })

    return results, alarms, thresholds




# Panggil anomaly_detection
results, alarms, thresholds = anomaly_detection(
    scores=y_scores_second_layer_values,
    y_scores_second_layer=y_scores_second_layer,
    hasil_agregasi=hasil_agregasi
)

print(f"threshold = {alarms}")

print(json.dumps(results, indent=4))


def validate_results(results):
    # Validasi diskrit tunggal
    grouped_results = defaultdict(list)
    for result in results:
        grouped_results[result["diskrit"]].append(result)

    diskrit_validation = {}
    threshold_validation = {}

    for diskrit, entries in grouped_results.items():
        # Periksa apakah ada lebih dari satu nilai alarm
        unique_alarms = set(entry["alarm"] for entry in entries)
        diskrit_validation[diskrit] = {
            "multiple_alarms": len(unique_alarms) > 1,
            "alarms": unique_alarms
        }

        # Periksa apakah threshold konsisten
        unique_thresholds = set(entry["threshold"] for entry in entries)
        threshold_validation[diskrit] = {
            "consistent_threshold": len(unique_thresholds) == 1,
            "thresholds": unique_thresholds
        }

    return {
        "diskrit_validation": diskrit_validation,
        "threshold_validation": threshold_validation
    }

# Validasi hasil
validation_results = validate_results(results)

# Tampilkan hasil validasi
print("Validasi Diskrit Tunggal:")
for diskrit, info in validation_results["diskrit_validation"].items():
    print(f"Diskrit {diskrit}: Multiple Alarms? {info['multiple_alarms']}, Alarms: {info['alarms']}")

print("\nValidasi Akurasi DTO:")
for diskrit, info in validation_results["threshold_validation"].items():
    print(f"Diskrit {diskrit}: Consistent Threshold? {info['consistent_threshold']}, Thresholds: {info['thresholds']}")
