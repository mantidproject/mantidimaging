# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from cil.framework import AcquisitionGeometry

from mantidimaging.core.utility.data_containers import ScalarCoR

from math import tan, radians, degrees


class Geometry(AcquisitionGeometry):
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
        super().__init__()
        parallel_3d = self.create_Parallel3D(*args, units=units, **kwargs)
        self.config = parallel_3d.config
        self.is_parallel = True

        self.set_panel(num_pixels=num_pixels, pixel_size=pixel_size)
        self.set_angles(angles=range(0, 180), angle_unit=angle_unit)

    def set_geometry_from_cor_tilt(self, cor: ScalarCoR, tilt: float) -> None:
        """
        Converts a centre of rotation (that uses MI conventions) to the CIL convention.

        :param cor: A ScalarCoR object defining the centre of rotation as a float value.
        :type cor: ScalarCoR
        :param tilt: A float value defining the tilt in degrees.
        :type tilt: float
        """

        # cil_cor = cor.value + (self.config.panel.num_pixels[0] / 2) * tan(radians(self.tilt))

        offset: float = (cor - self.config.panel.num_pixels[0] / 2) * self.config.panel.pixel_size[0]

        self.set_centre_of_rotation(offset=offset, angle=-tilt, angle_units='degree')

    @property
    def tilt(self) -> float:
        slope: float = self.get_centre_of_rotation()['angle'][0]
        tilt = -degrees(slope)
        return round(tilt)

    @property
    def cor(self) -> ScalarCoR:
        offset = self.get_centre_of_rotation()['offset'][0]
        num_pixels = self.config.panel.num_pixels[0] / 2
        pixel_size = self.config.panel.pixel_size[0]
        cil_cor = (offset / pixel_size) + num_pixels

        tilt_radians = -radians(self.tilt)
        mi_cor = cil_cor - num_pixels * tan(tilt_radians)

        return ScalarCoR(round(mi_cor))
