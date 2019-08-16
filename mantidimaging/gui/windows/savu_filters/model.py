import json
import os
from concurrent.futures import Future, ProcessPoolExecutor
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Dict, Optional, List, Tuple, TYPE_CHECKING, Union

import numpy as np
from PyQt5.QtWidgets import QWidget
from requests import Response

from mantidimaging.core.io import savu_config_writer
from mantidimaging.core.utility.savu_interop.plugin_list import SAVUPluginList, SAVUPluginListEntry, SAVUPlugin
from mantidimaging.gui.utility.qt_helpers import get_value_from_qwidget
from mantidimaging.gui.windows.savu_filters import preparation
from mantidimaging.gui.windows.savu_filters.job_run_response import JobRunResponseContent
from mantidimaging.gui.windows.savu_filters.path_config import INPUT_LOCAL
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_filters.view import SavuFiltersWindowPresenter  # noqa:F401

CurrentFilterData = Union[Tuple, Tuple[SAVUPlugin, List[QWidget]]]


def ensure_tuple(val):
    return val if isinstance(val, tuple) else (val,)


class SavuFiltersWindowModel(object):
    PROCESS_LIST_DIR = Path("~/mantidimaging/process_lists").expanduser()

    parameters_from_stack: Dict

    def __init__(self, presenter: 'SavuFiltersWindowPresenter'):
        super(SavuFiltersWindowModel, self).__init__()
        self.presenter: 'SavuFiltersWindowPresenter' = presenter

        self.parameters_from_stack = {}
        self.do_before_wrapper = lambda: lambda: None
        self.execute_wrapper = lambda: lambda _: None
        self.do_after_wrapper = lambda: lambda *_: None

        # Update the local filter registry
        self.filters: List[SAVUPlugin] = []

        if preparation.data is not None:
            request: Future = preparation.data
        else:
            raise RuntimeError("Could not retrieve any response object")
        try:
            response: Response = request.result(timeout=5)
            if response.status_code == 200:
                response_json: Dict = json.loads(response.content)
            else:
                preparation.prepare_data()
                raise ValueError(
                    f"Did not get valid data from the Savu backend. Error code {response.status_code}")
        except ConnectionError:
            preparation.prepare_data()
            raise RuntimeError("Savu backend is not running. Cannot open GUI.")
            # try contacting the SAVU backend again
        self.register_filters(response_json)

        self.preview_image_idx = 0

        # Execution info for current filter
        self.stack: Optional[StackVisualiserView] = None

    def register_filters(self, filters: Dict):
        """
        Builds a local registry of filters.

        Filter name is used to initially populate the combo box for filter
        selection.

        The _gui_register function is then used to setup the filter specific
        properties and the execution mode.

        :param filters: Filters received from the SAVU API
        """

        visible_filters: List[SAVUPlugin] = []
        for name, details in filters.items():
            # to filter out recons too `or "Recon" in name`
            if "Loader" in name or "Saver" in name:
                continue
            else:
                visible_filters.append(SAVUPlugin(name, details))
        self.filters = visible_filters

    @property
    def filter_names(self):
        return [f.name for f in self.filters]

    def filter(self, filter_idx) -> SAVUPlugin:
        """
        Returns the filter details
        """
        return self.filters[filter_idx]

    @property
    def stack_presenter(self):
        return self.stack.presenter if self.stack else None

    @property
    def num_images_in_stack(self):
        num_images = self.stack_presenter.images.sample.shape[0] if self.stack_presenter is not None else 0
        return num_images

    def setup_filter(self, filter_details):
        """
        Sets filter properties from result of registration function.
        """
        # TODO need to manually add parameters necessary for the SAVU filters in auto_props
        # self.auto_props, self.do_before, self.execute, self.do_after = filter_details
        # self.parameters_from_stack, self.do_before_wrapper, self.execute_wrapper,
        # self.do_after_wrapper = [], [], [], []
        pass

    def apply_filter(self, images, exec_kwargs):
        """
        Applies the selected filter to a given image stack.
        """
        log = getLogger(__name__)

        # Generate the execute partial from filter registration
        do_before_func = self.do_before_wrapper() if self.do_before_wrapper else lambda _: ()
        do_after_func = self.do_after_wrapper() if self.do_after_wrapper else lambda *_: None
        execute_func = self.execute_wrapper()

        # Log execute function parameters
        log.info("Filter kwargs: {}".format(exec_kwargs))
        if isinstance(execute_func, partial):
            log.info("Filter partial args: {}".format(execute_func.args))
            log.info("Filter partial kwargs: {}".format(execute_func.keywords))

            all_kwargs = execute_func.keywords.copy()
            all_kwargs.update(exec_kwargs)

            images.record_parameters_in_metadata(
                "{}.{}".format(execute_func.func.__module__, execute_func.func.__name__),
                *execute_func.args,
                **all_kwargs,
            )

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
            log.debug("Unknown execute return value: {}".format(type(ret_val)))

        # Do postprocessing using return value of preprocessing as parameter
        do_after_func(images.sample, *preproc_res)

    def do_apply_filter(self, current_filter: CurrentFilterData):
        """
        Applies the selected filter to the selected stack.
        """
        if not self.stack:
            raise ValueError("No stack selected")

        presenter = self.stack_presenter
        # TODO make & read from a config. This config should also be used to start the Docker service
        # the data path will be the root in the savu config, so it doesn't need to be part of the filepath
        common_prefix = os.path.commonprefix(presenter.images.filenames).replace(INPUT_LOCAL, "")
        num_images = presenter.images.count()

        # save out nxs file
        spl = SAVUPluginList(common_prefix, num_images, preview=presenter.images.indices)

        plugin = self._create_plugin_entry_from(current_filter)
        spl.add_plugin(plugin)

        # makes sure the directories exists, they are created recursively
        # if they already exist, nothing is done
        self.PROCESS_LIST_DIR.mkdir(parents=True, exist_ok=True)

        file = self.PROCESS_LIST_DIR / f"pl_{self.stack.name}_{len(spl)}.nxs"
        savu_config_writer.save(spl, file, overwrite=True)

        from mantidimaging.core.utility.savu_interop.webapi import SERVER_URL, JOB_SUBMIT_URL
        from requests_futures.sessions import FuturesSession

        session: FuturesSession = FuturesSession(executor=ProcessPoolExecutor(max_workers=1))
        files = {"process_list_file": file.read_bytes()}
        data = {"process_list_name": self.stack.name, "dataset": "/data"}

        # TODO get QUEUE parameter somewhere from the GUI
        # FIXME currently just sticking it into preview

        # send POST request (with progress updates..) to API
        future: Future = session.post(f"{SERVER_URL}/{JOB_SUBMIT_URL.format('preview')}", files=files, data=data)

        logger = getLogger(__name__)
        logger.info("Sent POST request and waiting for response")
        try:
            # wait until the job startup process is finished
            response: Response = future.result()
        except ConnectionError as e:
            msg = f"Failed to connect to Savu backend. Error: {e}"
            logger.error(msg)
            raise RuntimeError(msg)

        content_json = json.loads(response.content)
        if response.status_code == 200:
            try:
                content = JobRunResponseContent(content_json["job"]["id"], content_json["queue"])
            except TypeError as e:
                msg = f"Could not parse content from remote server.\nContent: {response.content}\nError: {e}"
                logger.error(msg)
                raise RuntimeError(msg)

            logger.info(content)
            self.presenter.do_job_submission_success(content)
        else:
            logger.error(f"Error code: {response.status_code}, message: {content_json['message']}")
            self.presenter.do_job_submission_failure(content_json)

        # reload changes? what do
        # TODO figure out how to get params like ROI later
        # Get auto parameters
        # exec_kwargs = get_auto_params_from_stack(self.stack_presenter, self.auto_props)
        #
        # self.apply_filter(self.stack_presenter.images, exec_kwargs)
        #
        # Refresh the image in the stack visualiser
        # self.stack_presenter.notify(SVNotification.REFRESH_IMAGE)

    def _create_plugin_entry_from(self, current_filter: CurrentFilterData):
        plugin = current_filter[0]
        data = {}
        description = {}
        hidden = []
        for index, param in enumerate(plugin.visible_parameters()):
            data[param.name] = get_value_from_qwidget(current_filter[1][index])
            description[param.name] = param.description
            if param.is_hidden:
                hidden.append(param.name)

        return SAVUPluginListEntry(active=True,
                                   data=np.string_(json.dumps(data)),
                                   desc=np.string_(json.dumps(description)),
                                   hide=np.string_(json.dumps(hidden)),
                                   id=np.string_(plugin.id),
                                   name=np.string_(plugin.name),
                                   user=np.string_("[]"))
