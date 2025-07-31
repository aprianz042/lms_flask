import os
import pymysql
import hashlib
import random
import string
import time
import json
import cv2

from flask import Flask, flash, render_template, Response, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from datetime import datetime

from function.frontal import half_flip
from function.head_data import data_wajah
from function.video_process import generate_video, frontal_video
from function.stopCam import stop_

from deepface import DeepFace

app = Flask(__name__)
socketio = SocketIO(app)

host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_DATABASE')

#global cap
#cap = cv2.VideoCapture(0)
#if not cap:
#    cap.release()

def get_db_connection():
    try:
        connection = pymysql.connect(host=host,
                                       user=user,
                                       password=password,
                                       database=database,
                                       cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/data')
def data():
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database.", 500  
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM user')
            users = cursor.fetchall()  
            
            cursor.execute('SELECT * FROM materi')
            materi = cursor.fetchall() 
    finally:
        connection.close() 

    return render_template('data.html', users=users, materi=materi)

# Route utama untuk halaman web
@app.route('/')
def index():
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database.", 500
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT berkas FROM materi WHERE id = 7')
            path = cursor.fetchone()  
            if path:
                path = path['berkas']
            else:
                path = None 
            konten = "video"       
    finally:
        connection.close() 
    return render_template('home.html', konten=konten, video=path)

# Route untuk menangani video stream
@app.route('/video_feed')
def video_feed():
    return Response(generate_video(socketio), mimetype='multipart/x-mixed-replace; boundary=frame')

#@app.route('/video_frontal')
#def video_frontal():
#    return Response(frontal_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/debug_video')
def debug_video():
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database.", 500
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT berkas FROM materi WHERE id = 1')
            path = cursor.fetchone()  
            if path:
                path = path['berkas']
            else:
                path = None 
            konten = "debug"       
    finally:
        connection.close()  # Pastikan koneksi ditutup setelah selesai
    return render_template('home.html', konten=konten, video=path)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/add_user')
def add_user():
    konten = "add_user"
    return render_template('home.html', konten=konten)

@app.route('/add_kelas')
def add_kelas():
    konten = "add_kelas"
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database.", 500 
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM kelas')
            kelas = cursor.fetchall() 
    finally:
        connection.close() 
    return render_template('home.html', kelas=kelas, konten=konten)

@app.route('/add_content')
def add_content():
    konten = "add_content"
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database.", 500 
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM materi')
            materi = cursor.fetchall() 

            cursor.execute('SELECT * FROM mata_kuliah')
            matkul = cursor.fetchall() 

            cursor.execute('SELECT * FROM pengajar WHERE kategori = "dosen" ')
            pengajar = cursor.fetchall()

            cursor.execute('SELECT * FROM kelas')
            kelas = cursor.fetchall() 
    finally:
        connection.close() 
    return render_template('home.html', materi=materi, konten=konten, matkul=matkul, pengajar=pengajar, kelas=kelas)

@app.route('/add_pengajar')
def add_pengajar():
    konten = "add_pengajar"
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database.", 500 
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM pengajar')
            pengajar = cursor.fetchall() 
    finally:
        connection.close() 
    return render_template('home.html', pengajar=pengajar, konten=konten)


def md5_hash(password):
    # Menghasilkan hash MD5 dari password
    return hashlib.md5(password.encode()).hexdigest()

# Endpoint untuk menambah data
@app.route('/insert_user', methods=['POST'])
def add_record_user():
    # Ambil data dari request JSON
    data = request.get_json()
    
    nama = data.get('nama')
    no_id = data.get('no_id')
    level = data.get('level')
    email = data.get('email')
    password = data.get('password')
    hashed_password = md5_hash(password)
        
    # Validasi input
    if level == 0:
        return jsonify({"error": "Level tidak boleh kosong"}), 400
    
    # Insert data ke database
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO user (nama, no_id, email, pass, level) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nama, no_id, email, hashed_password, level))
            connection.commit()
        return jsonify({"message": "Record inserted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

@app.route('/insert_kelas', methods=['POST'])
def add_record_kelas():
    # Ambil data dari request JSON
    data = request.get_json()
    nama_kelas = data.get('nama_kelas')

    # Cek apakah nama_kelas sudah ada di database
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Cek apakah nama kelas sudah ada
            check_sql = "SELECT COUNT(*) FROM kelas WHERE nama_kelas = %s"
            cursor.execute(check_sql, (nama_kelas,))  # Pastikan tuple dengan koma
            result = cursor.fetchone()

            print(result)
            
            # Cek hasil query, jika kelas sudah ada
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "Nama kelas sudah ada!"}), 400


            # Insert data ke database
            insert_sql = "INSERT INTO kelas (nama_kelas) VALUES (%s)"
            cursor.execute(insert_sql, (nama_kelas,))
            connection.commit()

        return jsonify({"message": "Kelas berhasil ditambahkan"}), 201
    except Exception as e:
        print(f"Error: {e}")  # Menampilkan error di console untuk debugging
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

