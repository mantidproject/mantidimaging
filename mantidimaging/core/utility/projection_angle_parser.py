# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from mantidimaging.core.utility.data_containers import ProjectionAngles


class ProjectionAngleFileParser:
    ERROR_MESSAGE = "The provided file cannot be read. Angles are expected in DEGREES as comma \
                    separated values on a single line, or a single angle value per line"

    def __init__(self, file: str) -> None:
        with open(file, 'r') as f:
            self.contents = f.readlines()

    def get_projection_angles(self) -> ProjectionAngles:
        if "," in self.contents[0]:
            if len(self.contents) > 2:
                # allows a file that has a single line of CSV angles,
                # and a new line after it
                raise RuntimeError(self.ERROR_MESSAGE)
            string_content = self.contents[0]
            # Handles the angles provided as comma separated values

            # angles are in CSV format 0,0.1,0.2...
            values = np.deg2rad([float(angle.strip()) for angle in string_content.split(",")])
        else:
            # Handles the angles provided as a value per line
            values = np.deg2rad([float(angle.strip()) for angle in self.contents])

        return ProjectionAngles(values)
