# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from cil.framework import AcquisitionGeometry


class Geometry(AcquisitionGeometry):
    centre_of_rotation: dict

    def __init__(self, detector_position=None, num_pixels=None, angles=None):
        """
        Uses CIL conventions to determine geometry and centre of rotation.
        """
        super().__init__()

        if detector_position is type(None):
            detector_position = [0, 10, 0]
        if num_pixels is type(None):
            num_pixels = [10, 10]
        if angles is type(None):
            angles = range(0, 180)

        self = self.create_Parallel3D(detector_position)
        self.set_panel(num_pixels)
        self.set_angles(angles)

        self.centre_of_rotation = self.get_centre_of_rotation()

        print(self)

    def get_acq_geometry(self) -> AcquisitionGeometry | None:
        return self

    def set_acq_geometry(self, geometry: AcquisitionGeometry) -> None:
        assert isinstance(geometry, AcquisitionGeometry)
        self._acq_geometry = geometry

    def convert_centre_of_rotation(self, centre_of_rotation):
        """
        Converts the MI centre of rotation (that uses MI conventions) to the CIL convention.
        """
        ...
