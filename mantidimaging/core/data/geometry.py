# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from cil.framework import AcquisitionGeometry


class Geometry(AcquisitionGeometry):
    centre_of_rotation: dict

    def __init__(self, *args, **kwargs):
        """
        Uses CIL conventions to determine geometry and centre of rotation.
        By default, the Geometry object is instantiated using a Parallel3D configuration.
        """

        temp = super().create_Parallel3D(*args, **kwargs)
        self.config = temp.config
        self.set_panel(kwargs["num_pixels"])
        self.set_angles(kwargs["angles"])
        print(self)

        self.centre_of_rotation = self.get_centre_of_rotation()

    def get_geometry(self) -> AcquisitionGeometry | None:
        return self

    def set_geometry(self, geometry: AcquisitionGeometry) -> None:
        self.config = geometry.config

    def convert_cor_single(self, cor) -> dict | None:
        """
        Converts the MI centre of rotation (that uses MI conventions) to the CIL convention.
        """

        result = {}
        cor = cor
        offset = 5.0
        angle = 5.0

        result["offset"] = (offset, 'units distance')
        result["angle"] = (angle, 'radian')

        return result

    def convert_cor_multiple(self, cors):
        ...

    def convert_tilt(self, tilt):
        ...
