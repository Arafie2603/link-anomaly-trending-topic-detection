# import numpy as np

# # Matriks Vt yang diberikan
# V_t = np.array([
#     [0.225, 0.054, 0.0036, 0.000675, 0.0000495],
#     [0, 1.296, 0.0864, 0.0162, 0.001188],
#     [0, 0, 0.576, 0.108, 0.00792],
#     [0, 0, 0, 2.025, 0.1485],
#     [0, 0, 0, 0, 1.089]
# ])

# # Menghitung invers dari Vt
# V_t_inv = np.linalg.inv(V_t)

# # Menampilkan hasil
# print("Invers dari Vt adalah:")
# print(V_t_inv)

# # Verifikasi hasil dengan mengalikan Vt dan V_t_inv
# identity_matrix = np.dot(V_t, V_t_inv)
# print("Hasil kali Vt dengan inversnya (harus mendekati matriks identitas):")
# print(identity_matrix)
# import numpy as np

# # Contoh V_t^-1
# V_t_inv = np.array([
#     [4.44e+08, -1.85e+07, 0, -3.21e-11, 7.03e-12],
#     [0, 7.72e+07, -1.16e+07, 1.34e-10, -1.67e-11],
#     [0, 0, 1.74e+08, -9.26e+06, 0],
#     [0, 0, 0, 4.94e+07, -6.73e+06],
#     [0, 0, 0, 0, 9.18e+07]
# ])

# # Vektor u dan v
# u = np.array([0.5, 1.2, 0.8, 1.5, 1.1])
# v = np.array([0.45, 0.108, 0.0072, 0.00135, 0.000099])

# # Menghitung V_t^-1 u dan v^T V_t^-1
# Vu = np.dot(V_t_inv, u)
# vVu = np.dot(v, Vu)

# # Menghitung pembilang
# numerator = np.outer(Vu, Vu)

# # Menghitung V_{t-1}^-1
# alpha = 1 / (1 - vVu)
# V_t_minus_1_inv = V_t_inv + alpha * numerator

# print("V_{t-1}^{-1} calculated from V_t^{-1}:")
# print(V_t_minus_1_inv)
# Suposición de datos ya definidos, redefino para claridad en el ejemplo
import numpy as np

# Definisi data secara lokal
# vt_invers_xtXTt = np.array([
#     [9.99E+13,	2.40E+14,	1.60E+14,	3.00E+14,	2.20E+14],
#     [4.17E+13,	1.00E+14,	6.67E+13,	1.25E+14,	9.17E+13],
#     [6.27E+1,	1.50E+14,	1.00E+14,	1.88E+14,	1.38E+14],
#     [3.33E+13,	8.00E+13,	5.34E+13,	1.00E+14,	7.34E+13],
#     [5.05E+13,	1.21E+14,	8.08E+13,	1.51E+14,	1.11E+14]
# ])

# vt_invers = np.array([
#     [4.44E+08,	-1.85E+07,	0,	-3.21E-11,	7.03E-12],
#     [0, 7.72E+07,	-1.16E+07,	1.34E-10,	-1.67E-11],
#     [0, 0,	1.74E+08,	-9.26E+06,	0],
#     [0, 0,	0,	4.94E+07,	-6.73E+06],
#     [0, 0,	0,	0,	9.18E+07]
# ])

# # Perhitungan
# result = vt_invers_xtXTt @ vt_invers
# print(result)
# import numpy as np

# # Diasumsikan nilai-nilai ini telah dihitung dengan benar
# V_t_inv_x_t_x_t_T_V_t_inv = np.array([
#     [4.44E+09, -1.85E+08, 0, -3.21E-10, 7.03E-11],
#     [0, 7.71604938E+08, -1.15740741E+08, 1.33852E-09, -1.67315E-10],
#     [0, 0, 1.73611111E+09, -9.2592592E+07, 0],
#     [0, 0, 0, 4.9382716E+08, -6.7340067E+07],
#     [0, 0, 0, 0, 9.18273646E+08]
# ])

# C_t = 4.6E+08
# r = 0.9

# # Menghitung penyebut
# denominator = 1 - r + C_t

# # Menghitung hasil akhir
# final_result = V_t_inv_x_t_x_t_T_V_t_inv / denominator
# print("Hasil Akhir:")
# print(final_result)
# import numpy as np

