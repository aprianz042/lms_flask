from flask import jsonify
from function.koneksi import get_db_connection

def get_matkul():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM mata_kuliah')
            mata_kuliah = cursor.fetchall() 

            cursor.execute('SELECT * FROM prodi')
            prodi = cursor.fetchall() 
        return mata_kuliah, prodi, None
    finally:
        connection.close()


def add_matkul(data):
    kode_prodi = data.get('kode_prodi')
    kode_mata_kuliah = data.get('kode_mata_kuliah')
    nama_mata_kuliah = data.get('nama_mata_kuliah')
    semester = data.get('semester')
    sks = data.get('sks')
     
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            check_sql = """
                SELECT COUNT(*) 
                FROM mata_kuliah 
                WHERE kode_mata_kuliah = %s
            """
            cursor.execute(check_sql, (kode_mata_kuliah)) 
            result = cursor.fetchone()
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "Kode mata kuliah sudah ada"}), 400

            insert_sql = """
                INSERT INTO mata_kuliah (kode_prodi, kode_mata_kuliah, nama_mata_kuliah, semester, sks) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (kode_prodi, kode_mata_kuliah, nama_mata_kuliah, semester, sks))
            connection.commit()
        return jsonify({"message": "Berhasil menambahkan mata kuliah"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def edit_matkul(data):
    id_mata_kuliah = data.get('id_mata_kuliah')
    kode_prodi = data.get('kode_prodi')
    kode_mata_kuliah = data.get('kode_mata_kuliah')
    nama_mata_kuliah = data.get('nama_mata_kuliah')
    semester = data.get('semester')
    sks = data.get('sks')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE mata_kuliah
                SET 
                kode_prodi = %s,
                kode_mata_kuliah = %s, 
                nama_mata_kuliah = %s, 
                semester = %s, 
                sks = %s 
                WHERE 
                id_mata_kuliah = %s 
            """
            cursor.execute(sql, (kode_prodi, kode_mata_kuliah, nama_mata_kuliah, semester, sks, id_mata_kuliah))
            connection.commit()
        return jsonify({"message": "Berhasil mengubah mata kuliah"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def delete_matkul(data):
    id_mata_kuliah = data.get('id_mata_kuliah')
    
    if not id_mata_kuliah:
        return jsonify({"error": "Pengajar tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM mata_kuliah WHERE id_mata_kuliah = %s"
            cursor.execute(sql, (id_mata_kuliah,))
            connection.commit()
            return jsonify({"message": "Mata kuliah berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
