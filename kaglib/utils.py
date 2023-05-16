# General utilities
import os
from tqdm import tqdm
from time import time
from fastprogress import progress_bar
import gc
import numpy as np
import h5py
from IPython.display import clear_output
from collections import defaultdict
from copy import deepcopy

# CV/ML
import cv2
import torch
import torch.nn.functional as F
import kornia as K
import kornia.feature as KF
from PIL import Image
import timm
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform

# 3D reconstruction
import pycolmap


def arr_to_str(a):
    return ';'.join([str(x) for x in a.reshape(-1)])


def load_torch_image(fname, device=torch.device('cpu')):
    img = K.image_to_tensor(cv2.imread(fname), False).float() / 255.
    img = K.color.bgr_to_rgb(img.to(device))
    return img


import copy


def create_submission(out_results, data_dict):
    with open(f'submission.csv', 'w') as f:
        f.write(
            'image_path,dataset,scene,rotation_matrix,translation_vector\n')
        for dataset in data_dict:
            for scene in data_dict[dataset]:
                for image in data_dict[dataset][scene]:
                    print(image)
                    if image in out_results[dataset][scene]:
                        print("IN")
                        R = out_results[dataset][scene][image]['R'].reshape(-1)
                        T = out_results[dataset][scene][image]['t'].reshape(-1)
                        print("R: ", R)
                        print("T: ", T)
                    else:
                        print("OUT")
                        R = np.eye(3).reshape(-1)
                        T = np.zeros((3))
                    f.write(
                        f'{image},{dataset},{scene},{arr_to_str(R)},{arr_to_str(T)}\n'
                    )


def read_csv_data_path(csv_path):
    data_dict = {}
    print(csv_path)
    with open(csv_path) as f:
        for i, l in enumerate(f):
            # Skip header.
            if l and i > 0:
                dataset, scene, image, _, _ = l.strip().split(',')
                if dataset not in data_dict:
                    data_dict[dataset] = {}
                if scene not in data_dict[dataset]:
                    data_dict[dataset][scene] = []
                data_dict[dataset][scene].append(image)

    for dataset in data_dict:
        for scene in data_dict[dataset]:
            print(
                f'{dataset} / {scene} -> {len(data_dict[dataset][scene])} images'
            )

    return data_dict


def print_data_dict(data_dict):
    for dataset in data_dict:
        for scene in data_dict[dataset]:
            print(
                f'{dataset} / {scene} -> {len(data_dict[dataset][scene])} images'
            )


def get_unique_idxs(A, dim=0):
    # https://stackoverflow.com/questions/72001505/how-to-get-unique-elements-and-their-firstly-appeared-indices-of-a-pytorch-tenso
    unique, idx, counts = torch.unique(A,
                                       dim=dim,
                                       sorted=True,
                                       return_inverse=True,
                                       return_counts=True)
    _, ind_sorted = torch.sort(idx, stable=True)
    cum_sum = counts.cumsum(0)
    cum_sum = torch.cat((torch.tensor([0],
                                      device=cum_sum.device), cum_sum[:-1]))
    first_indices = ind_sorted[cum_sum]
    return first_indices
