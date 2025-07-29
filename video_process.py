import cv2
from head_data import data_wajah
from frontal import half_flip
import json

# Fungsi untuk menangani video stream
def generate_video():
    # Inisialisasi webcam
    cap = cv2.VideoCapture(0)  # 0 berarti webcam default

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Ubah frame ke format yang bisa ditampilkan di HTML
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Analisis emosi menggunakan DeepFace
        #dominant_emotion = analyze_emotion(frame)
        #cv2.putText(frame, f"Emotion: {dominant_emotion}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        data_ = data_wajah(frame)
        face_detected = data_["face_detected"]
        if face_detected == True:
            arah_mata = data_["arah_mata"]
            arah_kepala = data_["arah_kepala"]
            cv2.putText(frame, f"arah_mata: {arah_mata}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"arah_kepala: {arah_kepala}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, f"Tidak ada wajah terdeteksi", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            arah_mata = None
            arah_kepala = None
        
        data = json.dumps({"face_detected": face_detected, "arah_mata": arah_mata, "arah_kepala": arah_kepala})
        yield f"data: {data}\n\n"

        #frontal = half_flip(frame)
        
        # Encode frame sebagai JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        # Hasilkan frame dalam format yang bisa ditampilkan
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
    cap.release()

def frontal_video():
    # Inisialisasi webcam
    cap = cv2.VideoCapture(0)  # 0 berarti webcam default

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frontal = half_flip(frame)
        # Encode frame sebagai JPEG
        _, jpeg = cv2.imencode('.jpg', frontal)
        frame_bytes = jpeg.tobytes()

        # Hasilkan frame dalam format yang bisa ditampilkan
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

    cap.release()