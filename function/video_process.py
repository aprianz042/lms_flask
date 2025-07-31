import cv2
import json
import threading
import queue
import base64

from flask_socketio import SocketIO, emit
from function.head_data import data_wajah
from function.frontal import half_flip
from deepface import DeepFace

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
        
        #data = json.dumps({"face_detected": face_detected, "arah_mata": arah_mata, "arah_kepala": arah_kepala})
        data = {
            "face_detected": face_detected,
            "arah_mata": arah_mata,
            "arah_kepala": arah_kepala
            }
        socketio.emit('analisis_wajah', data) 

        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
    cap.release()


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

def analyze_emotion(frame):
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        dominant_emotion = analysis[0]['dominant_emotion']
        return dominant_emotion
    except Exception as e:
        return "Error in analysis"