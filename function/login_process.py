from function.koneksi import get_db_connection

def proses_login(id_user):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM user WHERE id = %s', (id_user,))
        user = cursor.fetchone()
        if user:
            connection.close()
            return user['id'], user['nama'], user['no_id'], user['level']
        else:
            cursor.execute('SELECT * FROM pengajar WHERE id_pengajar = %s', (id_user,))
            pengajar = cursor.fetchone()         
            if pengajar:
                connection.close()
                return pengajar['id_pengajar'], pengajar['nama_pengajar'], pengajar['nip'], pengajar['kategori']
            else:
                cursor.execute('SELECT * FROM mahasiswa WHERE nim = %s', (id_user,))
                mhs = cursor.fetchone()                
                if mhs:
                    connection.close()
                    return mhs['id_mahasiswa'], mhs['nama_mahasiswa'], mhs['nim'], 'mahasiswa'
    return None

def get_session_user(username, password_hash):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM user WHERE no_id = %s AND pass = %s', (username, password_hash))
        user = cursor.fetchone()
        if user:
            connection.close()
            user_ = user['id']
            no_id_ = user['no_id']
            nama_ = user['nama']
            level_ = user['level']
        else:
            cursor.execute('SELECT * FROM pengajar WHERE nip = %s AND password = %s', (username, password_hash))
            pengajar = cursor.fetchone()
            if pengajar:
                connection.close()
                user_ = pengajar['id_pengajar'] 
                no_id_ = pengajar['nip']  
                nama_ = pengajar['nama_pengajar']
                level_ = pengajar['kategori'] 
            else:
                cursor.execute('SELECT * FROM mahasiswa WHERE nim = %s AND password = %s', (username, password_hash))
                mhs = cursor.fetchone()
                if mhs:
                    connection.close()
                    user_ = mhs['id_mahasiswa']
                    no_id_ = mhs['nim']  
                    nama_ = mhs['nama_mahasiswa'] 
                    level_ = "mahasiswa" 
                else:
                    user_ = None
                    no_id_ = None
                    nama_ = None 
                    level_ = None
        return user_, no_id_, nama_, level_

