from functools import partial
from logging import getLogger
from typing import Callable, TYPE_CHECKING, List, Any, Dict

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import get_parameters_from_stack

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout  # noqa: F401
    from mantidimaging.gui.windows.filters import FiltersWindowPresenter


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val, )


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

    def apply_filter(self, images: Images, stack_params: Dict[str, Any], progress=None):
        """
        Applies the selected filter to a given image stack.
        """
        log = getLogger(__name__)
        log.info(f"Filter kwargs: {stack_params}")

        input_kwarg_widgets = self.filter_widget_kwargs.copy()

        # Validate required kwargs are supplied so pre-processing does not happen unnecessarily
        if not self.selected_filter.validate_execute_kwargs(input_kwarg_widgets):
            raise ValueError("Not all required parameters specified")

        # Run filter
        exec_func: partial = self.selected_filter.execute_wrapper(**input_kwarg_widgets)
        exec_func.keywords["progress"] = progress
        self._apply_to(exec_func, images, stack_params)
        images_180deg = images.proj180deg
        # if the 180 projection has a memory mapped file then it is a loaded image
        # if it doesn't then it uses the middle of the stack as a 'guess' of the 180 degree proj
        if images_180deg.memory_filename is not None:
            log.info("Applying filter to 180 deg projection")
            self._apply_to(exec_func, images_180deg, stack_params)

    def _apply_to(self, exec_func, images, stack_params):
        exec_func(images, **stack_params)
        exec_func.keywords.update(stack_params)
        # store the executed filter in history if it executed successfully
        images.record_operation(
            self.selected_filter.__name__,  # type: ignore
            self.selected_filter.filter_name,
            *exec_func.args,
            **exec_func.keywords)

    def do_apply_filter(self, stack_view, stack_presenter, post_filter: Callable[[Any], None]):
        """
        Applies the selected filter to the selected stack.
        """
        if not stack_presenter:
            raise ValueError('No stack selected')

        # Get auto parameters
        stack_params = get_parameters_from_stack(stack_presenter, self.params_needed_from_stack)
        apply_func = partial(self.apply_filter, stack_presenter.images, stack_params)
        start_async_task_view(stack_view, apply_func, post_filter)
