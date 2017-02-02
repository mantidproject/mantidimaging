from __future__ import (absolute_import, division, print_function)
from imopr.sinogram import make_sinogram
import numpy as np


def execute(sample, flat, dark, config, indices):
    from recon.tools import tool_importer
    tool = tool_importer.do_importing(config.func.tool)

    inc = float(config.func.max_angle) / sample.shape[0]
    proj_angles = np.arange(0, sample.shape[0] * inc, inc)
    proj_angles = np.radians(proj_angles)

    from imopr.sinogram import make_sinogram
    sample = make_sinogram(sample)

    i1 = indices[0]
    try:
        i2 = indices[1]
    except IndexError:
        i2 = i1+1

    print("recon on:", i1, "cor:", config.func.cor)
    initial_guess = config.func.cor if config.func.cor is not None else None

    for i in range(i1, i2):
        cor = tool.find_center(tomo=sample, theta=proj_angles, sinogram_order=True, ind=i, init=initial_guess)
        print(cor)

    # stop python from exiting
    import matplotlib.pyplot as plt
    plt.show()

    return sample