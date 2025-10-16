# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np
from math import degrees
from logging import getLogger

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.geometry import GeometryType
from mantidimaging.core.data.imagestack import StackNotFoundError
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.geometry.model import GeometryWindowModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.geometry.view import GeometryWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main import MainWindowView


class GeometryWindowPresenter(BasePresenter):
    view: GeometryWindowView

    def __init__(self, view: GeometryWindowView, main_window: MainWindowView):
        super().__init__(view)
        self.view = view
        self.model = GeometryWindowModel()
        self.main_window = main_window

    def handle_stack_changed(self) -> None:
        current_stack_uuid = self.view.current_stack
        if current_stack_uuid is None:
            # Stack has likely been cleared from the main window
            self.view.clear_plot()
            self.view.set_widget_stack_page(0)
            return

        current_stack = self.main_window.get_stack(current_stack_uuid)
        if current_stack is None:
            raise StackNotFoundError("No ImageStack found for UUID")

        if current_stack.geometry is None:
            self.set_default_new_parameters(current_stack)
            self.view.set_widget_stack_page(1)
        else:
            self.update_parameters(current_stack)
            self.view.set_widget_stack_page(0)

        self.refresh_plot(current_stack)

    def update_parameters(self, stack: ImageStack) -> None:
        if stack.geometry is None:
            raise RuntimeError("Attempted to update parameters for ImageStack without geometry")

        geometry_type = stack.geometry.type.value

        angle_range = "N/A"
        real_projection_angles = stack.projection_angles()
        if real_projection_angles is not None:
            min_angle = degrees(real_projection_angles.value[0])
            max_angle = degrees(real_projection_angles.value[-1])
            angle_range = f"{min_angle:.2f}° - {max_angle:.2f}°"

        mi_cor = stack.geometry.cor.value
        mi_tilt = stack.geometry.tilt

        self.view.type = geometry_type
        self.view.angles = angle_range
        self.view.rotation_axis = mi_cor
        self.view.tilt = mi_tilt
        self.view.source_position = stack.geometry.source_position
        self.view.detector_position = stack.geometry.detector_position

    def set_default_new_parameters(self, stack: ImageStack) -> None:
        default_cor = stack.width / 2

        self.view.new_rotation_axis = default_cor
        self.view.new_tilt = .0
        self.view.new_min_angle = 0
        self.view.new_max_angle = 360
        # Source and detector positions cannot be 0
        self.view.new_source_position = -1.
        self.view.new_detector_position = 1.

    def handle_parameter_updates(self) -> None:
        updated_cor = ScalarCoR(self.view.rotation_axis)
        updated_tilt = self.view.tilt

        updated_source_pos = self.view.source_position
        updated_detector_pos = self.view.detector_position

        stack = self._get_current_stack_with_assert()
        assert stack.geometry is not None

        stack.geometry.set_geometry_from_cor_tilt(updated_cor, updated_tilt)
        stack.geometry.set_source_detector_positions(updated_source_pos, updated_detector_pos)

        self.refresh_plot(stack)

    def refresh_plot(self, stack: ImageStack) -> None:
        figure = self.model.generate_figure(stack)

        if figure is None:
            self.view.clear_plot()
        else:
            self.view.refresh_plot(figure)

    def handle_create_new_geometry(self) -> None:
        stack = self._get_current_stack_with_assert()

        new_type = self.view.new_type
        new_cor = ScalarCoR(self.view.new_rotation_axis)
        new_tilt = self.view.new_tilt
        new_min_angle = self.view.new_min_angle
        new_max_angle = self.view.new_max_angle
        new_source_position = self.view.new_source_position
        new_detector_position = self.view.new_detector_position

        new_angles = ProjectionAngles(
            np.linspace(np.deg2rad(new_min_angle), np.deg2rad(new_max_angle), stack.num_projections))

        geometry_type = GeometryType.PARALLEL3D
        if new_type == "Cone 3D":
            geometry_type = GeometryType.CONE3D

        stack.create_geometry(new_angles, geometry_type)
        assert stack.geometry is not None
        stack.geometry.set_geometry_from_cor_tilt(new_cor, new_tilt)
        stack.geometry.set_source_detector_positions(new_source_position, new_detector_position)

        self.handle_stack_changed()

    def handle_convert_geometry(self) -> None:
        stack = self._get_current_stack_with_assert()
        assert stack.geometry is not None

        current_type = stack.geometry.type
        new_type = GeometryType(self.view.conversion_type)

        if current_type == new_type:
            self.view.show_info_dialog(f"Geometry is already {new_type.value}")
            return

        confirmation = self.view.show_question_dialog("Confirm Conversion",
                                                      f"Convert {current_type.value} to {new_type.value}?")

        if not confirmation:
            LOG.debug("Conversion cancelled")
            return

        LOG.debug(f"Converting Geometry from {current_type} to {new_type}")

        existing_angles = stack.projection_angles()
        assert existing_angles is not None

        stack.create_geometry(existing_angles, new_type)
        self.handle_stack_changed()

    def _get_current_stack_with_assert(self) -> ImageStack:
        # It shouldn't be possible to call this method with an invalid stack selected
        current_stack_uuid = self.view.current_stack
        assert current_stack_uuid is not None

        current_stack = self.main_window.get_stack(current_stack_uuid)
        assert current_stack is not None

        return current_stack
