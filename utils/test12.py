import numpy as np

# Nilai skor
second_scores = [23.025850929940457, -6.398336724694618, -6.362778510083174, 
                 -6.806198891185467, -6.647921838748839, -6.7787344105298155, 
                 -6.0544346931294495, -6.541114644102221, -6.679299661102484, 
                 -6.902605915476471, -6.185877679866674, -6.449303053142949, 
                 -6.584217998410003]
def initialize_bins(scores, NH=20):
    """
    Initialize histogram bins.
    Parameters:
    scores: List or array of scores (input data).
    NH: Number of bins in the histogram.
    Returns:
    bins: The edges of the histogram bins.
    """
    a = np.mean(scores) + 3 * np.std(scores)  # Average + 3σ
    # print(f"")
    b = np.min(scores)  # Minimum of the data
    bin_edges = [-np.inf] + [b + (a - b) / (NH - 2) * i for i in range(NH - 2)] + [np.inf]
    print(bin_edges)
    return bin_edges, a, b

def initialize_histogram(NH=20):
    """
    Initialize a uniform histogram.
    Parameters:
    NH: Number of bins in the histogram.
    Returns:
    histogram: A uniform histogram array.
    """
    return np.ones(NH) / NH

def update_histogram(histogram, bins, score, r_H=0.001, lambda_H=0.5):
    """
    Update histogram mengikuti algoritma DTO lebih ketat
    """
    # print(f"bins = {bins}")
    # print(f"score = {score}")
    bin_index = np.digitize(score, bins) - 1
    # print(bin_index)
    
    # Inisialisasi histogram baru dengan metode kondisional
    updated_histogram = np.zeros_like(histogram)
    # print(f"histogram = {histogram}")
    # print(f"updated histogram = {updated_histogram}")
    
    for h in range(len(histogram)):
        # print(f"h = {bin_index}")
        
        # print(f"indeks -{h}")
        if h == bin_index:
            updated_histogram[h] = (1 - r_H) * histogram[h] + r_H
            # print(f"kondisi true = {updated_histogram[h]}")
        else:
            updated_histogram[h] = (1 - r_H) * histogram[h]
            # print(f"false = {updated_histogram[h]}")
    
    # Normalisasi dengan λ_H
    updated_histogram = (updated_histogram + lambda_H) / (np.sum(updated_histogram) + len(histogram) * lambda_H)
    
    return updated_histogram

def optimize_threshold(histogram, bins, rho=0.05):
    """
    Optimize the threshold based on the histogram.
    Parameters:
    histogram: Current histogram.
    bins: Bin edges of the histogram.
    rho: Tail probability threshold.
    Returns:
    threshold: The optimized threshold for anomaly detection.
    """
    cumulative_distribution = np.cumsum(histogram)
    threshold_index = np.argmax(cumulative_distribution >= (1 - rho))
    return bins[threshold_index]

def process_session(scores, NH=20, rho=0.05, r_H=0.001, lambda_H=0.5):
    """
    Process all sessions and calculate alarms and thresholds.
    Parameters:
    scores: List or array of anomaly scores.
    NH: Number of bins in the histogram.
    rho: Tail probability threshold.
    r_H: Discounting factor.
    lambda_H: Regularization parameter for smoothing.
    Returns:
    results: List of dictionaries containing session details.
    """
    bins, a, b = initialize_bins(scores, NH)
    histogram = initialize_histogram(NH)
    # print(histogram)
    results = []

    for i, score in enumerate(scores):
        histogram = update_histogram(histogram, bins, score, r_H, lambda_H)
        threshold = optimize_threshold(histogram, bins, rho)
        alarm = score >= threshold
        print(f"{score} >= {threshold} = {alarm}")
        results.append({"Session": i + 1, "Score": score, "Threshold": threshold, "Alarm": alarm})
    
    return results
results = process_session(second_scores)
# def initialize_histogram(NH=20, lambda_H=0.5):
#     """
#     Inisialisasi histogram awal
    
#     Parameters:
#     - NH: Jumlah total sel dalam histogram
#     - lambda_H: Parameter estimasi
    
#     Returns:
#     - q_1: Histogram awal
#     - q: Histogram terdiskonto
#     """
#     q_1 = np.ones(NH) / NH
#     q = np.ones(NH) / NH
#     return q_1, q

# def find_bin_index(score, NH=20, min_score=None, max_score=None):
#     """
#     Temukan indeks bin untuk skor tertentu
    
#     Parameters:
#     - score: Skor untuk ditempatkan
#     - NH: Jumlah total sel
#     - min_score: Batas bawah skor (jika None, akan dihitung dari data)
#     - max_score: Batas atas skor (jika None, akan dihitung dari data)
    
#     Returns:
#     - Indeks bin yang sesuai
#     """
#     # Tangani kasus NaN
#     if np.isnan(score):
#         return 0  # Kembalikan indeks bin pertama untuk NaN
    
#     # Jika min/max_score tidak ditentukan, gunakan skor itu sendiri
#     if min_score is None:
#         min_score = score
#     if max_score is None:
#         max_score = score
    
#     # Pastikan min_score <= max_score
#     min_score, max_score = min(min_score, max_score), max(min_score, max_score)
    
#     # Hitung lebar bin
#     bin_width = (max_score - min_score) / (NH - 2) if NH > 2 else 1
    
