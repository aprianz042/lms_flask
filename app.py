import os
import cv2
import numpy as np
from flask import Flask, render_template, Response, request, jsonify
from deepface import DeepFace
import pymysql
import hashlib
from werkzeug.utils import secure_filename
import random
import string
from datetime import datetime

app = Flask(__name__)

# Konfigurasi koneksi MySQL menggunakan PyMySQL
host = 'ipdnkalbar.ac.id'
user = 'u1049330_tesis'
password = 'kodokloncat'
database = 'u1049330_tesis'

# Fungsi untuk mendapatkan koneksi ke database MySQL dengan penanganan kesalahan
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
        return None  # Jika koneksi gagal, kembalikan None

# Route untuk menampilkan semua data user dan materi
@app.route('/data')
def data():
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database.", 500  # Mengembalikan error jika koneksi gagal

    try:
        with connection.cursor() as cursor:
            # Menjalankan query untuk mengambil semua data dari tabel user
            cursor.execute('SELECT * FROM user')
            users = cursor.fetchall()  # Mengambil semua data yang di-query
            
            # Menjalankan query untuk mengambil semua data dari tabel materi
            cursor.execute('SELECT * FROM materi')
            materi = cursor.fetchall()  # Mengambil semua materi dari tabel materi
    finally:
        connection.close()  # Pastikan koneksi ditutup setelah selesai

    return render_template('data.html', users=users, materi=materi)

# Fungsi untuk menganalisis emosi wajah menggunakan DeepFace
def analyze_emotion(frame):
    try:
        # Menganalisis wajah dari frame
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        # Mengambil emosi yang dominan
        dominant_emotion = analysis[0]['dominant_emotion']
        return dominant_emotion
    except Exception as e:
        return "Error in analysis"

# Fungsi untuk menangani video stream
def generate_video():
    # Inisialisasi webcam
    cap = cv2.VideoCapture(0)  # 0 berarti webcam default

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Ubah frame ke format yang bisa ditampilkan di HTML
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Analisis emosi menggunakan DeepFace
        dominant_emotion = analyze_emotion(frame)

        # Tulis teks emosi di frame
        cv2.putText(frame, f"Emotion: {dominant_emotion}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Encode frame sebagai JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        # Hasilkan frame dalam format yang bisa ditampilkan
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

    cap.release()

# Route utama untuk halaman web
@app.route('/')
def index():
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
            konten = "video"       
    finally:
        connection.close()  # Pastikan koneksi ditutup setelah selesai
    return render_template('home.html', konten=konten, video=path)

# Route untuk menangani video stream
@app.route('/video_feed')
def video_feed():
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/add_user')
def add_user():
    konten = "add_user"
    return render_template('home.html', konten=konten)

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
    finally:
        connection.close() 
    return render_template('home.html', materi=materi, konten=konten)


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
    mata_kuliah = data.get('mata_kuliah')
    judul = data.get('judul')
    jenis = data.get('jenis')
    deskripsi = data.get('deskripsi')
    kategori = data.get('kategori')
    id_pengampu = data.get('id_pengampu')
    berkas = request.files['berkas']  # Ambil file dari input "berkas"

    # Validasi input
    if jenis == "0" or kategori == "0":
        return jsonify({"error": "Jenis dan Kategori tidak boleh kosong"}), 400

    if not berkas:
        return jsonify({"error": "Berkas tidak boleh kosong"}), 400

    if not mata_kuliah or not judul or not deskripsi or not id_pengampu:
        return jsonify({"error": "Semua field (Mata Kuliah, Judul, Deskripsi, Dosen/Pelatih) harus diisi"}), 400

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
                INSERT INTO materi (mata_kuliah, judul, jenis, deskripsi, kategori, berkas, id_pengampu)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            # Menyimpan nama file yang diupload ke database
            cursor.execute(sql, (mata_kuliah, judul, jenis, deskripsi, kategori, filename, id_pengampu))
            connection.commit()
        return jsonify({"message": "Record inserted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    app.run(debug=True)
