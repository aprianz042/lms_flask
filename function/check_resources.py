__author__ = 'Douglas'

import urllib.request
import os
import bz2

dlib_facial_landmark_model_url = (
    "http://ufpr.dl.sourceforge.net/project/dclib/dlib/v18.10/"
    "shape_predictor_68_face_landmarks.dat.bz2"
)


def download_file(url, dest):
    file_name = os.path.basename(url)
    file_path = os.path.join(dest, file_name)

    print(f"Downloading: {file_name} to {file_path}")
    with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
        file_size = int(response.getheader("Content-Length"))
        print(f"File size: {file_size / 1024 / 1024:.2f} MB")

        downloaded = 0
        block_size = 8192
        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            downloaded += len(buffer)
            out_file.write(buffer)
            percent = downloaded * 100.0 / file_size
            print(f"\rDownloaded: {percent:.2f}% ({downloaded // 1024} KB)", end='')
    print("\nDownload complete!")


def extract_bz2(file_path):
    print("Extracting...")
    output_path = file_path[:-4]  # remove .bz2 extension
    with bz2.BZ2File(file_path, 'rb') as file, open(output_path, 'wb') as new_file:
        data = file.read()
        new_file.write(data)
    print(f"Extracted to: {output_path}")


def check_dlib_landmark_weights():
    dlib_models_folder = "dlib_models"
    dat_path = os.path.join(dlib_models_folder, "shape_predictor_68_face_landmarks.dat")
    bz2_path = dat_path + ".bz2"

    if not os.path.isdir(dlib_models_folder):
        os.makedirs(dlib_models_folder)

    if not os.path.isfile(dat_path):
        if not os.path.isfile(bz2_path):
            download_file(dlib_facial_landmark_model_url, dlib_models_folder)
        extract_bz2(bz2_path)
