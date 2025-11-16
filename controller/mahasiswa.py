from flask import jsonify
from function.koneksi import get_db_connection
from function.hashing import md5_hash


def get_mahasiswa():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            sql_data = """
                SELECT 
                    m.*,
                    k.nama_kelas
                FROM 
                    mahasiswa m
                JOIN 
                    kelas k ON m.id_kelas = k.id_kelas
                ORDER BY 
                    k.nama_kelas ASC, m.nama_mahasiswa ASC;
                """
            cursor.execute(sql_data)
            mahasiswa = cursor.fetchall() 

            cursor.execute('SELECT * FROM prodi')
            prodi = cursor.fetchall() 

            cursor.execute('SELECT * FROM provinsi')
            provinsi = cursor.fetchall() 

            cursor.execute('SELECT * FROM kelas')
            kelas = cursor.fetchall() 
        return mahasiswa, prodi, provinsi, kelas, None
    finally:
        connection.close()


def add_mahasiswa(data):
    nama_mahasiswa = data.get('nama_mahasiswa')
    nim = data.get('nim')
    email = data.get('email')
    asdaf = data.get('asdaf')
    nomor_telepon = data.get('nomor_telepon')
    program_studi = data.get('program_studi')
    kelas = data.get('kelas')
    password = md5_hash(nim)
    tahun_angkatan = data.get('tahun_angkatan')
    tanggal_lahir = data.get('tanggal_lahir')
    jenis_kelamin = data.get('jenis_kelamin')
     
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            check_sql = """
                SELECT COUNT(*) 
                FROM mahasiswa 
                WHERE nim = %s OR email = %s OR nomor_telepon = %s
            """
            cursor.execute(check_sql, (nim, email, nomor_telepon))  # Pastikan tuple dengan koma
            result = cursor.fetchone()
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "NIM, email, atau nomor HP sudah ada!"}), 400

            insert_sql = """
                INSERT INTO mahasiswa 
                (nama_mahasiswa, 
                nim, 
                email, 
                asdaf, 
                nomor_telepon, 
                program_studi, 
                id_kelas, 
                password, 
                tahun_angkatan, 
                tanggal_lahir, 
                jenis_kelamin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                nama_mahasiswa,
                nim,
                email,
                asdaf,
                nomor_telepon,
                program_studi,
                kelas,
                password,
                tahun_angkatan,
                tanggal_lahir,
                jenis_kelamin
            ))
            connection.commit()

        return jsonify({"message": "Berhasil menambahkan mahasiswa"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def edit_mahasiswa(data):
    id_mahasiswa = data.get('id_mahasiswa')
    nama_mahasiswa = data.get('nama_mahasiswa')
    nim = data.get('nim')
    email = data.get('email')
    asdaf = data.get('asdaf')
    nomor_telepon = data.get('nomor_telepon')
    program_studi = data.get('program_studi')
    kelas = data.get('kelas')
    tahun_angkatan = data.get('tahun_angkatan')
    tanggal_lahir = data.get('tanggal_lahir')
    jenis_kelamin = data.get('jenis_kelamin')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE mahasiswa
                SET 
                    nama_mahasiswa = %s, 
                    nim = %s, 
                    email = %s, 
                    asdaf = %s, 
                    nomor_telepon = %s, 
                    program_studi = %s, 
                    id_kelas = %s, 
                    tahun_angkatan = %s, 
                    tanggal_lahir = %s, 
                    jenis_kelamin = %s
                WHERE 
                    id_mahasiswa = %s
            """
            cursor.execute(sql, (
                nama_mahasiswa, 
                nim, 
                email, 
                asdaf, 
                nomor_telepon, 
                program_studi, 
                kelas, 
                tahun_angkatan, 
                tanggal_lahir, 
                jenis_kelamin, 
                id_mahasiswa
            ))
            connection.commit()

        return jsonify({"message": "Berhasil mengubah mahasiswa"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def delete_mahasiswa(data):
    id_mahasiswa = data.get('id_mahasiswa')
    
    if not id_mahasiswa:
        return jsonify({"error": "Mahasiswa tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM mahasiswa WHERE id_mahasiswa = %s"
            cursor.execute(sql, (id_mahasiswa,))
            connection.commit()
            return jsonify({"message": "Mahasiswa berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
