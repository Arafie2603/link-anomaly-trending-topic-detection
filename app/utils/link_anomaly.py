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
        self.probabilitas_mention = []
        self.probabilitas_user = []
        self.skor_anomaly = []
        self.first_stage_learning = []
        self.first_stage_scoring = []
        self.first_stage_smoothing = []
        self.second_stage_learning = []
        self.second_stage_scoring = []
        self.dt = []
        self.et = []
        self.taut = []
        self.st = []
        self.kt = []
        self.ct = []
        self.mt = []
        self.at = []
        self.vt_list = [] 
        self.histogram = []
        self.bins = []

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
            n = i

            for j in range(k+1):
                if j == 0:
                    iterasi *= (n + alpha) / (m + k + beta)
                iterasi *= (m + beta + j) / (n + m + alpha + beta + j)
            
            waktu_str = tweet['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            self.probabilitas_mention.append(iterasi)
            self.hasil_perhitungan.append({
                "id": tweet['id'],
                "created_at": waktu_str,
                "probabilitas_mention": iterasi,
                "mentions": tweet['jumlah_mention']
            })
        
        return self.hasil_perhitungan, self.probabilitas_mention

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
            self.probabilitas_user.append(pmention_list)

            for hasil in self.hasil_perhitungan:
                if hasil['id'] == tweet['id']:
                    hasil['probabilitas_user'] = pmention_list

        return self.hasil_perhitungan, self.probabilitas_user

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
                    self.skor_anomaly.append(skor_anomaly)
                    item['skor_anomaly'] = skor_anomaly

        return self.hasil_perhitungan, self.skor_anomaly

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
        stage_vt = []
        stage_ct = []
        stage_mt = []
        stage_at = []
        for t in range(len(X_t)):
            V_inv, M, c_t = self.update_matrices(V_inv, M, X_t[t], x_t[t + order], r)
            d_t_value = c_t / (1 - r + c_t)
            d_t.append(d_t_value)
            stage_vt.append(V_inv.tolist())
            stage_ct.append(c_t)
            stage_mt.append(M.tolist())

        A_t = np.dot(V_inv, M)
        e_t = [x_t[i + order] - np.dot(A_t, X_t[i]) for i in range(len(X_t))]
        tau_t = [(1 / (i - m)) * sum([e_t[j]**2 for j in range(m+1, i+1)]) for i in range(m+1, len(X_t))]
        s_t = [(i - m) * tau_t[i] for i in range(m+1, len(tau_t))]
        K_t = [np.sqrt(np.pi) / (1 - d_t[i]) * gamma((i+1 - m - 1) / 2) / gamma((i - m) / 2) for i in range(m+1, len(d_t))]
        p_SDNML = [K_t[i]**-1 * (s_t[i]**(-(i - m) / 2) / s_t[i - 1]**(-(i - m - 1) / 2)) for i in range(m+1, len(s_t))]
        log_p_SDNML = [-np.log(p_SDNML[i]) for i in range(len(p_SDNML))]
        self.first_stage_learning.append(p_SDNML)
        self.first_stage_scoring.append(log_p_SDNML)
        self.dt.append(d_t)
        self.et.append(e_t)
        self.taut.append(tau_t)
        self.st.append(s_t)
        self.kt.append(K_t)
        self.vt_list.extend(stage_vt)
        self.ct.extend(stage_ct)
        self.at.append(A_t)
        self.mt.extend(stage_mt)

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
        p_SDNML_second = [K_t_second[i]**-1 * (s_t_second[i]**(-(i - m) / 2) / s_t_second[i - 1]**(-(i - m - 1) / 2)) for i in range(m+1, len(s_t_second))]
        log_p_SDNML_second = [-np.log(p_SDNML_second[i]) for i in range(len(p_SDNML_second))]

        smoothed_second_scores = self.apply_smoothing(log_p_SDNML_second, T)
        yscore = np.array(smoothed_second_scores)

        self.second_stage_learning.append(p_SDNML_second)
        self.second_stage_scoring.append(log_p_SDNML_second)

        end_index = len(self.hasil_agregasi)
        start_index_second_smoothed = (order * 6)

        self.second_stage_learning.append(p_SDNML_second)
        self.second_stage_scoring.append(log_p_SDNML_second)

        for i in range(start_index_second_smoothed, end_index):
            relative_index = i - start_index_second_smoothed
            self.hasil_agregasi[i]['yscore'] = yscore[relative_index]

        return smoothed_second_scores

    
    def dynamic_threshold_optimization(self, scores, NH=20, rho=0.05, r_H=0.001, lambda_H=0.5):
        """
        Modified Dynamic Threshold Optimization (DTO) to include historical periods
        """
        import numpy as np
        import json
        from collections import defaultdict

        # Initialize bins
        scores = np.array(scores)
        a = np.mean(scores) + 1 * np.std(scores)
        filtered_scores = scores[scores > a]
        b = np.min(filtered_scores) if filtered_scores.size > 0 else a

        bin_edges = [-np.inf, a] + [a + (b - a) / (NH - 2) * i for i in range(NH - 3)] + [np.inf]
        bin_edges = np.sort(bin_edges)

        histogram = np.ones(NH) / NH
        results = []
        all_trending_periods = []

        M = len(scores)
        stage_histogram = []
        
        for j in range(M - 1):
            bin_index = np.digitize(scores[j], bin_edges) - 1
            updated_histogram = np.zeros_like(histogram)
            if bin_index == 0:
                bin_index = ''

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
            self.histogram.append(histogram)
            self.bins.append(bin_edges)

            alarm = scores[j] >= threshold
            
            if alarm:
                result = {
                    "Score": float(scores[j]),
                    "Threshold": float(threshold),
                    "Alarm": bool(alarm)
                }

                matching_data = next((item for item in self.hasil_agregasi if item.get('yscore') == result['Score']), None)

                if matching_data:
                    trending_period = {
                        "diskrit": matching_data['diskrit'],
                        "waktu_awal": matching_data['waktu_awal'],
                        "waktu_akhir": matching_data['waktu_akhir'],
                        "score": result['Score'],
                        "threshold": result['Threshold']
                    }
                    all_trending_periods.append(trending_period)

                results.append(result)
                
        stage_histogram.append(histogram)

        # Group trending periods by discrete time windows
        trending_by_time = defaultdict(list)
        for period in all_trending_periods:
            key = (period['waktu_awal'], period['waktu_akhir'])
            trending_by_time[key].append(period)

        # Format final output with historical periods
        final_trending_periods = []
        for time_window, periods in trending_by_time.items():
            current_diskrit = periods[0]['diskrit']
            
            # Get historical periods (3 periods before current_diskrit)
            historical_periods = []
            for i in range(3):
                historical_diskrit = current_diskrit - (3-i)
                historical_data = next((item for item in self.hasil_agregasi 
                                    if item['diskrit'] == historical_diskrit), None)
                if historical_data:
                    historical_periods.append({
                        "diskrit": historical_data['diskrit'],
                        "waktu_awal": historical_data['waktu_awal'],
                        "waktu_akhir": historical_data['waktu_akhir']
                    })

            trending_info = {
                "trending_diskrit": current_diskrit,
                "historical_periods": historical_periods,
                "historical_start": historical_periods[0]['waktu_awal'] if historical_periods else None,
                "historical_end": historical_periods[-1]['waktu_akhir'] if historical_periods else None,
                "current_period": {
                    "waktu_awal": time_window[0],
                    "waktu_akhir": time_window[1]
                },
                "trending_scores": [
                    {
                        "score": p['score'],
                        "threshold": p['threshold']
                    } for p in periods
                ],
                "jumlah_deteksi": len(periods)
            }
            final_trending_periods.append(trending_info)

        # Sort by discrete time
        final_trending_periods.sort(key=lambda x: x['trending_diskrit'])
        # Create directory for trending periods JSON
        json_dir = "trending_periods"
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        # Process trending periods and create JSONs
        if self.connection is not None:
            cursor = self.connection.cursor(dictionary=True)  # Use dictionary cursor for clearer data handling
            
            for period in final_trending_periods:
                trending_diskrit = period['trending_diskrit']
                historical_tweets = []
                
                # Get all tweets from historical periods
                for hist_period in period['historical_periods']:
                    hist_diskrit = hist_period['diskrit']
                    # Modify query to match your database structure
                    query = f"""
                        SELECT full_text, created_at 
                        FROM data_preprocessed 
                        WHERE created_at BETWEEN '{hist_period['waktu_awal']}' AND '{hist_period['waktu_akhir']}'
                        ORDER BY created_at ASC
                    """
                    
                    try:
                        cursor.execute(query)
                        period_tweets = cursor.fetchall()
                        # Extract only the full_text from each tweet
                        tweets = [tweet['full_text'] for tweet in period_tweets if tweet['full_text']]
                        historical_tweets.extend(tweets)
                    except Exception as e:
                        print(f"Error querying period {hist_diskrit}: {str(e)}")
                        continue

                # Create the JSON structure
                trending_data = {
                    "trending_info": {
                        "trending_diskrit": trending_diskrit,
                        "waktu_awal": period['current_period']['waktu_awal'],
                        "waktu_akhir": period['current_period']['waktu_akhir']
                    },
                    "historical_periods": period['historical_periods'],
                    "historical_start": period['historical_start'],
                    "historical_end": period['historical_end'],
                    "combined_historical_tweets": historical_tweets  # Add the collected tweets
                }

                # Save to JSON file
                json_filename = f"trending_{trending_diskrit}.json"
                json_path = os.path.join(json_dir, json_filename)
                
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(trending_data, f, indent=4, ensure_ascii=False)
                    print(f"Successfully saved {len(historical_tweets)} tweets for trending period {trending_diskrit}")
                except Exception as e:
                    print(f"Error saving JSON for trending period {trending_diskrit}: {str(e)}")

            cursor.close()

        return {
            "anomaly_results": results,
            "trending_periods": final_trending_periods,
            "total_trending_periods": len(final_trending_periods)
        }


    def process_link_anomaly(self, r: float = 0.0005) -> Dict[str, Any]:
        try:
            print("Fetching tweets data")
            self.fetch_tweets_data()
            
            print("Calculating mention probabilities")
            self.hitung_probabilitas_mention()
            print("Mention probabilities calculated:", self.probabilitas_mention)
            
            print("Calculating mention probabilities per user")
            self.hitung_mention_tiap_id()
            print("Mention probabilities per user calculated:", self.probabilitas_user)
            
            print("Calculating anomaly scores")
            self.hitung_skor_anomaly()
            print("Anomaly scores calculated:", self.skor_anomaly)
            
            print("Calculating aggregation scores")
            self.hitung_skor_agregasi()
            print("Aggregation scores calculated:", self.hasil_agregasi)
            
            print("Preparing data for SDNML")
            aggregation_scores = np.array([entry["s_x"] for entry in self.hasil_agregasi])
            aggregation_scores_list = aggregation_scores.tolist()
            print("Aggregation scores prepared:", aggregation_scores)
            
            print("Running first stage SDNML")
            smoothed_scores = self.first_stage(aggregation_scores)
            print("First stage SDNML results:", smoothed_scores)
            
            print("Running second stage SDNML")
            smoothed_second_scores = self.second_stage(smoothed_scores)
            print("Second stage SDNML results:", smoothed_second_scores)

            dto_results = self.dynamic_threshold_optimization(smoothed_second_scores)
             # Extract trending periods information
            trending_periods = dto_results.get('trending_periods', [])
            total_trending_periods = dto_results.get('total_trending_periods', 0)

            # Create a structured trending topics section
            trending_topics = {
                "total_periods": total_trending_periods,
                "periods": trending_periods
            }

            # Cetak hasil_agregasi untuk memeriksa y_score
            print("Hasil agregasi setelah second stage (dengan y_score):")
            for entry in self.hasil_agregasi:
                print(entry)
            
            print("Running dynamic threshold optimization")
            final_results = self.dynamic_threshold_optimization(smoothed_second_scores)
            print("Final results of dynamic threshold optimization:", final_results)
            print("dt----", )

            at_list = [arr.tolist() if isinstance(arr, np.ndarray) else arr for arr in self.at] 
            mt_list = [arr.tolist() if isinstance(arr,np.ndarray) else arr for arr in self.mt]
            histogram = [arr.tolist() if isinstance(arr,np.ndarray) else arr for arr in self.histogram]
            bins = [arr.tolist() if isinstance(arr,np.ndarray) else arr for arr in self.bins]
            cleaned_bins = [
                [x for x in arr if not (math.isinf(x) or x == float('inf') or x == float('-inf'))]
                for arr in bins
            ]
            # Prepare return data
            return {
                "probabilitas_mention": self.probabilitas_mention,
                "probabilitas_user": self.probabilitas_user,
                "hasil_agregasi": self.hasil_agregasi,
                "skor_anomaly": self.skor_anomaly,
                "dt": self.dt,
                "et": self.et,
                "taut": self.taut,
                "st": self.st,
                "kt": self.kt,
                "rat": at_list,
                "rct": self.ct,
                "rvt": self.vt_list,
                "rmt": mt_list,
                "rhistogram": histogram,
                "rbins": cleaned_bins,
                "agregat": aggregation_scores_list,
                "first_stage_learning": self.first_stage_learning,
                "first_stage_scoring": self.first_stage_scoring,
                "first_stage_smoothing": smoothed_scores,
                "second_stage_learning": self.second_stage_learning,
                "second_stage_scoring": self.second_stage_scoring,
                "second_stage_smoothing": smoothed_second_scores,
                "anomaly_detection_results": final_results,
                "all_anomaly": dto_results['anomaly_results'],
                "trending_topics": trending_topics
            }
        except Exception as e:
            print(f"Error in process_link_anomaly: {str(e)}")
            raise


                            