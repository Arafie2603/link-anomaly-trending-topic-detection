import numpy as np

# # Nilai r untuk diskon
# r = 0.9

# # Vektor xt yang diberikan
# xt = np.array([0.5, 1.2, 0.8, 1.5, 1.1])

# # Transpose dari xt untuk memudahkan perkalian matriks
# xt_transposed = xt.reshape(-1, 1)

# # Invers matriks Vt yang diberikan
# V_t_inv = np.array([
#     [4.44e+08, -1.85e+07, 0.0, -3.21e-11, 7.03e-12],
#     [0.0, 7.72e+07, -1.16e+07, 1.34e-10, -1.67e-11],
#     [0.0, 0.0, 1.74e+08, -9.26e+06, 0.0],
#     [0.0, 0.0, 0.0, 4.94e+07, -6.73e+06],
#     [0.0, 0.0, 0.0, 0.0, 9.18e+07]
# ])

# # Menghitung perkalian matriks V_t^-1 * xt
# V_t_inv_xt = V_t_inv @ xt
# print(V_t_inv_xt)
# print(xt_transposed.T)
# # Menghitung XTt * V_t^-1 * xt
# result = xt_transposed.T @ V_t_inv_xt

# # Skalar Ct = r * hasil dari perkalian di atas
# C_t = r * result

# print("Perkalian matriks (xt^T * V_t^-1 * xt):")
# print(result)

# print("Nilai Ct setelah dikalikan dengan r:")
# print(C_t)
"""--- Menghitung 𝑉_(𝑡−1)^(−1) 𝑥_𝑡 𝑥_𝑡^𝑇 𝑉_𝑡^(−1) ------"""
# import numpy as np

# # Matriks Vt^(-1) yang diberikan
# V_t_inv = np.array([
#     [4.44e+08, -1.85e+07, 0, -3.21e-11, 7.03e-12],
#     [0, 7.72e+07, -1.16e+07, 1.34e-10, -1.67e-11],
#     [0, 0, 1.74e+08, -9.26e+06, 0],
#     [0, 0, 0, 4.94e+07, -6.73e+06],
#     [0, 0, 0, 0, 9.18e+07]
# ])

# # Matriks V_t^(-1) * x_t * x_t^T yang diberikan
# V_t_inv_x_t_x_t_T = np.array([
#     [9.99e+13, 2.40e+14, 1.60e+14, 3.00e+14, 2.20e+14],
#     [4.17e+13, 1.00e+14, 6.67e+13, 1.25e+14, 9.17e+13],
#     [6.27e+13, 1.50e+14, 1.00e+14, 1.88e+14, 1.38e+14],
#     [3.33e+13, 8.00e+13, 5.34e+13, 1.00e+14, 7.34e+13],
#     [5.05e+13, 1.21e+14, 8.08e+13, 1.51e+14, 1.11e+14]
# ])

# # Mengalikan matriks V_t_inv_x_t_x_t_T dengan V_t_inv
# result_final = np.dot(V_t_inv_x_t_x_t_T, V_t_inv)

# # Menampilkan hasil akhir
# print(result_final)


# import numpy as np

# # r, 1-r, dan Ct
# r = 0.9
# one_minus_r = 1 - r
# Ct = 4.6017315e+08  # As previously calculated

# # V_t^(-1) * x_t * x_t^T * V_t^(-1), pembilang
# numerator = np.array([
#     [9.99e+13, 2.40e+14, 1.60e+14, 3.00e+14, 2.20e+14],
#     [4.17e+13, 1.00e+14, 6.67e+13, 1.25e+14, 9.17e+13],
#     [6.27e+13, 1.50e+14, 1.00e+14, 1.88e+14, 1.38e+14],
#     [3.33e+13, 8.00e+13, 5.34e+13, 1.00e+14, 7.34e+13],
#     [5.05e+13, 1.21e+14, 8.08e+13, 1.51e+14, 1.11e+14]
# ])

# # Calculate denominator
# denominator = numerator / one_minus_r + Ct

# # Print denominator
# print(denominator)
# import numpy as np

# # Definisi matriks dan nilai
# V_t_inv = np.array([
#     [4.44e+09, -1.85e+08, 0, -3.21e-10, 7.03e-11],
#     [0, 771604938, -115740741, 1.33852e-09, -1.67315e-10],
#     [0, 0, 1736111110, -92592592.6, 0],
#     [0, 0, 0, 493827160, -67340067.3],
#     [0, 0, 0, 0, 918273646]
# ])
# numerator_adjusted = np.array([
#     [9.99e+22, 2.40e+23, 1.60e+23, 3.00e+23, 2.20e+23],
#     [4.17e+22, 1.00e+23, 6.67e+22, 1.25e+09, 9.17e+22],
#     [6.27e+22, 1.50e+23, 1.00e+23, 1.88e+23, 1.38e+23],
#     [3.33e+22, 8.00e+22, 5.34e+22, 1.00e+23, 7.34e+22],
#     [5.05e+22, 1.21e+23, 8.08e+22, 1.51e+23, 1.11e+23]
# ])
# Ct = 4.6017315e+08
# one_minus_r = 0.1

# # Perhitungan
# denominator = one_minus_r + Ct
# second_term = (numerator_adjusted / denominator) * (-9)
# V_t_minus_1_inv = V_t_inv + second_term

# # Output
# print("Updated inverse matrix V_{t-1}^{-1} is:\n", V_t_minus_1_inv)


"""----- Hitung Estimasi Koefisien AR -----"""
import numpy as np

# Matriks invers yang diperbarui dari hasil Sherman-Morrison-Woodbury
V_t_minus_1_inv = np.array([
    [-1.95e+23, -4.69e+23, -3.13e+23, -5.87e+23, -4.30e+23],
    [-8.16e+22, -1.96e+23, -1.30e+23, -2.44e+09, -1.79e+23],
    [-1.23e+23, -2.93e+23, -1.96e+23, -3.68e+23, -2.70e+23],
    [-6.51e+22, -1.56e+23, -1.04e+23, -1.96e+23, -1.44e+23],
    [-9.88e+22, -2.37e+23, -1.58e+23, -2.95e+23, -2.17e+23]
])

# Vektor respon hipotetis
r_t = np.array([0.45, 0.108, 0.0072, 0.00135, 0.0000999])

# Menghitung estimasi koefisien AR
a_t_hat = np.dot(V_t_minus_1_inv, r_t)

print("Estimasi koefisien AR (a_t_hat) adalah:", a_t_hat)
