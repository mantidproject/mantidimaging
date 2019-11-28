from functools import partial
from logging import getLogger
from typing import Callable, TYPE_CHECKING, List, Any, Dict

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.filters.loader import load_filter_packages
from mantidimaging.gui.utility import get_parameters_from_stack
from mantidimaging.gui.windows.stack_visualiser import SVNotification

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout  # noqa: F401


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val,)


class FiltersWindowModel(object):
    filters: List[BaseFilter]
    selected_filter: BaseFilter
    filter_widget_kwargs: Dict[str, Any]

    def __init__(self):
        super(FiltersWindowModel, self).__init__()

        # Update the local filter registry
        self.filters = load_filter_packages(ignored_packages=['mantidimaging.core.filters.wip'])

        self.preview_image_idx = 0

        # Execution info for current filter
        self.stack = None
        self.selected_filter = self.filters[0]
        self.filter_widget_kwargs = None

    @property
    def filter_names(self):
        return [f.filter_name for f in self.filters]

    def filter_registration_func(self, filter_idx: int) -> Callable[['QFormLayout', Callable], Dict[str, Any]]:
        """
        Gets the function used to register the GUI of a given filter.

        :param filter_idx: Index of the filter in the registry
        """
        return self.filters[filter_idx].register_gui

    @property
    def stack_presenter(self):
        return self.stack.presenter if self.stack else None

    @property
    def num_images_in_stack(self):
        num_images = self.stack_presenter.images.sample.shape[0] \
            if self.stack_presenter is not None else 0
        return num_images

    @property
    def params_needed_from_stack(self):
        return self.selected_filter.sv_params()

    def setup_filter(self, filter_idx, filter_widget_kwargs):
        self.selected_filter = self.filters[filter_idx]
        self.filter_widget_kwargs = filter_widget_kwargs

    def apply_filter(self, images: Images, stack_params: Dict[str, Any]):
        """
        Applies the selected filter to a given image stack.
        """
        log = getLogger(__name__)

        # Generate the execute partial from filter registration
        do_before = self.selected_filter.do_before_wrapper()
        do_after = self.selected_filter.do_after_wrapper()

        # Log execute function parameters
        log.info(f"Filter kwargs: {stack_params}")

        input_kwarg_widgets = self.filter_widget_kwargs.copy()

        # Validate required kwargs are supplied so pre-processing does not happen unnecessarily
        if not self.selected_filter.validate_execute_kwargs(input_kwarg_widgets):
            raise ValueError("Not all required parameters specified")

        # Do pre-processing and save result
        preproc_result = do_before(images.sample)
        preproc_result = ensure_tuple(preproc_result)

        # Run filter
        exec_func: partial = self.selected_filter.execute_wrapper(**input_kwarg_widgets)
        ret_val = exec_func(images.sample, **stack_params)

        # Handle the return value from the algorithm dialog
        if isinstance(ret_val, tuple):
            # Tuples are assumed to be three elements containing sample, flat
            # and dark images
            images.sample, images.flat, images.dark = ret_val
        elif isinstance(ret_val, np.ndarray):
            # Single Numpy arrays are assumed to be just the sample image
            images.sample = ret_val
        else:
            log.debug(f'Unknown execute return value: {type(ret_val)}')

        # Do postprocessing using return value of pre-processing as parameter
        do_after(images.sample, *preproc_result)

        # store the executed filter in history if it all executed successfully
        exec_func.keywords.update(stack_params)
        images.record_operation(self.selected_filter.__module__,
                                self.selected_filter.filter_name,
                                *exec_func.args, **exec_func.keywords)

    def do_apply_filter(self):
        """
        Applies the selected filter to the selected stack.
        """
        if not self.stack_presenter:
            raise ValueError('No stack selected')

        # Get auto parameters
        stack_params = get_parameters_from_stack(self.stack_presenter, self.params_needed_from_stack)

        self.apply_filter(self.stack_presenter.images, stack_params)

        # Refresh the image in the stack visualiser
        self.stack_presenter.notify(SVNotification.REFRESH_IMAGE)
