# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import Callable, TYPE_CHECKING, List, Any, Dict

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BaseMainWindowView

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout  # noqa: F401  # pragma: no cover
    from mantidimaging.gui.windows.operations import FiltersWindowPresenter  # pragma: no cover
    from mantidimaging.core.data import Images


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val, )


class FiltersWindowModel(object):
    filters: List[BaseFilter]
    selected_filter: BaseFilter
    filter_widget_kwargs: Dict[str, Any]

    def __init__(self, presenter: 'FiltersWindowPresenter'):
        super().__init__()

        self.presenter = presenter
        # Update the local filter registry
        self.filters = load_filter_packages(ignored_packages=['mantidimaging.core.operations.wip'])
        self._format_filters()

        self.preview_image_idx = 0

        # Execution info for current filter
        self._stack = None
        self.selected_filter = self.filters[0]
        self.filter_widget_kwargs = {}

    def _format_filters(self):
        def value_from_enum(enum):
            if enum == FilterGroup.Basic:
                return 0
            elif enum == FilterGroup.Advanced:
                return 2
            else:
                return 1

        self.filters.sort(key=lambda filter__: value_from_enum(filter__.group_name()))

    @property
    def filter_names(self):
        filter_names = []
        no_group_divider_added = False
        no_advanced_added = False
        for filter_ in self.filters:
            if filter_.group_name() == FilterGroup.NoGroup and not no_group_divider_added:
                filter_names.append(self.presenter.divider)
                no_group_divider_added = True
            elif filter_.group_name() == FilterGroup.Advanced and not no_advanced_added:
                filter_names.append(self.presenter.divider)
                no_advanced_added = True
            filter_names.append(filter_.filter_name)
        return filter_names

    def filter_registration_func(
            self, filter_name: str) -> Callable[['QFormLayout', Callable, BaseMainWindowView], Dict[str, Any]]:
        """
        Gets the function used to register the GUI of a given filter.

        :param filter_name: Name of the filter in the registry
        """
        filter_idx = self._find_filter_index_from_filter_name(filter_name)
        return self.filters[filter_idx].register_gui

    def link_histograms(self) -> bool:
        """
        Gets the link histogram status of a filter.
        :return: True if the histograms should be linked, False otherwise.
        """
        return self.selected_filter.link_histograms

    def show_negative_overlay(self) -> bool:
        return self.selected_filter.show_negative_overlay

    @property
    def params_needed_from_stack(self):
        return self.selected_filter.sv_params()

    def _find_filter_index_from_filter_name(self, filter_name):
        for index, filter_ in enumerate(self.filters):
            if filter_.filter_name == filter_name:
                return index
        return 0

    def setup_filter(self, filter_name, filter_widget_kwargs):
        filter_idx = self._find_filter_index_from_filter_name(filter_name)
        self.selected_filter = self.filters[filter_idx]
        self.filter_widget_kwargs = filter_widget_kwargs

    def apply_to_stacks(self, stacks: List['Images'], progress=None):
        """
        Applies the selected filter to a given image stack.

        It gets the image reference out of the StackVisualiserView and forwards
        it to the function that actually processes the images.
        """
        for stack in stacks:
            self.apply_to_images(stack, progress=progress)

    def apply_to_images(self, images, progress=None):
        input_kwarg_widgets = self.filter_widget_kwargs.copy()

        # Validate required kwargs are supplied so pre-processing does not happen unnecessarily
        if not self.selected_filter.validate_execute_kwargs(input_kwarg_widgets):
            raise ValueError("Not all required parameters specified")

        # Run filter
        exec_func: partial = self.selected_filter.execute_wrapper(**input_kwarg_widgets)
        exec_func.keywords["progress"] = progress
        exec_func(images)
        # store the executed filter in history if it executed successfully
        images.record_operation(
            self.selected_filter.__name__,  # type: ignore
            self.selected_filter.filter_name,
            *exec_func.args,
            **exec_func.keywords)

    def do_apply_filter(self, stacks: List['Images'], post_filter: Callable[[Any], None]):
        """
        Applies the selected filter to the selected stack.
        """
        if len(stacks) == 0:
            raise ValueError('No stack selected')

        # Get auto parameters
        # Generate sub-stack and run filter
        apply_func = partial(self.apply_to_stacks, stacks)
        start_async_task_view(self.presenter.view, apply_func, post_filter)

    def do_apply_filter_sync(self, stacks: List['Images'], post_filter: Callable[[Any], None]):
        """
        Applies the selected filter to the selected stack in a synchronous manner
        """
        if len(stacks) == 0:
            raise ValueError('No stack selected')

        # Get auto parameters
        # Generate sub-stack and run filter
        self.apply_to_stacks(stacks)

    def get_filter_module_name(self, filter_idx):
        """
        Returns the class name of the filter index passed to it
        """
        return self.filters[filter_idx].__module__
