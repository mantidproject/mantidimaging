from functools import partial
from logging import getLogger
from typing import Dict, Callable, Optional

import numpy as np

from mantidimaging.core.utility.registrator import get_package_children, import_items, register_into
from mantidimaging.gui.utility import get_parameters_from_stack
from mantidimaging.gui.windows.stack_visualiser import SVNotification


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val, )


class FiltersWindowModel(object):
    parameters_from_stack: Dict
    do_before_wrapper: Callable[[], Optional[partial]]
    execute_wrapper: Callable[[], partial]
    do_after_wrapper: Callable[[], Optional[partial]]

    def __init__(self):
        super(FiltersWindowModel, self).__init__()

        # Update the local filter registry
        self.filters = None
        self.register_filters('mantidimaging.core.filters', ignored_packages=['mantidimaging.core.filters.wip'])

        self.preview_image_idx = 0

        # Execution info for current filter
        self.stack = None
        self.do_before_wrapper = lambda: lambda: None
        self.execute_wrapper = lambda: lambda _: None
        self.do_after_wrapper = lambda: lambda *_: None

    def register_filters(self, package_name, ignored_packages=None):
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

        filter_packages = [p[1] for p in filter_packages]

        loaded_filters = import_items(filter_packages, ['execute', 'NAME', '_gui_register'])

        loaded_filters = filter(lambda f: f.available() if hasattr(f, 'available') else True, loaded_filters)

        def register_filter(filter_list, module):
            filter_list.append((module.NAME, module._gui_register))

        self.filters = []
        register_into(self.filters, loaded_filters, register_filter)

    @property
    def filter_names(self):
        return [f[0] for f in self.filters]

    def filter_registration_func(self, filter_idx):
        """
        Gets the function used to register the GUI of a given filter.

        :param filter_idx: Index of the filter in the registry
        """
        return self.filters[filter_idx][1]

    @property
    def stack_presenter(self):
        return self.stack.presenter if self.stack else None

    @property
    def num_images_in_stack(self):
        num_images = self.stack_presenter.images.sample.shape[0] \
            if self.stack_presenter is not None else 0
        return num_images

    def setup_filter(self, filter_specifics):
        """
        Sets filter properties from result of registration function.
        """
        self.parameters_from_stack, self.do_before_wrapper, self.execute_wrapper, self.do_after_wrapper = \
            filter_specifics

    def apply_filter(self, images, exec_kwargs):
        """
        Applies the selected filter to a given image stack.
        """
        log = getLogger(__name__)

        # Generate the execute partial from filter registration
        do_before_func = self.do_before_wrapper() if self.do_before_wrapper else lambda _: ()
        do_after_func = self.do_after_wrapper() if self.do_after_wrapper else lambda *_: None
        execute_func: partial = self.execute_wrapper()

        # Log execute function parameters
        log.info("Filter kwargs: {}".format(exec_kwargs))

        all_kwargs = execute_func.keywords.copy()

        if isinstance(execute_func, partial):
            log.info("Filter partial args: {}".format(execute_func.args))
            log.info("Filter partial kwargs: {}".format(execute_func.keywords))

            all_kwargs.update(exec_kwargs)

        # Do pre-processing and save result
        preproc_result = do_before_func(images.sample)
        preproc_result = ensure_tuple(preproc_result)

        # Run filter
        ret_val = execute_func(images.sample, **exec_kwargs)

        # Handle the return value from the algorithm dialog
        if isinstance(ret_val, tuple):
            # Tuples are assumed to be three elements containing sample, flat
            # and dark images
            images.sample, images.flat, images.dark = ret_val
        elif isinstance(ret_val, np.ndarray):
            # Single Numpy arrays are assumed to be just the sample image
            images.sample = ret_val
        else:
            log.debug('Unknown execute return value: {}'.format(type(ret_val)))

        # Do postprocessing using return value of pre-processing as parameter
        do_after_func(images.sample, *preproc_result)

        # store the executed filter in history if it all executed successfully
        images.record_parameters_in_metadata('{}.{}'.format(execute_func.func.__module__, execute_func.func.__name__),
                                             *execute_func.args, **all_kwargs)

    def do_apply_filter(self):
        """
        Applies the selected filter to the selected stack.
        """
        if not self.stack_presenter:
            raise ValueError('No stack selected')

        # Get auto parameters
        exec_kwargs = get_parameters_from_stack(self.stack_presenter, self.parameters_from_stack)

        self.apply_filter(self.stack_presenter.images, exec_kwargs)

        # Refresh the image in the stack visualiser
        self.stack_presenter.notify(SVNotification.REFRESH_IMAGE)
