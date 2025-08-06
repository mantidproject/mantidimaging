# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations

from math import degrees
from typing import TYPE_CHECKING

from matplotlib.figure import Figure

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.geometry import Geometry
from mantidimaging.core.utility.data_containers import ScalarCoR
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.geometry.model import GeometryWindowModel

from cil.utilities.display import show_geometry

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

        # self._connect_signals()

    def handle_stack_changed(self) -> None:
        current_stack = self.main_window.get_stack(self.view.current_stack)

        if current_stack.geometry is None:
            self.handle_no_geometry_exists()
        else:
            self.handle_geometry_exists(current_stack)

        self.update_plot(current_stack)

    def handle_geometry_exists(self, stack: ImageStack) -> None:
        self.update_parameters(stack)
        self.view.set_widget_stack_page(0)

    def handle_no_geometry_exists(self) -> None:
        self.view.set_widget_stack_page(1)

    def update_parameters(self, stack: ImageStack) -> None:
        geometry_type = "N/A"
        if stack.geometry is not None:
            geometry_type = f"{stack.geometry.geom_type}{stack.geometry.dimension}"

        angle_range = "N/A"
        real_projection_angles = stack.real_projection_angles()
        if real_projection_angles is not None:
            min_angle = degrees(real_projection_angles.value[0])
            max_angle = degrees(real_projection_angles.value[-1])
            angle_range = f"{min_angle:.2f}° - {max_angle:.2f}°"

        mi_cor = .0
        mi_tilt = .0
        if stack.geometry is not None:
            mi_cor = stack.geometry.cor.value
            mi_tilt = stack.geometry.tilt
            print(f"Got COR and TILT from stack: {mi_cor}, {mi_tilt}")

        self.view.type = geometry_type
        self.view.angles = angle_range
        self.view.rotation_axis = mi_cor
        self.view.tilt = mi_tilt

    def update_plot(self, stack: ImageStack) -> None:
        geometry = stack.geometry

        if geometry is None:
            self.view.clear_plot()
            return

        figure: Figure = show_geometry(geometry).figure
        self.view.update_plot(figure)

    def handle_parameter_updates(self):
        updated_cor = ScalarCoR(self.view.rotation_axis)
        updated_tilt = self.view.tilt

        current_stack = self.main_window.get_stack(self.view.current_stack)

        current_stack.geometry.set_geometry_from_cor_tilt(updated_cor, updated_tilt)

        self.update_plot(current_stack)

    def handle_create_geometry(self):
        new_cor = self.view.new_cor
        new_tilt = self.view.new_tilt
        new_min_angle = self.view.new_min_angle
        new_max_angle = self.view.new_max_angle
