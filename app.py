import os
import random
import string
import base64

from io import BytesIO
from PIL import Image
from flask import Flask, flash, render_template, Response, request, session, jsonify, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit

from werkzeug.utils import secure_filename
from datetime import datetime

from function.koneksi import get_db_connection
from function.frontal import half_flip
from function.head_data import data_wajah
from function.video_process import generate_video, frontal_video, proses_img
from function.stopCam import stop_
from function.hashing import md5_hash

from controller.operator import *
from controller.prodi import *
from controller.kelas import *
from controller.pengajar import *

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = base64.b64encode(os.urandom(24)).decode('utf-8')

################################## Login / Logout / Session ##################################
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" 

class User(UserMixin):
    def __init__(self, id, nama, user_id, level):
        self.id = id
        self.nama = nama
        self.user_id = user_id 
        self.level = level

@login_manager.user_loader
def load_user(id_user):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM user WHERE id = %s', (id_user,))
        user = cursor.fetchone()
        connection.close()
        if user:
            return User(user['id'], user['nama'], user['no_id'], user['level'])
        else:
            cursor.execute('SELECT * FROM pengajar WHERE id_pengajar = %s', (id_user,))
            pengajar = cursor.fetchone()
            connection.close()
            if pengajar:
                return User(pengajar['id_pengajar'], pengajar['nama_pengajar'], pengajar['nip'], pengajar['kategori'])
            else:
                cursor.execute('SELECT * FROM mahasiswa WHERE id_mahasiswa = %s', (id_user,))
                mhs = cursor.fetchone()
                connection.close()
                if mhs:
                    return User(mhs['id_mahasiswa'], mhs['nama_mahasiswa'], mhs['nim'], "mahasiswa") 
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Cek password dengan hash untuk keamanan
        password_hash = md5_hash(password)

        # Koneksi ke database untuk verifikasi username dan password
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM user WHERE no_id = %s AND pass = %s', (username, password_hash))
            user = cursor.fetchone()
            connection.close()
            if user:
                user_obj = User(user['id'], user['nama'], user['no_id'], user['level'])
                login_user(user_obj)
                session['id'] = user['id']
                session['user_id'] = user['no_id']  
                session['nama'] = user['nama'] 
                session['level'] = user['level'] 
                return redirect(url_for('home'))
            else:
                cursor.execute('SELECT * FROM pengajar WHERE nip = %s AND password = %s', (username, password_hash))
                pengajar = cursor.fetchone()
                connection.close()
                if pengajar:
                    user_obj = User(pengajar['id_pengajar'], pengajar['nama_pengajar'], pengajar['nip'], pengajar['kategori'])
                    login_user(user_obj)
                    session['id'] = pengajar['id_pengajar']
                    session['user_id'] = pengajar['nip']  
                    session['nama'] = pengajar['nama_pengajar'] 
                    session['level'] = pengajar['kategori'] 
                    return redirect(url_for('home'))
                else:
                    cursor.execute('SELECT * FROM mahasiswa WHERE nim = %s AND password = %s', (username, password_hash))
                    mhs = cursor.fetchone()
                    connection.close()
                    if mhs:
                        user_obj = User(mhs['id_mahasiswa'], mhs['nama_mahasiswa'], mhs['nim'], "mahasiswa")
                        login_user(user_obj)
                        session['id'] = mhs['id_mahasiswa']
                        session['user_id'] = mhs['nim']  
                        session['nama'] = mhs['nama_mahasiswa'] 
                        session['level'] = "mahasiswa" 
                        return redirect(url_for('home'))
                    else:
                        return "Login gagal. Username atau password salah."

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('id', None) 
    session.pop('nama', None) 
    session.pop('user_id', None) 
    session.pop('level', None)   
    return redirect(url_for('login'))
################################## Login / Logout / Session ##################################

################################## Index ##################################
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
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
    return render_template('home.html', konten=konten, video=path, session=session)
################################## Index ##################################


################################## Fungsi Webcam / Video ##################################
@socketio.on('images')
def handle_image(data):
    proses_img(data)    

