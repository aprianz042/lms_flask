from flask import jsonify
from function.koneksi import get_db_connection
from function.hashing import md5_hash


def get_pengajar():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM pengajar')
            pengajar = cursor.fetchall() 
        return pengajar, None
    finally:
        connection.close()


def add_pengajar(data):
    nama_pengajar = data.get('nama_pengajar')
    nip = data.get('nip')
    email = data.get('email')
    nomor_hp = data.get('nomor_hp')
    alamat = data.get('alamat')
    program_studi = data.get('program_studi')
    kategori = data.get('kategori')
    jabatan = data.get('jabatan')
    tanggal_lahir = data.get('tanggal_lahir')
    pendidikan_terakhir = data.get('pendidikan_terakhir')
    status = data.get('status')
    password = data.get('password')
    hashed_password = md5_hash(password)
     
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            check_sql = """
                SELECT COUNT(*) 
                FROM pengajar 
                WHERE nip = %s OR email = %s OR nomor_hp = %s
            """
            cursor.execute(check_sql, (nip, email, nomor_hp))  # Pastikan tuple dengan koma
            result = cursor.fetchone()
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "NIP, email, atau nomor HP sudah ada!"}), 400

            insert_sql = """
                INSERT INTO pengajar (nama_pengajar, nip, email, nomor_hp, alamat, program_studi, kategori, jabatan, tanggal_lahir, pendidikan_terakhir, password, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (nama_pengajar, nip, email, nomor_hp, alamat, program_studi, kategori, jabatan, tanggal_lahir, pendidikan_terakhir, hashed_password, status))
            connection.commit()
        return jsonify({"message": "Berhasil menambahkan pengajar"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def edit_pengajar(data):
    id_pengajar = data.get('id_pengajar')
    nama_pengajar = data.get('nama_pengajar')
    nip = data.get('nip')
    email = data.get('email')
    nomor_hp = data.get('nomor_hp')
    alamat = data.get('alamat')
    program_studi = data.get('program_studi')
    kategori = data.get('kategori')
    jabatan = data.get('jabatan')
    tanggal_lahir = data.get('tanggal_lahir')
    pendidikan_terakhir = data.get('pendidikan_terakhir')
    status = data.get('status')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE pengajar
                SET 
                nama_pengajar = %s, 
                nip = %s, 
                email = %s, 
                nomor_hp = %s, 
                alamat = %s, 
                program_studi = %s, 
                kategori = %s, 
                jabatan = %s, 
                tanggal_lahir = %s, 
                pendidikan_terakhir = %s, 
                status = %s 
                WHERE 
                id_pengajar = %s 
            """
            cursor.execute(sql, (nama_pengajar, nip, email, nomor_hp, alamat, program_studi, kategori, jabatan, tanggal_lahir, pendidikan_terakhir, status, id_pengajar))
            connection.commit()
        return jsonify({"message": "Berhasil mengubah pengajar"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def delete_pengajar(data):
    id_pengajar = data.get('id_pengajar')
    
    if not id_pengajar:
        return jsonify({"error": "Pengajar tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM pengajar WHERE id_pengajar = %s"
            cursor.execute(sql, (id_pengajar,))
            connection.commit()
            return jsonify({"message": "Pengajar berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
