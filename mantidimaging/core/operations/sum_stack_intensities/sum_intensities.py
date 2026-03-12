# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING
from collections.abc import Callable

from mantidimaging import helper as helper
import numpy as np

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout, QComboBox
    from mantidimaging.core.data import ImageStack


class SumIntensitiesFilter(BaseFilter):
    """
    Sum stack intensities as a new stack to emulate longer exposure times for Tomography and
    Time of Flight (ToF) datasets.

    Use cases:
        - The stacks to be summed have exactly the same shape (x,y) and number of slices (z).
        The z-axis could be either rotation angle or ToF bin.
        - Stacks where values on the z-axis are identical, e.g. 2 tomography scans taken at the same rotation angles.

    The new stack will be saved either in-place or as a new stack within a new dataset, depending on the user's choice.
    """

    filter_name = 'Sum Stack Intensities'
    link_histograms = True
    allow_for_180_projection = False
    valid_types = ['Tomography', 'Time of Flight (ToF)']

    @staticmethod
    def filter_func(images: ImageStack,
                    stack_type: str | None = None,
                    secondary_stack: ImageStack | None = None,
                    progress: Any = None) -> ImageStack:
        """
        Validate and prepare stacks for summing intensities.
        """
        helper.check_data_stack(images)
        helper.check_data_stack(secondary_stack)

        if not stack_type or stack_type not in SumIntensitiesFilter.valid_types:
            raise ValueError(f"Invalid stack type: {stack_type}. Valid types are: {SumIntensitiesFilter.valid_types}")

        if secondary_stack is None:
            raise ValueError("Secondary stack cannot be None.")

        primary_shape = images.full_stack_shape or images.data.shape
        secondary_shape = secondary_stack.full_stack_shape or secondary_stack.data.shape
        if primary_shape != secondary_shape:
            raise ValueError(
                f'The primary and secondary stacks must have the same shape. '
                f'The primary stack shape is: {primary_shape}, '
                f'The secondary stack shape is: {secondary_shape}. '
                'Append Stacks may be a more suitable operation for stacks that differ in the number of slices.')

        params = {'stack_type': stack_type, 'secondary_stack': secondary_stack}
        SumIntensitiesFilter.compute_function(images, params)

        return images

    @staticmethod
    def sum_tof_stacks(primary_stack: ImageStack, secondary_stack: ImageStack, progress=None) -> None:
        """
        Sum ToF stacks by index position

        All bins added directl. If stacks differ in bin number only, overlapping prefix (min of two counts) is summed.
       """
        num_slices = min(primary_stack.data.shape[0], secondary_stack.data.shape[0])
        primary_stack.data[:num_slices] += secondary_stack.data[:num_slices]

    @staticmethod
    def _prepare_angles(primary_stack: ImageStack, secondary_stack: ImageStack) -> tuple[np.ndarray, np.ndarray] | None:
        """
        Extract angles from both stacks and return in degrees, or synthetic indices if angles
        unavailable.
        """
        primary_stack_angles = primary_stack.projection_angles()
        secondary_stack_angles = secondary_stack.projection_angles()

        if primary_stack_angles is not None and secondary_stack_angles is not None:
            return (np.rad2deg(primary_stack_angles.value), np.rad2deg(secondary_stack_angles.value))

        return None

    @staticmethod
    def sum_tomography_stacks(primary_stack: ImageStack, secondary_stack: ImageStack) -> None:
        """
        Sum tompgrahpy stacks by matching projections on their rotion angle or just by projection order if no
        angles are available.

        For each projection in primary stack, the closest-angle projection in the secondary stack is found
        and added in-place.  If no angles exist, just match by projection order
        """

        stack_angles = SumIntensitiesFilter._prepare_angles(primary_stack, secondary_stack)

        for projection in range(primary_stack.num_images):
            if stack_angles is not None:
                primary_stack_angles_deg, secondary_stack_angles_deg = stack_angles
                secondary_idx = np.argmin(np.abs(secondary_stack_angles_deg - primary_stack_angles_deg[projection]))
            else:
                secondary_idx = min(projection, secondary_stack.num_images - 1)
            primary_stack.data[projection] += secondary_stack.data[secondary_idx]

    @staticmethod
    def compute_function(primary_stack: ImageStack, params: dict[str, Any]) -> None:
        """
        Dispatch to the appropriate summation method based on stack type.
        """
        stack_type = params['stack_type']
        secondary_stack = params['secondary_stack']

        if stack_type == 'Tomography':
            SumIntensitiesFilter.sum_tomography_stacks(primary_stack, secondary_stack)
        elif stack_type == 'Time of Flight (ToF)':
            SumIntensitiesFilter.sum_tof_stacks(primary_stack, secondary_stack)
        else:
            raise ValueError(f"Unsupported stack type: {stack_type}")

    @staticmethod
    def register_gui(form: QFormLayout, on_change: Callable, view: Any) -> dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        _, stack_type_widget = add_property_to_form(
            "Type",
            Type.CHOICE,
            valid_values=SumIntensitiesFilter.valid_types,
            form=form,
            filters_view=view,
            on_change=on_change,
            tooltip="Select the type of stack to sum intensities. i.e. Time of Flight (ToF) or Tomography")

        _, stack_to_sum_widget = add_property_to_form("Select Stack Stack to Sum",
                                                      Type.STACK,
                                                      form=form,
                                                      filters_view=view,
                                                      on_change=on_change,
                                                      tooltip="Stack to sum intensities onto main sample stack")

        assert isinstance(stack_to_sum_widget, DatasetSelectorWidgetView)
        stack_to_sum_widget.setMaximumWidth(375)
        stack_to_sum_widget.subscribe_to_main_window(view.main_window)

        return {'stack_type_widget': stack_type_widget, 'stack_to_sum_widget': stack_to_sum_widget}

    @staticmethod
    def execute_wrapper(  # type: ignore
            stack_type_widget: QComboBox, stack_to_sum_widget: DatasetSelectorWidgetView) -> partial:
        stack_type_value = stack_type_widget.currentText()
        secondary_stack_value = BaseFilter.get_images_from_stack(stack_to_sum_widget, "Sum Intensities")
        return partial(SumIntensitiesFilter.filter_func,
                       stack_type=stack_type_value,
                       secondary_stack=secondary_stack_value)

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.NoGroup
