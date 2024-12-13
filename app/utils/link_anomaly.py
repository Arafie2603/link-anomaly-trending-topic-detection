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
def hitung_mention_tiap_id(target_id, tweets_data):
    temp_mentions = []  # List untuk menyimpan semua mention yang pernah muncul
    temp_pmention = []
    m = 0  # Total mention dalam dataset
    y = 0.5  # Parameter y
    pmention = []  # Probabilitas mention dalam bentuk list jika ada lebih dari satu

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
            if tweet['jumlah_mention'] > 1:
                for mention in mentions_list:
                    mu = temp_mentions.count(mention)
                    if mu == 0:
                        p = y / (m + y)
                    else:
                        p = mu / (m + y)
                    temp_pmention.append(p)
                pmention.extend(temp_pmention)  # Simpan nilai probabilitas dalam bentuk list
            else:
                mention = mentions_list[0]
                mu = temp_mentions.count(mention)
                if mu == 0:
                    pmention.append(y / (m + y))
                else:
                    pmention.append(mu / (m + y))

        # Tambahkan mention baru ke `temp_mentions` setelah memproses tweet ini
        temp_mentions.extend(mentions_list)

    return pmention

def hitung_probabilitas_user(tweets):
    for row in tweets:
        pmention = hitung_mention_tiap_id(row['id'], tweets)
        for item in hasil_perhitungan:
            if item['id'] == row['id']:
                item['probabilitas_user'] = pmention  # Simpan list probabilitas

    return hasil_perhitungan

hasil_probabilitas_user = hitung_probabilitas_user(tweets_data)
print('---------- Hitung Skor Anomaly ----------')
# print(json.dumps(hasil_perhitungan, indent=4))
def hitung_skor_anomaly(hasil):
    for skor in hasil:
        nilai_mention = skor['probabilitas_mention']
        nilai_user_list = skor['probabilitas_user']

        # Hitung skor anomaly untuk setiap item
        for item in hasil_perhitungan:
            if item['id'] == skor['id']:
                if isinstance(nilai_user_list, list):
                    # Hitung log dari semua probabilitas dalam list
                    log_user = sum(-math.log10(user) for user in nilai_user_list)
                else:
                    log_user = -math.log10(nilai_user_list)
                
                skor_anomaly = -math.log10(nilai_mention) + log_user
                item['skor_anomaly'] = skor_anomaly
# print(hasil_perhitungan)
hitung_skor_anomaly(hasil_perhitungan)


hasil_agregasi = []
def hitung_skor_agregasi(hasil_skor):
    waktu_awal_string = hasil_skor[0]['created_at']
    waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")

    window_r = timedelta(hours=24)  
    jumlah_diskrit = 40  

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

