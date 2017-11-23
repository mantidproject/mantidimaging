from __future__ import (absolute_import, division, print_function)

from logging import getLogger

import numpy as np


def generate(max_angle, number_radiograms, radians=True):
    """
    Generate equidistance projection angles.

    :param max_angle: The maximum angle of the tomography
    :param number_radiograms: The number of radiograms in the tomography
    :param radians: Default True, if True - return the radians
                    If False - return the degrees
    :returns: list of projection angles
    """
    # TODO use tomopy's generation ?
    # calculate the equidistant increment between angles
    inc = float(max_angle) / number_radiograms
    # arrange from angle 0 to the maximum angle, with a step of the increment
    proj_angles = np.arange(0, number_radiograms * inc, inc)
    getLogger(__name__).debug(
            'Generated projection angles: {}'.format(proj_angles))
    if radians:
        return np.radians(proj_angles)
    else:
        return proj_angles
