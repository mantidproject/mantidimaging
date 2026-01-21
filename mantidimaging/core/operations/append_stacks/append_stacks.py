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

        sample_data = images.data
        sample_angles = images.projection_angles()
        stack_to_append_data = stack_to_append.data
        stack_to_append_angles = stack_to_append.projection_angles()

        print(f"{sample_angles=}")
        print(f"{stack_to_append_angles=}")


        #out_angles = np.concatenate((sample_angles, stack_to_append_angles))
        #print(f"{out_angles=}\n{out_angles.shape}")
        #images.set_projection_angles()

        # print(f"{sample_data=}")
        # print(f"{sample_angles=}")
        # print(f"{stack_to_append_data=}")
        # print(f"{stack_to_append_angles=}")

        out_shape = (sample_data.shape[0] + stack_to_append_data.shape[0], sample_data.shape[1], sample_data.shape[2])
        out_angles_shape = (sample_angles.value.shape[0] + stack_to_append_angles.value.shape[0]) if sample_angles is not None else None

        print(f"{out_shape=}")
        print(f"{sample_data.shape=}")
        print(f"{stack_to_append_data.shape=}")

        output = pu.create_array(out_shape, images.dtype)
        output_angles = np.empty(out_angles_shape, images.dtype)
        # execute_single(sample_data, stack_to_append_data, sample_angles, stack_to_append_angles, progress, out=output.array)
        execute_single(images, stack_to_append, progress, out=output.array, out_ang=output_angles)

        print("++++++++++++++ AFTER EXECUTE +++++++++++++++++")
        print(f"======================{output.array.shape=}=========================")
        print(f"======================{output_angles=}=========================")

        images.shared_array = output
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

# def execute_single(data, data_to_append, data_angles, data_to_append_angles, progress=None, out=None):
#     progress = Progress.ensure_instance(progress, task_name='Append Stacks')
#     # progress.set_estimated_steps(data.shape[0] + data_to_append.shape[0])
#     # prob_occupied = numpy.zeros_like(data, dtype=numpy.float32)
#     progress.add_estimated_steps(1)
#
#     with progress:
#         progress.update(msg=f"Appending Stacks")
#
#         output = out[:] if out is not None else data[:]
#         output = np.concatenate((data, data_to_append))
#
#         if data_angles and data_to_append_angles:
#             out_angles = np.concatenate((data_angles, data_to_append_angles))
#
#
#     return output

def execute_single(stack, stack_to_append, progress=None, out=None, out_ang=None):
    progress = Progress.ensure_instance(progress, task_name='Append Stacks')
    # progress.set_estimated_steps(data.shape[0] + data_to_append.shape[0])
    # prob_occupied = numpy.zeros_like(data, dtype=numpy.float32)
    progress.add_estimated_steps(1)
    print(f"{out=}")
    print(f"{out_ang=}")

    # angles = stack.projection_angles().value
    if angles := stack.projection_angles():
        angles = angles.value
    if angles_to_append := stack_to_append.projection_angles():
        angles_to_append = angles_to_append.value

    with progress:
        progress.update(msg=f"Appending Stacks")

        output = out[:] if out is not None else stack.data
        output_angles = out_ang[:] if out_ang is not None else angles

        if stack_to_append.data:
            output[0] = np.concatenate((stack.data, stack_to_append.data))

        if angles_to_append:
            output_angles = np.concatenate((angles, angles_to_append))

    return output, output_angles
