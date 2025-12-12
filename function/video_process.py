import cv2
import base64
import numpy as np

from io import BytesIO
from PIL import Image
from flask_socketio import SocketIO, emit
from function.head_data import data_wajah

from function.frontal import half_flip
from function.debug_vid import half_flip_debug
#from function.frontal_lms import half_flip
#from function.frontalization import half_flip

from function.func_headpose import main_front
from deepface import DeepFace
from function.predict_cnn import prediksi_cnn


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
        
        img = half_flip(img)
        if img is not None:
            print("proses half2d")
        
        emosi, _ = analyze_emotion(img)
        w_emo = emo_i(emosi)
        
        if (arah_kepala == "tengah") and (arah_mata != "tertutup" and arah_mata != "Error"):
            w_head = 1
            w_eye = 2.5

        elif (arah_kepala == "kiri" or arah_kepala == "kanan") and (arah_mata != "tertutup" and arah_mata != "Error"):
            w_head = 0
            w_eye = 2.5

        elif (arah_kepala == "tengah" and arah_mata == "tertutup"):
            w_head = 1
            w_eye = 0

        else:
            w_head = 0
            w_eye = 0

    else:
        emosi = "No face detected"
        w_emo = 0
        w_head = 0
        w_eye = 0
    
    indeks_i = engagement_index(w_head, w_eye, w_emo)

    data = {
        "face_detected": face_detected,
        "emosi": emosi,
        "engagement": indeks_i
        }
    
    emit('analisis_wajah', data)

def analyze_emotion(frame):
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        dominant_emotion = analysis[0]['dominant_emotion']
        emotion_dict = {
            'angry': round(analysis[0]['emotion']['angry'], 4),
            'disgust': round(analysis[0]['emotion']['disgust'], 4),
            'fear': round(analysis[0]['emotion']['fear'], 4),
            'happy': round(analysis[0]['emotion']['happy'], 4),
            'sadness': round(analysis[0]['emotion']['sad'], 4),
            'surprise': round(analysis[0]['emotion']['surprise'], 4),
            'neutral': round(analysis[0]['emotion']['neutral'], 4),
        }
        return dominant_emotion, emotion_dict
        
        #pred = prediksi_cnn(frame)
        #return pred
    except Exception as e:
        return "Error in analysis"
    
def emo_i(emo):
    weights = {
        "angry": 0.1,
        "disgust": 0.9,
        "fear": 0.5,
        "happy": 1.1,
        "sadness": 0.3,   
        "surprise": 0.7,
        "neutral": 1.4
    }
    ei = weights.get(emo, 0)
    return ei

def engagement_index(whead, weye, wemo):
    sumW = whead + weye + wemo
    if sumW > 4.5:
        ei = "Highly Engaged"
    elif sumW >= 4 and sumW < 4.5:
        ei = "Confused"
    elif sumW >= 2.5 and sumW < 4:
        ei = "Boredom"
    elif sumW < 2.5 and sumW != 0:
        ei = "Sleepy"
    else:
        ei = "Very Not Engaged"
    return ei

    

def engagement_ori(prob):
    weights = {
        "angry": 0.1,
        "disgust": 0.9,
        "fear": 0.5,
        "happy": 1.1,
        "sadness": 0.3,   
        "surprise": 0.7,
        "neutral": 1.4
    }
    ei = 0.0
    for emotion in weights:
        if emotion in prob:
            ei += float(prob[emotion]) * float(weights[emotion])

    neutral = float(prob.get('neutral', 0))
    happy = float(prob.get('happy', 0))
    surprise = float(prob.get('surprise', 0))
    angry = float(prob.get('angry', 0))
    fear = float(prob.get('fear', 0))
    sadness = float(prob.get('sadness', 0))
    disgust = float(prob.get('disgust', 0))

    if (neutral > 0.6 or happy > 0.5 or surprise > 0.6):
        status = "engaged"
    elif(angry > 0.2 or fear > 0.3 or sadness > 0.3 or disgust > 0.3):
        status = "disengaged"
    else:
        status = "disengaged"
        ei = 0.0         
    ei = round(float(ei), 2)
    return status, ei





def frontal_video():
    cap = cv2.VideoCapture(0)  
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frontal = half_flip_debug(frame)
        #frontal = main_front(frame)
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
        
        emosi, _ = analyze_emotion(frame)
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
