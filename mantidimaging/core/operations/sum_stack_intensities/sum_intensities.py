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
    from PyQt5.QtWidgets import QFormLayout
    from mantidimaging.core.data import ImageStack


class SumIntensitiesFilter(BaseFilter):
    """
    Sum stack intensities as a new stack to emulate longer exposure times for Tomography and
    Time of Flight (ToF) datasets.

    The stacks to be summed should have exactly the same shape (x,y) and number of slices (z).
    The z-axis could be either rotation angle or ToF bin.
    If angles differ acros stacks, a notification highlighting this will be raised

    The new stack will be saved in-place.
    """

    filter_name = 'Sum Stack Intensities'
    link_histograms = True
    allow_for_180_projection = False
    valid_types = ['Tomography', 'Time of Flight (ToF)']
    angle_variance_threshold = 0.1

    @staticmethod
    def filter_func(images: ImageStack, secondary_stack: ImageStack | None = None, progress: Any = None) -> ImageStack:
        """
        Validate stacks and sum their intensities in-place.
        """
        helper.check_data_stack(images)
        helper.check_data_stack(secondary_stack)

        if secondary_stack is None:
            raise ValueError("Secondary stack cannot be None.")

        shape_error = SumIntensitiesFilter._check_shapes_match(images, secondary_stack)
        if shape_error:
            raise ValueError(shape_error)

        SumIntensitiesFilter.sum_stacks(images, secondary_stack)
        return images

    @staticmethod
    def _check_shapes_match(primary_stack: ImageStack, secondary_stack: ImageStack) -> str | None:
        """
        Returns an error message string if shapes differ
        """
        primary_shape = primary_stack.full_stack_shape or primary_stack.data.shape
        secondary_shape = secondary_stack.full_stack_shape or secondary_stack.data.shape
        if primary_shape != secondary_shape:
            return (f'Stacks must have the same shape.\n'
                    f'{primary_stack.name}: {primary_shape},\n'
                    f'{secondary_stack.name}: {secondary_shape}.\n'
                    'Append Stacks may be a more suitable operation.')
        return None

    @staticmethod
    def sum_stacks(primary_stack: ImageStack, secondary_stack: ImageStack) -> None:
        """
        Sum stacks element-wise.

        Primary stack is modified in-place, secondary stack is left unchanged.
        Assumes stacks have already been validated for shape compatibility.
        During preview, primary_stack may be a single-slice subset; secondary is sliced to match.
        """
        primary_stack.data += secondary_stack.data[:len(primary_stack.data)]

    @staticmethod
    def _prepare_angles(primary_stack: ImageStack, secondary_stack: ImageStack) -> tuple[np.ndarray, np.ndarray] | None:
        """
        Extract angles from both stacks and return them in degrees.
        Returns None if angles are unavailable in either stack.
        """
        primary_stack_angles = primary_stack.projection_angles()
        secondary_stack_angles = secondary_stack.projection_angles()

        if primary_stack_angles is not None and secondary_stack_angles is not None:
            return (np.rad2deg(primary_stack_angles.value), np.rad2deg(secondary_stack_angles.value))

        return None

    @staticmethod
    def _check_angle_mismatch(primary_angles_deg: np.ndarray, secondary_angles_deg: np.ndarray) -> list[str]:
        """
        Check for projection angle variance > angle_variance_threshold degrees between matched projections.
        Returns a list of up to 3 mismatch description strings.
        """
        num_projections = min(len(primary_angles_deg), len(secondary_angles_deg))
        mismatches = []
        for proj in range(num_projections):
            diff = abs(primary_angles_deg[proj] - secondary_angles_deg[proj])
            if diff > SumIntensitiesFilter.angle_variance_threshold:
                mismatches.append(
                    f"[{proj}]: ({primary_angles_deg[proj]:.1f}°, {secondary_angles_deg[proj]:.1f}°) -> Δ{diff:.1f}°")
                if len(mismatches) == 3:
                    break
        return mismatches

    @staticmethod
    def _get_notification_text(primary_stack: ImageStack, secondary_stack: ImageStack) -> str | None:
        """
        Returns a warning string when stacks may not be compatible, or None when they are.

        Returns None when projection angles are present and match within the threshold —
        the expected good state that requires no user attention.
        """
        shape_error = SumIntensitiesFilter._check_shapes_match(primary_stack, secondary_stack)
        if shape_error:
            return shape_error

        angles = SumIntensitiesFilter._prepare_angles(primary_stack, secondary_stack)
        if angles is None:
            return ("No projection angles available in one or both stacks: "
                    "summation will be applied in projection order.")

        mismatches = SumIntensitiesFilter._check_angle_mismatch(*angles)
        if mismatches:
            mismatch_lines = "\n".join(mismatches)
            return (f"Warning: projection angle variance > {SumIntensitiesFilter.angle_variance_threshold}° "
                    f"detected:\n{mismatch_lines}\nAppend Stacks may be a more suitable operation.")
        return None

    @staticmethod
    def _update_angle_notification(view: Any, stack_to_sum_widget: DatasetSelectorWidgetView) -> None:
        """
        Update notification text based on stack selection angle and shape validation
        """
        secondary_stack = BaseFilter.get_images_from_stack(stack_to_sum_widget, "Sum Intensities")
        if secondary_stack is None:
            view.clear_notification_dialog()
            return

        primary_stack = view.main_window.get_stack(view.stackSelector.current())
        notification = SumIntensitiesFilter._get_notification_text(primary_stack, secondary_stack)
        if notification is None:
            view.clear_notification_dialog()
        else:
            view.show_error_dialog(notification)

    @staticmethod
    def register_gui(form: QFormLayout, on_change: Callable, view: Any) -> dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        _, stack_to_sum_widget = add_property_to_form("Stack to Sum",
                                                      Type.STACK,
                                                      form=form,
                                                      filters_view=view,
                                                      on_change=on_change,
                                                      tooltip="Stack to sum intensities onto main sample stack")

        assert isinstance(stack_to_sum_widget, DatasetSelectorWidgetView)
        stack_to_sum_widget.setMaximumWidth(375)
        stack_to_sum_widget.subscribe_to_main_window(view.main_window)

        def update() -> None:
            SumIntensitiesFilter._update_angle_notification(view, stack_to_sum_widget)

        view.previews_updated.connect(update)

        return {'stack_to_sum_widget': stack_to_sum_widget}

    @staticmethod
    def execute_wrapper(  # type: ignore
            stack_to_sum_widget: DatasetSelectorWidgetView) -> partial:
        secondary_stack_value = BaseFilter.get_images_from_stack(stack_to_sum_widget, "Sum Intensities")
        return partial(SumIntensitiesFilter.filter_func, secondary_stack=secondary_stack_value)

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.NoGroup
