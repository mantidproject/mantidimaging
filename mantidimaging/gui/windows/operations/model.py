from functools import partial
from typing import Callable, TYPE_CHECKING, List, Any, Dict

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import get_parameters_from_stack

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout  # noqa: F401
    from mantidimaging.gui.windows.operations import FiltersWindowPresenter
    from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val,)


class FiltersWindowModel(object):
    filters: List[BaseFilter]
    selected_filter: BaseFilter
    filter_widget_kwargs: Dict[str, Any]

    def __init__(self, presenter: 'FiltersWindowPresenter'):
        super(FiltersWindowModel, self).__init__()

        self.presenter = presenter
        # Update the local filter registry
        self.filters = load_filter_packages(ignored_packages=['mantidimaging.core.operations.wip'])

        self.preview_image_idx = 0

        # Execution info for current filter
        self._stack = None
        self.selected_filter = self.filters[0]
        self.filter_widget_kwargs = {}

    @property
    def filter_names(self):
        return [f.filter_name for f in self.filters]

    def filter_registration_func(
            self, filter_idx: int) -> Callable[['QFormLayout', Callable, BaseMainWindowView], Dict[str, Any]]:
        """
        Gets the function used to register the GUI of a given filter.

        :param filter_idx: Index of the filter in the registry
        """
        return self.filters[filter_idx].register_gui

    @property
    def params_needed_from_stack(self):
        return self.selected_filter.sv_params()

    def setup_filter(self, filter_idx, filter_widget_kwargs):
        self.selected_filter = self.filters[filter_idx]
        self.filter_widget_kwargs = filter_widget_kwargs

    def apply_to_stacks(self, stacks: List['StackVisualiserView'], stack_params, progress=None):
        """
        Applies the selected filter to a given image stack.

        It gets the image reference out of the StackVisualiserView and forwards
        it to the function that actually processes the images.
        """
        for stack in stacks:
            self.apply_to_images(stack.presenter.images, stack_params, progress=progress)


    def apply_to_images(self, images, stack_params, progress=None):
        input_kwarg_widgets = self.filter_widget_kwargs.copy()

        # Validate required kwargs are supplied so pre-processing does not happen unnecessarily
        if not self.selected_filter.validate_execute_kwargs(input_kwarg_widgets):
            raise ValueError("Not all required parameters specified")

        # Run filter
        exec_func: partial = self.selected_filter.execute_wrapper(**input_kwarg_widgets)
        exec_func.keywords["progress"] = progress
        exec_func(images, **stack_params)
        exec_func.keywords.update(stack_params)
        # store the executed filter in history if it executed successfully
        images.record_operation(
            self.selected_filter.__name__,  # type: ignore
            self.selected_filter.filter_name,
            *exec_func.args,
            **exec_func.keywords)

    def do_apply_filter(self, stacks: List['StackVisualiserView'], post_filter: Callable[[Any], None]):
        """
        Applies the selected filter to the selected stack.
        """
        if len(stacks) == 0:
            raise ValueError('No stack selected')

        # Get auto parameters
        stack_params = get_parameters_from_stack(stacks[0].presenter, self.params_needed_from_stack)
        apply_func = partial(self.apply_to_stacks, stacks, stack_params)
        start_async_task_view(self.presenter.view, apply_func, post_filter)

    def get_filter_module_name(self, filter_idx):
        """
        Returns the class name of the filter index passed to it
        """
        return self.filters[filter_idx].__module__
