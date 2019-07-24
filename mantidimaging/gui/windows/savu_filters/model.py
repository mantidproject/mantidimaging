import json
from concurrent.futures import Future
from functools import partial
from logging import getLogger
from pathlib import Path

import numpy as np
from requests import Response

from mantidimaging.core.io import savu_config_writer
from mantidimaging.core.utility.savu_interop.plugin_list import SAVUPluginList
from mantidimaging.gui.windows.savu_filters import preparation
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val,)


class Panic(Exception):
    def __init__(self, message):
        message = f"EVERYTHING HAS GONE TERRIBLY WRONG.\n\n{message}"
        super().__init__(message)


class SavuFiltersWindowModel(object):
    PROCESS_LIST_DIR = Path("~/mantidimaging/process_lists").expanduser()

    def __init__(self):
        super(SavuFiltersWindowModel, self).__init__()

        # Update the local filter registry
        self.filters = []
        request = preparation.data  # type: Future
        if not request.running():
            self.response = request.result()  # type: Response
            if self.response.status_code == 200:
                self.response = json.loads(self.response.content)
            else:
                self.response = {}
        else:
            raise Panic("HELP")
        self.register_filters(self.response)

        self.preview_image_idx = 0

        # Execution info for current filter
        self.stack: StackVisualiserView = None
        self.do_before = None
        self.execute = None
        self.do_after = None

    def register_filters(self, filters: {}):
        """
        Builds a local registry of filters.

        Filter name is used to initially populate the combo box for filter
        selection.

        The _gui_register function is then used to setup the filter specific
        properties and the execution mode.

        :param filters: Filters received from the SAVU API
        """

        visible_filters = []
        for name, details in filters.items():
            if "Loader" in name or "Saver" in name or "Recon" in name:
                continue
            else:
                visible_filters.append((name, details))
        self.filters = visible_filters

    @property
    def filter_names(self):
        return [f[0] for f in self.filters]

    def filter_details(self, filter_idx):
        """
        Returns the filter details
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

    def setup_filter(self, filter_details):
        """
        Sets filter properties from result of registration function.
        """
        # TODO need to manually add parameters necessary for the SAVU filters in auto_props
        # self.auto_props, self.do_before, self.execute, self.do_after = filter_details
        self.auto_props, self.do_before, self.execute, self.do_after = [], [], [], []

    def apply_filter(self, images, exec_kwargs):
        """
        Applies the selected filter to a given image stack.
        """
        log = getLogger(__name__)

        # Generate the execute partial from filter registration
        do_before_func = self.do_before() if self.do_before else lambda _: ()
        do_after_func = self.do_after() if self.do_after else lambda *_: None
        execute_func = self.execute()

        # Log execute function parameters
        log.info("Filter kwargs: {}".format(exec_kwargs))
        if isinstance(execute_func, partial):
            log.info("Filter partial args: {}".format(execute_func.args))
            log.info("Filter partial kwargs: {}".format(execute_func.keywords))

            all_kwargs = execute_func.keywords.copy()
            all_kwargs.update(exec_kwargs)

            images.record_parameters_in_metadata(
                '{}.{}'.format(execute_func.func.__module__,
                               execute_func.func.__name__),
                *execute_func.args, **all_kwargs)

        # Do preprocessing and save result
        preproc_res = do_before_func(images.sample)
        preproc_res = ensure_tuple(preproc_res)

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

        # Do postprocessing using return value of preprocessing as parameter
        do_after_func(images.sample, *preproc_res)

    def do_apply_filter(self):
        """
        Applies the selected filter to the selected stack.
        """
        if not self.stack_presenter:
            raise ValueError('No stack selected')

        # TODO
        # save out nxs file
        spl = SAVUPluginList()

        # makes sure the directories exists, they are created recursively
        # if they already exist, nothing is done
        self.PROCESS_LIST_DIR.mkdir(parents=True, exist_ok=True)

        title = self.stack.windowTitle() if self.stack is not None else ""
        savu_config_writer.save(spl, self.PROCESS_LIST_DIR / f"pl_{title}_{len(spl)}.nxs", overwrite=True)
        # send POST request (with progress updates..) to API
        # listen for end
        # reload changes? what do
        # TODO figure out how to get params like ROI later
        # Get auto parameters
        # exec_kwargs = get_auto_params_from_stack(
        #     self.stack_presenter, self.auto_props)
        #
        # self.apply_filter(self.stack_presenter.images, exec_kwargs)
        #
        # Refresh the image in the stack visualiser
        # self.stack_presenter.notify(SVNotification.REFRESH_IMAGE)
