import frontalize
import facial_feature_detector as feature_detection
import camera_calibration as calib
import scipy.io as io
import cv2
import numpy as np
import os
import check_resources as check
import matplotlib.pyplot as plt
from face_mask_mediapipe import extract_face_mask
import time


this_path = os.path.dirname(os.path.abspath(__file__))

def get_face_contour_mask(image, landmarks):
    # landmarks shape: (68, 2)
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # Gunakan titik 0-16 (jawline)
    jaw_points = landmarks[0:17]

    # Tambahkan titik di bagian atas untuk nutupin area atas (simulasi atas kepala)
    top_center = np.array([[landmarks[27][0], landmarks[27][1] - 40]])  # landmark 27: hidung atas
    contour = np.vstack([jaw_points, top_center[::-1]])

    cv2.fillPoly(mask, [contour.astype(np.int32)], 255)

    masked = cv2.bitwise_and(image, image, mask=mask)
    return masked


def demo():
    try:
        start_time = time.time()
        # Cek dan siapkan model landmark dlib
        check.check_dlib_landmark_weights()

        # Load model 3D
        model_path = os.path.join(this_path, "frontalization_models", "model3Ddlib.mat")
        model3D = frontalize.ThreeD_Model(model_path, 'model_dlib')

        # Load gambar input
        img_path = os.path.join(this_path, "images/uji4.jpg")
        img = cv2.imread(img_path, 1)
        if img is None:
            raise FileNotFoundError(f"Image not found: {img_path}")

        #plt.figure()
        #plt.title('Query Image')
        #plt.imshow(img[:, :, ::-1])

        # Deteksi landmarks wajah
        lmarks = feature_detection.get_landmarks(img)
        if lmarks.shape[0] == 0:
            raise ValueError("No facial landmarks detected.")

        # Gunakan wajah pertama
        landmarks = lmarks[0]

        #plt.figure()
        #plt.title('Landmarks Detected')
        #plt.imshow(img[:, :, ::-1])
        #plt.scatter(landmarks[:, 0], landmarks[:, 1], c='r', s=10)

        # Kalibrasi kamera
        proj_matrix, camera_matrix, rmat, tvec = calib.estimate_camera(model3D, landmarks)

        # Load eye mask
        eyemask_path = os.path.join(this_path, "frontalization_models", "eyemask.mat")
        eyemask = np.asarray(io.loadmat(eyemask_path)['eyemask'])

        # Lakukan frontalization
        frontal_raw, frontal_sym, _, _, cropped_frontal_raw, cropped_frontal_sym = frontalize.frontalize(img, proj_matrix, model3D.ref_U, eyemask)

        # Tampilkan hasil

        masked_raw, mask1 = extract_face_mask(frontal_sym)
        masked_sym, mask2 = extract_face_mask(cropped_frontal_sym)
       
        #plt.figure()
        #plt.title('Frontalized (no symmetry)')
        #plt.imshow(frontal_raw[:, :, ::-1])

        #plt.figure()
        #plt.title('Frontalized (with symmetry)')
        #plt.imshow(frontal_sym[:, :, ::-1])

        #plt.figure()
        #plt.title('Frontalized (no symmetry) crop')
        #plt.imshow(masked_raw[:, :, ::-1])

        plt.figure()
        plt.title('Frontalized (with symmetry) crop')
        plt.imshow(masked_sym[:, :, ::-1])

        plt.show()
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Waktu eksekusi: {elapsed_time:.4f} detik")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    demo()
