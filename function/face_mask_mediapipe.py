import mediapipe as mp
import cv2
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

def extract_face_mask(image):
    with mp_face_mesh.FaceMesh(static_image_mode=True,
                                max_num_faces=1,
                                refine_landmarks=True,
                                min_detection_confidence=0.5) as face_mesh:

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_image)

        if not results.multi_face_landmarks:
            return None, None

        face_landmarks = results.multi_face_landmarks[0]

        # Ambil index landmark yang menyusun wajah luar (contour)
        FACE_OVAL = [
            10, 338, 297, 332, 284, 251, 389, 356,
            454, 323, 361, 288, 397, 365, 379, 378,
            400, 377, 152, 148, 176, 149, 150, 136,
            172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109
        ]

        h, w, _ = image.shape
        points = []
        for idx in FACE_OVAL:
            x = int(face_landmarks.landmark[idx].x * w)
            y = int(face_landmarks.landmark[idx].y * h)
            points.append((x, y))

        # Buat mask wajah
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [np.array(points, dtype=np.int32)], 255)

        # Terapkan mask ke gambar
        face_on_black = cv2.bitwise_and(image, image, mask=mask)
        #face_on_black = cv2.cvtColor(face_on_black, cv2.COLOR_BGR2RGB)
        return face_on_black, mask
