from __future__ import (absolute_import, division, print_function)
from imopr.visualiser import show_3d

import numpy as np


def execute(sample, flat, dark, config, indices):
    i1 = indices[0]
    i2 = indices[1]
    show_3d(sample[i1:i2], 0)

    sample = make_sinogram(sample)

    show_3d(sample[i1:i2], 0)

    # stop python from exiting
    import matplotlib.pyplot as plt
    plt.show()

    return sample


def make_sinogram(sample):
    sample = np.swapaxes(sample, 0, 1)
    return sample

