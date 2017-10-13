from __future__ import (absolute_import, division, print_function)

from logging import getLogger

import numpy as np
import matplotlib.pyplot as plt

from mantidimaging.core.imopr.utility import handle_indices
from mantidimaging.core.imopr.visualiser import show_3d, show_image


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    getLogger(__name__).info("Running IMOPR with action SINOGRAM")

    if len(indices) == 0:
        show_3d(sample[:], axis=1)
    elif len(indices) == 1:
        show_image(sample[:, indices[0], :])
    else:
        i1, i2 = handle_indices(indices)

        show_3d(sample[i1:i2], axis=1)

    plt.show()


def make_sinogram(sample):
    return np.swapaxes(sample, 0, 1)
