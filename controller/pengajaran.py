from flask import jsonify
from function.koneksi import get_db_connection

def get_isimateri(id):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_select = "SELECT * FROM materi WHERE id_pengampu = %s;"
            cursor.execute(sql_select, (id))
            materi = cursor.fetchall() 
        return materi, None
    finally:
        connection.close()

def get_pengajaran(id_pengajar):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            sql_select = """
                SELECT 
                    p.id_pengampu,
                    p.id_prodi,
                    p.id_pengajar,
                    p.id_mata_kuliah,
                    p.id_kelas,
                    p.tahun_ajaran,
                    p.semester,
                    pr.nama_prodi,
                    pr.kode_prodi,
                    pg.nama_pengajar,
                    mk.nama_mata_kuliah,
                    mk.kode_mata_kuliah,
                    k.nama_kelas
                FROM 
                    pengampu p
                JOIN 
                    prodi pr ON p.id_prodi = pr.id_prodi
                JOIN 
                    pengajar pg ON p.id_pengajar = pg.id_pengajar
                JOIN 
                    mata_kuliah mk ON p.id_mata_kuliah = mk.id_mata_kuliah
                JOIN 
                    kelas k ON p.id_kelas = k.id_kelas
                WHERE 
                    p.id_pengajar = %s;
                """
            cursor.execute(sql_select, (id_pengajar))
            pengampu = cursor.fetchall() 

            cursor.execute('SELECT * FROM prodi')
            prodi = cursor.fetchall() 

            cursor.execute('SELECT * FROM pengajar')
            pengajar = cursor.fetchall() 

            cursor.execute('SELECT * FROM mata_kuliah')
            mata_kuliah = cursor.fetchall() 

            cursor.execute('SELECT * FROM kelas')
            kelas = cursor.fetchall() 
        return pengampu, prodi, pengajar, mata_kuliah, kelas, None
    finally:
        connection.close()


def add_pengajaran(data):
    id_prodi = data.get('id_prodi')
    id_pengajar = data.get('id_pengajar')
    id_mata_kuliah = data.get('id_mata_kuliah')
    id_kelas = data.get('id_kelas')
    tahun_ajaran = data.get('tahun_ajaran')
    semester = data.get('semester')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            insert_sql = """
                INSERT INTO pengampu 
                (id_prodi,
                id_pengajar, 
                id_mata_kuliah, 
                id_kelas, 
                tahun_ajaran, 
                semester)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                id_prodi,
                id_pengajar,
                id_mata_kuliah,
                id_kelas,
                tahun_ajaran,
                semester
            ))
            connection.commit()

        return jsonify({"message": "Berhasil menambahkan pengampu"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


def edit_pengajaran(data):
    id_pengampu = data.get('id_pengampu')
    id_prodi = data.get('id_prodi')
    id_pengajar = data.get('id_pengajar')
    id_mata_kuliah = data.get('id_mata_kuliah')
    id_kelas = data.get('id_kelas')
    tahun_ajaran = data.get('tahun_ajaran')
    semester = data.get('semester')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE pengampu
                SET 
                    id_prodi = %s, 
                    id_pengajar = %s, 
                    id_mata_kuliah = %s, 
                    id_kelas = %s, 
                    tahun_ajaran = %s, 
                    semester = %s
                WHERE 
                    id_pengampu = %s
            """
            cursor.execute(sql, (
                id_prodi, 
                id_pengajar, 
                id_mata_kuliah, 
                id_kelas, 
                tahun_ajaran, 
                semester, 
                id_pengampu
            ))
            connection.commit()

        return jsonify({"message": "Berhasil mengubah pengampu"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def delete_pengajaran(data):
    id_pengampu = data.get('id_pengampu')
    
    if not id_pengampu:
        return jsonify({"error": "Pengampu tidak ditemukan"}), 400
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM pengampu WHERE id_pengampu = %s"
            cursor.execute(sql, (id_pengampu,))
            connection.commit()
            return jsonify({"message": "pengampu berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()
