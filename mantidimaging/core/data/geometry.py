# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from cil.framework import AcquisitionGeometry

from mantidimaging.core.utility.data_containers import ScalarCoR


class Geometry(AcquisitionGeometry):
    cor_list: list[dict] | None = None
    is_parallel: bool = False

    def __init__(self,
                 num_pixels: list | tuple = (10, 10),
                 pixel_size: list | tuple = (1., 1.),
                 angle_unit: str = "radian",
                 units: str = "default",
                 *args,
                 **kwargs):
        """
        Uses CIL conventions to determine geometry and centre of rotation.
        By default, the Geometry object is instantiated using a Parallel3D configuration.

        :param num_pixels: (num_pixels_h, num_pixels_v) containing the number of pixels of the panel.
        :type num_pixels: list, tuple
        :param pixel_size: (pixel_size_h, pixel_size_v) containing the size of the pixels of the panel.
        :type pixel_size: list, tuple
        :param angle_unit: The units of the stored angles, "degree" or "radian".
        :type angle_unit: str
        :param units: The units of distance used for the configuration, consistent for geometry and panel.
        :type units: str
        """

        temp = super().create_Parallel3D(*args, units=units, **kwargs)
        self.set_geometry(temp)
        self.is_parallel = True

        self.set_panel(num_pixels=num_pixels, pixel_size=pixel_size)
        self.set_angles(angles=range(0, 180), angle_unit=angle_unit)
        self.set_cor(self.get_centre_of_rotation())

    def set_geometry(self, geo: AcquisitionGeometry) -> None:
        """
        Sets the Geometry object's configuration to that of the object supplied.

        :param geo: Configuration will be set to this object's configuration.
        :type geo: AcquisitonGeometry
        """
        self.config = geo.config

    def set_cor(self, cor: dict) -> None:
        """
        Sets the Geometry object's centre of rotation.
        Supplied distance and angle units will be converted to those set by the configuration.

        :param cor: Dictionary object defining the centre of rotation as an "offset" and an "angle".
        :type cor: dict
        """

        self.set_centre_of_rotation(offset=cor["offset"][0],
                                    distance_units=cor["offset"][1],
                                    angle=cor["angle"][0],
                                    angle_units=cor["angle"][1])

    def set_cor_list(self, cor_list: list[dict]) -> None:
        """
        Sets the Geometry object's list of per-slice centre of rotations.

        :param cor_list: List of dictionary objects defining the centre of rotation as an "offset" and an "angle".
        :type cor_list: list[dict]
        """
        self.cor_list = cor_list

    def convert_cor(self, cor: ScalarCoR, tilt: float) -> dict:
        """
        Converts a centre of rotation (that uses MI conventions) to the CIL convention.

        :param cor: A ScalarCoR object defining the centre of rotation as a float value.
        :type cor: ScalarCoR
        :param tilt: A float value defining the tilt in degrees.
        :type tilt: float
        """
        cil_cor: dict = {}
        offset: float = (cor.value - self.config.panel.num_pixels[0] / 2) * self.config.panel.pixel_size[0]
        cil_cor["offset"] = (offset, "pixels")
        cil_cor["angle"] = (-tilt, "degree")

        return cil_cor

    def convert_cor_list(self, cor_list: list[ScalarCoR], tilt: float) -> list[dict]:
        """
        Converts a list of per-slice centre of rotations (that use MI conventions) to the CIL convention.

        :param cor_list: List of ScalarCoR objects defining the centre of rotation.
        :type angles: list[ScalarCoR]
        :param tilt: A float value defining the tilt in degrees.
        :type angles: float
        """
        cil_cor_list: list = []

        for cor in cor_list:
            cil_cor = self.convert_cor(cor, tilt)
            cil_cor_list.append(cil_cor)
        self.set_cor(cil_cor_list[self.config.panel.num_pixels[1] // 2])
        self.set_cor_list(cil_cor_list)

        return cil_cor_list
