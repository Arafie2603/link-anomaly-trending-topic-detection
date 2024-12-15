from flask import Blueprint, jsonify, render_template, current_app, Response, request
from app.utils.db_connection import create_connection
import json
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