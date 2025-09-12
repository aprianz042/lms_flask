import os, time
import json
from flask import jsonify, request
from function.koneksi import get_db_connection
import string
import random

def save_emotion(data, sesi):
    emotion_data = data.get('emotionData')

    id_mahasiswa = sesi
    id_materi = emotion_data[0].get('materi_id')
    
    timestamp = time.localtime()
    last_accessDB = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)

    last_access = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    emo_file = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '_' + last_access + '.json'
    file_path = os.path.join('emo_data', emo_file)

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO enrollment (id_mahasiswa, id_materi, last_access, emo_file)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (id_mahasiswa, id_materi, last_accessDB , emo_file))
            connection.commit()
            
            with open(file_path, 'w') as f:
                json.dump(emotion_data, f, indent=2)

        return jsonify({'status': 'success', 'filename': emo_file}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

'''
emotion_data = data.get('emotionData')
if emotion_data:
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    random_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + timestamp + '.json'
    file_path = os.path.join('emo_data', random_filename)
    try:
        with open(file_path, 'w') as f:
            json.dump(emotion_data, f, indent=2)
        return jsonify({'status': 'success', 'filename': random_filename}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
else:
    return jsonify({'status': 'error', 'message': 'No emotion data received'}), 400
'''