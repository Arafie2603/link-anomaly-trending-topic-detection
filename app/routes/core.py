from flask import Blueprint, jsonify, render_template, current_app, Response, request
from app.utils.db_connection import create_connection
from data.convert_to_database import TwitterDataProcessor
import os
import pandas as pd
core_bp = Blueprint("core", __name__, url_prefix="/")
processing_pool = None

@core_bp.route("/")
def home_route():
    """
    route untuk menampilkan halaman utama
    """
    return render_template("pages/index.html")

@core_bp.route("/anomaly/preprocessing")
def preprocessing_route():
    """
    route untuk menampilkan halaman preprocessing
    """
    return render_template("pages/preprocessing.html")

@core_bp.route("/import")
def page_import_data():
    return render_template("pages/import.html")

@core_bp.route("/api/data")
def api_data():
    """
    API route yang menyediakan data dari dataset Twitter dengan pagination.

    Return:
    - JSON: Mengembalikan data dalam format JSON, termasuk jumlah total data.
    """
    db = create_connection()
    cursor = db.cursor()

    # Mendapatkan parameter halaman dan jumlah per halaman dari query string
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Hitung offset berdasarkan halaman dan jumlah per halaman
    offset = (page - 1) * per_page

    # Hitung total jumlah data
    cursor.execute("SELECT COUNT(*) FROM data_twitter")
    total_count = cursor.fetchone()[0]

    # Ambil data dari database dengan limit dan offset
    cursor.execute(
        "SELECT * FROM data_twitter LIMIT %s OFFSET %s",
        (per_page, offset)
    )
    data = cursor.fetchall()

    # Format data
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

    # Mengembalikan data dalam format JSON
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

    # Simpan file CSV ke disk sementara
    filepath = os.path.join('/tmp', file.filename)
    file.save(filepath)

    try:
        # Baca file CSV menggunakan pandas
        df = pd.read_csv(filepath)

        # Proses dan masukkan data ke dalam database
        processor = TwitterDataProcessor()
        processor.create_table(db)
        processor.insert_data(db, df)

        return jsonify({"success": "Data successfully uploaded and processed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

    

# @core_bp.route("/run_preprocessing", methods=['POST'])
# def run_preprocessing():
#     """
#     Melakukan pra-pemrosesan data dan menyimpan hasilnya ke database.

#     Return:
#     - JSON: Respon berisi pesan keberhasilan atau kesalahan, dan data yang diproses.
#     """
#     db = create_connection()
#     cursor = db.cursor()
#     try:
#         cursor.execute(
#             "SELECT id, date, username, rawContent FROM dataset_twitter")
#         data = cursor.fetchall()

#         processed_data = preprocessing.preprocess(data)

#         insert_sql = """
#             INSERT INTO dataset_preprocessed (id, time, user_twitter, tweet, jumlah_mention, id_user_mentioned)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         """
#         cursor.executemany(insert_sql, processed_data)  # Batch insert
#         db.commit()
#         return jsonify({"success": "Data processed and stored successfully", "data": processed_data})

#     except mysql.connector.Error as err:
#         db.rollback()
#         return jsonify({"error": "Failed to process data: {}".format(str(err))}), 500

#     finally:
#         cursor.close()
#         db.close()

