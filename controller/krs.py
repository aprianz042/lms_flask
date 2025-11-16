from flask import jsonify
from function.koneksi import get_db_connection

def get_krs():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    
    try:
        with connection.cursor() as cursor:
            sql_data = """
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
                    kelas k ON p.id_kelas = k.id_kelas;
                """
            cursor.execute(sql_data)
            data = cursor.fetchall()

            cursor.execute(
                """
                SELECT 
                    kr.id_krs,
                    kr.id_mahasiswa,
                    kr.id_mata_kuliah,
                    kr.id_kelas,
                    kr.id_pengampu,
                    kr.nilai,
                    kr.tahun_ajaran,
                    kr.semester,
                    kr.status,
                    mhs.nama_mahasiswa,
                    mk.nama_mata_kuliah,
                    kls.nama_kelas,
                    pg.nama_pengajar
                FROM 
                    krs kr
                JOIN 
                    mahasiswa mhs ON kr.id_mahasiswa = mhs.id_mahasiswa
                JOIN
                    mata_kuliah mk ON kr.id_mata_kuliah = mk.id_mata_kuliah
                JOIN
                    kelas kls ON kr.id_kelas = kls.id_kelas
                JOIN 
                    pengajar pg ON kr.id_pengampu = pg.id_pengajar                 
                ORDER BY 
                    kr.id_kelas ASC, mk.nama_mata_kuliah ASC;
                """)
            krs = cursor.fetchall()

            mahasiswa_mata_kuliah = {}
            for row in krs:
                mahasiswa_id = row['id_mahasiswa']
                mata_kuliah_pengajar = f"{row['nama_mata_kuliah']} - {row['nama_pengajar']}" 
                if mahasiswa_id not in mahasiswa_mata_kuliah:
                    mahasiswa_mata_kuliah[mahasiswa_id] = {
                        'nama_mahasiswa': row['nama_mahasiswa'],
                        'mata_kuliah': [],  
                        'nama_kelas': row['nama_kelas']
                    }
                mahasiswa_mata_kuliah[mahasiswa_id]['mata_kuliah'].append(mata_kuliah_pengajar)

            d_krs = []
            for mahasiswa_id, data in mahasiswa_mata_kuliah.items():
                d_krs.append({
                    'id_mahasiswa': mahasiswa_id,
                    'nama_mahasiswa': data['nama_mahasiswa'],
                    'mata_kuliah': data['mata_kuliah'],  
                    'nama_kelas': data['nama_kelas'],
                })

        return data, d_krs, None
    finally:
        connection.close()


def get_krs_data():
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_data = """
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
                    kelas k ON p.id_kelas = k.id_kelas;
                """
            cursor.execute(sql_data)
            data = cursor.fetchall()
            return data
    finally:
        connection.close()

def add_krs_ori(data):
    id_ampuan = data.get('id_ampuan')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql_data = """
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
                    p.id_pengampu = %s
                ORDER BY 
                    p.id_kelas ASC, mk.nama_mata_kuliah ASC;
                """
            cursor.execute(sql_data, (id_ampuan,))  
            krs = cursor.fetchall()

            sql_mhs = "SELECT * FROM mahasiswa WHERE id_kelas = %s"
            mahasiswa_data = [] 
            for kelas_data in krs:
                cursor.execute(sql_mhs, (kelas_data['id_kelas'],))  
                mahasiswa_data.extend(cursor.fetchall())  

            data_to_insert = []
            for mahasiswa in mahasiswa_data:
                data = (
                    mahasiswa['id_mahasiswa'],  
                    krs[0]['id_mata_kuliah'],  
                    krs[0]['id_kelas'],        
                    krs[0]['id_pengampu'],     
                    '',                        
                    krs[0]['tahun_ajaran'],
                    krs[0]['semester'],
                    'on_going'                 
                )
                data_to_insert.append(data)

            sql_insert = """
            INSERT INTO krs (id_mahasiswa, id_mata_kuliah, id_kelas, id_pengampu, nilai, tahun_ajaran, semester, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.executemany(sql_insert, data_to_insert)
            connection.commit()

        return jsonify({"message": "Berhasil menambahkan KRS"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

def add_krs(data):
    id_ampuan = data.get('id_ampuan')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql_data = """
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
                    p.id_pengampu = %s
                ORDER BY 
                    p.id_kelas ASC, mk.nama_mata_kuliah ASC;
                """
            cursor.execute(sql_data, (id_ampuan,))
            krs = cursor.fetchall()

            sql_mhs = "SELECT * FROM mahasiswa WHERE id_kelas = %s"
            mahasiswa_data = []
            for kelas_data in krs:
                cursor.execute(sql_mhs, (kelas_data['id_kelas'],))
                mahasiswa_data.extend(cursor.fetchall())

            data_to_insert = []
            for mahasiswa in mahasiswa_data:
                # Validasi: cek apakah record sudah ada di tabel krs
                cek_sql = """
                SELECT 1 FROM krs 
                WHERE 
                    id_mahasiswa = %s AND
                    id_mata_kuliah = %s AND
                    id_kelas = %s AND
                    id_pengampu = %s
                LIMIT 1;
                """
                data_cek = (
                    mahasiswa['id_mahasiswa'],
                    krs[0]['id_mata_kuliah'],
                    krs[0]['id_kelas'],
                    krs[0]['id_pengampu']
                )
                cursor.execute(cek_sql, data_cek)
                sudah_ada = cursor.fetchone()
                if sudah_ada:
                    continue  # Skip kalau sudah ada

                # Append ke list insert jika belum ada
                data = (
                    mahasiswa['id_mahasiswa'],
                    krs[0]['id_mata_kuliah'],
                    krs[0]['id_kelas'],
                    krs[0]['id_pengampu'],
                    '',
                    krs[0]['tahun_ajaran'],
                    krs[0]['semester'],
                    'on_going'
                )
                data_to_insert.append(data)

            if data_to_insert:
                sql_insert = """
                INSERT INTO krs (id_mahasiswa, id_mata_kuliah, id_kelas, id_pengampu, nilai, tahun_ajaran, semester, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.executemany(sql_insert, data_to_insert)
                connection.commit()

        return jsonify({"message": "Berhasil menambahkan KRS"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


def add_krs_single(data):
    id_ampuan = data.get('id_ampuan_s')
    id_mahasiswa = data.get('id_mhs')
    tahun_ajaranS = data.get('tahun_ajaranS')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql_data = """
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
                    p.id_pengampu = %s
                ORDER BY 
                    p.id_kelas ASC, mk.nama_mata_kuliah ASC;
                """
            cursor.execute(sql_data, (id_ampuan,))  
            krs = cursor.fetchall()
           
            sql_insert = """
            INSERT INTO krs (id_mahasiswa, id_mata_kuliah, id_kelas, id_pengampu, nilai, tahun_ajaran, semester, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(sql_insert, (
                id_mahasiswa,
                krs[0]['id_mata_kuliah'],  
                krs[0]['id_kelas'],        
                krs[0]['id_pengampu'],     
                '',                        
                tahun_ajaranS,
                krs[0]['semester'],
                'on_going'  
            ))
            connection.commit()

        return jsonify({"message": "Berhasil menambahkan KRS"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()



def edit_krs(data):
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

def delete_krs(data):
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
