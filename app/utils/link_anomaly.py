import sys
import os
import math
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.special import gamma
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

class LinkAnomalyDetector:
    def __init__(self, db_connection):
        """
        Initialize the Link Anomaly Detector with database connection
        
        Args:
            db_connection: Database connection object
        """
        self.connection = db_connection
        self.tweets_data = []
        self.hasil_perhitungan = []
        self.hasil_agregasi = []

    def fetch_tweets_data(self) -> List[Dict]:
        """Fetch tweets data from database and process it"""
        if self.connection is not None:
            cursor = self.connection.cursor()
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
                self.tweets_data.append(tweet)

            cursor.close()

        # Process datetime objects
        for tweet in self.tweets_data:
            if isinstance(tweet['created_at'], str):
                tweet['created_at'] = datetime.strptime(tweet['created_at'], "%Y-%m-%d %H:%M:%S")
        
        self.tweets_data.sort(key=lambda x: x['created_at'])
        return self.tweets_data

    def hitung_probabilitas_mention(self) -> List[Dict]:
        """Calculate mention probabilities for each tweet"""
        alpha = 0.5
        beta = 0.5
        m = 0

        for i, tweet in enumerate(self.tweets_data):
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

            self.hasil_perhitungan.append({
                "id": tweet['id'],
                "created_at": waktu_str,
                "probabilitas_mention": iterasi,
                "mentions": tweet['jumlah_mention']
            })
        
        return self.hasil_perhitungan

    def hitung_mention_tiap_id(self) -> List[Dict]:
        """Calculate mention probabilities for each user"""
        temp_mentions = []
        mention_list_uji = []
        m = 0
        y = 0.5

        for tweet in self.tweets_data:
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
                    p = y / (m + y) if mu == 0 else mu / (m + y)
                    pmention_list.append(p)
            else:
                pmention_list = []
                mu = temp_mentions.count(mentions_list)
                p = y / (m + y) if mu == 0 else mu / (m + y)
                pmention_list.append(p)
                
            mention_list_uji.extend(mentions_list)

            for hasil in self.hasil_perhitungan:
                if hasil['id'] == tweet['id']:
                    hasil['probabilitas_user'] = pmention_list

        return self.hasil_perhitungan

    def hitung_skor_anomaly(self) -> List[Dict]:
        """Calculate anomaly scores"""
        for skor in self.hasil_perhitungan:
            for item in self.hasil_perhitungan:
                if item['id'] == skor['id']:
                    probabilitas_mention = skor.get('probabilitas_mention', [])
                    probabilitas_user = skor.get('probabilitas_user', [])
                    
                    temp_puser = []
                    if item['mentions'] > 1:
                        temp_puser = [math.log(i) for i in probabilitas_user]
                    else:
                        temp_puser.append(math.log(probabilitas_user[0]))
                    
                    skor_anomaly = -math.log(probabilitas_mention) - sum(temp_puser)
                    item['skor_anomaly'] = skor_anomaly

        return self.hasil_perhitungan

    def hitung_skor_agregasi(self) -> List[Dict]:
        """Calculate aggregation scores"""
        waktu_awal = datetime.strptime(self.hasil_perhitungan[0]['created_at'], "%Y-%m-%d %H:%M:%S")
        waktu_akhir_data = datetime.strptime(self.hasil_perhitungan[-1]['created_at'], "%Y-%m-%d %H:%M:%S")

        window_r = timedelta(hours=24)
        waktu_akhir = waktu_awal + window_r
        total_durasi = (waktu_akhir_data - waktu_awal).total_seconds()
        jumlah_diskrit = int(total_durasi // window_r.total_seconds()) + 1

        for index in range(jumlah_diskrit):
            jml_skor_anomaly = 0
            jumlah_mention_agregasi = 0
            
            for data in self.hasil_perhitungan:
                tweet_waktu = datetime.strptime(data['created_at'], "%Y-%m-%d %H:%M:%S")

                if waktu_awal <= tweet_waktu < waktu_akhir:
                    jml_skor_anomaly += data['skor_anomaly']
                    jumlah_mention_agregasi += data['mentions']
                    
            s_x = (1 / (window_r.total_seconds() / 3600)) * jml_skor_anomaly
            self.hasil_agregasi.append({
                "diskrit": index + 1,
                "waktu_awal": waktu_awal.strftime('%Y-%m-%d %H:%M:%S'),
                "waktu_akhir": waktu_akhir.strftime('%Y-%m-%d %H:%M:%S'),
                "s_x": s_x,
                "jumlah_mention_agregasi": jumlah_mention_agregasi
            })
            
            waktu_awal = waktu_akhir
            waktu_akhir += window_r

        return self.hasil_agregasi

    @staticmethod
    def create_X_t(x_t: np.ndarray, order: int) -> np.ndarray:
        """Create X_t matrix for SDNML calculation"""
        n = len(x_t)
        X_t = np.zeros((n - order, order))
        for t in range(order, n):
            X_t[t - order] = x_t[t - order:t][::-1]
        return X_t

    @staticmethod
    def update_matrices(V_prev_inv: np.ndarray, M_prev: np.ndarray, x_t: np.ndarray, xt: float, r: float = 0.0005) -> Tuple[np.ndarray, np.ndarray, float]:
        """Update matrices for SDNML calculation"""
        x_t = x_t[:, np.newaxis]
        c_t = r * (x_t.T @ V_prev_inv @ x_t)
        V_t = (1 / (1 - r)) * V_prev_inv - (r / (1 - r)) * (V_prev_inv @ np.outer(x_t.flatten(), x_t) @ V_prev_inv) / (1 - r + c_t)
        M_t = (1 - r) * M_prev + r * x_t.flatten() * xt
        return V_t, M_t, c_t.item()

    @staticmethod
    def apply_smoothing(scores: List[float], T: int) -> List[float]:
        """Apply smoothing to scores"""
        smoothed_scores = []
        for t in range(T - 1, len(scores)):
            smoothed_score = np.mean(scores[t-T+1:t+1])
            smoothed_scores.append(smoothed_score)
        return smoothed_scores
    
    def first_stage(self, aggregation_scores: np.ndarray, order: int = 2, r: float = 0.0005, m: int = 0, T: int = 2) -> List[float]:
        """Perform first stage SDNML calculation"""
        x_t = aggregation_scores
        X_t = self.create_X_t(x_t, order=order)

        V0 = np.identity(order)
        M0 = np.zeros(order)
        V_inv = V0
        M = M0

        d_t = []
        for t in range(len(X_t)):
            V_inv, M, c_t = self.update_matrices(V_inv, M, X_t[t], x_t[t + order], r)
            d_t_value = c_t / (1 - r + c_t)
            d_t.append(d_t_value)

        A_t = np.dot(V_inv, M)
        e_t = [x_t[i + order] - np.dot(A_t, X_t[i]) for i in range(len(X_t))]
        tau_t = [(1 / (i - m)) * sum([e_t[j]**2 for j in range(m+1, i+1)]) for i in range(m+1, len(X_t))]
        s_t = [(i - m) * tau_t[i] for i in range(m+1, len(tau_t))]
        K_t = [np.sqrt(np.pi) / (1 - d_t[i]) * gamma((i+1 - m - 1) / 2) / gamma((i+1 - m) / 2) for i in range(m+1, len(d_t))]
        p_SDNML = [K_t[i]**-1 * (s_t[i]**(-(i+1 - m) / 2) / s_t[i - 1]**(-(i+1 - m - 1) / 2)) for i in range(m+1, len(s_t))]
        log_p_SDNML = [-np.log(p_SDNML[i]) for i in range(len(p_SDNML))]

        return self.apply_smoothing(log_p_SDNML, T)

    def second_stage(self, smoothed_scores: List[float], order: int = 2, r: float = 0.0005, m: int = 0, T: int = 2) -> List[float]:
        """Perform second stage SDNML calculation"""
        x_t_second = smoothed_scores
        X_t_second = self.create_X_t(x_t_second, order=order)

        V0_second = np.identity(order)
        M0_second = np.zeros(order)
        V_inv_second = V0_second
        M_second = M0_second

        d_t_second = []
        for t in range(len(X_t_second)):
            V_inv_second, M_second, c_t_second = self.update_matrices(V_inv_second, M_second, X_t_second[t], x_t_second[t + order], r)
            d_t_value_second = c_t_second / (1 - r + c_t_second)
            d_t_second.append(d_t_value_second)

        A_t_second = np.dot(V_inv_second, M_second)
        e_t_second = [x_t_second[i + order] - np.dot(A_t_second, X_t_second[i]) for i in range(len(X_t_second))]
        tau_t_second = [(1 / (i - m)) * sum([e_t_second[j]**2 for j in range(m+1, i+1)]) for i in range(m+1, len(X_t_second))]
        s_t_second = [(i - m) * tau_t_second[i] for i in range(m+1, len(tau_t_second))]
        K_t_second = [np.sqrt(np.pi) / (1 - d_t_second[i]) * gamma((i+1 - m - 1) / 2) / gamma((i+1 - m) / 2) for i in range(m+1, len(d_t_second))]
        p_SDNML_second = [K_t_second[i]**-1 * (s_t_second[i]**(-(i+1 - m) / 2) / s_t_second[i - 1]**(-(i+1 - m - 1) / 2)) for i in range(m+1, len(s_t_second))]
        log_p_SDNML_second = [-np.log(p_SDNML_second[i]) for i in range(len(p_SDNML_second))]

        smoothed_second_scores = self.apply_smoothing(log_p_SDNML_second, T)
        yscore = np.array(smoothed_second_scores)

        end_index = len(self.hasil_agregasi) - (order + 1)
        start_index_second_smoothed = (order * order * T) + T - 1

        for i in range(start_index_second_smoothed, end_index):
            relative_index = i - start_index_second_smoothed
            self.hasil_agregasi[i]['yscore'] = yscore[relative_index]

        return smoothed_second_scores

    
    def dynamic_threshold_optimization(self, scores, NH=20, rho=0.05, r_H=0.001, lambda_H=0.5):
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
        import numpy as np
        import json

        # Inisialisasi bin
        scores = np.array(scores)
        a = np.mean(scores) + 2 * np.std(scores)
        filtered_scores = scores[scores > a]
        b = np.min(filtered_scores) if filtered_scores.size > 0 else a

        bin_edges = [-np.inf, a] + [a + (b - a) / (NH - 2) * i for i in range(NH - 3)] + [np.inf]
        bin_edges = np.sort(bin_edges)

        histogram = np.ones(NH) / NH
        results = []

        M = len(scores)
        for j in range(M - 1):
            bin_index = np.digitize(scores[j], bin_edges) - 1
            updated_histogram = np.zeros_like(histogram)

            for h in range(len(histogram)):
                if h == bin_index:
                    updated_histogram[h] = (1 - r_H) * histogram[h] + r_H
                else:
                    updated_histogram[h] = (1 - r_H) * histogram[h]

            updated_histogram = (updated_histogram + lambda_H) / (np.sum(updated_histogram) + NH * lambda_H)
            histogram = updated_histogram
            cumulative_distribution = np.cumsum(histogram)
            threshold_index = np.argmax(cumulative_distribution >= (1 - rho))
            threshold = bin_edges[threshold_index]

            alarm = scores[j] >= threshold

            # Simpan hasil
            results.append({
                "Session": j + 1,
                "Score": float(scores[j]),  # Pastikan tipe data float
                "Threshold": float(threshold),  # Konversi threshold ke float
                "Alarm": bool(alarm)  # Konversi alarm ke bool
            })

        # Tambahkan informasi waktu dan diskrit dari hasil_agregasi
        waktu_awal = ""
        waktu_akhir = ""
        for result in results:
            if result['Alarm']:
                matching_data = next((item for item in self.hasil_agregasi if item.get('yscore') == result['Score']), None)

                if matching_data:
                    result['Diskrit'] = matching_data['diskrit']
                    result['Waktu_Awal'] = matching_data['waktu_awal']
                    result['Waktu_Akhir'] = matching_data['waktu_akhir']
                    waktu_awal = matching_data['waktu_awal']
                    waktu_akhir = matching_data['waktu_akhir']

        # Jika waktu awal dan waktu akhir valid, ambil data tweet dari database
        if waktu_awal and waktu_akhir:
            cursor = self.connection.cursor()
            query = f"SELECT full_text FROM data_preprocessed WHERE created_at BETWEEN '{waktu_awal}' AND '{waktu_akhir}'"
            cursor.execute(query)
            hasil_twitt_trending = cursor.fetchall()

            # Simpan hasil ke file JSON
            with open('hasil_twitt_trending.json', 'w') as file:
                json.dump(hasil_twitt_trending, file)
            print(f"{waktu_awal}")

        return results





    def process_link_anomaly(self, r: float = 0.0005) -> Dict[str, Any]:
        try:
            print("Fetching tweets data")
            self.fetch_tweets_data()
            
            print("Calculating mention probabilities")
            self.hitung_probabilitas_mention()
            print("Mention probabilities calculated:", self.hasil_perhitungan)
            
            print("Calculating mention probabilities per user")
            self.hitung_mention_tiap_id()
            print("Mention probabilities per user calculated:", self.hasil_perhitungan)
            
            print("Calculating anomaly scores")
            self.hitung_skor_anomaly()
            print("Anomaly scores calculated:", self.hasil_perhitungan)
            
            print("Calculating aggregation scores")
            self.hitung_skor_agregasi()
            print("Aggregation scores calculated:", self.hasil_agregasi)
            
            print("Preparing data for SDNML")
            aggregation_scores = np.array([entry["s_x"] for entry in self.hasil_agregasi])
            print("Aggregation scores prepared:", aggregation_scores)
            
            print("Running first stage SDNML")
            smoothed_scores = self.first_stage(aggregation_scores)
            print("First stage SDNML results:", smoothed_scores)
            
            print("Running second stage SDNML")
            smoothed_second_scores = self.second_stage(smoothed_scores)
            print("Second stage SDNML results:", smoothed_second_scores)

            # Cetak hasil_agregasi untuk memeriksa y_score
            print("Hasil agregasi setelah second stage (dengan y_score):")
            for entry in self.hasil_agregasi:
                print(entry)
            
            print("Running dynamic threshold optimization")
            final_results = self.dynamic_threshold_optimization(smoothed_second_scores)
            print("Final results of dynamic threshold optimization:", final_results)
            
            # Prepare return data
            return {
                "anomaly_detection_results": final_results
            }
        except Exception as e:
            print(f"Error in process_link_anomaly: {str(e)}")
            raise


                            