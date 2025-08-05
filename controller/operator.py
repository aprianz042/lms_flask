from flask import jsonify
from function.koneksi import get_db_connection
from function.hashing import md5_hash

# Fungsi untuk mendapatkan data operator
def get_operators():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM user WHERE level = "operator"')
            operator = cursor.fetchall()
        return operator, None
    finally:
        connection.close()

# Fungsi untuk menambahkan operator
def add_operator(data):
    nama = data.get('nama')
    no_id = data.get('no_id')
    level = data.get('level')
    email = data.get('email')
    password = data.get('password')
    hashed_password = md5_hash(password)
    
    if level == 0:
        return jsonify({"error": "Level tidak boleh kosong"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO user (nama, no_id, email, pass, level) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nama, no_id, email, hashed_password, level))
            connection.commit()
        return jsonify({"message": "Berhasil menambahkan operator"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Fungsi untuk mengedit operator
def edit_operator(data):
    id = data.get('id')
    nama = data.get('nama')
    no_id = data.get('no_id')
    level = data.get('level')
    email = data.get('email')
    
    if not level:
        return jsonify({"error": "Level tidak boleh kosong"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE user SET nama = %s, no_id = %s, email = %s, level = %s WHERE id = %s"
            cursor.execute(sql, (nama, no_id, email, level, id))
            connection.commit()
        return jsonify({"message": "Berhasil mengubah operator"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Fungsi untuk menghapus operator
def delete_operator(data):
    operator_id = data.get('id')
    
    if not operator_id:
        return jsonify({"error": "ID operator tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM user WHERE id = %s"
            cursor.execute(sql, (operator_id,))
            connection.commit()
            return jsonify({"message": "Operator berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
