# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np


class SVModel:
    def __init__(self):
        pass

    @staticmethod
    def sum_images(images):
        return np.sum(images, axis=0)

    @staticmethod
    def swap_axes(images):
        return np.swapaxes(images, 0, 1)
