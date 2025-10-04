import function.frontalize as frontalize
import function.facial_feature_detector as feature_detection
import function.camera_calibration as calib
import scipy.io as io
import cv2
import numpy as np
import os
from function.face_mask_mediapipe import extract_face_mask
from function.face_crop import *

this_path = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(this_path, "model", "model3Ddlib.mat")
model3D = frontalize.ThreeD_Model(model_path, 'model_dlib')
eyemask_path = os.path.join(this_path, "model", "eyemask.mat")
eyemask = np.asarray(io.loadmat(eyemask_path)['eyemask'])

def get_face_contour_mask(image, landmarks):
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    jaw_points = landmarks[0:17]
    top_center = np.array([[landmarks[27][0], landmarks[27][1] - 40]])  # landmark 27: hidung atas
    contour = np.vstack([jaw_points, top_center[::-1]])
    cv2.fillPoly(mask, [contour.astype(np.int32)], 255)
    masked = cv2.bitwise_and(image, image, mask=mask)
    return masked

def main_front(img_path):
    try:
        img = img_path
        if img is None:
            return img_path

        lmarks = feature_detection.get_landmarks(img)
        if lmarks.shape[0] == 0:
            #print("no face detected")
            return img_path
        
        landmarks = lmarks[0]
        proj_matrix, camera_matrix, rmat, tvec = calib.estimate_camera(model3D, landmarks)
        frontal_raw, frontal_sym, _, _, cropped_frontal_raw, cropped_frontal_sym = frontalize.frontalize(img, proj_matrix, model3D.ref_U, eyemask)
        masked_sym, mask2 = extract_face_mask(cropped_frontal_sym)
        output = main_process(masked_sym[:, :, ::-1])
        return output
    except Exception as e:
        return img_path
