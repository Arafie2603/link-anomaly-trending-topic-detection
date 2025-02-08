from flask import Blueprint, jsonify, render_template, current_app, Response, request
from app.utils.extensions import socketio
from app.utils.db_connection import create_connection
from data.convert_to_database import TwitterDataProcessor
from data.preprocessing import Preprocessor
from app.utils.link_anomaly import LinkAnomalyDetector
from app.utils.lda import LDAModel
import json 
import logging
import math
import mysql
import os
import pandas as pd

core_bp = Blueprint("core", __name__, url_prefix="/")
processing_pool = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# =========== PAGE ===========
@core_bp.route("/")
def home_route():
    """
    route untuk menampilkan halaman utama
    """
    return render_template("pages/index.html")
@core_bp.route('/run_link_anomaly')
def link_anomaly_route():
    return render_template("pages/link_anomaly.html")

@core_bp.route("/anomaly/preprocessing")
def preprocessing_route():
    """
    route untuk menampilkan halaman preprocessing
    """
    return render_template("pages/preprocessing.html")

@core_bp.route("/import")
def page_import_data():
    return render_template("pages/import.html")

@core_bp.route("/topic_modeling")
def topic_modeling_route():
    return render_template("pages/modeling.html")

from flask import render_template
from app.utils.pengujian_data import PENGUJIAN_DATA

@core_bp.route('/pengujian')
def pengujian_route():
    return render_template('pages/pengujian.html', data=PENGUJIAN_DATA)

# =========== API DATA ===========
@core_bp.route("/api/data")
def api_data():
    """
    API route yang menyediakan data dari dataset Twitter dengan pagination.

    Return:
    - JSON: Mengembalikan data dalam format JSON, termasuk jumlah total data.
    """
    db = create_connection()
    cursor = db.cursor()

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    offset = (page - 1) * per_page

    cursor.execute("SELECT COUNT(*) FROM data_twitter")
    total_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT * FROM data_twitter LIMIT %s OFFSET %s",
        (per_page, offset)
    )
    data = cursor.fetchall()

    response_data = [
        {
            "conversation_id_str": row[0],
            "created_at": row[1],
            "favorite_count": row[2],
            "full_text": row[3],
            "id_str": row[4],
            "image_url": row[5],
            "in_reply_to_screen_name": row[6],
            "lang": row[7],
            "location": row[8],
            "quote_count": row[9],
            "reply_count": row[10],
            "retweet_count": row[11],
            "tweet_url": row[12],
            "user_id_str": row[13],
            "username": row[14],
        }
        for row in data
    ]

    return jsonify({
        "data": response_data,
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,
    })


@core_bp.route("/api/total_data_stats")
def total_data_stats():
    """
    route untuk menampilkan total data mentah yang digunakan dalam program
    """
    db = create_connection()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM data_twitter")

    total_data = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM data_preprocessed WHERE full_text != 'n/a'")
    preprocessed_data = cursor.fetchone()[0]

    return jsonify({"total_data": total_data, "preprocessed_data": preprocessed_data})