#     # Tentukan bin berdasarkan skor
#     if score < min_score:
#         return 0
#     elif score >= max_score:
#         return NH - 1
#     else:
#         bin_index = int((score - min_score) / bin_width) + 1
#         return bin_index

# def update_histogram(q_1, q, score, r_H=0.001, lambda_H=0.5, NH=20, min_score=None, max_score=None):
#     """
#     Update histogram berdasarkan skor
    
#     Parameters:
#     - q_1: Histogram sebelumnya
#     - q: Histogram terdiskonto sebelumnya
#     - score: Skor anomali
#     - r_H: Parameter diskonto
#     - lambda_H: Parameter estimasi
#     - NH: Jumlah total sel
#     - min_score: Batas bawah skor (opsional)
#     - max_score: Batas atas skor (opsional)
    
#     Returns:
#     - q_1_updated: Histogram yang diperbarui
#     - q_updated: Histogram terdiskonto yang diperbarui
#     """
#     # Temukan bin yang sesuai untuk skor
#     bin_index = find_bin_index(score, NH, min_score, max_score)
    
#     # Salin histogram
#     q_1_updated = q_1.copy()
    
#     # Update histogram dengan aturan diskonto
#     for h in range(NH):
#         if h == bin_index:
#             # Bin dengan skor yang sama
#             q_1_updated[h] = (1 - r_H) * q_1_updated[h] + r_H
#         else:
#             # Bin lainnya
#             q_1_updated[h] = (1 - r_H) * q_1_updated[h]
    
#     # Normalisasi histogram
#     q_updated = (q_1_updated + lambda_H) / (np.sum(q_1_updated) + NH * lambda_H)
    
#     return q_1_updated, q_updated

# def compute_threshold(q, rho=0.05, NH=20):
#     """
#     Hitung threshold berdasarkan distribusi histogram
    
#     Parameters:
#     - q: Histogram terdiskonto
#     - rho: Parameter ambang batas
#     - NH: Jumlah total sel
    
#     Returns:
#     - Nilai threshold
#     """
#     # Hitung kumulatif probabilitas dari histogram
#     cumulative_prob = np.cumsum(q)
    
#     # Temukan threshold yang memenuhi kondisi
#     for i in range(NH):
#         if cumulative_prob[i] >= 1 - rho:
#             return i  # Indeks bin sebagai threshold
    
#     return NH - 1  # Default ke bin terakhir

# def detect_anomaly(score, threshold):
#     """
#     Deteksi anomali berdasarkan skor
    
#     Parameters:
#     - score: Skor yang akan diperiksa
#     - threshold: Threshold yang digunakan
    
#     Returns:
#     - Boolean apakah merupakan anomali
#     """
#     return score >= threshold

# def dynamic_threshold_optimization(scores, 
#                                    NH=20, 
#                                    rho=0.05, 
#                                    lambda_H=0.5, 
#                                    r_H=0.001):
#     """
#     Fungsi utama untuk Dynamic Threshold Optimization
    
#     Parameters:
#     - scores: Daftar skor anomali
#     - NH: Jumlah total sel dalam histogram
#     - rho: Parameter ambang batas
#     - lambda_H: Parameter estimasi
#     - r_H: Parameter diskonto
    
#     Returns:
#     - anomalies: Daftar boolean anomali
#     - thresholds: Daftar threshold
#     """
#     # Inisialisasi histogram
#     q_1, q = initialize_histogram(NH, lambda_H)
    
#     # Tentukan min dan max score untuk normalisasi
#     min_score = np.nanmin(scores)
#     max_score = np.nanmax(scores)
    
#     # Variabel untuk menyimpan hasil
#     anomalies = []
#     thresholds = []
    
#     # Proses setiap skor
#     for score in scores:
#         # Update histogram
#         q_1, q = update_histogram(
#             q_1, q, score, r_H, lambda_H, NH, 
#             min_score, max_score
#         )
        
#         # Hitung threshold
#         threshold = compute_threshold(q, rho, NH)
#         thresholds.append(threshold)
        
#         # Deteksi anomali
#         is_anomaly = detect_anomaly(score, threshold)
#         anomalies.append(is_anomaly)
    
#     return anomalies, thresholds

# def example_usage():
#     """
#     Contoh penggunaan Dynamic Threshold Optimization
#     """
#     # Data contoh (skor anomali) dengan NaN
#     anomaly_scores = [23.025850929940457, -6.398336724694618, -6.362778510083174, 
#                  -6.806198891185467, -6.647921838748839, -6.7787344105298155, 
#                  -6.0544346931294495, -6.541114644102221, -6.679299661102484, 
#                  -6.902605915476471, -6.185877679866674, -6.449303053142949, 
#                  -6.584217998410003]
    
#     # Jalankan optimasi threshold dinamis
#     anomalies, thresholds = dynamic_threshold_optimization(anomaly_scores)
    
#     # Cetak hasil
#     for j, (score, threshold, is_anomaly) in enumerate(
#         zip(anomaly_scores, thresholds, anomalies)
#     ):
#         print(f"Sesi {j}: Skor={score}, Threshold={threshold}, Anomali={is_anomaly}")
    
#     print("\nAnomalies:", anomalies)
#     print("Thresholds:", thresholds)
# # for result in results:
# #     print(result)
# example_usage()