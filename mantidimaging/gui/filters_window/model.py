from __future__ import (absolute_import, division, print_function)

from logging import getLogger

import numpy as np

from mantidimaging.gui.stack_visualiser.sv_presenter \
        import Notification as SVNotification

from mantidimaging.core.utility.registrator import (
        get_package_children,
        import_items,
        register_into
    )


class FiltersWindowModel(object):

    def __init__(self, main_window):
        super(FiltersWindowModel, self).__init__()

        self.main_window = main_window

        self.stack_uuids = []

        # Update the local filter registry
        self.filters = None
        self.register_filters('mantidimaging.core.filters',
                              ['mantidimaging.core.filters.wip'])

        # Execution info for current filter
        self.stack_idx = 0
        self.do_before = None
        self.execute = None
        self.do_after = None

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
        filter_packages = get_package_children(package_name, packages=True,
                                               ignore=ignored_packages)

        filter_packages = [p[1] for p in filter_packages]

        loaded_filters = import_items(filter_packages,
                                      ['execute', 'NAME', '_gui_register'])

        def register_filter(filter_list, module):
            filter_list.append((module.NAME, module._gui_register))

        self.filters = []
        register_into(loaded_filters, self.filters, register_filter)

    @property
    def filter_names(self):
        return [f[0] for f in self.filters]

    def filter_registration_func(self, filter_idx):
        """
        Gets the function used to register the GUI of a given filter.

        :param filter_idx: Index of the filter in the registry
        """
        return self.filters[filter_idx][1]

    def get_stack(self):
        if not self.stack_uuids:
            return None

        stack_uuid = None if self.stack_idx > len(self.stack_uuids) else \
            self.stack_uuids[self.stack_idx]

        return self.main_window.get_stack_visualiser(stack_uuid)

    def do_apply_filter(self):
        """
        Applys the selected filter to the selected stack.
        """
        log = getLogger(__name__)

        def ensure_tuple(val):
            return val if isinstance(val, tuple) else (val,)

        # Get stack
        stack = self.get_stack()
        if not stack:
            raise ValueError('No stack selected')
        stack = stack.presenter

        # Get auto parameters
        # TODO
        parameters = ()
        parameters = ensure_tuple(parameters)

        # Generate the execute partial from filter registration
        execute_func = self.execute()

        # Do preprocessing and save result
        preproc_res = self.do_before(stack.images.get_sample()) if \
            self.do_before else ()
        preproc_res = ensure_tuple(preproc_res)

        # Run filter
        ret_val = execute_func(stack.images.get_sample(), *parameters)

        # Handle the return value from the algorithm dialog
        if isinstance(ret_val, tuple):
            # Tuples are assumed to be three elements containing sample, flat
            # and dark images
            stack.images.sample, stack.images.flat, stack.images.dark = ret_val
        elif isinstance(ret_val, np.ndarray):
            # Single Numpy arrays are assumed to be just the sample image
            stack.images.sample = ret_val
        else:
            log.debug('Unknown execute return value: {}'.format(type(ret_val)))

        # Do postprocessign using return value of preprocessing as parameter
        if self.do_after:
            self.do_after(stack.images.get_sample(), *preproc_res)

        # Refresh the image in the stack visualiser
        stack.notify(SVNotification.REFRESH_IMAGE)
