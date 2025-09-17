import os
import base64
import json
import random
import string

from collections import Counter, defaultdict

from flask import Flask, flash, render_template, Response, request, session, jsonify, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit

from function.koneksi import get_db_connection
from function.head_data import *
from function.video_process import *
from function.stopCam import *
from function.hashing import *
from function.generate_file import *
from function.login_process import*

from controller.home import *
from controller.operator import *
from controller.prodi import *
from controller.kelas import *
from controller.pengajar import *
from controller.matkul import *
from controller.mahasiswa import *
from controller.pengampu import *
from controller.krs import *
from controller.pengajaran import *
from controller.materi import *
from controller.daftarMatkul import *
from controller.materiKuliah import *
from controller.enrollment import *
from controller.save_emo import *
from controller.emotion import *


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
    id, nama, no_id, level = proses_login(id_user)
    return User(id, nama, no_id, level) 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = md5_hash(password)
        id, no_id, nama, level = get_session_user(username, password_hash)
        if id:
            user_obj = User(id, nama, no_id, level)
            login_user(user_obj)
            session['id'] = id
            session['user_id'] = no_id
            session['nama'] = nama
            session['level'] = level
            return redirect(url_for('home'))
        else:
            return jsonify({"error": "Username / Password Salah !!!"}), 400
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

################################## Fungsi Webcam / Video ##################################
@socketio.on('images')
def handle_image(data):
    proses_img(data)    

