import sys
import os
import matplotlib.pyplot as plt
import math
import json
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from collections import defaultdict
import statistics
from datetime import datetime, timedelta
from scipy.special import gamma

# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.utils.db_connection import create_connection

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
for tweet in tweets_data:
    if isinstance(tweet['created_at'], str):
        tweet['created_at'] = datetime.strptime(tweet['created_at'], "%Y-%m-%d %H:%M:%S")
tweets_data.sort(key=lambda x: x['created_at']) 

"""
Penjelasan tiap variabel di bagian perhitungan skor anomaly tahap pertama:
m = Jumlah mention dalam rentang waktu perhitungan
n = Indeks tweet pada rentang waktu perhitungan 
k = jumlah mention pada tweet dalam training
alpha, beta = nilai konstan, merujuk pada penelitian Takahashi
iterasi = variabel yang menampung perhitungan pada setiap tweets
"""

print('---------- Hasil Probabilitas Mention (TAHAPAN PERTAMA) ----------')
hasil_perhitungan = []
def hitung_probabilitas_mention(tweets):
    alpha = 0.5
    beta = 0.5
    m = 0

    for i, tweet in enumerate(tweets):
        iterasi = 1.0
        k = tweet['jumlah_mention']  
        temp_m = tweet['jumlah_mention'] 
        m += temp_m
        n = i + 1

        for j in range(k+1):
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

print('---------- Hasil Probabilitas Mention User (TAHAPAN KEDUA) ----------')
def hitung_mention_tiap_id(tweets_data):
    temp_mentions = []
    mention_list_uji = []
    m = 0  
    y = 0.5 

    for tweet in tweets_data:
        mentions = tweet['mentions']
        jumlah_mention = tweet['jumlah_mention']
        m += jumlah_mention

        
        if isinstance(mentions, str):
            mentions_list = mentions.split(',') 
        else:
            mentions_list = mentions
        mentions_list = mentions_list[0].split(',')
        
        if tweet['jumlah_mention'] > 1:
            pmention_list = []  
            for mention in mentions_list: 
                mu = mention_list_uji.count(mention)
                if mu == 0:
                    p = y / (m + y)
                else:
                    p = mu / (m + y)
                pmention_list.append(p)
        else:
            pmention_list = []
            mu = temp_mentions.count(mentions_list) 
            if mu == 0:
                p = y / (m + y)
            else:
                p = mu / (m + y)
            pmention_list.append(p) 
        mention_list_uji.extend(mentions_list)

        for hasil in hasil_perhitungan:
            if hasil['id'] == tweet['id']:
                hasil['probabilitas_user'] = pmention_list

    return hasil_perhitungan  
hasil_probabilitas_user = hitung_mention_tiap_id(tweets_data)

print('---------- Hitung Skor Anomaly ----------')
def hitung_skor_anomaly(hasil):
    for skor in hasil:

        for item in hasil:
            if item['id'] == skor['id']:
                probabilitas_mention = skor.get('probabilitas_mention', [])
                probabilitas_user = skor.get('probabilitas_user', [])
                # print(f"probabili user = {probabilitas_user}")
                temp_puser = []
                if item['mentions'] > 1:
                    for i in probabilitas_user:
                        calculate = math.log(i)
                        temp_puser.append(calculate)
                else:
                    calculate = math.log(probabilitas_user[0])
                    temp_puser.append(calculate)
                # print(temp_puser)
                skor_anomaly = -math.log(probabilitas_mention)-sum(temp_puser)
                # print(f"item {item['id']} = {skor_anomaly}")
                item['skor_anomaly'] = skor_anomaly

hasil_skor_anomaly = hitung_skor_anomaly(hasil_perhitungan)

"""
2. Menghitung Agregasi Skor Anomaly
    - diskrit waktu yang ditentukan 24 jam pada var window_r
    - jumlah_diskrit ditentukan secara dinamis melalui program, menyesuaikan dengan data yang ada dalam dataset/database
    - waktu awal diinisialisasi dengan waktu_awal var
"""

hasil_agregasi = []

