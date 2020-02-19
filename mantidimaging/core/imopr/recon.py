from logging import getLogger

import numpy as np

from mantidimaging.core.imopr.sinogram import make_sinogram
from mantidimaging.core.imopr.utility import handle_indices
from mantidimaging.core.imopr.visualiser import show_3d
from mantidimaging.core.tools.importer import timed_import


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    getLogger(__name__).info("Running IMOPR with action RECON")

    tool = timed_import(config)

    inc = float(config.func.max_angle) / sample.shape[0]
    proj_angles = np.arange(0, sample.shape[0] * inc, inc)
    proj_angles = np.radians(proj_angles)

    sample = make_sinogram(sample)

    i1, i2 = handle_indices(indices)

    sample = tool.run_reconstruct(sample[i1:i2, :, :],
                                  config,
                                  config.helper,
                                  sinogram_order=True,
                                  proj_angles=proj_angles)

    show_3d(sample, 0, block=True)

    return sample
