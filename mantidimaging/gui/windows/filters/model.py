from functools import partial
from logging import getLogger
from typing import Callable, TYPE_CHECKING, List, Optional

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.utility.registrator import get_package_children, import_items
from mantidimaging.gui.utility import get_parameters_from_stack
from mantidimaging.gui.windows.stack_visualiser import SVNotification

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout  # noqa: F401


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val,)


class FiltersWindowModel(object):
    filters: List[BaseFilter]
    selected_filter: BaseFilter
    apply_filter_func: Optional[partial]

    def __init__(self):
        super(FiltersWindowModel, self).__init__()

        # Update the local filter registry
        self.filters = FiltersWindowModel.load_filter_packages(
            'mantidimaging.core.filters', ignored_packages=['mantidimaging.core.filters.wip'])

        self.preview_image_idx = 0

        # Execution info for current filter
        self.stack = None
        self.selected_filter = self.filters[0]
        self.apply_filter_func = None

    @staticmethod
    def load_filter_packages(package_name, ignored_packages=None) -> List[BaseFilter]:
        """
        Builds a local registry of filters.

        Filter name is used to initially populate the combo box for filter
        selection.

        The _gui_register function is then used to setup the filter specific
        properties and the execution mode.

        :param package_name: Name of the root package in which to search for
                             filters
        :param ignored_packages: List of ignore rules
        """
        filter_packages = get_package_children(package_name, packages=True, ignore=ignored_packages)
        filter_package_names = [p.name for p in filter_packages]
        loaded_filters = import_items(filter_package_names, required_attributes=['FILTER_CLASS'])
        loaded_filters = filter(lambda f: f.available() if hasattr(f, 'available') else True, loaded_filters)

        return [f.FILTER_CLASS() for f in loaded_filters]

    @property
    def filter_names(self):
        return [f.filter_name for f in self.filters]

    def filter_registration_func(self, filter_idx: int) -> Callable[['QFormLayout', Callable], Callable]:
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
        return self.selected_filter.params

    def setup_filter(self, filter_idx, apply_filter_func):
        self.selected_filter = self.filters[filter_idx]
        self.apply_filter_func = apply_filter_func

    def apply_filter(self, images: Images, exec_kwargs):
        """
        Applies the selected filter to a given image stack.
        """
        assert self.apply_filter_func is not None
        log = getLogger(__name__)

        # Generate the execute partial from filter registration
        do_before_func = self.selected_filter.do_before_func
        do_after_func = self.selected_filter.do_after_func

        # Log execute function parameters
        log.info(f"Filter kwargs: {exec_kwargs}")

        all_kwargs = self.apply_filter_func.keywords.copy()

        if isinstance(self.apply_filter_func, partial):
            log.info(f"Filter partial args: {self.apply_filter_func.args}")
            log.info(f"Filter partial kwargs: {self.apply_filter_func.keywords}")

            all_kwargs.update(exec_kwargs)

        # Do pre-processing and save result
        preproc_result = do_before_func(images.sample)
        preproc_result = ensure_tuple(preproc_result)

        # Run filter
        ret_val = self.apply_filter_func(images.sample, **exec_kwargs)

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
        do_after_func(images.sample, *preproc_result)

        # store the executed filter in history if it all executed successfully
        images.record_operation(f'{self.apply_filter_func.func.__module__}',
                                *self.apply_filter_func.args, **all_kwargs)

    def do_apply_filter(self):
        """
        Applies the selected filter to the selected stack.
        """
        if not self.stack_presenter:
            raise ValueError('No stack selected')

        # Get auto parameters
        exec_kwargs = get_parameters_from_stack(self.stack_presenter, self.params_needed_from_stack)

        self.apply_filter(self.stack_presenter.images, exec_kwargs)

        # Refresh the image in the stack visualiser
        self.stack_presenter.notify(SVNotification.REFRESH_IMAGE)
