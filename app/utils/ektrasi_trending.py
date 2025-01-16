import json 
import sys
import os
# Tambahkan root proyek ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.utils.db_connection import create_connection

connections = create_connection()
cursors = connections.cursor()
waktu_awal = '2024-11-03 22:39:00'
waktu_akhir = '2024-11-04 22:39:00'
query = f"SELECT full_text FROM data_preprocessed WHERE created_at BETWEEN '{waktu_awal}' AND '{waktu_akhir}'"
cursors.execute(query)

hasil_twitt_trending = cursors.fetchall()
with open('hasil_twitt_trending_diskrit22.json', 'w') as file:
    json.dump(hasil_twitt_trending, file)