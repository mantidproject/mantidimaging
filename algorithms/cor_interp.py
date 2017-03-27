from __future__ import (absolute_import, division, print_function)


def execute(data_length, slices, cors):
    import numpy as np
    return np.interp(list(range(data_length)), slices, cors)