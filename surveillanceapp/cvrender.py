import cv2
import numpy as np
import os
from django.conf import settings


def overlap_play(img1):
    img2 = cv2.imread(os.path.join(settings.BASE_DIR, 'static', 'img/play.png'))
    start_row = int((img1.shape[0] - img2.shape[0]) / 2)
    start_col = int((img1.shape[1] - img2.shape[1]) / 2)
    cv2.addWeighted(src1=img1[start_row:start_row + img2.shape[0], start_col:start_col + img2.shape[1]],
                    alpha=0.5,
                    src2=img2,
                    beta=0.5,
                    gamma=0,
                    dst=img1[start_row:start_row + img2.shape[0], start_col:start_col + img2.shape[1]])
    return img1