@app.route('/video_feed')
def video_feed():
    return Response(generate_video(socketio), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_frontal')
def video_frontal():
    return Response(frontal_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

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
################################## Fungsi Webcam / Video ##################################

################################## MODULE USER / OPERATOR ##################################
@app.route('/operator')
@login_required
def operator():
    konten = "operator"
    operator, error = get_operators()
    if error:
        return error, 500
    return render_template('home.html', operator=operator, konten=konten)

@app.route('/insert_operator', methods=['POST'])
@login_required
def add_record_user():
    data = request.get_json()
    return add_operator(data)

@app.route('/edit_operator', methods=['POST'])
@login_required
def edit_record_user():
    data = request.get_json()
    return edit_operator(data)

@app.route('/hapus_operator', methods=['POST'])
@login_required
def hapus_operator():
    data = request.get_json()
    return delete_operator(data)
################################## END MODULE USER / OPERATOR ##################################

################################## MODULE PRODI ##################################
@app.route('/prodi')
@login_required
def prodi():
    konten = "prodi"
    prodi, error = get_prodi()
    if error:
        return error, 500
    return render_template('home.html', prodi=prodi, konten=konten)

@app.route('/insert_prodi', methods=['POST'])
@login_required
def add_record_prodi():
    data = request.get_json()
    return add_prodi(data)

@app.route('/edit_prodi', methods=['POST'])
@login_required
def edit_record_prodi():
    data = request.get_json()
    return edit_prodi(data)

@app.route('/hapus_prodi', methods=['POST'])
@login_required
def hapus_prodi():
    data = request.get_json()
    return delete_prodi(data)
################################## END MODULE PRODI ##################################

################################## MODULE KELAS ##################################
@app.route('/kelas')
@login_required
def kelas():
    konten = "kelas"
    kelas, error = get_kelas()
    if error:
        return error, 500
    return render_template('home.html', kelas=kelas, konten=konten)

@app.route('/insert_kelas', methods=['POST'])
@login_required
def add_record_kelas():
    data = request.get_json()
    return add_kelas(data)

@app.route('/edit_kelas', methods=['POST'])
@login_required
def edit_record_kelas():
    data = request.get_json()
    return edit_kelas(data)

@app.route('/hapus_kelas', methods=['POST'])
@login_required
def hapus_kelas():
    data = request.get_json()
    return delete_kelas(data)
################################## END MODULE KELAS ##################################


################################## MODULE PENGAJAR ##################################
@app.route('/pengajar')
@login_required
def pengajar():
    konten = "pengajar"
    pengajar, error = get_pengajar()
    if error:
        return error, 500
    return render_template('home.html', pengajar=pengajar, konten=konten)

@app.route('/insert_pengajar', methods=['POST'])
@login_required
def add_record_pengajar():
    data = request.get_json()
    return add_pengajar(data)

@app.route('/edit_pengajar', methods=['POST'])
@login_required
def edit_record_pengajar():
    data = request.get_json()
    return edit_pengajar(data)

@app.route('/hapus_pengajar', methods=['POST'])
@login_required
def hapus_pengajar():
    data = request.get_json()
    return delete_pengajar(data)
################################## END MODULE PENGAJAR ##################################

################################## MODULE KONTEN ##################################
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
        return jsonify({"message": "Record inserted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

@app.route('/hapus/<int:id>', methods=['POST'])
def hapus(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT berkas FROM materi WHERE id = %s", (id,))
            result = cursor.fetchone()
            
            if result:
                berkas = result["berkas"] 
                berkas_path = os.path.join('static', 'materi', berkas)  
                
                if os.path.exists(berkas_path):
                    os.remove(berkas_path) 
                
                cursor.execute("DELETE FROM materi WHERE id = %s", (id,))
                connection.commit()
                return jsonify({"message": "Record deleted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()    
    return redirect(url_for('add_content'))
################################## END MODULE KONTEN ##################################

################################## DEBUG DB ##################################
@app.route('/debug_db')
def debug_db():
    konten = "debug_db"
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            # Menyiapkan list untuk menyimpan field dari setiap tabel
            table_fields = {}
            for table in tables:
                # Mengambil nama kolom pertama dari hasil query (karena hasil SHOW TABLES hanya punya satu kolom)
                table_name = list(table.values())[0]  # Menyesuaikan jika kolom hasilnya adalah nama tabel

                cursor.execute(f"DESCRIBE {table_name}")  # Dapatkan field tabel
                fields = cursor.fetchall()
                table_fields[table_name] = fields
            return render_template('home.html', table_fields=table_fields, konten=konten)
    finally:
        connection.close()

################################## END DEBUG DB ##################################


if __name__ == '__main__':
    #app.run(debug=True, threaded=True)
    socketio.run(app, debug=True)
