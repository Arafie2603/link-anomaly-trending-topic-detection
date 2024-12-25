import sys
import os
import json

# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.utils.db_connection import create_connection
from app.utils.link_anomaly import LinkAnomalyDetector

def main():
    try:
        print("Creating database connection")
        db = create_connection()

        print("Initializing LinkAnomalyDetector")
        detector = LinkAnomalyDetector(db)

        print("Running process_link_anomaly")
        results = detector.process_link_anomaly()

        # Checking for trending tweets file
        trending_tweets = None
        if os.path.exists("hasil_twitt_trending.json"):
            with open("hasil_twitt_trending.json", "r") as file:
                trending_tweets = json.load(file)
        
        # Preparing response data
        response_data = {
            "status": "success",
            "message": "Link anomaly detection completed successfully",
            "data": {
                "anomaly_detection_results": results["anomaly_detection_results"],
                "aggregation_scores": [
                    {
                        "diskrit": score["diskrit"],
                        "waktu_awal": score["waktu_awal"],
                        "waktu_akhir": score["waktu_akhir"],
                        "s_x": float(score["s_x"]),
                        "jumlah_mention_agregasi": score["jumlah_mention_agregasi"]
                    }
                    for score in results["aggregation_scores"]
                ],
                "statistics": results["anomaly_detection_results"]["statistics"],
                "trending_tweets": trending_tweets
            }
        }

        print("Response data prepared:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        
    finally:
        # Ensure database connection is closed
        if 'db' in locals() and db and db.is_connected():
            db.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()
