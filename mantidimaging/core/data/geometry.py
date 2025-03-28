# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from cil.framework import AcquisitionGeometry
from mantidimaging.core.utility.data_containers import ScalarCoR


class Geometry(AcquisitionGeometry):
    cor_list: list[dict]
    is_parallel: bool

    def __init__(self, num_pixels=(10, 10), *args, **kwargs):
        """
        Uses CIL conventions to determine geometry and centre of rotation.
        By default, the Geometry object is instantiated using a Parallel3D configuration.
        """

        temp = super().create_Parallel3D(*args, **kwargs)
        self.set_geometry(temp)
        self.is_parallel = True

        self.set_panel(num_pixels=num_pixels, pixel_size=(1.))
        self.set_angles(angles=range(0, 180))

        print(self)

    def set_geometry(self, geometry: AcquisitionGeometry) -> None:
        """
        Sets the Geometry object's configuration to that of the object supplied.
        """
        self.config = geometry.config

    def set_cor(self, cor):
        """
        Sets the Geometry object's centre of rotation. If the centre of rotation
        uses the MI convention, it is converted to the CIL convention.
        """
        if cor is ScalarCoR:
            cor = self.convert_cor(cor)

        self.set_centre_of_rotation(offset=cor["offset"][0],
                                    distance_units=cor["offset"][1],
                                    angle=cor["angle"][0],
                                    angle_units=cor["angle"][1])

    def set_cor_list(self, cor_list):
        """
        Sets the Geometry object's list of per-slice centre of rotations. If the list
        uses the MI convention, it is converted to the CIL convention.
        """
        if cor_list is list[ScalarCoR]:
            self.cor_list = self.convert_cor_list(cor_list)
        else:
            self.cor_list = cor_list

    def set_pixel_size(self, pixel_size: float):
        """
        Sets the Geometry object's pixel size attribute.
        This is the size of the pixels in the panel.
        """
        self.config.panel.pixel_size = pixel_size

    def set_pixel_num_h(self, pixel_num_h: int):
        """
        Sets the Geometry object's number of horizontal pixels attribute.
        This is the number of horizontal pixels of the panel.
        """
        self.config.panel.num_pixels[0] = pixel_num_h

    def set_pixel_num_v(self, pixel_num_v: int):
        """
        Sets the Geometry object's number of vertical pixels attribute.
        This is the number of vertical pixels of the panel.
        """
        self.config.panel.num_pixels[1] = pixel_num_v

    def convert_cor(self, cor: ScalarCoR, tilt: float) -> dict:
        """
        Converts a centre of rotation (that uses MI conventions) to the CIL convention.
        """
        cil_cor: dict = {}
        offset: float = (cor.value - self.pixel_num_h / 2) * self.config.panel.pixel_size
        cil_cor["offset"] = (offset, "pixels")
        cil_cor["angle"] = (tilt, "degree")
        self.set_cor(cil_cor)
        print(cil_cor)
        return cil_cor

    def convert_cor_list(self, cor_list: list[ScalarCoR], tilt: float) -> list[dict]:
        """
        Converts a list of per-slice centre of rotations (that use MI conventions) to the CIL convention.
        """
        cil_cor_list: list = []
        for cor in cor_list:
            cil_cor = self.convert_cor(cor, tilt)
            cil_cor_list.append(cil_cor)
        self.set_cor_list(cil_cor_list)
        self.set_cor(cil_cor_list[self.pixel_num_v // 2])
        print(cil_cor_list)
        return cil_cor_list
