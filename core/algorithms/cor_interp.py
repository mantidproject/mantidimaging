from __future__ import (absolute_import, division, print_function)


def execute(data_length, slice_ids, cors_for_slices):
    import numpy as np
    return np.interp(list(range(data_length)), slice_ids, cors_for_slices)
