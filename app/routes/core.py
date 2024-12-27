from flask import Blueprint, jsonify, render_template, current_app, Response, request
from app.utils.extensions import socketio
from app.utils.db_connection import create_connection
from data.convert_to_database import TwitterDataProcessor
from data.preprocessing import Preprocessor
from app.utils.pool_manager import PoolManager
import json 
import logging
import mysql
import os
import pandas as pd
from app.utils.link_anomaly import LinkAnomalyDetector

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
    API route yang menyediakan data yang telah dipra-proses dengan pagination.
    """
    db = create_connection()
    cursor = db.cursor()

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))  

    offset = (page - 1) * per_page
    cursor.execute("SELECT COUNT(*) FROM data_preprocessed")
    total_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT * FROM data_preprocessed LIMIT %s OFFSET %s",
        (per_page, offset)
    )
    data = cursor.fetchall()

    # Format data
    response_data = [
        {
            "id": row[0],
            "created_at": row[1],
            "username": row[2],
            "full_text": row[3],
            "mentions": row[4],
            "jumlah_mention": row[5],
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
                "second_stage_smooth": results['second_stage_smooth'],
                "agregat": results['agregat'],
                "dt": results['dt'],
                "et": results['et'],
                "taut": results['taut'],
                "st": results['st'],
                "kt": results['kt'],
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