@core_bp.route("/api/preprocessing")
def api_data_preprocessing():
    """
    API route yang menyediakan data yang telah dipra-proses dengan pagination,
    termasuk data tweet asli.
    """
    db = create_connection()
    cursor = db.cursor(dictionary=True)  # Use dictionary cursor for easier data handling

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))  

        offset = (page - 1) * per_page
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM data_preprocessed")
        total_count = cursor.fetchone()['count']

        # Modified query to handle possible NULL values and use proper aliases
        cursor.execute("""
            SELECT 
                dp.id,
                dp.tweet_id_str,
                dp.created_at,
                dp.username,
                dp.full_text as processed_text,
                dp.mentions,
                dp.jumlah_mention,
                dt.full_text as original_text,
                dt.favorite_count,
                dt.conversation_id_str,
                dt.image_url,
                dt.in_reply_to_screen_name,
                dt.lang,
                dt.location,
                dt.quote_count,
                dt.reply_count,
                dt.retweet_count,
                dt.tweet_url
            FROM data_preprocessed dp
            LEFT JOIN data_twitter dt ON dp.tweet_id_str = dt.id_str
            ORDER BY dp.created_at DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        data = cursor.fetchall()

        # Format data
        response_data = [
            {
                "id": row['id'],
                "tweet_id_str": row['tweet_id_str'],
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else None,
                "username": row['username'],
                "processed_text": row['processed_text'],
                "mentions": row['mentions'],
                "jumlah_mention": row['jumlah_mention'],
                "original_data": {
                    "original_text": row['original_text'],
                    "favorite_count": row['favorite_count'],
                    "conversation_id_str": row['conversation_id_str'],
                    "image_url": row['image_url'],
                    "in_reply_to_screen_name": row['in_reply_to_screen_name'],
                    "lang": row['lang'],
                    "location": row['location'],
                    "quote_count": row['quote_count'],
                    "reply_count": row['reply_count'],
                    "retweet_count": row['retweet_count'],
                    "tweet_url": row['tweet_url']
                }
            }
            for row in data
        ]

        return jsonify({
            "data": response_data,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page,
        })

    except Exception as e:
        logger.error(f"Error in api_data_preprocessing: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        db.close()
        
@core_bp.route("/api/deleted_preprocessing_data", methods=['POST'])
def deleted_preprocessing_data():
    """
    Menghapus semua data yang telah dipra-proses dari database.

    Return:
    - JSON: Respon berisi pesan keberhasilan atau kesalahan.
    """
    db = None
    cursor = None
    try:
        db = create_connection()
        cursor = db.cursor()
        
        # Check if table exists first
        cursor.execute("SHOW TABLES LIKE 'data_preprocessed'")
        if not cursor.fetchone():
            return jsonify({
                "error": "Table data_preprocessed does not exist"
            }), 404

        # Check if there's data to delete
        cursor.execute("SELECT COUNT(*) FROM data_preprocessed")
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({
                "message": "No data to delete"
            }), 200

        cursor.execute("DELETE FROM data_preprocessed")
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Successfully deleted data",
            "rows_affected": count
        }), 200

    except mysql.connector.Error as e:
        if db:
            db.rollback()
        return jsonify({
            "error": f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        if db:
            db.rollback()
        return jsonify({
            "error": f"Unexpected error: {str(e)}"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

@core_bp.route("/api/checking_data_preprocessed", methods=['GET'])
def checking_data_preprocessed():
    db = create_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM data_preprocessed LIMIT 1)"
        )
        exists = cursor.fetchone()[0]
        return jsonify({"exists": bool(exists)})
    finally:
        cursor.close()
        db.close()
@core_bp.route("/api/upload_csv", methods=['POST'])
def upload_csv_file():
    db = create_connection()
    if 'fileInput' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['fileInput']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file format. Please upload a CSV file."}), 400

    filepath = os.path.join('/tmp', file.filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
        processor = TwitterDataProcessor()
        processor.create_table(db)
        processor.insert_data(db, df)

        return jsonify({"success": "Data successfully uploaded and processed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

# =========== Utilitas ===========

@core_bp.route("/run_preprocessing", methods=['POST'])
def run_preprocessing_route():
    """
    Melakukan pra-pemrosesan data dan menyimpan hasilnya ke database.

    Return:
    - JSON: Respon berisi pesan keberhasilan atau kesalahan, dan data yang diproses.
    """
    preprocessor = Preprocessor(socketio)
    result = preprocessor.run_preprocessing()

    if "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result), 200


@core_bp.route("/api/run_link_anomaly", methods=['POST'])
def run_link_anomaly():
    try:
        logger.info("Creating database connection")
        db = create_connection()
        cursor = db.cursor()

        cursor.execute("SELECT mentions FROM data_preprocessed ORDER by created_at asc")
        mentions = cursor.fetchall()
        mentions = [item[0] for item in mentions]  # Flatten the list of tuples

        cursor.execute("SELECT * FROM data_preprocessed ORDER BY created_at asc LIMIT 5")
        twitter_mentions = cursor.fetchall()

        logger.info("Initializing LinkAnomalyDetector")
        detector = LinkAnomalyDetector(db)

        logger.info("Running process_link_anomaly")
        results = detector.process_link_anomaly()
        logger.info(f"Results: {results}")

        waktu_awal = None
        waktu_akhir = None
        for result in results["anomaly_detection_results"]:
            if "Waktu_Awal" in result and "Waktu_Akhir" in result:
                waktu_awal = result["Waktu_Awal"]
                waktu_akhir = result["Waktu_Akhir"]
                break  

        logger.info("Preparing response data")

        response_data = {
            "status": "success",
            "message": "Link anomaly detection completed successfully",
            "data": {
                "probabilitas_user": results['probabilitas_user'],
                "probabilitas_mention": results['probabilitas_mention'],
                "skor_anomaly": results['skor_anomaly'],
                "hasil_agregasi": results['hasil_agregasi'],
                "first_stage_learning": results['first_stage_learning'],
                "first_stage_scoring": results['first_stage_scoring'],
                "first_stage_smoothing": results['first_stage_smoothing'],
                "anomaly_detection_results": results["anomaly_detection_results"],
                "second_stage_learning": results['second_stage_learning'],
                "second_stage_scoring": results['second_stage_scoring'],
                "second_stage_smoothing": results['second_stage_smoothing'],
                "agregat": results['agregat'],
                "rdt": results['dt'],
                "ret": results['et'],
                "mentions": mentions,
                "limit_twitt": twitter_mentions,
                "taut": results['taut'],
                "rst": results['st'],
                "rkt": results['kt'],
                "rvt": results['rvt'],
                "rct": results['rct'],
                "rmt": results['rmt'],
                "rat": results['rat'],
                "rbins": results['rbins'],
                "all_anomaly": results['all_anomaly'],
                "trending_topics": results['trending_topics'],
                "rhistogram": results['rhistogram'],
                "waktu_awal": waktu_awal,
                "waktu_akhir": waktu_akhir,
            }
        }

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        error_response = {
            "status": "error",
            "message": f"An error occurred during link anomaly detection: {str(e)}",
            "error_details": str(e)
        }
        return jsonify(error_response), 500

    finally:
        if 'db' in locals() and db and db.is_connected():
            db.close()

    logger.info("Returning response data")
    return jsonify(response_data), 200


@core_bp.route("/api/run_lda", methods=['GET'])
def run_lda():
    """
    Flask Blueprint endpoint to run LDA on multiple trending periods
    Returns:
        JSON response with topics and their associated words/weights for each trending period
    """
    try:
        trending_dir = "trending_periods"
        if not os.path.exists(trending_dir):
            return jsonify({
                "status": "error",
                "message": "Directory trending_periods tidak ditemukan"
            }), 404

        # Get all trending period JSON files
        trending_files = [f for f in os.listdir(trending_dir) if f.endswith('.json')]
        
        if not trending_files:
            return jsonify({
                "status": "error",
                "message": "Tidak ada file trending yang ditemukan"
            }), 404

        all_results = {}
        
        # Process each trending period
        for file_name in trending_files:
            file_path = os.path.join(trending_dir, file_name)
            
            # Load trending period data
            with open(file_path, 'r', encoding='utf-8') as file:
                trending_data = json.load(file)
            
            # Extract tweets from the trending period
            tweets = trending_data.get('combined_historical_tweets', [])
            
            if not tweets:
                print(f"No tweets found in {file_name}")
                continue

            # Initialize and run LDA
            lda = LDAModel(n_topics=10, max_iterations=900)
            tokenized_data = lda.tokenize_data(tweets)
            
            # Fit model
            lda.fit(tokenized_data)
            
            # Get topic words
            topic_word_list = lda.get_topic_words()
            
            # Format topics for this trending period
            formatted_topics = {}
            for topic, words in topic_word_list.items():
                formatted_topics[topic] = [
                    {"word": word, "weight": round(weight, 4)} 
                    for word, weight in words
                ]
            
            # Store results for this trending period
            trending_diskrit = trending_data['trending_info']['trending_diskrit']
            all_results[f"trending_{trending_diskrit}"] = {
                "period_info": {
                    "trending_diskrit": trending_diskrit,
                    "waktu_awal": trending_data['trending_info']['waktu_awal'],
                    "waktu_akhir": trending_data['trending_info']['waktu_akhir'],
                    "historical_start": trending_data['historical_start'],
                    "historical_end": trending_data['historical_end']
                },
                "topics": formatted_topics
            }

        # Save combined results
        output_dir = "lda_results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, "all_trending_topics.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=4, ensure_ascii=False)

        return jsonify({
            "status": "success",
            "results": all_results,
            "message": f"LDA analysis completed for {len(all_results)} trending periods"
        }), 200

    except json.JSONDecodeError as e:
        return jsonify({
            "status": "error",
            "message": f"File JSON tidak valid: {str(e)}"
        }), 400
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Terjadi kesalahan: {str(e)}"
        }), 500
    
    
@core_bp.route("/get_period_tweets", methods=['GET'])
def get_period_tweets():
    """Get tweets from data_preprocessed table for specific time range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_query = """
            SELECT COUNT(*) 
            FROM data_preprocessed 
            WHERE created_at BETWEEN %s AND %s
        """
        
        # Get paginated tweets
        tweets_query = """
            SELECT full_text, created_at 
            FROM data_preprocessed 
            WHERE created_at BETWEEN %s AND %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        with create_connection() as conn:
            with conn.cursor() as cur:
                # Get total count
                cur.execute(count_query, (start_date, end_date))
                total_tweets = cur.fetchone()[0]
                
                # Get tweets
                cur.execute(tweets_query, (start_date, end_date, per_page, offset))
                tweets = cur.fetchall()
                
        return jsonify({
            "status": "success",
            "data": {
                "tweets": tweets,
                "total": total_tweets,
                "page": page,
                "per_page": per_page,
                "total_pages": math.ceil(total_tweets / per_page)
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500