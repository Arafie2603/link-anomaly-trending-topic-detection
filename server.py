from flask import Flask
from flask_cors import CORS
from app.routes.core import core_bp  # Import Blueprint dari routes.py

app = Flask(__name__)

# Daftarkan blueprint
app.register_blueprint(core_bp)
CORS(app)
if __name__ == "__main__":
    app.run(debug=True)
