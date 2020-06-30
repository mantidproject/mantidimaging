import math

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
    if radians:
        return np.linspace(0, (math.tau / 360) * max_angle, number_radiograms)
    else:
        return np.linspace(0, 360, number_radiograms)
