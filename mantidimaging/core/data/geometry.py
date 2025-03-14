# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import numpy

from cil.framework import AcquisitionGeometry
from cil.framework.framework import SystemConfiguration, Parallel2D, Parallel3D, Cone2D, Cone3D


class Geometry(AcquisitionGeometry):
    centre_of_rotation: dict

    def __init__(self,
                 configuration: SystemConfiguration | None = Parallel3D,
                 source_position: list | tuple | numpy.ndarray | None = None,
                 ray_direction: list | tuple | numpy.ndarray | None = None,
                 detector_position: list | tuple | numpy.ndarray | None = None,
                 detector_direction_x: list | tuple | numpy.ndarray | None = None,
                 detector_direction_y: list | tuple | numpy.ndarray | None = None,
                 rotation_axis_position: list | tuple | numpy.ndarray | None = None,
                 rotation_axis_direction: list | tuple | numpy.ndarray | None = None,
                 num_pixels: int | list | tuple | None = None,
                 angles: list | numpy.ndarray | range | None = None,
                 units: str | None = None):
        """
        Uses CIL conventions to determine geometry and centre of rotation.
        By default, the Geometry object is instantiated using a Parallel3D configuration.

        :param configuration: The type of system configuration that the Geometry will use
        :type configuration: SystemConfiguration, optional
        :param source_position: A 2D or 3D vector describing the position of the source
        :type source_position: list, tuple, ndarray, optional
        :param ray_direction: A 2D or 3D vector describing the x-ray direction
        :type ray_direction: list, tuple, ndarray, optional
        :param detector_position: A 2D or 3D vector describing the position of the centre of the detector
        :type detector_position: list, tuple, ndarray, optional
        :param detector_direction_x: A 2D or 3D vector describing the direction of the detector_x
        :type detector_direction_x: list, tuple, ndarray, optional
        :param detector_direction_y: A 2D or 3D vector describing the direction of the detector_y
        :type detector_direction_y: list, tuple, ndarray, optional
        :param rotation_axis_position: A 2D or 3D vector describing the position of the axis of rotation
        :type rotation_axis_position: list, tuple, ndarray, optional
        :param rotation_axis_direction: A 2D or 3D vector describing the direction of the axis of rotation
        :type rotation_axis_direction: list, tuple, ndarray, optional
        :param num_pixels: num_pixels_h or (num_pixels_h, num_pixels_v) containing the number of pixels of the panel
        :type num_pixels: int, list, tuple, optional
        :param angles: The angular positions of the acquisition data
        :type angles: list, ndarray, optional
        :param units: Label the units of distance used for the configuration, consistent for the geometry and panel
        :type units: string, optional
        :return: returns a configured Geometry object
        :rtype: Geometry
        """

        if ray_direction is None:
            ray_direction = [0, 1, 0]
        if detector_position is None:
            detector_position = [0, 0, 0]
        if detector_direction_x is None:
            detector_direction_x = [1, 0, 0]
        if detector_direction_y is None:
            detector_direction_y = [0, 0, 1]
        if rotation_axis_position is None:
            rotation_axis_position = [0, 0, 0]
        if rotation_axis_direction is None:
            rotation_axis_direction = [0, 0, 1]
        if num_pixels is None:
            num_pixels = [10, 10]
        if angles is None:
            angles = range(0, 180)
        if units is None:
            units = 'units distance'

        if configuration is Parallel2D:
            self.__dict__ = super().create_Parallel2D().__dict__.copy()
            self.config.system = Parallel2D(ray_direction, detector_position, detector_direction_x,
                                            detector_direction_y, rotation_axis_position, rotation_axis_direction,
                                            units)
        elif configuration is Parallel3D:
            self.__dict__ = super().create_Parallel3D().__dict__.copy()
            self.config.system = Parallel3D(ray_direction, detector_position, detector_direction_x,
                                            detector_direction_y, rotation_axis_position, rotation_axis_direction,
                                            units)
        elif configuration is Cone2D:
            self.__dict__ = super().create_Cone2D().__dict__.copy()
            self.config.system = Cone2D(source_position, detector_position, detector_direction_x,
                                        rotation_axis_position, units)
        elif configuration is Cone3D:
            self.__dict__ = super().create_Cone3D().__dict__.copy()
            self.config.system = Cone3D(source_position, detector_position, detector_direction_x, detector_direction_y,
                                        rotation_axis_position, rotation_axis_direction, units)

        self.set_panel(num_pixels)
        self.set_angles(angles)

        self.centre_of_rotation = self.get_centre_of_rotation()

        print(self)

    def get_acq_geometry(self) -> AcquisitionGeometry | None:
        return self

    def set_acq_geometry(self, geometry: AcquisitionGeometry) -> None:
        assert isinstance(geometry, AcquisitionGeometry)
        self._acq_geometry = geometry

    def convert_centre_of_rotation(self, centre_of_rotation, tilt) -> dict | None:
        """
        Converts the MI centre of rotation (that uses MI conventions) to the CIL convention.
        """
        result = {}
        centre_of_rotation = centre_of_rotation
        tilt = tilt
        offset = 5.0
        angle = 5.0

        result["offset"] = (offset, 'units distance')
        result["angle"] = (angle, 'radian')

        return result
