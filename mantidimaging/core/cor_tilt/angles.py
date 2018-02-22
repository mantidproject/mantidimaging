import math

import numpy as np


def cors_to_tilt_angle(slice_upper, m):
    adj = slice_upper
    opp = m * slice_upper
    hyp = np.sqrt(adj ** 2 + opp ** 2)
    return np.arcsin(opp / hyp)


def tilt_angle_to_cors(theta, cor_zero, slice_range):
    # Calculate max COR
    adj = slice_range[-1] - slice_range[0]
    adj_a = (math.pi / 2) - theta
    cor_max = ((adj / np.sin(adj_a)) * np.sin(theta)) + cor_zero

    # Interpolate COR over range
    interpolated_cors = np.interp(
            slice_range,
            np.linspace(slice_range[0], slice_range[-1], 2),
            np.asarray([cor_zero, cor_max]))

    return interpolated_cors
