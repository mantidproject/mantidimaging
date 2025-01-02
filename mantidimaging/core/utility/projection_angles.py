# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import math

import numpy as np

from mantidimaging.core.utility.data_containers import ProjectionAngles


def generate(max_angle, number_radiograms) -> ProjectionAngles:
    """
    Generate equidistance projection angles.

    :param max_angle: The maximum angle of the tomography
    :param number_radiograms: The number of radiograms in the tomography
    :returns: list of projection angles
    """
    return ProjectionAngles(np.linspace(0, (math.tau / 360) * max_angle, number_radiograms))
