from __future__ import absolute_import, division, print_function

import numpy as np


def execute(data_length, slice_ids, cors_for_slices):
    return np.interp(list(range(data_length)), slice_ids, cors_for_slices)
