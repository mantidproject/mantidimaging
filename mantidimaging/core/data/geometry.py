# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from cil.framework import AcquisitionGeometry
from mantidimaging.core.utility.data_containers import ScalarCoR


class Geometry(AcquisitionGeometry):
    cor: dict
    cor_list: list[dict]
    tilt: float
    pixel_num_v: int
    pixel_num_h: int

    def __init__(self, *args, **kwargs):
        """
        Uses CIL conventions to determine geometry and centre of rotation.
        By default, the Geometry object is instantiated using a Parallel3D configuration.
        """

        temp = super().create_Parallel3D(*args, **kwargs)
        self.config = temp.config
        self.set_panel(num_pixels=[10, 10])
        self.set_angles(angles=range(0, 180))

        self.cor = self.get_centre_of_rotation()

        print(self)

    def get_geometry(self) -> AcquisitionGeometry | None:
        """
        Returns the Geometry object.
        """
        return self

    def set_geometry(self, geometry: AcquisitionGeometry) -> None:
        """
        Sets the Geometry object's configuration to that of the object supplied.
        """
        self.config = geometry.config

    def get_cor(self, distance_units='default', angle_units='radian'):
        """
        Returns the Geometry object's centre of rotation attribute.
        """
        cor = super().get_centre_of_rotation(distance_units, angle_units)
        return cor

    def set_cor(self, cor):
        """
        Sets the Geometry object's centre of rotation. If the centre of rotation
        uses the MI convention, it is converted to the CIL convention.
        """
        if cor is ScalarCoR:
            self.cor = self.convert_cor(cor)
        else:
            self.cor = cor

    def get_cor_list(self):
        """
        Returns the Geometry object's list of per-slice centre of rotations attribute.
        """
        return self.cor_list

    def set_cor_list(self, cor_list):
        """
        Sets the Geometry object's list of per-slice centre of rotations. If the list
        uses the MI convention, it is converted to the CIL convention.
        """
        if cor_list is list[ScalarCoR]:
            self.cor_list = self.convert_cor_list(cor_list)
        else:
            self.cor_list = cor_list

    def get_tilt(self):
        """
        Returns the Geometry object's tilt attribute.
        """
        return self.tilt

    def set_tilt(self, tilt):
        """
        Sets the Geometry object's tilt attribute.
        """
        self.tilt = tilt

    def set_pixel_num_v(self, pixel_num_v: int):
        """
        Sets the Geometry object's number of vertical pixels attribute.
        This is the number of vertical pixels of the panel.
        """
        self.pixel_num_v = pixel_num_v

    def set_pixel_num_h(self, pixel_num_h: int):
        """
        Sets the Geometry object's number of horizontal pixels attribute.
        This is the number of horizontal pixels of the panel.
        """
        self.pixel_num_h = pixel_num_h

    def convert_cor(self, cor: ScalarCoR) -> dict:
        """
        Converts a centre of rotation (that uses MI conventions) to the CIL convention.
        """
        cil_cor: dict = {}  # Convert the MI COR to a CIL COR
        cil_cor["offset"] = (cor.value, 'units distance')
        cil_cor["angle"] = (self.tilt, 'radian')
        print(cil_cor)
        return cil_cor

    def convert_cor_list(self, cor_list: list[ScalarCoR]) -> list[dict]:
        """
        Converts a list of per-slice centre of rotations (that use MI conventions) to the CIL convention.
        """
        cil_cor_list: list = []
        for cor in cor_list:
            cil_cor = self.convert_cor(cor)
            cil_cor_list.append(cil_cor)
        print(cil_cor_list)
        return cil_cor_list
