import numpy as np

# Definisi bobot untuk setiap diskrit berdasarkan perhitungan manual sebelumnya
weights = np.array([0.9])

# Data skor agregasi dari setiap diskrit
aggregation_scores = np.array([0.8, 0.43, 1.01, 1.07, 1.44])

# Membentuk vektor x_t (masing-masing nilai skor agregasi dikalikan dengan bobot sesuai diskritnya)
x_t = weights * aggregation_scores

# Membentuk matriks V_t dengan perkalian vektor x_t dan x_t^T
V_t = np.outer(x_t, x_t)

print("Hasil Matriks V_t (5x5):\n", V_t)
