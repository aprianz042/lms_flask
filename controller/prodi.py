from flask import jsonify
from function.koneksi import get_db_connection
from function.hashing import md5_hash

# Fungsi untuk mendapatkan data operator
def get_prodi():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM prodi')
            operator = cursor.fetchall()
        return operator, None
    finally:
        connection.close()

# Fungsi untuk menambahkan operator
def add_prodi(data):
    kode_prodi = data.get('kode_prodi')
    nama_prodi = data.get('nama_prodi')
     
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            check_sql = "SELECT COUNT(*) FROM prodi WHERE kode_prodi = %s"
            cursor.execute(check_sql, (kode_prodi,))  
            result = cursor.fetchone() 
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "Kode Prodi Tidak Boleh Sama!"}), 400

            sql = "INSERT INTO prodi (kode_prodi, nama_prodi) VALUES (%s, %s)"
            cursor.execute(sql, (kode_prodi, nama_prodi))
            connection.commit()
        return jsonify({"message": "Berhasil menambahkan prodi"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Fungsi untuk mengedit operator
def edit_prodi(data):
    id_prodi = data.get('id_prodi')
    kode_prodi = data.get('kode_prodi')
    nama_prodi = data.get('nama_prodi')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE prodi SET kode_prodi = %s, nama_prodi = %s WHERE id_prodi = %s"
            cursor.execute(sql, (kode_prodi, nama_prodi, id_prodi))
            connection.commit()
        return jsonify({"message": "Berhasil mengubah prodi"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Fungsi untuk menghapus operator
def delete_prodi(data):
    operator_id = data.get('id_prodi')
    
    if not operator_id:
        return jsonify({"error": "ID operator tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM prodi WHERE id_prodi = %s"
            cursor.execute(sql, (operator_id,))
            connection.commit()
            return jsonify({"message": "Prodi berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
