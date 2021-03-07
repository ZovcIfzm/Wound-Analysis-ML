"""Load and process images and labels."""
from typing import List, Tuple
from os import environ, listdir, path
from math import comb
from itertools import combinations
from PIL import Image  # type: ignore
from PIL.ImageFilter import GaussianBlur  # type: ignore
import numpy as np  # type: ignore
from tqdm import tqdm  # type: ignore

IMG_DIR = 'images'
LABEL_FILE = 'labels.txt'
NORM = 255


def gpu_init():
    """Set CUDA GPU environment."""
    environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
    environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
    environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices'
    environ['CUDA_VISIBLE_DEVICES'] = '0'


def _open_img(fpath: str,
              width: int,
              height: int,
              blur_radius: int) -> np.ndarray:
    """Open, resize, and blur image."""
    img = Image.open(path.join(IMG_DIR, fpath)) \
        .resize((width, height)) \
        .filter(GaussianBlur(blur_radius))
    return np.asarray_chkfinite(img)


def _load_imgs(width: int, height: int, blur_radius: int) -> np.ndarray:
    """Load, preprocess, and normalize images from IMG_DIR."""
    direc = listdir(IMG_DIR)
    images = np.empty((len(direc), height, width, 3), dtype=int)
    for idx, fpath in tqdm(enumerate(direc), total=len(direc)):
        images[idx, ...] = _open_img(fpath, width, height, blur_radius)
    return images / NORM


def load_data(hyp: dict) -> Tuple[np.ndarray, List[int]]:
    """Load images and labels with hyperparameters."""
    print('Loading and processing data...')
    images = _load_imgs(
        hyp['img_width'],
        hyp['img_height'],
        hyp['blur_radius'])
    labels = np.loadtxt(LABEL_FILE, dtype=int)
    return images, labels


def generate_pairs(images: np.ndarray, labels: List[int]) \
        -> Tuple[np.ndarray, np.ndarray]:
    """Generate Siamese image pairs."""
    num_combs = comb(len(labels), 2)
    img_pairs = np.empty((num_combs, 2, *images.shape[1:]))
    for idx, img_pair in enumerate(combinations(images, 2)):
        img_pairs[idx, ...] = np.stack(img_pair)
    lbl_pairs = np.fromiter((left == right for left, right
                             in combinations(labels, 2)), dtype=bool)
    return img_pairs, lbl_pairs


def split_pairs(images: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Split images into left and right of pairs."""
    return images[:, 0, ...], images[:, 1, ...]