# def hitung_skor_agregasi(hasil_skor):
#     # Pastikan hasil_skor diurutkan berdasarkan waktu
#     hasil_skor_sorted = sorted(hasil_skor, key=lambda x: x['created_at'])
    
#     # Ambil waktu awal dan akhir dari dataset
#     waktu_awal_string = hasil_skor_sorted[0]['created_at']
#     waktu_akhir_string = hasil_skor_sorted[-1]['created_at']
    
#     waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")
#     waktu_akhir_final = datetime.strptime(waktu_akhir_string, "%Y-%m-%d %H:%M:%S")
    
#     # Hitung total durasi dataset
#     total_durasi = waktu_akhir_final - waktu_awal
    
#     # Tetapkan window_r (misalnya 12 jam)
#     window_r = timedelta(hours=12)
    
#     # Hitung jumlah diskrit berdasarkan total durasi dan window
#     jumlah_diskrit = math.ceil(total_durasi.total_seconds() / window_r.total_seconds())
    
#     # Reset waktu awal dan akhir
#     waktu_awal = datetime.strptime(waktu_awal_string, "%Y-%m-%d %H:%M:%S")
#     waktu_akhir = waktu_awal + window_r

#     # Global variable untuk menyimpan hasil agregasi
#     global hasil_agregasi
#     hasil_agregasi = []

#     for index in range(jumlah_diskrit):
#         jml_skor_anomaly = 0  
#         jumlah_mention_agregasi = 0 
#         diskrit_anomaly = []
        
#         for data in hasil_skor:
#             temp_waktu = data['created_at']
#             tweet_waktu = datetime.strptime(temp_waktu, "%Y-%m-%d %H:%M:%S")

#             if waktu_awal <= tweet_waktu < waktu_akhir:
#                 jml_skor_anomaly += data['skor_anomaly']
#                 jumlah_mention_agregasi += data['mentions'] 
#                 diskrit_anomaly.append(data)  

#         # Hindari pembagian dengan nol
#         if window_r.total_seconds() > 0:
#             s_x = (1 / window_r.total_seconds() / 3600) * jml_skor_anomaly  
#         else:
#             s_x = 0

#         # Tambahkan ke hasil agregasi hanya jika ada data
#         if jml_skor_anomaly > 0 or jumlah_mention_agregasi > 0:
#             hasil_agregasi.append({
#                 "diskrit": index + 1, 
#                 "waktu_awal": waktu_awal.strftime('%Y-%m-%d %H:%M:%S'), 
#                 "waktu_akhir": waktu_akhir.strftime('%Y-%m-%d %H:%M:%S'), 
#                 "s_x": s_x,
#                 "jumlah_mention_agregasi": jumlah_mention_agregasi
#             })
        
#         # Update waktu_awal dan waktu_akhir untuk iterasi berikutnya
#         waktu_awal = waktu_akhir
#         waktu_akhir += window_r

#         # Berhenti jika sudah melewati waktu akhir dataset
#         if waktu_awal > waktu_akhir_final:
#             break

#     return hasil_agregasi
# import math
# from datetime import datetime, timedelta

# def hitung_skor_anomaly(hasil):
#     """
#     Menghitung skor anomali untuk setiap item dalam hasil perhitungan.
    
#     Args:
#         hasil (list): Daftar data yang akan dihitung skor anomalinya
#     """
#     print('---------- Hitung Skor Anomaly ----------')
    
#     for skor in hasil:
#         nilai_mention = skor['probabilitas_mention']
#         nilai_user_list = skor['probabilitas_user']

#         # Hitung skor anomaly untuk setiap item
#         for item in hasil_perhitungan:
#             if item['id'] == skor['id']:
#                 # Hitung log probabilitas user
#                 if isinstance(nilai_user_list, list):
#                     # Jika user adalah list, hitung log dari semua probabilitas
#                     log_user = sum(-math.log10(user) for user in nilai_user_list)
#                 else:
#                     # Jika user adalah single value
#                     log_user = -math.log10(nilai_user_list)
                
#                 # Hitung skor anomali
#                 skor_anomaly = -math.log10(nilai_mention) + log_user
#                 item['skor_anomaly'] = skor_anomaly
    
#     return hasil_perhitungan

import numpy as np

# Skor input
# scores = [-22.598203261335065, 7.330221118633201, 5.56778456706762, 4.776498159125967, 4.409077210939798, 4.207411631894919, 3.9901165528634355, 3.844278299839122, 3.7478011843099837, 3.680463349822027, 3.6333896366084883, 3.599039542975687, 3.573486249786621]
scores = [7.069707909406017, 9.26616156651682, 3.923571714498773, 5.00757566807694, 3.6189431728452512,
          7.136553043606244, 4.149777126303692, 3.360341309283678, 2.3911587297636028, 4.5862746576153866,
          3.2766587738212225, 2.4380408469665724, 1.873799341907808, 3.671281128205075, 1.1632881790291878,
          0.928837160110753, 1.11434886128591, 0.13933406219882663, 0.2660348384079981, -0.17043435149162017,
          -0.10619378565631371, -0.07232205413208967, 0.10237497426743841, -0.38954414683551464, 0.248978979431305,
          0.12840900559690197, 0.09528677135383093, 0.00000000000932032, 0.0000000004899432, 0.00000000210312]
print(f"Panjang scores = {len(scores)}")

# Ukuran jendela tetap
T = 5

# Fungsi untuk menghitung nilai rata-rata dari skor dalam jendela berukuran T
def smooth_scores(scores, T):
    smoothed_scores = []
    for i in range(len(scores)):
        if i < T - 1:  # Jika indeks kurang dari T-1, tidak cukup data untuk membuat jendela penuh
            continue
        window = scores[i - T + 1:i + 1]
        print(f"Jendela ke-{i}: {window}")
        avg_score = np.mean(window)
        smoothed_scores.append(avg_score)
    return smoothed_scores

# Pemanggilan pertama
smoothed_scores = smooth_scores(scores, T)

# Menggunakan hasil `smoothed_scores` sebagai input untuk pemanggilan kedua
smoothed_second = smooth_scores(smoothed_scores, T)

# Menampilkan hasil dari pemanggilan pertama
print("\nHasil smoothing pertama:")
for t, y in enumerate(smoothed_scores, start=T):
    print(f"y_{t} = {y}")

# Menampilkan hasil dari pemanggilan kedua
print("\nHasil smoothing kedua:")
for t, y in enumerate(smoothed_second, start=T):
    print(f"y'_{t} = {y}")
