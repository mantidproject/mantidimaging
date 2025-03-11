# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from cil.framework import AcquisitionGeometry

from mantidimaging.core.data import ImageStack


class ImageStackGeometry(ImageStack, AcquisitionGeometry):
    acq_geometry: AcquisitionGeometry
    centre_of_rotation: dict

    def __init__(self):
        self.acq_geometry = self.create_Parallel3D(detector_position=[0, 10, 0])
        self.acq_geometry.set_panel(num_pixels=[10, 10])
        self.acq_geometry.set_angles(angles=range(0, 180))

        self.centre_of_rotation = self.get_centre_of_rotation()

    def get_acq_geometry(self) -> AcquisitionGeometry | None:
        return self.acq_geometry

    def set_acq_geometry(self, value: AcquisitionGeometry) -> None:
        assert isinstance(value, AcquisitionGeometry)
        self._acq_geometry = value

    def convert_centre_of_rotation(self, value):
        ...

    def convert_tilt(self, value):
        ...
