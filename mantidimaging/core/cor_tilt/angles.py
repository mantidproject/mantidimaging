import numpy as np


def cors_to_tilt_angle(slice_upper, m):
    adj = slice_upper
    opp = m * slice_upper
    hyp = np.sqrt(adj ** 2 + opp ** 2)
    return np.arcsin(opp / hyp)
