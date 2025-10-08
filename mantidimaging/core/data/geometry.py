# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from enum import Enum
from math import tan, radians, degrees

from cil.framework import AcquisitionGeometry
from mantidimaging.core.utility.data_containers import ScalarCoR


class GeometryType(Enum):
    PARALLEL3D = "Parallel 3D"
    CONE3D = "Cone 3D"


class Geometry(AcquisitionGeometry):

    def __init__(self,
                 type: GeometryType = GeometryType.PARALLEL3D,
                 num_pixels: list | tuple = (10, 10),
                 pixel_size: list | tuple = (1., 1.),
                 source_position: list | tuple = (0, -1, 0),
                 detector_position: list | tuple = (0, 1, 0),
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

        if type == GeometryType.PARALLEL3D:
            parallel_3d = self.create_Parallel3D(*args, units=units, **kwargs)
            self.config = parallel_3d.config
        else:
            conebeam_3d = self.create_Cone3D(*args,
                                             source_position=source_position,
                                             detector_position=detector_position,
                                             units=units,
                                             **kwargs)
            self.config = conebeam_3d.config

        self.set_panel(num_pixels=num_pixels, pixel_size=pixel_size)
        self.set_angles(angles=range(0, 180), angle_unit=angle_unit)

    def set_geometry_from_cor_tilt(self, cor: ScalarCoR, tilt: float) -> None:
        """
        Set's the geometry's CIL-convention Offset and Angle from the MI-convention Centre-of-Rotation and Tilt.

        :param cor: A ScalarCoR object defining the MI-convention centre of rotation as a float value.
        :type cor: ScalarCoR
        :param tilt: A float value defining the tilt in degrees.
        :type tilt: float
        """

        pixel_x_midpoint = self.config.panel.num_pixels[0] / 2
        pixel_y_midpoint = self.config.panel.num_pixels[1] / 2
        pixel_size = self.config.panel.pixel_size[0]

        tilt_radians = -radians(tilt)
        midpoint_cor = cor.value + pixel_y_midpoint * tan(tilt_radians)

        offset: float = (midpoint_cor - pixel_x_midpoint) * pixel_size

        self.set_centre_of_rotation(offset=offset, angle=-tilt, angle_units='degree')

    def get_cor_at_slice_index(self, slice_idx: int) -> ScalarCoR:
        """
        Returns a single scalar cor at the specified index

        :param slice_idx: The slice index.
        :return: ScalarCoR object with cor at the specified index
        """
        gradient = -tan(radians(self.tilt))
        cor = (gradient * slice_idx) + self.cor.value
        return ScalarCoR(cor)

    def get_all_cors(self) -> list[ScalarCoR]:
        """
        Returns all cors across How many cors will be generated,
                             this should be equal to the image height
                             (i.e. number of sinograms that will be reconstructed)
        :return: List of cors for every slice of the image height
        """
        image_height = self.config.panel.num_pixels[1]
        return [self.get_cor_at_slice_index(i) for i in range(image_height)]

    @property
    def cor(self) -> ScalarCoR:
        """
        Converts the internal CIL-convention COR (defined at the midpoint of the image) to MI-convention.

        :return (ScalarCoR) : the MI-convention Centre-of-Rotation (defined at the top of the image).
        """
        offset = self.get_centre_of_rotation()['offset'][0]
        pixel_x_midpoint = self.config.panel.num_pixels[0] / 2
        pixel_y_midpoint = self.config.panel.num_pixels[1] / 2
        pixel_size = self.config.panel.pixel_size[0]
        midpoint_cor = (offset / pixel_size) + pixel_x_midpoint

        tilt_radians = -radians(self.tilt)
        cor = midpoint_cor - pixel_y_midpoint * tan(tilt_radians)

        return ScalarCoR(cor)

    @cor.setter
    def cor(self, cor: ScalarCoR) -> None:
        self.set_geometry_from_cor_tilt(cor=cor, tilt=self.tilt)

    @property
    def tilt(self) -> float:
        """
        Returns the tilt in degrees
        """
        tilt: float = self.get_centre_of_rotation()['angle'][0]
        return -degrees(tilt)

    @tilt.setter
    def tilt(self, tilt: float) -> None:
        self.set_geometry_from_cor_tilt(cor=self.cor, tilt=tilt)

    @property
    def type(self) -> GeometryType:
        """
        Returns the MI Geometry type.

        Wraps CIL `AcquisitionGeometry`'s internal data based on the types currently supported by Mantid Imaging.

        :return (GeometryType) : The MI Geometry enum with a display-friendly value field.
        """
        if self.config.system.geometry == "parallel":
            return GeometryType.PARALLEL3D
        else:
            return GeometryType.CONE3D

    def set_source_detector_positions(self, source_pos: float, detector_pos: float) -> None:
        if source_pos != 0 and self.type == GeometryType.CONE3D:
            self.config.system.source.position = [0, source_pos, 0]

        if detector_pos != 0 and self.type == GeometryType.CONE3D:
            self.config.system.detector.position = [0, detector_pos, 0]

    @property
    def source_position(self) -> float:
        source_pos = 0
        if self.type == GeometryType.CONE3D:
            source_pos = self.config.system.source.position[1]
        return source_pos

    @property
    def detector_position(self) -> float:
        detector_pos = 0
        if self.type == GeometryType.CONE3D:
            detector_pos = self.config.system.detector.position[1]
        return detector_pos
