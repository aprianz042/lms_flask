__author__ = 'Douglas'

import dlib
import os
import numpy as np

this_path = os.path.dirname(os.path.abspath(__file__))


def _shape_to_np(shape):
    # Convert dlib shape object to numpy array (68 x 2)
    coords = np.zeros((68, 2), dtype='float32')
    for i in range(68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords


def get_landmarks(img):
    predictor_path = os.path.join(this_path, "model", "shape_predictor_68_face_landmarks.dat")

    if not os.path.isfile(predictor_path):
        raise FileNotFoundError(
            f"Missing model file: {predictor_path}\n"
            "You can download it from:\n"
            "http://sourceforge.net/projects/dclib/files/dlib/v18.10/shape_predictor_68_face_landmarks.dat.bz2"
        )

    # Inisialisasi detektor dan prediktor
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    # Deteksi wajah
    dets = detector(img, 1)
    #print("Number of faces detected: {}".format(len(dets)))

    lmarks = []
    shapes = []
    for det in dets:
        shape = predictor(img, det)
        shapes.append(shape)
        lmarks.append(_shape_to_np(shape))

    if len(lmarks) == 0:
        raise ValueError("No facial landmarks found.")

    return np.asarray(lmarks, dtype='float32')  # shape: (N_faces, 68, 2)


def display_landmarks(img, dets, shapes):
    # Opsional untuk visualisasi
    win = dlib.image_window()
    win.clear_overlay()
    win.set_image(img)
    for shape in shapes:
        win.add_overlay(shape)
    win.add_overlay(dets)
    dlib.hit_enter_to_continue()