# Diasumsikan nilai-nilai ini telah didefinisikan dengan benar
# r = 0.9
# V_t_inv = np.array([
#     [4.44e+08, -1.85e+07, 0.0, -3.21e-11, 7.03e-12],
#     [0.0, 7.72e+07, -1.16e+07, 1.34e-10, -1.67e-11],
#     [0.0, 0.0, 1.74e+08, -9.26e+06, 0.0],
#     [0.0, 0.0, 0.0, 4.94e+07, -6.73e+06],
#     [0.0, 0.0, 0.0, 0.0, 9.18e+07]
# ])

# x_t = np.array([0.25, 0.6, 0.4, 0.75, 0.55])

# # Menghitung x_t^T * V_t^-1 * x_t
# c_t = r * np.dot(x_t, V_t_inv @ x_t)

# # Menghitung 1/(1-r) * V_t^-1
# part_one = (1 / (1 - r)) * V_t_inv

# # Menghitung (r/(1-r)) * (V_t^-1 * x_t * x_t^T * V_t^-1) / (1 - r + c_t)
# x_t_x_t_T = np.outer(x_t, x_t)
# V_t_inv_x_t_x_t_T_V_t_inv = V_t_inv @ x_t_x_t_T @ V_t_inv
# part_two = (r / (1 - r)) * (V_t_inv_x_t_x_t_T_V_t_inv) / (1 - r + c_t)

# # Menggabungkan kedua bagian untuk mendapatkan V_t^-1 yang diperbarui
# V_t_inv_updated = part_one - part_two

# print("V_t^-1 yang diperbarui:")
# print(V_t_inv_updated)


# import numpy as np

# # Contoh V_t^-1
# V_t_inv = np.array([
#     [4.44e+08, -1.85e+07, 0.0, -3.21e-11, 7.03e-12],
#     [0.0, 7.72e+07, -1.16e+07, 1.34e-10, -1.67e-11],
#     [0.0, 0.0, 1.74e+08, -9.26e+06, 0.0],
#     [0.0, 0.0, 0.0, 4.94e+07, -6.73e+06],
#     [0.0, 0.0, 0.0, 0.0, 9.18e+07]
# ])

# r = 0.9  # Faktor diskon

# # Menghitung 1/(1-r) * V_t^-1
# V_t_inv_scaled = (1 / (1 - r)) * V_t_inv

# print("V_t^-1 yang diperbarui dengan skala 1/(1-r):")
# print(V_t_inv_scaled)

# import numpy as np

# # Diasumsikan nilai-nilai ini telah didefinisikan dengan benar
# r = 0.9
# V_t_inv = np.array([
#     [4.44e+08, -1.85e+07, 0.0, -3.21e-11, 7.03e-12],
#     [0.0, 7.72e+07, -1.16e+07, 1.34e-10, -1.67e-11],
#     [0.0, 0.0, 1.74e+08, -9.26e+06, 0.0],
#     [0.0, 0.0, 0.0, 4.94e+07, -6.73e+06],
#     [0.0, 0.0, 0.0, 0.0, 9.18e+07]
# ])

# x_t = np.array([0.25, 0.6, 0.4, 0.75, 0.55])  # Vektor observasi baru

# # Menghitung c_t
# c_t = r * np.dot(x_t, V_t_inv @ x_t)
# print(c_t)

# # Menghitung V_t_inv * x_t * x_t^T * V_t_inv
# x_t_x_t_T = np.outer(x_t, x_t)
# V_t_inv_x_t_x_t_T_V_t_inv = V_t_inv @ x_t_x_t_T @ V_t_inv

# # Menghitung pengurangan
# adjustment = - (r / (1 - r)) * (V_t_inv_x_t_x_t_T_V_t_inv / (1 - r + c_t))

# print("Pengurangan yang dihasilkan untuk update V_t^-1:")
# print(adjustment)
import numpy as np

# Nilai r untuk diskon
r = 0.9

# Vektor xt yang diberikan
xt = np.array([0.5, 1.2, 0.8, 1.5, 1.1])

# Transpose dari xt (xt sebagai kolom)
xt_transposed = xt.reshape(-1, 1)

# Invers matriks Vt yang diberikan
V_t_inv = np.array([
    [4.44e+08, -1.85e+07, 0.0, -3.21e-11, 7.03e-12],
    [0.0, 7.72e+07, -1.16e+07, 1.34e-10, -1.67e-11],
    [0.0, 0.0, 1.74e+08, -9.26e+06, 0.0],
    [0.0, 0.0, 0.0, 4.94e+07, -6.73e+06],
    [0.0, 0.0, 0.0, 0.0, 9.18e+07]
])

# Menghitung Ct = r * xt^T * V_t^-1 * xt
C_t = r * np.dot(xt_transposed.T, V_t_inv @ xt)

# Menampilkan hasil C_t
print("Nilai c_t:")
print(C_t)