"""
r = 0.0005
# print(json.dumps(hasil_agregasi, indent=4))
aggregation_scores = np.array([entry["s_x"] for entry in hasil_agregasi])
print(f"agregasi = {aggregation_scores}")

x_t = aggregation_scores


def create_X_t(x_t, order):
    n = len(x_t)
    X_t = np.zeros((n - order, order))
    for t in range(order, n):
        X_t[t - order] = x_t[t - order:t][::-1]
    return X_t

# Bentuk X_t berdasarkan data x_t
order = 3 
m = 0
X_t = create_X_t(x_t, order=order)
print(f"Nilai x_bar_t = {X_t}")

# Inisialisasi matriks V0 dan M0
V0 = np.identity(order)
M0 = np.zeros(order)
# print(M0)
# Fungsi untuk memperbarui V_t dan M_t dengan identitas Sherman-Morrison-Woodbury
def update_matrices(V_prev_inv, M_prev, x_t, xt):
    x_t = x_t[:, np.newaxis] 
    c_t = r * x_t.T @ V_prev_inv @ x_t
    V_t = (1 / (1 - r)) * V_prev_inv - (r / (1 - r)) * (V_prev_inv @ np.outer(x_t, x_t) @ V_prev_inv) / (1 - r + c_t)
    M_t = (1 - r) * M_prev + r * x_t.flatten() * xt
    # print(f"--- perhitungan Vt ---")
    # print(M_t)
    # print(V_t)
    # print("----------")
    # print("\n")
    return V_t, M_t, c_t.item()

V_inv = V0
# print(V_inv)
M = M0
d_t = []

for t in range(len(X_t)):
    V_inv, M, c_t = update_matrices(V_inv, M, X_t[t], x_t[t + order])
    d_t_value = c_t / (1 - r + c_t)  
    d_t.append(d_t_value)
    # print(V_inv)

V = V_inv

A_t = np.dot(V, M)
# print(A_t)
print("--- d_t")
print(d_t)
# Hitung residuals (sisa) e_t
e_t = [x_t[i + order] - np.dot(A_t, X_t[i]) for i in range(len(X_t))]
print("--- e_t ---")
print(x_t[0 + 3])
print(e_t)
tau_t = [(1 / (i - m)) * sum([e_t[j]**2 for j in range(m+1, i + 1)]) for i in range(m+1, len(X_t))]
print(len(tau_t))
print(len(X_t))
print("--- tau_t ---")
print(tau_t)
length_st = len(X_t) - (order+1)
s_t = [(i - m) * tau_t[i] for i in range(m+1, length_st)]
print("--- s_t ---")
print(length_st)
print(len(s_t))
print(s_t)
K_t = [np.sqrt(np.pi) / (1 - d_t[i]) * gamma((i+1 - m - 1) / 2) / gamma((i+1 - m) / 2) for i in range(m+1, len(d_t))]
# K_t = [np.sqrt(np.pi) / (1 - d_t[i]) * gamma((i - m - 1) / 2) / gamma((i - m) / 2) for i in range(m+1, len(d_t) - 1)]
print("--- K_t ---")
print(K_t)
length_firstLayer = length_st - (order+1)
p_SDNML = [K_t[i]**-1 * (s_t[i]**(-(i+1 - m) / 2) / s_t[i - 1]**(-(i+1 - m - 1) / 2)) for i in range(m+1, length_firstLayer)]
# p_SDNML = [K_t[i]**-1 * (s_t[i]**(-(i - m) / 2) / s_t[i - 1]**(-(i - m - 1) / 2)) for i in range(1, len(s_t))]
print("--- psdnml ---")
print((s_t[1]**(-(t - m) / 2) / s_t[1 - 1]**(-(t - m - 1) / 2)))
print(p_SDNML)

log_p_SDNML = [
    -np.log(np.abs(p_SDNML[i])) 
    for i in range(len(p_SDNML))
]
print("--- first score stage ---")
print(log_p_SDNML)

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
        smoothed_scores.append(smoothed_score)
    return smoothed_scores


# Hitung first score berdasarkan panjang kode SDNML
# print("--- First layer scoring -----")
first_scores = []
for t in range(len(log_p_SDNML)):
        score = log_p_SDNML[t]
        first_scores.append(score)
        # print(f"Panjang kode SDNML untuk x_{t + 1}: {score}")
print(first_scores)
T = 3  
smoothed_scores = apply_smoothing(first_scores, T)
print("--- smoothed scores ---")
print(smoothed_scores)

X_t_second = create_X_t(smoothed_scores, order=order)
x_t_second = smoothed_scores
V0_second = np.identity(order)
M0_second = np.zeros(order)

V_inv_second = V0_second
M_second = M0_second
# print(x_t_second)
d_t_second = []
for t in range(len(X_t_second)):
    V_inv_second, M_second, c_t_second = update_matrices(V_inv_second, M_second, X_t_second[t], x_t[t + order])
    d_t_value = c_t_second / (1 - r + c_t_second)
    d_t_second.append(d_t_value)

print("--- d_t second ---")
print()
print(d_t_second)
print("--- score layer ---")
A_t_second = np.dot(V_inv_second, M_second)
# print(A_t_second)
e_t_second = [x_t_second[i + order] - np.dot(A_t_second, X_t_second[i]) for i in range(len(X_t_second))]
print("--- et second ---")
print(len(e_t_second))
print(e_t_second)

tau_t_second = [(1 / (i - m)) * sum([e_t_second[j]**2 for j in range(m+1, i+1)]) for i in range(m+1, len(X_t_second))]
print("--- tau_t_second ---")
print(tau_t_second)

length_st_second = len(X_t_second) - (order+1)
s_t_second = [(i - m) * tau_t_second[i] for i in range(m+1, length_st_second)]
print("--- s_t_second ---")

print(s_t_second)
K_t_second = [np.sqrt(np.pi) / (1 - d_t_second[i]) * gamma((i+1 - m - 1) / 2) / gamma((i+1 - m) / 2) for i in range(m+1, len(d_t_second))]
print("--- kt_second ---")
# print(d_t_second[4])
# print(np.sqrt(np.pi) / (1 - d_t_second[4]) * gamma((t - m - 1) / 2) / gamma((t - m) / 2))
print(K_t_second)
length_firstLayer_second = length_st_second - (order+1)
p_SDNML_second = [K_t_second[i]**-1 * (s_t_second[i]**(-(i+1 - m) / 2) / s_t_second[i - 1]**(-(i+1 - m - 1) / 2)) for i in range(m+1, length_firstLayer_second)]
print("--- second layer learn ---")
print(p_SDNML_second)
log_p_SDNML_second = [
    -np.log(np.abs(p_SDNML_second[i])) 
    for i in range(len(p_SDNML_second))
]

print("--- second score stage ---")
print(p_SDNML_second[0])
print(-np.log(np.abs(p_SDNML_second[0])) )
print(log_p_SDNML_second)


second_scores = log_p_SDNML_second
print("--- smoothed score ---")
smoothed_scores_second = apply_smoothing(second_scores, T)
print(smoothed_scores_second)


def initialize_bins(scores, NH):
    a = np.mean(scores) + 2 * np.std(scores)  
    b = np.min(scores)  
    bin_edges = [-np.inf] + [b + (a - b) / (NH - 2) * i for i in range(NH - 2)] + [np.inf]
    print(bin_edges)
    return bin_edges, a, b

def initialize_histogram(NH):
    return np.ones(NH) / NH

def update_histogram(histogram, bins, score, r_H, lambda_H):
    bin_index = np.digitize(score, bins) - 1
    updated_histogram = np.zeros_like(histogram)

    for h in range(len(histogram)):
        if h == bin_index:
            updated_histogram[h] = (1 - r_H) * histogram[h] + r_H
        else:
            updated_histogram[h] = (1 - r_H) * histogram[h]
    updated_histogram = (updated_histogram + lambda_H) / (np.sum(updated_histogram) + len(histogram) * lambda_H)
    
    return updated_histogram

def optimize_threshold(histogram, bins, rho):
    cumulative_distribution = np.cumsum(histogram)
    threshold_index = np.argmax(cumulative_distribution >= (1 - rho))
    return bins[threshold_index]

def process_session(scores, NH=20, rho=0.05, r_H=0.001, lambda_H=0.5):
    bins, a, b = initialize_bins(scores, NH)
    histogram = initialize_histogram(NH)
    results = []

    for i, score in enumerate(scores):
        histogram = update_histogram(histogram, bins, score, r_H, lambda_H)
        threshold = optimize_threshold(histogram, bins, rho)
        alarm = score >= threshold
        print(f"{score} >= {threshold} = {alarm}")
        results.append({"Session": i + 1, "Score": score, "Threshold": threshold, "Alarm": alarm})
    
    return results
results = process_session(second_scores)
        
# print(json.dumps(hasil_agregasi, indent=4))
print(second_scores)
print(f"std = {np.std(second_scores)}")