@app.route('/insert_pengajar', methods=['POST'])
def add_record_pengajar():
    # Ambil data dari request JSON
    data = request.get_json()
    
    # Ambil data dari JSON
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

    # Cek apakah nip, email, atau nomor_hp sudah ada di database
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Cek apakah nip, email, atau nomor_hp sudah ada
            check_sql = """
                SELECT COUNT(*) 
                FROM pengajar 
                WHERE nip = %s OR email = %s OR nomor_hp = %s
            """
            cursor.execute(check_sql, (nip, email, nomor_hp))  # Pastikan tuple dengan koma
            result = cursor.fetchone()

            print(result)
            
            # Cek hasil query, jika data sudah ada
            if result["COUNT(*)"] > 0:
                return jsonify({"error": "NIP, email, atau nomor HP sudah ada!"}), 400

            # Insert data ke database
            insert_sql = """
                INSERT INTO pengajar (nama_pengajar, nip, email, nomor_hp, alamat, program_studi, kategori, jabatan, tanggal_lahir, pendidikan_terakhir, password, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s %s, %s, %s)
            """
            cursor.execute(insert_sql, (nama_pengajar, nip, email, nomor_hp, alamat, program_studi, kategori, jabatan, tanggal_lahir, pendidikan_terakhir, hashed_password, status))
            connection.commit()

        return jsonify({"message": "Pengajar berhasil ditambahkan"}), 201
    except Exception as e:
        print(f"Error: {e}")  # Menampilkan error di console untuk debugging
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


ALLOWED_EXTENSIONS = {'pdf', 'mp4', 'docx', 'xlsx', 'rar', 'zip'}  # Daftar ekstensi yang diizinkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_filename(extension):
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    now = datetime.now()
    timestamp = now.strftime("%d%m%Y_%H%M%S")  # Format: tanggal_bulan_tahun_jam_menit_detik
    filename = f"IPDN_{random_string}_{timestamp}.{extension}"
    return filename

@app.route('/insert_content', methods=['POST'])
def add_record_content():
    # Ambil data dari request form
    data = request.form  # Mengambil data form, bukan JSON karena ada file
    
    id_mata_kuliah = data.get('mata_kuliah')
    id_kelas =  data.get('kelas')
    tahun_ajaran = data.get('tahun_ajaran')
    semester = data.get('semester')
    judul_materi = data.get('judul')
    jenis = data.get('jenis')
    deskripsi = data.get('deskripsi')
    kategori = data.get('kategori')
    id_pengampu = data.get('id_pengampu')
    berkas = request.files['berkas']  # Ambil file dari input "berkas"

    # Validasi input
    if jenis == "0" or kategori == "0" or id_pengampu == "0" or id_mata_kuliah == "0":
        return jsonify({"error": "Jenis dan Kategori tidak boleh kosong"}), 400

    if not berkas:
        return jsonify({"error": "Berkas tidak boleh kosong"}), 400

    # Periksa ekstensi file
    if not allowed_file(berkas.filename):
        return jsonify({"error": "Tipe file tidak diizinkan. Hanya file PDF, video, dan audio yang diperbolehkan."}), 400

    # Mengambil ekstensi file
    extension = berkas.filename.rsplit('.', 1)[1].lower()
    
    # Generate nama file baru
    filename = generate_filename(extension)

    # Menyimpan file yang diupload ke folder yang ditentukan
    upload_folder = os.path.join('static', 'materi')  # Folder penyimpanan file
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)  # Membuat folder jika belum ada
    file_path = os.path.join(upload_folder, filename)
    berkas.save(file_path)  # Menyimpan file di folder

    # Insert data ke database
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO materi (id_mata_kuliah, id_kelas, tahun_ajaran, semester, judul_materi, jenis, deskripsi, kategori, berkas, id_pengampu)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Menyimpan nama file yang diupload ke database
            cursor.execute(sql, (id_mata_kuliah, id_kelas, tahun_ajaran, semester ,judul_materi, jenis, deskripsi, kategori, filename, id_pengampu))
            connection.commit()
        return jsonify({"message": "Record inserted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


# Fungsi untuk menghapus data berdasarkan id
@app.route('/hapus/<int:id>', methods=['POST'])
def hapus(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Query untuk mendapatkan nama berkas berdasarkan id
            cursor.execute("SELECT berkas FROM materi WHERE id = %s", (id,))
            result = cursor.fetchone()
            
            if result:
                berkas = result["berkas"]  # Ambil nama berkas
                berkas_path = os.path.join('static', 'materi', berkas)  # Lokasi file yang akan dihapus
                
                # Cek jika file ada dan hapus file
                if os.path.exists(berkas_path):
                    os.remove(berkas_path)  # Menghapus file dari direktori
                
                # Query untuk menghapus materi berdasarkan id
                cursor.execute("DELETE FROM materi WHERE id = %s", (id,))
                connection.commit()
                return jsonify({"message": "Record deleted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
    
    # Setelah berhasil menghapus, redirect kembali ke halaman utama
    return redirect(url_for('add_content'))

if __name__ == '__main__':
    #app.run(debug=True, threaded=True)
    socketio.run(app, debug=True)
