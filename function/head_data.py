import cv2
import mediapipe as mp
import numpy as np

def resize_width(img, new_width):
    """Resize gambar dengan lebar tetap dan tinggi otomatis."""
    height, width = img.shape[:2]
    aspect_ratio = height / width  # Hitung rasio tinggi terhadap lebar
    new_height = int(new_width * aspect_ratio)  # Hitung tinggi otomatis
    resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    return resized_img

# Fungsi untuk menghitung Eye Aspect Ratio (EAR)
def eye_ratio(a,b,c,d):
    ratio = (a - b) / (c - d + 1e-6)
    return ratio

def ratio_horizontal(a, b, c):
    ratio = (a - b) / (c - b + 1e-6)
    return ratio

def koordinat(poin, frame_w, frame_h):
    koor = poin.x * frame_w, poin.y * frame_h
    return koor

def adjust_gamma(image, gamma):
    invGamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** invGamma * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(image, table)

def adjust_brightness_contrast(image, alpha, beta):
    return cv2.addWeighted(image, alpha, image, 0, beta)

def sharpen_image(image):
    kernel = np.array([[-1, -1, -1],
                       [-1, 9, -1],
                       [-1, -1, -1]])
    return cv2.filter2D(image, -1, kernel)

res = 500
scaleFactor = 1.2
minNeighbors = 3
minSize = (50, 50)

EAR_THRESHOLD = 0.2  # Jika lebih kecil dari ini, mata dianggap tertutup

LEFT_EYE_IDX = [362, 374, 263, 386]
RIGHT_EYE_IDX = [133, 145, 33, 159] 
right_eye_indices = [54, 151, 4, 123]  
left_eye_indices = [284, 151, 4, 352] 

face_cascade = cv2.CascadeClassifier('haarcascade/haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade/haarcascade_eye.xml')
eye_cascade_l = cv2.CascadeClassifier('haarcascade/haarcascade_lefteye_2splits.xml')
eye_cascade_r = cv2.CascadeClassifier('haarcascade/haarcascade_righteye_2splits.xml')

def adjust_face(imgs):
    frame = cv2.imread(imgs)
    frame = adjust_brightness_contrast(frame, 1.0, 5)
    faces = face_cascade.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
    for (x, y, w, h) in faces:
        face_crop = frame[y:y+h, x:x+w]
        face_crop = resize_width(face_crop, res)
    return face_crop

