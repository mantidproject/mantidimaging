from __future__ import (absolute_import, division, print_function)
from imopr.visualiser import show_3d

import numpy as np


def execute(sample, flat, dark, config, indices):
    import pydevd
    pydevd.settrace('localhost', port=59003, stdoutToServer=True, stderrToServer=True)

    from imopr import helper
    helper.print_start("Running IMOPR with action SINOGRAM")

    i1, i2 = helper.handle_indices(indices)

    show_3d(sample[i1:i2], 0)

    sample = make_sinogram(sample)
    print(sample.shape)
    show_3d(sample, 0)

    # stop python from exiting
    import matplotlib.pyplot as plt
    plt.show()

    return sample


def make_sinogram(sample):
    return np.swapaxes(sample, 0, 1)
