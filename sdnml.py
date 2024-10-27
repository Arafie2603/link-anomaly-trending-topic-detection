import numpy as np

# Definisi bobot untuk setiap diskrit
weights = np.array([0.9, 0.09, 0.009, 0.0009, 0.00009])  

# Data skor agregasi dari setiap diskrit
aggregation_scores = np.array([-0.15, -0.52, 0.06, 0.12, 0.49])

# Membentuk hasil matriks V_t untuk setiap bobot
V_t_list = []  # List untuk menyimpan semua matriks V_t

for weight in weights:
    # Membentuk matriks V_t dengan perkalian semua kombinasi
    V_t = np.zeros((5, 5))  # Inisialisasi matriks kosong 5x5
    for i in range(len(aggregation_scores)):
        for j in range(len(aggregation_scores)):
            V_t[i][j] = weight * aggregation_scores[i] * aggregation_scores[j]
    
    V_t_list.append(V_t)  # Menyimpan matriks V_t ke dalam list

# Menampilkan hasil untuk setiap V_t
for idx, V_t in enumerate(V_t_list, start=1):
    print(f"Hasil Matriks V_t untuk Bobot w{idx} (Vt{idx}):")
    for row in V_t:
        print("\t".join(f"{value:.6f}" for value in row))  # Menampilkan setiap baris
    print()  # Ganti baris
