from flask import Flask
from flask_cors import CORS
from app.routes.core import core_bp
from app.utils.extensions import socketio  # Import socketio dari extensions.py
from multiprocessing import freeze_support

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.register_blueprint(core_bp)
CORS(app)

# Hubungkan socketio dengan aplikasi Flask
socketio.init_app(app)

if __name__ == "__main__":
    freeze_support()
    socketio.run(app, debug=True, use_reloader=False)
