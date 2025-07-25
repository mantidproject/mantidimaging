# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING
from collections.abc import Callable

from mantidimaging import helper as helper
import numpy as np

from mantidimaging.core.parallel import shared as ps
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

        if images.full_stack_shape != secondary_stack.data.shape:
            raise ValueError(
                f'The primary and secondary stacks must have the same shape. '
                f'The primary stack shape is: { images.full_stack_shape }, '
                f'The secondary stack shape is: {secondary_stack.data.shape}. '
                'Append Stacks may be a more suitable operation for stacks that differ in the number of slices.')

        params = {'stack_type': stack_type, 'secondary_stack': secondary_stack}
        ps.run_compute_func(SumIntensitiesFilter.compute_function, images.data.shape[0], images.shared_array, params,
                            progress)

        return images

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params: dict):
        """
        Function to compute the sum of stack intensities
        """
        stack_type = params['stack_type']

        if stack_type == 'Tomography':
            pass
        elif stack_type == 'Time of Flight (ToF)':
            pass
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
