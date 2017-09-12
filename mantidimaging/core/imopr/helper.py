from __future__ import (absolute_import, division, print_function)

import numpy as np

# TODO should change the name of this file so its not confused with
# the other helper.py that's not in imopr


def handle_indices(indices, retstep=False):
    args = len(indices)
    if args == 1:
        # return start, stop as start + 1
        if not retstep:
            return indices[0], indices[0] + 1
        else:
            return indices[0], indices[0] + 1, 1
    elif args == 2:
        # return start, stop
        if not retstep:
            return indices[0], indices[0] + 1
        else:
            return indices[0], indices[1]
    elif args >= 3:
        # return start, stop, step
        if not retstep:
            return indices[0], indices[1]
        else:
            return indices[0], indices[1], indices[2]


def new_cor_array(num_cors):
    return np.ndarray(shape=(num_cors), dtype='int, float')


def save_cors_to_file(filename, cors):
    np.savetxt(filename, cors, fmt='%i %f', header='slice_index cor')


def load_cors_from_file(filename):
    return np.loadtxt(filename, dtype='int, float', ndmin=1)
