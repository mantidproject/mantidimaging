from __future__ import (absolute_import, division, print_function)

from functools import partial
from logging import getLogger

import numpy as np

from mantidimaging.gui.stack_visualiser import Notification as SVNotification

from mantidimaging.core.utility.registrator import (
        get_package_children,
        import_items,
        register_into
    )


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val,)


def get_auto_params_from_stack(stack, params):
    return {k: stack.get_parameter_value(v) for (k, v) in params.items()} \
        if params else {}


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
        """
        Gets the presenter for the selected stack.
        """
        if not self.stack_uuids:
            return None

        return None if idx > len(self.stack_uuids) else self.stack_uuids[idx]