print('---------- Hitung Skor Agregasi ----------')
def hitung_skor_agregasi(hasil_skor):
    waktu_awal_string = hasil_skor[0]['created_at']
    waktu_akhir_string = hasil_skor[-1]['created_at']

    waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")
    waktu_akhir_data = datetime.strptime(waktu_akhir_string, "%Y-%m-%d %H:%M:%S")

    window_r = timedelta(hours=24) 

    waktu_akhir = waktu_awal + window_r
    total_durasi = (waktu_akhir_data - waktu_awal).total_seconds()
    jumlah_diskrit = int(total_durasi // window_r.total_seconds())+1

    for index in range(jumlah_diskrit):
        jml_skor_anomaly = 0  
        jumlah_mention_agregasi = 0 
        
        for data in hasil_skor:
            temp_waktu = data['created_at']
            tweet_waktu = datetime.strptime(temp_waktu, "%Y-%m-%d %H:%M:%S")

            if waktu_awal <= tweet_waktu < waktu_akhir:
                jml_skor_anomaly += data['skor_anomaly']
                jumlah_mention_agregasi += data['mentions'] 
        s_x = (1 / (window_r.total_seconds() / 3600)) * jml_skor_anomaly  
        hasil_agregasi.append({
            "diskrit": index + 1, 
            "waktu_awal": waktu_awal.strftime('%Y-%m-%d %H:%M:%S'), 
            "waktu_akhir": waktu_akhir.strftime('%Y-%m-%d %H:%M:%S'), 
            "s_x": s_x,
            "jumlah_mention_agregasi": jumlah_mention_agregasi
        })
        
        waktu_awal = waktu_akhir
        waktu_akhir += window_r

    return hasil_agregasi

hasil_skor_agregasi = hitung_skor_agregasi(hasil_perhitungan)
# print(json.dumps(hasil_agregasi, indent=4))
# ========================== IMPLEMENTASI SDNML ==========================

"""
Langkah 1: First Layer Learn
Langkah - langkahnya :
    1. Melakukan inisialisasi data dari agregasi :
        a. x_t = data dari hasil_agregasi
        b. X_t = vektor (transpose) dari hasil_agregasi
        c. Menentukan nilai order, order menentukan seberapa banyak data masa lalu yang diinginkan untuk prediksi
        d. m = merupakan nilai yang paling kecil sehingga perhitungan dapat diselesaikan secara unik (tiap indeks memiliki nilai yang berbeda)
    2. Melakukan inisialisasi matrix :
        a. V0 = inisialisasi untuk menghitung invers matrix Sherman-Morisson-Woodburry Vt
        b. M0 = inisalisasi untuk menghitung Mt
    3. Perhitungan Persamaan 4,5,6,7:
        a. menghitung secara bersamaan Vt, Mt, dt, ct pada func update_matrices
        b. mencari nilai A_t dengan melakukan perkalian pada matriks Vt dan Mt
        c. mencari nilai s_t dengan menghitung e_t terlebih dahulu, keduanya dihitung dengan iterasi yang dimulai m+1 sesuai pada rumus
        d. mencari nilai k_t gamma pada k_t merupakan untuk mencari nilai faktorial 
        e. mencari nilai first layer learn dengan fungsi kepadatan p_SDNML 
"""
r = 0.0005
aggregation_scores = np.array([entry["s_x"] for entry in hasil_agregasi])
print(f"agregasi = {aggregation_scores}")
x_t = aggregation_scores

def create_X_t(x_t, order):
    n = len(x_t)
    X_t = np.zeros((n - order, order))
    for t in range(order, n):
        X_t[t - order] = x_t[t - order:t][::-1]
    return X_t

order = 2 
m = 0
X_t = create_X_t(x_t, order=order)
print(f"Nilai x_bar_t = {X_t}")

V0 = np.identity(order)
M0 = np.zeros(order)

def update_matrices(V_prev_inv, M_prev, x_t, xt, r=0.0005):
    x_t = x_t[:, np.newaxis] 
    c_t = r * (x_t.T @ V_prev_inv @ x_t)
    V_t = (1 / (1 - r)) * V_prev_inv - (r / (1 - r)) * (V_prev_inv @ np.outer(x_t.flatten(), x_t) @ V_prev_inv) / (1 - r + c_t)
    M_t = (1 - r) * M_prev + r * x_t.flatten() * xt
    print("V_t dan M_t:")
    # print(V_t)
    # print("\nM_t:")
    # print(M_t)
    # print("\n")
    
    return V_t, M_t, c_t.item()

V_inv = V0
M = M0
d_t = []
print(x_t[0 + order])
for t in range(len(X_t)):
    V_inv, M, c_t = update_matrices(V_inv, M, X_t[t], x_t[t + order])
    d_t_value = c_t / (1 - r + c_t)  
    d_t.append(d_t_value)
    # print(V_inv)
V = V_inv
A_t = np.dot(V, M)
print(A_t)
print("--- d_t")
print(d_t)

e_t = [x_t[i + order] - np.dot(A_t, X_t[i]) for i in range(len(X_t))]
print("--- e_t ---")
print(e_t)
tau_t = [(1 / (i - m)) * sum([e_t[j]**2 for j in range(m+1, i+1)]) for i in range(m+1, len(X_t))]
print("--- tau_t ---")
print(tau_t)

length_st = len(tau_t)
s_t = [(i - m) * tau_t[i] for i in range(m+1, length_st)]
print("--- s_t ---")
print(tau_t[m+1])
print(s_t)

K_t = [np.sqrt(np.pi) / (1 - d_t[i]) * gamma((i+1 - m - 1) / 2) / gamma((i - m) / 2) for i in range(m+1, len(d_t))]
print("--- K_t ---")
print(d_t[0+1])
print(K_t)

length_firstLayer = len(s_t)
p_SDNML = [K_t[i]**-1 * (s_t[i]**(-(i+1 - m) / 2) / s_t[i - 1]**(-(i+1 - m - 1) / 2)) for i in range(m+1, length_firstLayer)]
print("--- psdnml ---")
print(p_SDNML)

print("--- first score stage ---")
"""
Langkah 2: First Scoring Stage
Langkah - langkahnya :
    1. mencari nilai firdt score learn melalui log_p_SDNML dengan mencari -nilai log dari p_SDNML (first layer)
"""
log_p_SDNML = [
    -np.log(p_SDNML[i]) 
    for i in range(len(p_SDNML))
]
first_scores = []
for t in range(len(log_p_SDNML)):
        score = log_p_SDNML[t]
        first_scores.append(score)
        # print(f"Panjang kode SDNML untuk x_{t + 1}: {score}")
print(first_scores)


print("--- Smoothing ---")
"""
Langkah 3: Smoothing
    1. mencari nilai smoothing dengan mengambil skor rerata pada jendela waktu konstan T dan
        kemudian menggeser jendela tersebut dari waktu ke waktu yang diaplikasikan pada func apply_smoothing
"""
def apply_smoothing(scores, T):
    """
    Terapkan smoothing pada skor menggunakan jendela waktu T.
    scores: Daftar skor yang sudah dihitung.
    T: Ukuran jendela untuk smoothing.
    """
    print(f"first index smooth = {scores[0]}")
    smoothed_scores = []
    for t in range(T - 1, len(scores)):  
        smoothed_score = np.mean(scores[t-T+1:t+1])  
        print(f"indeks {scores[t]}, = {scores[t-T+1:t+1]}")
        smoothed_scores.append(smoothed_score)
    return smoothed_scores
T = 2  
smoothed_scores = apply_smoothing(first_scores, T)

# Informasi agregasi setelah smoothing tahap 1
# started_indeks = order*order+T

# start_value_smoothed = smoothed_scores[0]
# start_value_hasil_agregasi = hasil_agregasi[started_indeks-1]
# started_indeks = hasil_agregasi.index(start_value_hasil_agregasi)

# end_index = len(hasil_agregasi)-1

# for i in range(started_indeks, end_index):
#     relative_index = i - started_indeks
#     hasil_agregasi[i]['first_layer'] = first_scores[relative_index]
# print(smoothed_scores)


print("--- Second Learning Stage ---")
"""
Langkah 4: Second Learning Stage
Langkah - langkahnya :
    1. Mengulangi langkah pada first layer, dengan pendefinisian yang berbeda
    2. Tahapan pada first dan second dapat diimplementasikan dengan func agar tidak boilerplate
        dan dapat dengan mudah di maintenance, namun pada studi kasus saat ini saya belum menerapkannya
        dengan berbagai macam alasan 
"""

X_t_second = create_X_t(smoothed_scores, order=order)
x_t_second = smoothed_scores

V0_second = np.identity(order)
M0_second = np.zeros(order)

V_inv_second = V0_second
M_second = M0_second

print("--- d_t second ---")
d_t_second = []
for t in range(len(X_t_second)):
    V_inv_second, M_second, c_t_second = update_matrices(V_inv_second, M_second, X_t_second[t], x_t_second[t + order])
    d_t_value_second = c_t_second / (1 - r + c_t_second)
    d_t_second.append(d_t_value_second)
print(d_t_second)

A_t_second = np.dot(V_inv_second, M_second)
print("--- et second ---")
e_t_second = [x_t_second[i + order] - np.dot(A_t_second, X_t_second[i]) for i in range(len(X_t_second))]
print(e_t_second)

print("--- tau_t_second ---")
tau_t_second = [(1 / (i - m)) * sum([e_t_second[j]**2 for j in range(m+1, i+1)]) for i in range(m+1, len(X_t_second))]
print(tau_t_second)

print("--- s_t_second ---")
length_st_second = len(tau_t_second)
s_t_second = [(i - m) * tau_t_second[i] for i in range(m+1, length_st_second)]
print(tau_t_second[m+1])
print(s_t_second)

print("--- kt_second ---")
K_t_second = [np.sqrt(np.pi) / (1 - d_t_second[i]) * gamma((i+1 - m - 1) / 2) / gamma((i+1 - m) / 2) for i in range(m+1, len(d_t_second))]
print(K_t_second)

print("--- PSDNML second ---")
length_second_learn = len(s_t_second)
p_SDNML_second = [K_t_second[i]**-1 * (s_t_second[i]**(-(i+1 - m) / 2) / s_t_second[i - 1]**(-(i+1 - m - 1) / 2)) for i in range(m+1, length_second_learn)]
print(p_SDNML_second)

print("--- Second Scoring Stage ---")
"""
Langkah 5: Second Scoring Stage
Langkah - langkahnya :
    1. mencari nilai Second Score Learn melalui log_p_SDNML_second dengan mencari -nilai log dari p_SDNML_second (Second Learn)
"""
log_p_SDNML_second = [
    -np.log(p_SDNML_second[i]) 
    for i in range(len(p_SDNML_second))
]
print(log_p_SDNML_second)

second_scores = log_p_SDNML_second
print("--- smoothing ---")
smoothed_second_scores = apply_smoothing(second_scores, T)
yscore = np.array(smoothed_second_scores)
print(yscore)

end_index = len(hasil_agregasi)-(order+1)
start_index_second_smoothed = (order * order * T) + T - 1
print(start_index_second_smoothed)
for i in range(start_index_second_smoothed, end_index):
    relative_index = i - start_index_second_smoothed
    hasil_agregasi[i]['yscore'] = yscore[relative_index]

"""
Langkah akhir: Implementasi Dynamic Threshold Optimation (DTO)
    1. Langkah akhir ini bertujuan untuk mendeteksi kumpulan diskrit yang memiliki trend topic
        dengan ditandai sebagai alarm True pada data score
    2. implementasi dari DTO diatur oleh fungsi dynamic_threshold_optimization, yang memiliki parameter yang sesuai
        pada referensi penelitian Kenji Yamanishi mengenai Dynamic Syslog Mining for Network Failure Monitoring
    3. a merupakan rerata dari data kemudian + 2 * np.std(scores) std merupakan standar deviasi pada input data
        sementara b merupakan nilai minimum pada data.
    4. inisalisasi bins 
    5. inisialisasi histogram
    6. lakukan looping dengan M - 1, M (data size)
    7. Updating rule di atur pada looping h 
    8. Threshold optimization diatur oleh threshold_index 
    9. Alarm output diatur pada variabel alarm
"""

def dynamic_threshold_optimization(scores, NH=20, rho=0.05, r_H=0.001, lambda_H=0.5):
    """
    Implementasi Dynamic Threshold Optimization (DTO) dalam satu fungsi
    
    Parameters:
    - scores: List skor yang akan dianalisis
    - NH: Jumlah bin histogram (default: 20)
    - rho: Parameter untuk threshold (default: 0.05)
    - r_H: Parameter diskounting (default: 0.001)
    - lambda_H: Parameter estimasi (default: 0.5)
    
    Returns:
    - results: List dictionary berisi hasil untuk setiap sesi
    """
    # Inisialisasi bin
    print(f"scores = {scores}")
    a = np.mean(scores) + 2 * np.std(scores)
    print(f"debug = {np.mean(scores)} dari {scores}")
    filtered_scores = scores[scores > a]
    if filtered_scores.size > 0:
        b = np.min(filtered_scores)
    else:
        b = np.min(filtered_scores)  
    
    print(f"a = {a}")
    print(f"b = {b}")


    bin_edges = [-np.inf, a] + [a + (b - a) / (NH - 2) * i for i in range(NH - 3)] + [np.inf]
    print(bin_edges)
    bin_edges = np.sort(bin_edges)  
    
    histogram = np.ones(NH) / NH
    print(f"histogram awal  = {histogram}")
    results = []
    
    M = len(scores)
    for j in range(M - 1):
        bin_index = np.digitize(scores[j], bin_edges) - 1
        # print(f"bindex = {bin_index} \n")
        
        updated_histogram = np.zeros_like(histogram)
        for h in range(len(histogram)):
            if h == bin_index:
                updated_histogram[h] = (1 - r_H) * histogram[h] + r_H
                # print(f"iterasi {h} || 1 - {r_H} * {histogram[h] + r_H} = {updated_histogram[h]}\n")
            else:
                updated_histogram[h] = (1 - r_H) * histogram[h]
                # print(f"iterasi {h} --- 1 - {r_H} * {histogram[h] + r_H} = {updated_histogram[h]}\n")

        updated_histogram = (updated_histogram + lambda_H) / (np.sum(updated_histogram) + NH * lambda_H)
        # print(updated_histogram)
        histogram = updated_histogram
        # print(f"histo di to = {histogram}")
        cumulative_distribution = np.cumsum(histogram)
        # print(f"cumu_dist = {cumulative_distribution}")
        
        threshold_index = np.argmax(cumulative_distribution >= (1 - rho))
        threshold = bin_edges[threshold_index]
        
        alarm = scores[j] >= threshold
        
        # Simpan hasil
        results.append({
            "Session": j + 1, 
            "Score": scores[j], 
            "Threshold": threshold, 
            "Alarm": alarm
        })
    
    return results
results = dynamic_threshold_optimization(yscore)
print(json.dumps(hasil_agregasi, indent=4))
for result in results:
    if result['Alarm']:
        matching_data = next((item for item in hasil_agregasi if item.get('yscore') == result['Score']), None)

        if matching_data:
            result['Diskrit'] = matching_data['diskrit']
            result['Waktu_Awal'] = matching_data['waktu_awal']
            result['Waktu_Akhir'] = matching_data['waktu_akhir']
waktu_awal = ""
waktu_akhir = ""
for result in results:
    print(f"Sesi {result['Session']}: Skor {result['Score']}, Threshold {result['Threshold']}, Alarm {result['Alarm']}")
    if 'Diskrit' in result:
        waktu_awal = result['Waktu_Awal']
        waktu_akhir = result['Waktu_Akhir']
        print(f"Diskrit {result['Diskrit']} | Waktu Awal: {result['Waktu_Awal']} | Waktu Akhir: {result['Waktu_Akhir']}")
        print("\n")

connections = create_connection()
cursors = connections.cursor()

query = f"SELECT full_text FROM data_preprocessed WHERE created_at BETWEEN '{waktu_awal}' AND '{waktu_akhir}'"
cursors.execute(query)

hasil_twitt_trending = cursors.fetchall()
with open('hasil_twitt_trending.json', 'w') as file:
    json.dump(hasil_twitt_trending, file)