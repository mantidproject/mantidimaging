# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any
from PyQt5.QtWidgets import QComboBox

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.utility.qt_helpers import Type

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
