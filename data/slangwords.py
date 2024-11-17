import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import create_connection


def insert_slangwords(connection, file_path):
    try:
        cursor = connection.cursor()

        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip().split('\t')
                if len(line) >= 2:
                    kata_tidak_baku, kata_baku = line[0], line[1]
                    query = "INSERT INTO slangwords (kata_tidak_baku, kata_baku) VALUES (%s, %s)"
                    values = (kata_tidak_baku, kata_baku)
                    cursor.execute(query, values)
                else:
                    print(f"Ignoring invalid line: {line}")

        connection.commit()
        print("Data slangword inserted successfully.")
    except Exception as e:
        print(f"Error inserting data: {e}")
        connection.rollback()


def close_connection(connection):
    connection.close()
    print("Koneksi ditutup.")


connection = create_connection()

file_path = "C:\\Users\\arraf\\OneDrive\\Dokumen\\Kuliah\\Skripsi\\link-anomaly\\link-anomaly-trending-topic-detection\\kamus\\slangword.txt"

insert_slangwords(connection, file_path)

close_connection(connection)