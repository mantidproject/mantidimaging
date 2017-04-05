from __future__ import (absolute_import, division, print_function)
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

    print("Reading indices..")
    i1, i2 = helper.handle_indices(indices)

    for i in range(i1, i2, 1):
        print("Running COR for index", i)
        cor = tool.find_center_vo(tomo=sample[:, :, :], ind=i, ratio=0.5)
        print(cor)

    return sample
