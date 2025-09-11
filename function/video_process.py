import cv2
import base64
import numpy as np

from io import BytesIO
from PIL import Image
from flask_socketio import SocketIO, emit
from function.head_data import data_wajah

from function.frontal import half_flip
#from function.frontalization import half_flip

from deepface import DeepFace

from keras.models import model_from_json
from keras.preprocessing import image

"""
model = model_from_json(open("model/fer.json", "r").read())
model.load_weights('model/fer.h5')

def prediksi(img):
    predictions = model.predict(img)
    max_index = np.argmax(predictions[0])
    emotions = ('angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral')
    predicted_emotion = emotions[max_index]
    return predicted_emotion
"""

def proses_img(data):
    # Data diterima dari klien dalam format base64
    img_data = base64.b64decode(data.split(',')[1])  # Mengambil bagian base64 setelah koma
    
    # Membaca image menggunakan OpenCV
    img = Image.open(BytesIO(img_data))
    img = np.array(img)

    data_ = data_wajah(img)
    face_detected = data_["face_detected"]
    if face_detected == True:
        arah_mata = data_["arah_mata"]
        arah_kepala = data_["arah_kepala"]
        if (arah_kepala == "kiri" and arah_mata == "kanan") or (arah_kepala == "kanan" and arah_mata == "kiri") or (arah_kepala == "tengah" and arah_mata == "tengah"):
            fokus = "fokus"

            img = half_flip(img)
            if img is not None:
                print("proses half2d")
            emosi = analyze_emotion(img)
        else:
            fokus = "tidak fokus"
            emosi = "Bad Processed"

    else:
        arah_mata = "Not Detected"
        arah_kepala = "Not Detected"
        emosi = "Not Processed"
        fokus = "Not Detected"
    
    data = {
        "face_detected": face_detected,
        "arah_mata": arah_mata,
        "arah_kepala": arah_kepala,
        "fokus": fokus,
        "emosi" : emosi
        }
    
    emit('analisis_wajah', data)

def analyze_emotion(frame):
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        dominant_emotion = analysis[0]['dominant_emotion']
        return dominant_emotion
    except Exception as e:
        return "Error in analysis"

def frontal_video():
    cap = cv2.VideoCapture(0)  
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frontal = half_flip(frame)
        _, jpeg = cv2.imencode('.jpg', frontal)
        frame_bytes = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
    cap.release()


#########################################################################################################

def proses_video(data):
    img_data = base64.b64decode(data.split(',')[1])  # Mengambil bagian base64 setelah koma    
    img = Image.open(BytesIO(img_data))
    img = np.array(img)
    
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, buffer = cv2.imencode('.png', gray_img)
    gray_img_base64 = base64.b64encode(buffer).decode('utf-8')

    emit('image_response', f"data:image/png;base64,{gray_img_base64}")

def generate_video(socketio):
    cap = cv2.VideoCapture(0)  
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        data_ = data_wajah(frame)
        face_detected = data_["face_detected"]
        if face_detected == True:
            arah_mata = data_["arah_mata"]
            arah_kepala = data_["arah_kepala"]
            
        else:
            arah_mata = "Not Detected"
            arah_kepala = "Not Detected"
        
        emosi = analyze_emotion(frame)
        #data = json.dumps({"face_detected": face_detected, "arah_mata": arah_mata, "arah_kepala": arah_kepala})
        data = {
            "face_detected": face_detected,
            "arah_mata": arah_mata,
            "arah_kepala": arah_kepala,
            "emosi" : emosi
            }
        socketio.emit('analisis_wajah', data) 

        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
    cap.release()
