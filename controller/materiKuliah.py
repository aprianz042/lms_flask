import os
from function.generate_file import *
from flask import jsonify, request
from function.koneksi import get_db_connection

def get_materiKuliah(id):
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

            sql_pengampu = """
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
                    p.id_pengampu = %s;
                """
            cursor.execute(sql_pengampu, (id))
            pengampu = cursor.fetchone()
            
        return materi, pengampu, None
    finally:
        connection.close()