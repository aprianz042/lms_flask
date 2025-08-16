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