def data_wajah(img):
    #imgs = adjust_face(img)
    
    #frame = cv2.imread(imgs)
    imgs = img
    frame = imgs
    frame_h, frame_w, _ = frame.shape        
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    gray = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2GRAY)
    
    with mp.solutions.face_mesh.FaceMesh(refine_landmarks=True) as face_mesh:
        output = face_mesh.process(rgb_frame)
        landmark_points = output.multi_face_landmarks
    
        if landmark_points:
            detect = 1
            landmarks = landmark_points[0].landmark
    
            kelopak_kanan_atas = landmarks[159]
            kelopak_kanan_bawah = landmarks[145]
            batas_mata_kanan_right = landmarks[33]
            batas_mata_kanan_left = landmarks[133]
            
            kelopak_kiri_atas = landmarks[386]
            kelopak_kiri_bawah = landmarks[374]
            batas_mata_kiri_right = landmarks[362]
            batas_mata_kiri_left = landmarks[263]
            
            pupil_kanan = landmarks[468]
            pupil_kiri = landmarks[473]
    
            atas_hidung = landmarks[6]
    
            poin_kelopak_kanan_atas = koordinat(kelopak_kanan_atas, frame_w, frame_h)
            poin_kelopak_kanan_bawah = koordinat(kelopak_kanan_bawah, frame_w, frame_h)
            poin_batas_mata_kanan_right = koordinat(batas_mata_kanan_right, frame_w, frame_h)
            poin_batas_mata_kanan_left = koordinat(batas_mata_kanan_left, frame_w, frame_h)
            
            poin_kelopak_kiri_atas = koordinat(kelopak_kiri_atas, frame_w, frame_h)
            poin_kelopak_kiri_bawah = koordinat(kelopak_kiri_bawah, frame_w, frame_h)
            poin_batas_mata_kiri_right = koordinat(batas_mata_kiri_right, frame_w, frame_h)
            poin_batas_mata_kiri_left = koordinat(batas_mata_kiri_left, frame_w, frame_h)        
            
            poin_pupil_kanan = koordinat(pupil_kanan, frame_w, frame_h)
            poin_pupil_kiri = koordinat(pupil_kiri, frame_w, frame_h)
    
            poin_atas_hidung = koordinat(atas_hidung, frame_w, frame_h)
            
            ################################### Keadaan Mata #################################
            def get_eye_bbox(eye_indices):
                eye_points = [(int(landmarks[o].x * rgb_frame.shape[1]), 
                       int(landmarks[o].y * rgb_frame.shape[0])) for o in eye_indices]
                x_min, y_min = np.min(eye_points, axis=0)
                x_max, y_max = np.max(eye_points, axis=0)
                return x_min, y_min, x_max, y_max
            
            eyes_ratio_kanan = eye_ratio(poin_kelopak_kanan_atas[1], 
                                         poin_kelopak_kanan_bawah[1], 
                                         poin_batas_mata_kanan_right[0], 
                                         poin_batas_mata_kanan_left[0])
    
            eyes_ratio_kiri = eye_ratio(poin_kelopak_kiri_atas[1], 
                                        poin_kelopak_kiri_bawah[1], 
                                        poin_batas_mata_kiri_right[0], 
                                        poin_batas_mata_kiri_left[0])

    
            left_x1, left_y1, left_x2, left_y2 = get_eye_bbox(left_eye_indices)
            right_x1, right_y1, right_x2, right_y2 = get_eye_bbox(right_eye_indices)

            left_eye_roi = rgb_frame[left_y1:left_y2, left_x1:left_x2]
            right_eye_roi = rgb_frame[right_y1:right_y2, right_x1:right_x2]
            
            left_eye_roi = adjust_brightness_contrast(left_eye_roi, 1.2, 30)
            left_eye_roi = cv2.GaussianBlur(left_eye_roi, (5, 5), 10)

            right_eye_roi = adjust_brightness_contrast(right_eye_roi, 1.2, 30)
            right_eye_roi = cv2.GaussianBlur(right_eye_roi, (5, 5), 10)
                
            # Cek mata kanan
            if eyes_ratio_kanan < EAR_THRESHOLD:
                status_mata_kanan = "tertutup"
                arah_mata_kanan = "tertutup"
            else:
                deteksi_mata_kanan = eye_cascade.detectMultiScale(right_eye_roi, scaleFactor=scaleFactor, minNeighbors=minNeighbors, minSize=minSize)
                jumlah_deteksi_mata_kanan = len(deteksi_mata_kanan)
                if jumlah_deteksi_mata_kanan == 0:
                    deteksi_mata_kanan = eye_cascade_r.detectMultiScale(right_eye_roi, scaleFactor=scaleFactor, minNeighbors=minNeighbors, minSize=minSize)
                    jumlah_deteksi_mata_kanan = len(deteksi_mata_kanan)        
                if jumlah_deteksi_mata_kanan > 0:
                    status_mata_kanan = "terbuka"
                    ###################################### Arah Mata ########################################
                    ratio_mata_kanan = ratio_horizontal(poin_pupil_kanan[0], poin_batas_mata_kanan_right[0], poin_batas_mata_kanan_left[0])
                    if ratio_mata_kanan < 0.4:
                        arah_mata_kanan = "kanan"
                    elif ratio_mata_kanan > 0.6:
                        arah_mata_kanan = "kiri"
                    else:
                        arah_mata_kanan = "tengah"
                    ########################################################################################
                else:
                    status_mata_kanan = "tertutup_objek"
                    arah_mata_kanan = "tertutup_objek"
                
            # Cek mata kiri
            if eyes_ratio_kiri < EAR_THRESHOLD:
                status_mata_kiri = "tertutup"
                arah_mata_kiri = "tertutup"
            else:
                deteksi_mata_kiri = eye_cascade.detectMultiScale(left_eye_roi, scaleFactor=scaleFactor, minNeighbors=minNeighbors, minSize=minSize)
                jumlah_deteksi_mata_kiri = len(deteksi_mata_kiri)
                if jumlah_deteksi_mata_kiri == 0:
                    deteksi_mata_kiri = eye_cascade_l.detectMultiScale(left_eye_roi, scaleFactor=scaleFactor, minNeighbors=minNeighbors, minSize=minSize)
                    jumlah_deteksi_mata_kiri = len(deteksi_mata_kiri)
                if jumlah_deteksi_mata_kiri > 0:
                    status_mata_kiri = "terbuka"
                    ###################################### Arah Mata ########################################
                    ratio_mata_kiri = ratio_horizontal(poin_pupil_kiri[0], poin_batas_mata_kiri_left[0], poin_batas_mata_kiri_right[0])
                    if ratio_mata_kiri < 0.4:
                        arah_mata_kiri = "kiri"
                    elif ratio_mata_kiri > 0.6:
                        arah_mata_kiri = "kanan"
                    else:
                        arah_mata_kiri = "tengah"
                    ########################################################################################
                else:
                    status_mata_kiri = "tertutup_objek"
                    arah_mata_kiri = "tertutup_objek"
    
            for idx in LEFT_EYE_IDX:
                x, y = int(landmarks[idx].x * frame_w), int(landmarks[idx].y * frame_h)
                #cv2.circle(rgb_frame, (x, y), 5, (0, 0, 255), -1)
    
            for idx in RIGHT_EYE_IDX:
                x, y = int(landmarks[idx].x * frame_w), int(landmarks[idx].y * frame_h)
                #cv2.circle(rgb_frame, (x, y), 5, (0, 0, 255), -1)
    
    
            ######################################## Head pose ######################################        
            # Hitung headpose horizontal
            headpose = ratio_horizontal(poin_atas_hidung[0], poin_batas_mata_kanan_right[0], poin_batas_mata_kiri_left[0])
            print(headpose)

            if headpose < 0.4:
                arah_kepala = "kanan"
                if status_mata_kiri == "terbuka":
                    arah_mata = arah_mata_kiri
                else:
                    arah_mata = "tertutup"

            elif headpose > 0.6:
                arah_kepala = "kiri"
                if status_mata_kanan == "terbuka":
                    arah_mata = arah_mata_kanan
                else:
                    arah_mata = "tertutup"
            
            else:
                arah_kepala = "tengah"
                if status_mata_kiri == "terbuka":
                    arah_mata = arah_mata_kiri
                elif status_mata_kanan == "terbuka":
                    arah_mata = arah_mata_kanan
                else:
                    arah_mata = "tertutup"

            gaze_ = {
                "face_detected": True,
                "arah_mata": arah_mata,
                "arah_kepala": arah_kepala
            }
        else:
            gaze_ = {
                "face_detected": False,
                "arah_mata": "Error",
                "arah_kepala": "Error"
            }
    return gaze_

#gambar = "images/uji (8).jpg"
#x = data_wajah(gambar)
#print(x["status_mata_kanan"])
#print(x)