#@app.route('/video_feed')
#def video_feed():
#    return Response(generate_video(socketio), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_frontal')
def video_frontal():
    return Response(frontal_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/debug_video')
def debug_video():
    konten = "debug_video"
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
    finally:
        connection.close()  # Pastikan koneksi ditutup setelah selesai
    return render_template('home.html', konten=konten, video=path, session=session)
################################## Fungsi Webcam / Video ##################################

################################## Index / HOME ##################################
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    konten = "home" 
    data_home, error = get_data_home()
    if error:
        return error, 500
    return render_template('home.html', data_home=data_home, konten=konten, session=session)
################################## Index / HOME ##################################


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


################################## MODULE MATAKULIAH ##################################
@app.route('/matkul')
@login_required
def matkul():
    konten = "matkul"
    matkul, daftar_prodi, error = get_matkul()
    if error:
        return error, 500
    return render_template('home.html', matkul=matkul, daftar_prodi=daftar_prodi, konten=konten)

@app.route('/insert_matkul', methods=['POST'])
@login_required
def add_record_matkul():
    data = request.get_json()
    return add_matkul(data)

@app.route('/edit_matkul', methods=['POST'])
@login_required
def edit_record_matkul():
    data = request.get_json()
    return edit_matkul(data)

@app.route('/hapus_matkul', methods=['POST'])
@login_required
def hapus_matkul():
    data = request.get_json()
    return delete_matkul(data)
################################## END MODULE MATAKULIAH ##################################


################################## MODULE MAHASISWA ##################################
@app.route('/mahasiswa')
@login_required
def mahasiswa():
    konten = "mahasiswa"
    mahasiswa, daftar_prodi, prov, kelas, error = get_mahasiswa()
    if error:
        return error, 500
    return render_template('home.html', 
                           mahasiswa=mahasiswa, 
                           daftar_prodi=daftar_prodi, 
                           prov=prov, 
                           kelas=kelas, 
                           konten=konten)

@app.route('/insert_mahasiswa', methods=['POST'])
@login_required
def add_record_mahasiswa():
    data = request.get_json()
    return add_mahasiswa(data)

@app.route('/edit_mahasiswa', methods=['POST'])
@login_required
def edit_record_mahasiswa():
    data = request.get_json()
    return edit_mahasiswa(data)

@app.route('/hapus_mahasiswa', methods=['POST'])
@login_required
def hapus_mahasiswa():
    data = request.get_json()
    return delete_mahasiswa(data)
################################## END MODULE MAHASISWA ##################################


################################## MODULE PENGAMPU ##################################
@app.route('/pengampu')
@login_required
def pengampu():
    konten = "pengampu"
    pengampu, daftar_prodi, pengajar, matkul, kelas, error = get_pengampu()
    if error:
        return error, 500
    return render_template('home.html', 
                           pengampu=pengampu, 
                           daftar_prodi=daftar_prodi, 
                           pengajar=pengajar,
                           matkul=matkul, 
                           kelas=kelas, 
                           konten=konten)

@app.route('/insert_pengampu', methods=['POST'])
@login_required
def add_record_pengampu():
    data = request.get_json()
    return add_pengampu(data)

@app.route('/edit_pengampu', methods=['POST'])
@login_required
def edit_record_pengampu():
    data = request.get_json()
    return edit_pengampu(data)

@app.route('/hapus_pengampu', methods=['POST'])
@login_required
def hapus_pengampu():
    data = request.get_json()
    return delete_pengampu(data)
################################## END MODULE PENGAMPU ##################################

################################## MODULE KRS ##################################
@app.route('/krs')
@login_required
def krs():
    konten = "krs"
    data, d_krs, error = get_krs()
    if error:
        return error, 500
    return render_template('home.html', 
                           data=data, 
                           d_krs=d_krs,
                           konten=konten)

@app.route('/insert_krs', methods=['POST'])
@login_required
def add_record_krs():
    data = request.get_json()
    return add_krs(data)

@app.route('/edit_krs', methods=['POST'])
@login_required
def edit_record_krs():
    data = request.get_json()
    return edit_krs(data)

@app.route('/hapus_krs', methods=['POST'])
@login_required
def hapus_krs():
    data = request.get_json()
    return delete_krs(data)
################################## END MODULE KRS ##################################

################################## MODULE PENGAJARAN ##################################
@app.route('/pengajaran')
@login_required
def pengajaran():
    konten = "pengajaran"
    ampuan, daftar_prodi, pengajar, matkul, kelas, error = get_pengajaran(session['id'])
    if error:
        return error, 500
    return render_template('home.html', 
                           ampuan=ampuan, 
                           daftar_prodi=daftar_prodi, 
                           pengajar=pengajar,
                           matkul=matkul, 
                           kelas=kelas, 
                           konten=konten)

@app.route('/insert_pengajaran', methods=['POST'])
@login_required
def add_record_pengajaran():
    data = request.get_json()
    return add_pengajaran(data)

@app.route('/edit_pengajaran', methods=['POST'])
@login_required
def edit_record_pengajaran():
    data = request.get_json()
    return edit_pengajaran(data)

@app.route('/hapus_pengajaran', methods=['POST'])
@login_required
def hapus_pengajaran():
    data = request.get_json()
    return delete_pengajaran(data)
################################## END MODULE PENGAJARAN ##################################

################################## MODULE PELAJARAN ##################################
@app.route('/materi/<int:id>')
@login_required
def materi(id):
    konten = "materi"
    materi, matkul, pengampu, error = get_materi(id)
    peserta = get_peserta_kelas(pengampu['id_kelas'], id)
    if error:
        return error, 500
    return render_template('home.html', 
                           konten=konten, 
                           materi=materi, 
                           matkul=matkul, 
                           pengampu=pengampu,
                           peserta=peserta,
                           session=session)

@app.route('/insert_materi', methods=['POST'])
@login_required
def add_record_materi():
    data = request.form
    berkas = request.files.get('berkas')
    return add_materi(data, berkas)

@app.route('/edit_materi', methods=['POST'])
@login_required
def edit_record_materi():
    data = request.form
    berkas = request.files.get('berkas')
    if berkas:
        return edit_materi(data, berkas)
    else:
        return edit_materi(data, None)

@app.route('/hapus_materi', methods=['POST'])
@login_required
def hapus_materi():
    data = request.get_json()
    return delete_materi(data)
################################## END MODULE PELAJARAN ##################################


################################## MODULE DAFTAR MATKUL ##################################
@app.route('/daftarMatkul')
@login_required
def daftarMatkul():
    konten = "daftarMatkul"
    dMatkul, error = get_daftarMatkul(session['id'])
    if error:
        return error, 500
    
    daftar_materi = []
    for mata_kuliah in dMatkul:
        materi, pengampu, error = get_materiKuliah(mata_kuliah['id_pengampu'])  # filter materi berdasarkan id_pengampu
        if error:
            return error, 500
        daftar_materi.append({'materi': materi})
    return render_template('home.html', 
                           dMatkul=dMatkul, 
                           konten=konten, 
                           daftar_materi=daftar_materi)   
    #return render_template('home.html', dMatkul=dMatkul, konten=konten)

@app.route('/materiKuliah/<int:id>')
@login_required
def materiKuliah(id):
    konten = "materiKuliah"
    materi, pengampu, error = get_materiKuliah(id)
    if error:
        return error, 500
    return render_template('home.html', 
                           konten=konten, 
                           materi=materi, 
                           pengampu=pengampu,
                           session=session)
################################## END MODULE MAHASISWA ##################################


################################## MODULE ENROLLMENT ##################################
@app.route('/enrollment/<int:id>')
@login_required
def enrollment(id):
    konten = "enrollment"
    materi, error = get_enrollment(id)
    if error:
        return error, 500
    return render_template('home.html', konten=konten, materi=materi, session=session)

@app.route('/save-emotion-data', methods=['POST'])
@login_required
def save_emotion_data():
    data = request.get_json()
    sesi = session['id']
    return save_emotion(data, sesi)
################################## END MODULE ENROLLMENT ##################################


################################## MODULE EMOTION ##################################
@app.route('/emotion/<int:materi>/<int:mahasiswa>')
#@login_required
def emotion(materi, mahasiswa):
    konten = "emotion"
    emotion, error = get_emotion(materi, mahasiswa)
    if emotion is not None:
        grafik_emo = grafik_emotion(emotion['emo_file'])
        grafik_fok = grafik_fokus(emotion['emo_file'])
        grafik_pie = grafik_emotion_pie(emotion['emo_file'])
        grafik_bar = grafik_emotion_bars(emotion['emo_file'])
        analisis = analisis_gemini(emotion['emo_file'])
        return render_template('home.html', 
                            konten=konten, 
                            emotion=emotion, 
                            grafik_emo=grafik_emo,
                            grafik_fokus=grafik_fok,
                            grafik_pie=grafik_pie,
                            grafik_bar=grafik_bar,
                            analisis=analisis,
                            session=session)
    else:
        mahsw, error = get_mhs(mahasiswa)
        return render_template('home.html', 
                            konten=konten, 
                            mahsw=mahsw,
                            session=session)
################################## END MODULE EMOTION ##################################


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
