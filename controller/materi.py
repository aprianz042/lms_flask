import os
from function.generate_file import *
from flask import jsonify, request
from function.koneksi import get_db_connection

ALLOWED_EXTENSIONS = {'pdf', 'mp4', 'docx', 'xlsx', 'rar', 'zip'}  # Daftar ekstensi yang diizinkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_materi(id):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_select = """
                SELECT 
                    m.id, m.id_mata_kuliah, m.id_kelas, m.tahun_ajaran, m.semester, m.judul_materi, m.jenis, m.deskripsi, m.kategori, m.berkas, m.id_pengampu,
                    mk.nama_mata_kuliah,
                    kl.nama_kelas,
                    p.id_pengajar,
                    pg.nama_pengajar
                FROM 
                    materi m
                JOIN
                    mata_kuliah mk ON m.id_mata_kuliah = mk.id_mata_kuliah
                JOIN 
                    kelas kl ON m.id_kelas = kl.id_kelas
                JOIN
                    pengampu p ON m.id_pengampu = p.id_pengampu
                JOIN 
                    pengajar pg ON p.id_pengajar = pg.id_pengajar
                WHERE m.id_pengampu = %s;"""
            cursor.execute(sql_select, (id))
            materi = cursor.fetchall() 

            cursor.execute('SELECT * FROM mata_kuliah')
            mata_kuliah = cursor.fetchall()
        return materi, mata_kuliah, None
    finally:
        connection.close()

def add_materi(data):
    id_mata_kuliah = data.get('mata_kuliah')
    id_kelas =  data.get('kelas')
    tahun_ajaran = data.get('tahun_ajaran')
    semester = data.get('semester')
    judul_materi = data.get('judul')
    jenis = data.get('jenis')
    deskripsi = data.get('deskripsi')
    kategori = data.get('kategori')
    id_pengampu = data.get('id_pengampu')
    berkas = request.files['berkas'] 

    if jenis == "0" or kategori == "0" or id_pengampu == "0" or id_mata_kuliah == "0":
        return jsonify({"error": "Jenis dan Kategori tidak boleh kosong"}), 400
    if not berkas:
        return jsonify({"error": "Berkas tidak boleh kosong"}), 400
    if not allowed_file(berkas.filename):
        return jsonify({"error": "Tipe file tidak diizinkan. Hanya file PDF, video, dan audio yang diperbolehkan."}), 400
    extension = berkas.filename.rsplit('.', 1)[1].lower()
    filename = generate_filename(extension)
    upload_folder = os.path.join('static', 'materi')  
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)  
    file_path = os.path.join(upload_folder, filename)
    berkas.save(file_path) 
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO materi (id_mata_kuliah, id_kelas, tahun_ajaran, semester, judul_materi, jenis, deskripsi, kategori, berkas, id_pengampu)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (id_mata_kuliah, id_kelas, tahun_ajaran, semester ,judul_materi, jenis, deskripsi, kategori, filename, id_pengampu))
            connection.commit()
        return jsonify({"message": "Berhasil tambah materi"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def edit_materi(data):
    id_materi = data.get('id_materi')
    id_mata_kuliah = data.get('mata_kuliah')
    id_kelas =  data.get('kelas')
    tahun_ajaran = data.get('tahun_ajaran')
    semester = data.get('semester')
    judul_materi = data.get('judul')
    jenis = data.get('jenis')
    deskripsi = data.get('deskripsi')
    kategori = data.get('kategori')
    id_pengampu = data.get('id_pengampu')
    berkas = request.files['berkas'] 

    if jenis == "0" or kategori == "0" or id_pengampu == "0" or id_mata_kuliah == "0":
        return jsonify({"error": "Jenis dan Kategori tidak boleh kosong"}), 400
    if not berkas:
        return jsonify({"error": "Berkas tidak boleh kosong"}), 400
    if not allowed_file(berkas.filename):
        return jsonify({"error": "Tipe file tidak diizinkan. Hanya file PDF, video, dan audio yang diperbolehkan."}), 400
    extension = berkas.filename.rsplit('.', 1)[1].lower()
    filename = generate_filename(extension)
    upload_folder = os.path.join('static', 'materi')  
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)  
    file_path = os.path.join(upload_folder, filename)
    berkas.save(file_path) 
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE 
                    materi 
                SET 
                    id_mata_kuliah = %s, 
                    id_kelas = %s, 
                    tahun_ajaran = %s, 
                    semester = %s, 
                    judul_materi = %s, 
                    jenis = %s, 
                    deskripsi = %s, 
                    kategori = %s, 
                    berkas = %s, 
                    id_pengampu = %s
                WHERE 
                    id_materi = %s
            """
            cursor.execute(sql, (id_mata_kuliah, id_kelas, tahun_ajaran, semester ,judul_materi, jenis, deskripsi, kategori, filename, id_pengampu, id_materi))
            connection.commit()
        return jsonify({"message": "Berhasil ubah materi"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def delete_materi(data):
    id_materi = data.get('id_materi')
    
    if not id_materi:
        return jsonify({"error": "Kelas tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM materi WHERE id_materi = %s"
            cursor.execute(sql, (id_materi,))
            connection.commit()
            return jsonify({"message": "Kelas berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
