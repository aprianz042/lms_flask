__author__ = 'Douglas'

import scipy.io as scio
import cv2
import numpy as np

np.set_printoptions(formatter={'float_kind': lambda x: "%.4f" % x})


class ThreeD_Model:
    def __init__(self, path, name):
        self.load_model(path, name)

    def load_model(self, path, name):
        model = scio.loadmat(path)[name]
        self.out_A = np.asarray(model['outA'][0, 0], dtype='float32')  # 3x3
        self.size_U = model['sizeU'][0, 0][0]  # 1x2
        self.model_TD = np.asarray(model['threedee'][0, 0], dtype='float32')  # 68x3
        self.indbad = model['indbad'][0, 0]  # 0x1
        self.ref_U = np.asarray(model['refU'][0, 0])


def frontalize(img, proj_matrix, ref_U, eyemask):
    ACC_CONST = 800
    img = img.astype('float32')
    print(f"Query image shape: {img.shape}")

    bgind = np.sum(np.abs(ref_U), 2) == 0

    threedee = np.reshape(ref_U, (-1, 3), order='F').T
    temp_proj = proj_matrix @ np.vstack((threedee, np.ones((1, threedee.shape[1]))))
    temp_proj2 = temp_proj[:2, :] / temp_proj[2:3, :]

    bad = (
        (temp_proj2[0, :] < 1) |
        (temp_proj2[1, :] > img.shape[0]) |
        (temp_proj2[0, :] > img.shape[1]) |
        (bgind.flatten(order='F'))
    )

    temp_proj2 -= 1
    badind = np.nonzero(bad)[0]
    temp_proj2[:, badind] = 0

    y_coords = np.clip(temp_proj2[1, :].round().astype(np.int64), 0, 319)
    x_coords = np.clip(temp_proj2[0, :].round().astype(np.int64), 0, 319)
    ind = np.ravel_multi_index((y_coords, x_coords), dims=(320, 320), order='F')

    synth_frontal_acc = np.zeros(ref_U.shape[:2], dtype='float32')
    synth_frontal_acc = synth_frontal_acc.flatten(order='F')
    c, ic = np.unique(ind, return_inverse=True)
    count = np.bincount(ic)
    synth_frontal_acc[c] = count
    synth_frontal_acc = synth_frontal_acc.reshape((320, 320), order='F')
    synth_frontal_acc[bgind] = 0
    synth_frontal_acc = cv2.GaussianBlur(synth_frontal_acc, (15, 15), 30., borderType=cv2.BORDER_REPLICATE)

    mapX = temp_proj2[0, :].astype(np.float32).reshape((-1, 320), order='F')
    mapY = temp_proj2[1, :].astype(np.float32).reshape((-1, 320), order='F')

    frontal_raw = cv2.remap(img, mapX, mapY, cv2.INTER_CUBIC)
    frontal_raw = frontal_raw.reshape((-1, 3), order='F')
    frontal_raw[badind, :] = 0
    frontal_raw = frontal_raw.reshape((320, 320, 3), order='F')

    midcolumn = int(np.round(ref_U.shape[1] / 2))
    sumaccs = synth_frontal_acc.sum(axis=0)
    sum_left = sumaccs[:midcolumn].sum()
    sum_right = sumaccs[midcolumn + 1:].sum()
    sum_diff = sum_left - sum_right

    if abs(sum_diff) > ACC_CONST:
        ones = np.ones((ref_U.shape[0], midcolumn), dtype='float32')
        zeros = np.zeros((ref_U.shape[0], midcolumn), dtype='float32')
        weights = np.hstack((zeros, ones)) if sum_diff > ACC_CONST else np.hstack((ones, zeros))
        weights = cv2.GaussianBlur(weights, (33, 33), 60.5, borderType=cv2.BORDER_REPLICATE)

        synth_frontal_acc /= np.max(synth_frontal_acc)
        weight_take_from_org = 1. / np.exp(0.5 + synth_frontal_acc)
        weight_take_from_sym = 1 - weight_take_from_org

        weight_take_from_org *= np.fliplr(weights)
        weight_take_from_sym *= np.fliplr(weights)

        weight_take_from_org = np.repeat(weight_take_from_org[:, :, np.newaxis], 3, axis=2)
        weight_take_from_sym = np.repeat(weight_take_from_sym[:, :, np.newaxis], 3, axis=2)
        weights = np.repeat(weights[:, :, np.newaxis], 3, axis=2)

        denominator = weights + weight_take_from_org + weight_take_from_sym
        frontal_sym = (
            frontal_raw * weights +
            frontal_raw * weight_take_from_org +
            np.fliplr(frontal_raw) * weight_take_from_sym
        ) / denominator

        frontal_sym = frontal_sym * (1 - eyemask) + frontal_raw * eyemask

        frontal_raw = np.clip(frontal_raw, 0, 255).astype('uint8')
        frontal_sym = np.clip(frontal_sym, 0, 255).astype('uint8')
    else:
        frontal_sym = frontal_raw.astype('uint8')

    return frontal_raw, frontal_sym
