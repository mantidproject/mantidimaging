# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any
from PyQt5.QtWidgets import QComboBox

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.core.utility.progress_reporting import Progress

from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class AppendStacks(BaseFilter):
    """
    Append Stacks
    """
    filter_name = "Append Stacks"
    link_histograms = True
    allow_for_180_projection = False

    TYPES = ["Tomography", "Time of Flight (ToF)"]

    @staticmethod
    def filter_func(images: ImageStack,
                    append_type: str | None = None,
                    stack_to_append: ImageStack | None = None,
                    progress=None) -> ImageStack:
        """
        """

        h.check_data_stack(images)
        h.check_data_stack(stack_to_append)

        sample_data = images.data
        sample_angles = images.projection_angles()

        stack_to_append_data = stack_to_append.data if stack_to_append is not None else None
        stack_to_append_angles = stack_to_append.projection_angles() if stack_to_append is not None else None

        if sample_data is not None and stack_to_append_data is not None:
            out_shape = (sample_data.shape[0] + stack_to_append_data.shape[0], sample_data.shape[1],
                         sample_data.shape[2])
            output = pu.create_array(out_shape, images.dtype)
        else:
            output = None

        if sample_angles is not None and stack_to_append_angles is not None:
            out_angles_shape = (sample_angles.value.shape[0] + stack_to_append_angles.value.shape[0])
            output_angles = np.empty(out_angles_shape, images.dtype)
        else:
            output_angles = None

        if images.shape[0] != 1 and stack_to_append is not None and output is not None:
            execute_single(images, stack_to_append, progress, out=output.array, out_ang=output_angles)
            images.shared_array = output
        if output_angles is not None:
            images.set_projection_angles(ProjectionAngles(output_angles))

        return images

    @staticmethod
    def register_gui(form, on_change, view) -> dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        _, type_widget = add_property_to_form("Type",
                                              Type.CHOICE,
                                              valid_values=AppendStacks.TYPES,
                                              form=form,
                                              on_change=on_change,
                                              tooltip="Type of stack.")
        _, stack_to_append_widget = add_property_to_form("Select Stack to Append",
                                                         Type.STACK,
                                                         form=form,
                                                         filters_view=view,
                                                         on_change=on_change,
                                                         tooltip="Stack to append.")

        assert isinstance(stack_to_append_widget, DatasetSelectorWidgetView)
        stack_to_append_widget.setMaximumWidth(375)
        stack_to_append_widget.subscribe_to_main_window(view.main_window)
        stack_to_append_widget.try_to_select_relevant_stack("Flat")

        return {'type_widget': type_widget, 'stack_to_append_widget': stack_to_append_widget}

    @staticmethod
    def execute_wrapper(type_widget: QComboBox, stack_to_append_widget: DatasetSelectorWidgetView):  # type: ignore
        stack_to_append_images = BaseFilter.get_images_from_stack(stack_to_append_widget, "stack to append")

        return partial(AppendStacks.filter_func,
                       stack_to_append=stack_to_append_images,
                       append_type=type_widget.currentText())


def execute_single(stack: ImageStack, stack_to_append: ImageStack, progress=None, out=None, out_ang=None):
    progress = Progress.ensure_instance(progress, task_name='Append Stacks')
    progress.add_estimated_steps(1)

    if isinstance(stack_angles := stack.projection_angles(), ProjectionAngles):
        angles = stack_angles.value
    else:
        angles = np.full(stack.shape[0], 0)
    if isinstance(stack_to_append_angles := stack_to_append.projection_angles(), ProjectionAngles):
        angles_to_append = stack_to_append_angles.value
    else:
        angles_to_append = np.full(stack_to_append.shape[0], 0)

    with progress:
        progress.update(msg=f"Appending Stacks {stack.name} and {stack_to_append.name}")

        output = out[:] if out is not None else stack.data
        output_angles = out_ang[:] if out_ang is not None else angles

        if stack_to_append.data is not None:
            output[:] = np.concatenate((stack.data, stack_to_append.data))[:]

        if angles_to_append is not None:
            output_angles[:] = np.concatenate((angles, angles_to_append))[:]

    return output, output_angles
