import os
from function.generate_file import *
from flask import jsonify, request
from function.koneksi import get_db_connection

def get_daftarMatkul(id):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_daftarMatkul = """
                SELECT 
                    k.id_krs,
                    k.id_mahasiswa,
                    k.id_mata_kuliah,
                    k.nilai,
                    k.id_pengampu,
                    mhs.nama_mahasiswa,
                    mhs.nim,
                    mhs.id_kelas,
                    mhs.email,
                    mhs.nomor_telepon,
                    mk.nama_mata_kuliah,
                    pg.id_pengajar,
                    p.nama_pengajar
                FROM 
                    krs k
                JOIN
                    mahasiswa mhs ON k.id_mahasiswa = mhs.id_mahasiswa
                JOIN
                    mata_kuliah mk ON k.id_mata_kuliah = mk.id_mata_kuliah  
                JOIN
                    pengampu pg ON k.id_pengampu = pg.id_pengampu
                JOIN
                    pengajar p ON pg.id_pengajar = p.id_pengajar                    
                WHERE
                    k.id_mahasiswa = %s;
                """
            cursor.execute(sql_daftarMatkul, (id))
            result = cursor.fetchall()
        return result, None
    finally:
        connection.close()

def get_enrollment(id):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_daftarMatkul = """
                SELECT 
                    k.id_krs,
                    k.id_mahasiswa,
                    k.id_mata_kuliah,
                    k.nilai,
                    mhs.nama_mahasiswa,
                    mhs.nim,
                    mhs.id_kelas,
                    mhs.email,
                    mhs.nomor_telepon,
                    mk.nama_mata_kuliah
                FROM 
                    krs k
                JOIN
                    mahasiswa mhs ON k.id_mahasiswa = mhs.id_mahasiswa
                JOIN
                    mata_kuliah mk ON k.id_mata_kuliah = mk.id_mata_kuliah                    
                WHERE
                    k.id_mahasiswa = %s;
                """
            cursor.execute(sql_daftarMatkul, (id))
            result = cursor.fetchall()
        return result, None
    finally:
        connection.close()