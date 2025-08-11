from flask import jsonify
from function.koneksi import get_db_connection

def get_data_home():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    (SELECT COUNT(*) FROM mahasiswa) AS total_mahasiswa,
                    (SELECT COUNT(*) FROM pengajar) AS total_pengajar,
                    (SELECT COUNT(*) FROM kelas) AS total_kelas,
                    (SELECT COUNT(*) FROM mata_kuliah) AS total_mata_kuliah;
                """
            
            cursor.execute(query)
            result = cursor.fetchone()

        return result, None
    finally:
        connection.close()