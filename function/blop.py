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

    # Use points 0-16 for jawline
    jaw_points = landmarks[0:17]

    # Add a point on top to close the upper area (simulate the top of the head)
    top_center = np.array([[landmarks[27][0], landmarks[27][1] - 40]])  # landmark 27: nose tip
    contour = np.vstack([jaw_points, top_center[::-1]])

    cv2.fillPoly(mask, [contour.astype(np.int32)], 255)

    masked = cv2.bitwise_and(image, image, mask=mask)
    return masked


def demo():
    try:
        start_time = time.time()  # Initialize start time for total execution
        check.check_dlib_landmark_weights()

        model_path = os.path.join(this_path, "frontalization_models", "model3Ddlib.mat")
        model3D = frontalize.ThreeD_Model(model_path, 'model_dlib')

        dir_ = 'uji'
        for filename in os.listdir(dir_):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(dir_, filename)
                img = cv2.imread(img_path, 1)
                
                if img is None:
                    print(f"Image not found: {img_path}")
                    continue  # Skip to next image
                
                # Resize the image to a fixed height, keeping aspect ratio
                fixed_height = 480
                aspect_ratio = img.shape[1] / img.shape[0]
                new_width = int(fixed_height * aspect_ratio)
                img = cv2.resize(img, (new_width, fixed_height))  # Resize image with fixed height

                lmarks = feature_detection.get_landmarks(img)
                if lmarks.shape[0] == 0:
                    print(f"No facial landmarks detected in image {filename}. Skipping...")
                    continue  # Skip to next image
                
                landmarks = lmarks[0]
                proj_matrix, camera_matrix, rmat, tvec = calib.estimate_camera(model3D, landmarks)
                
                eyemask_path = os.path.join(this_path, "frontalization_models", "eyemask.mat")
                eyemask = np.asarray(io.loadmat(eyemask_path)['eyemask'])
                
                # Perform frontalization
                frontal_raw, frontal_sym, _, _, cropped_frontal_raw, cropped_frontal_sym = frontalize.frontalize(img, proj_matrix, model3D.ref_U, eyemask)
                
                # Apply face masks
                masked_raw, mask1 = extract_face_mask(frontal_sym)
                masked_sym, mask2 = extract_face_mask(cropped_frontal_sym)

                # Track time per image
                end_time = time.time()
                elapsed_time = end_time - start_time  # Time taken to process this image
                print(f"Processed {filename} in {elapsed_time:.4f} seconds")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    demo()
