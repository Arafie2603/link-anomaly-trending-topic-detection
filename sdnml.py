import numpy as np

# Definisi bobot untuk setiap diskrit
weights = np.array([0.9, 0.09, 0.009, 0.0009, 0.00009])  

# Data skor agregasi dari setiap diskrit
aggregation_scores = np.array([0.8, 0.43, 1.01, 1.07, 1.44])

# Membentuk hasil matriks V_t untuk setiap bobot
V_t_list = []  # List untuk menyimpan semua matriks V_t

for weight in weights:
    # Membentuk vektor x_t
    x_t = weight * aggregation_scores

    # Membentuk matriks V_t dengan perkalian vektor x_t dan x_t^T
    V_t = np.outer(x_t, x_t)
    V_t_list.append(V_t)  # Menyimpan matriks V_t ke dalam list

# Menampilkan hasil untuk setiap V_t
for idx, V_t in enumerate(V_t_list, start=1):
    print(f"Hasil Matriks V_t untuk Bobot w{idx} (Vt{idx}):")
    for row in V_t:
        print("\t".join(f"{value:.5f}" for value in row))  # Menampilkan setiap baris
    print()  # Ganti baris
