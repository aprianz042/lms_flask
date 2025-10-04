import mediapipe as mp
import cv2
import numpy as np
from skimage.transform import PiecewiseAffineTransform, warp

############################################## Mediapipe Utils ########################################################################################
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_detection = mp.solutions.face_detection
mp_selfie_segmentation = mp.solutions.selfie_segmentation

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, 
                       max_num_hands=2, 
                       min_detection_confidence=0.2)

mp_face_mesh = mp.solutions.face_mesh
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True)


# Ambil daftar koneksi untuk Tesselation, Contours, dan Irises
connections = {
    "tesselation": (mp_face_mesh.FACEMESH_TESSELATION, 'cyan'),
    "contours": (mp_face_mesh.FACEMESH_CONTOURS, 'red'),
    "irises": (mp_face_mesh.FACEMESH_IRISES, 'magenta')
}

# Atur linewidth untuk setiap koneksi
linewidths = {
    "tesselation": 0.5,  # Lebih tipis
    "contours": 2.5,  # Medium
    "irises": 1.0  # Lebih tebal
}


def landmark_wajah(face):
    annotated_image = face
    results = face_mesh.process(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
    if not results.multi_face_landmarks:
        stat = 'gagal'
        return annotated_image, stat
    else:
        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(image=annotated_image,
                                      landmark_list=face_landmarks,
                                      connections=mp_face_mesh.FACEMESH_TESSELATION,
                                      landmark_drawing_spec=None,
                                      connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
            mp_drawing.draw_landmarks(image=annotated_image,
                                      landmark_list=face_landmarks,
                                      connections=mp_face_mesh.FACEMESH_CONTOURS,
                                      landmark_drawing_spec=None,
                                      connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style())
            mp_drawing.draw_landmarks(image=annotated_image,
                                      landmark_list=face_landmarks,
                                      connections=mp_face_mesh.FACEMESH_IRISES,
                                      landmark_drawing_spec=None,
                                      connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_iris_connections_style())
        return annotated_image, results.multi_face_landmarks[0].landmark



def list_poin_wajah(dua_D):
    face_poin = [dua_D[152], dua_D[148], dua_D[176], dua_D[149], dua_D[150], dua_D[136], dua_D[172], dua_D[58], dua_D[132],
                  dua_D[93], dua_D[234], dua_D[127], dua_D[162], dua_D[21], dua_D[54], dua_D[103], dua_D[67], dua_D[109],
                  dua_D[10], dua_D[338], dua_D[297], dua_D[332], dua_D[284], dua_D[251], dua_D[389], dua_D[356], dua_D[454],
                  dua_D[323], dua_D[361], dua_D[288], dua_D[397], dua_D[365], dua_D[379], dua_D[378], dua_D[400], dua_D[377]
                 ]
    return face_poin

def images_warping(data_wajah, data_landmark_src, data_landmark_dst):
    im = data_wajah
    im_rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    
    src_landmarks = data_landmark_src  # bentuk (N, 2)
    dst_landmarks = data_landmark_dst  # bentuk (N, 2)
    
    image_shape = im_rgb.shape
    height, width = image_shape[:2]
    
    tform = PiecewiseAffineTransform()
    tform.estimate(dst_landmarks, src_landmarks)  # dari target ke source
    
    warped = warp(im_rgb, tform, output_shape=(height, width))
    warped = (warped * 255).astype(np.uint8)
    return warped

def potong_area_(img, landmark_region):
    mask = np.zeros_like(img, dtype=np.uint8)
    cv2.fillConvexPoly(mask, np.array(landmark_region, dtype=np.int32), (255, 255, 255))
    # Ambil area wajah saja
    hasil = cv2.bitwise_and(img, mask)
    # Hitung bounding box dari polygon landmark
    x, y, w, h = cv2.boundingRect(np.array(landmark_region, dtype=np.int32))
    # Crop hasil sesuai bounding box
    hasil_crop = hasil[y:y+h, x:x+w]
    return hasil_crop


def main_process(imgs):
    images = imgs 
    images = cv2.cvtColor(images, cv2.COLOR_BGR2RGB)     
    img_ori = images.copy()                                   # img_ori = gambar asli
    img_roll = img_ori                          # img_roll = headpose yang sudah di luruskan (yang diproses selanjutnya)
    img_r = img_roll.copy() 
    img_height, img_width, _ = img_roll.shape 
    mesh_wajah, landmark_face = landmark_wajah(img_roll)      # proses landmarking wajah dari gambar yang sudah corect roll (img_roll)
    
    if len(landmark_face) == 0:                               # jika landmark == 0 atau tidak ada wajah terdeteksi maka proses selesai
        return None
    else:
        dua_D = []                                            # proses mengkonversi koordinat landmark (x,y,z) dari 3D menjadi 2D
        for i in range(len(landmark_face)):
            ix = int(landmark_face[i].x * img_width)
            iy = int(landmark_face[i].y * img_height)
            dua_D.append([ix, iy])        
            
        poin_wajah_full = list_poin_wajah(dua_D)
        warpp_full = images_warping(img_r, poin_wajah_full, poin_wajah_full)
        face_ori = potong_area_(warpp_full, poin_wajah_full)
        output = cv2.resize(face_ori, (128, 128))
    return output