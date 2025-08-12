from flask import jsonify
from function.koneksi import get_db_connection

def get_kelas():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM kelas')
            kelas = cursor.fetchall()
        return kelas, None
    finally:
        connection.close()

def add_kelas(data):
    nama_kelas = data.get('nama_kelas')
     
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            check_sql = "SELECT COUNT(*) FROM kelas WHERE nama_kelas = %s"
            cursor.execute(check_sql, (nama_kelas,))  
            result = cursor.fetchone() 
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "Nama kelas Tidak Boleh Sama!"}), 400

            sql = "INSERT INTO kelas (nama_kelas) VALUES (%s)"
            cursor.execute(sql, (nama_kelas))
            connection.commit()
        return jsonify({"message": "Berhasil menambahkan kelas"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def edit_kelas(data):
    id_kelas = data.get('id_kelas')
    nama_kelas = data.get('nama_kelas')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            check_sql = "SELECT COUNT(*) FROM kelas WHERE nama_kelas = %s"
            cursor.execute(check_sql, (nama_kelas,))  
            result = cursor.fetchone() 
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "Nama kelas Tidak Boleh Sama!"}), 400

            sql = "UPDATE kelas SET nama_kelas = %s WHERE id_kelas = %s"
            cursor.execute(sql, (nama_kelas, id_kelas))
            connection.commit()
        return jsonify({"message": "Berhasil mengubah prodi"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def delete_kelas(data):
    id_kelas = data.get('id_kelas')
    
    if not id_kelas:
        return jsonify({"error": "Kelas tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM kelas WHERE id_kelas = %s"
            cursor.execute(sql, (id_kelas,))
            connection.commit()
            return jsonify({"message": "Kelas berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
