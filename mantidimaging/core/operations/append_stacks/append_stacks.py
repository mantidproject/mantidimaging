# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any
from PyQt5.QtWidgets import QComboBox, QCheckBox

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.io.instrument_log import LogColumn
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

    TYPES = ["Tomography"]

    @staticmethod
    def filter_func(images: ImageStack,
                    append_type: str | None = None,
                    stack_to_append: ImageStack | None = None,
                    order_angles: bool | None = None,
                    progress=None) -> ImageStack:
        """
        """
        if images.is_temporary:
            return images

        assert images is not None and stack_to_append is not None

        h.check_data_stack(images)
        h.check_data_stack(stack_to_append)

        if order_angles:
            assert images.log_file, "Stack has no log file!"
            assert stack_to_append.log_file, "Stack to append has no log file!"
            assert images.log_file.has_projection_angles(), "Stack does not have Projection Angle data!"
            assert stack_to_append.log_file.has_projection_angles(), \
                "Stack to append does not have Projection Angle data!"
            try:
                # get stacks projection angle order
                final_images_proj_angles_ind = (np.array([
                    images.log_file.get_column(LogColumn.PROJECTION_ANGLE) +
                    stack_to_append.log_file.get_column(LogColumn.PROJECTION_ANGLE)
                ]).argsort()).flatten()
            except Exception as exc:
                raise KeyError(f"The chosen stacks do not have projection angle data! Error {exc}") from exc
        else:
            final_images_proj_angles_ind = np.arange(images.num_images + stack_to_append.num_images)

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
            out, output_angles = execute_single(images,
                                                stack_to_append,
                                                progress,
                                                ang_order=final_images_proj_angles_ind,
                                                out=output.array,
                                                out_ang=output_angles)
            images.shared_array.array = out
        if images.filenames is not None and stack_to_append.filenames is not None:
            images.filenames += stack_to_append.filenames
            images.filenames = (np.array(images.filenames)[final_images_proj_angles_ind]).tolist()
        if output_angles is not None:
            images.set_projection_angles(ProjectionAngles(output_angles))

        # Append (and order) the log_file columns
        if images.log_file is not None and stack_to_append.log_file is not None:
            image_columns = list(images.log_file.data.keys())
            for column in image_columns:
                appended_column = images.log_file.get_column(column) + stack_to_append.log_file.get_column(column)
                del images.log_file.data[column]
                appended_column = np.array(appended_column)[final_images_proj_angles_ind]
                appended_column = appended_column.tolist()
                images.log_file.data[column] = appended_column

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
        _, order_widget = add_property_to_form("Sort in Projection Angle order",
                                               Type.BOOL,
                                               form=form,
                                               filters_view=view,
                                               on_change=on_change,
                                               tooltip="Sort in Projection Angle order.")

        assert isinstance(stack_to_append_widget, DatasetSelectorWidgetView)
        stack_to_append_widget.setMaximumWidth(375)
        stack_to_append_widget.subscribe_to_main_window(view.main_window)
        stack_to_append_widget.try_to_select_relevant_stack("Flat")

        return {
            'type_widget': type_widget,
            'stack_to_append_widget': stack_to_append_widget,
            'order_widget': order_widget
        }

    @staticmethod
    def execute_wrapper(  # type: ignore
            type_widget: QComboBox, stack_to_append_widget: DatasetSelectorWidgetView,
            order_widget: QCheckBox) -> partial:
        stack_to_append_images = BaseFilter.get_images_from_stack(stack_to_append_widget, "stack to append")
        return partial(AppendStacks.filter_func,
                       stack_to_append=stack_to_append_images,
                       append_type=type_widget.currentText(),
                       order_angles=order_widget.isChecked())


def execute_single(stack: ImageStack,
                   stack_to_append: ImageStack,
                   progress=None,
                   ang_order=None,
                   out=None,
                   out_ang=None):

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
        output_angles = out_ang[:] if out_ang is not None else None

        if stack_to_append.data is not None:
            output[:] = np.concatenate((stack.data, stack_to_append.data))[:]
            output = output[ang_order]

        if output_angles is not None:
            output_angles[:] = np.concatenate((angles, angles_to_append))[:]
            output_angles = output_angles[ang_order]

    return output, output_angles
