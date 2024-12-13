import mysql.connector
from mysql.connector import Error
from .config import Config
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**Config.DATABASE_CONFIG)
        print('Connection to MySQL DB successful')
    except Error as e:
        print(f'The error {e} occurred')
    return connection

# Menguji koneksi
if __name__ == "__main__":
    create_connection()
