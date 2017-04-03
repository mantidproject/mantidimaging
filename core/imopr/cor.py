from __future__ import (absolute_import, division, print_function)
from core.imopr.sinogram import make_sinogram
import numpy as np


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    from core.imopr import helper
    helper.print_start("Running IMOPR with action COR")

    from core.tools import importer
    tool = importer.timed_import(config)

    print("Calculating projection angles..")
    inc = float(config.func.max_angle) / sample.shape[0]
    proj_angles = np.arange(0, sample.shape[0] * inc, inc)
    proj_angles = np.radians(proj_angles)

    print("Processing indices..")
    i1, i2, step = helper.handle_indices(indices, retstep=True)
    initial_guess = config.func.cors if config.func.cors is not None else None

    for i in range(i1, i2, step):
        print("Running COR for index", i, end=" ")
        cor = tool.find_center(
            tomo=sample[:, :, :],
            theta=proj_angles,
            sinogram_order=True,
            ind=i,
            init=initial_guess)
        print(cor)

    return sample
