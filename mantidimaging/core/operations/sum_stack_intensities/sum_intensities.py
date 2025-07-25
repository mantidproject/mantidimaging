# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING
from collections.abc import Callable

from mantidimaging import helper as h
import numpy as np

from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout
    from mantidimaging.core.data import ImageStack


class SumIntensitiesFilter(BaseFilter):
    """
    Sum stack intensities as a new stack to emulate a longer exposure time for Tomograghy and ToF datasets.

    Use cases:
        - The stacks to be summed have exactly the same shape (x,y) and number of slices (z).
        The z-axis could be either rotation angle or ToF bin.
        - Stacks where values on the z-axis are identical, e.g. 2 tomography scans taken at the same rotation angles.

    If the stacks have different shapes or number of slices, the user should be shown a warning and suggestion
    to use the append operation instead or should select compatible stacks.

    The new stack will be saved either in-place or as a new stack within a new dataset, depending on the user's choice.
    """

    filter_name = "Sum Stack Intensities"
    link_histograms = True
    valid_types = ['Tomography', 'ToF']

    @staticmethod
    def filter_func(images: ImageStack,
                    stack_type: str | None = None,
                    secondary_stack: ImageStack | None = None,
                    progress: Any = None) -> ImageStack:
        """
        Sums the intensities of the secondary stack onto the main stack.
        """
        h.check_data_stack(images)

        if images is None or images.data is None:
            raise ValueError('images parameter must not be None')

        if secondary_stack is None or secondary_stack.data is None:
            raise ValueError('secondary_stack parameter must not be None')

        if not stack_type:
            raise ValueError('stack_type parameter must not be None or empty')

        # preview will only show the first image in the stack
        if images.data.shape[0] != 1 and images.data.data.shape != secondary_stack.data.shape:
            raise ValueError(f'The main and secondary stacks must have the same shape. '
                             f'The sample shape is: {images.data.data.shape}, '
                             f'The secondary stack shape is: {secondary_stack.data.shape}')

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
        elif stack_type == 'ToF':
            pass
        else:
            raise ValueError(f"Unsupported stack type: {stack_type}")

    @staticmethod
    def register_gui(form: QFormLayout, on_change: Callable, view: Any) -> dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        _, stack_type_selector = add_property_to_form(
            "Select Stack Type",
            Type.CHOICE,
            valid_values=SumIntensitiesFilter.valid_types,
            form=form,
            filters_view=view,
            on_change=on_change,
            tooltip="Select the ype of stack to sum intensities. i.e. ToF or Tomography")

        _, secondary_stack_selector = add_property_to_form(
            "Secondary Sample Stack",
            Type.STACK,
            form=form,
            filters_view=view,
            on_change=on_change,
            tooltip="Secondary sample stack to sum intensities onto main sample stack")

        assert isinstance(secondary_stack_selector, DatasetSelectorWidgetView)
        secondary_stack_selector.setMaximumWidth(375)
        try:
            secondary_stack_selector.subscribe_to_main_window(view.main_window)
        except AttributeError:
            pass

        return {'stack_type': stack_type_selector, 'secondary_stack': secondary_stack_selector}

    @staticmethod
    def execute_wrapper(stack_type, secondary_stack, **kwargs) -> partial:
        stack_type_value = stack_type.currentText()
        secondary_stack_value = BaseFilter.get_images_from_stack(secondary_stack, "Sum Intensities")
        return partial(SumIntensitiesFilter.filter_func,
                       stack_type=stack_type_value,
                       secondary_stack=secondary_stack_value)

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic
