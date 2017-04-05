from __future__ import (absolute_import, division, print_function)
import numpy as np


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    from core.imopr import helper
    helper.print_start(
        "Running IMOPR with action COR using tomopy find_center_pc")

    from core.tools import importer
    tool = importer.timed_import(config)

    inc = float(config.func.max_angle) / sample.shape[0]
    proj_angles = np.arange(0, sample.shape[0] * inc, inc)
    proj_angles = np.radians(proj_angles)

    i1, i2 = helper.handle_indices(indices)

    cor = tool._tomopy.find_center_pc(sample[i1], sample[i2])
    print(cor)

    return sample
