"""
1. Perhitungan Skor Anomaly
- Perhitungan probabilitas mention menggunakan persamaan (3.10)
- Perhitungan probabilitas user menggunakan persamaan (3.11)

"""
import sys
import os

# for adding dependencies to support import export module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.tweets import tweets_data
def hitung_probabilitas(n, m, k):
    alpha = 0.5
    beta = 0.5
    
    hasil = 1.0  

    for i in range(n + 1): 
        if i == 0:
            iterasi = (n + alpha) / (m + k + beta)
        else:
            iterasi = (m + beta + 0) / (n + m + alpha + beta + 0)
        print(f"Hasil iterasi {i}: {iterasi}")
        hasil *= iterasi

    print(f"Hasil akhir: {hasil}")
    return hasil

# Contoh penggunaan
n = 1  
m = 2  
k = 2  

hitung_probabilitas(n, m, k)
