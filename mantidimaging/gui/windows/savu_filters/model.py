import ast
import json
import os
from concurrent.futures import Future, ProcessPoolExecutor
from logging import getLogger
from pathlib import Path
from typing import Dict, Optional, List, Tuple, TYPE_CHECKING, Union

import numpy as np
from PyQt5.QtWidgets import QWidget

from mantidimaging.core.configs.savu_backend_docker import RemoteConfig, RemoteConstants
from mantidimaging.core.io import savu_config_writer
from mantidimaging.core.utility.savu_interop.plugin_list import SAVUPluginList, SAVUPluginListEntry, SAVUPlugin
from mantidimaging.gui.utility.qt_helpers import get_value_from_qwidget
from mantidimaging.gui.windows.savu_filters.job_run_response import JobRunResponseContent
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_filters.view import SavuFiltersWindowPresenter  # noqa:F401

CurrentFilterData = Union[Tuple, Tuple[SAVUPlugin, List[QWidget]]]


class SavuFiltersWindowModel(object):
    PROCESS_LIST_DIR = Path("~/mantidimaging/process_lists").expanduser()

    parameters_from_stack: Dict

    def __init__(self, presenter: 'SavuFiltersWindowPresenter', plugins_json: Dict):
        super(SavuFiltersWindowModel, self).__init__()
        self.presenter: 'SavuFiltersWindowPresenter' = presenter

        self.parameters_from_stack = {}

        # Update the local filter registry
        self.filters: List[SAVUPlugin] = []

        self.register_filters(plugins_json)

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
    def image_shape(self):
        return self.stack_presenter.images.sample.shape

    def setup_filter(self, filter_details):
        """
        Sets filter properties from result of registration function.
        """
        # TODO need to manually add parameters necessary for the SAVU filters in auto_props
        # self.auto_props, self.do_before, self.execute, self.do_after = filter_details
        # self.parameters_from_stack, self.do_before_wrapper, self.execute_wrapper,
        # self.do_after_wrapper = [], [], [], []
        pass

    def do_apply_filter(self, current_filter: CurrentFilterData, indices):
        """
        Applies the selected filter to the selected stack.
        """
        plugin = SavuFiltersWindowModel.create_plugin_entry_from(current_filter)
        self.apply_process_list([plugin], indices)

    def apply_process_list(self, plugin_entries: List[SAVUPluginListEntry], indices):
        if not plugin_entries:
            raise ValueError("No plugins selected")

        if not self.stack:
            raise ValueError("No stack selected")

        if indices[0] >= indices[1]:
            raise ValueError("Invalid indices, start must be less than end")

        dataset = self._get_dataset_path()
        pl_path = self.save_process_list(plugin_entries, indices)
        self.do_apply_process_list(pl_path, dataset)

    def save_process_list(self, plugin_entries: List[SAVUPluginListEntry], indices, name: Optional[str] = None):
        prefix = self._get_file_prefix()

        # save out nxs file
        spl = SAVUPluginList(prefix, self.stack_presenter.images.count(), indices)
        for plugin in plugin_entries:
            spl.add_plugin(plugin)
        spl.finalize()

        # makes sure the directories exists, they are created recursively
        # if they already exist, nothing is done
        self.PROCESS_LIST_DIR.mkdir(parents=True, exist_ok=True)

        if name is None:
            name = f"pl_{self.stack.name}_{len(spl)}.nxs" if self.stack else "pl_unnamed.nxs"
        elif not name.endswith(".nxs"):
            name = name + ".nxs"

        file = self.PROCESS_LIST_DIR / name
        savu_config_writer.save(spl, file, overwrite=True)
        return file

    def _get_file_prefix(self):
        file_paths = self.stack_presenter.images.filenames
        file_names = [path.split(os.sep)[-1] for path in file_paths]
        common_prefix = os.path.commonprefix(file_names)
        return common_prefix

    def _get_dataset_path(self):
        file_paths = self.stack_presenter.images.filenames
        file_names = [path.split(os.sep)[-1] for path in file_paths]
        return file_paths[0] \
            .replace(RemoteConfig.LOCAL_DATA_DIR, RemoteConstants.DATA_DIR) \
            .replace(file_names[0], "") \
            .rstrip(os.sep)

    def do_apply_process_list(self, pl_path, dataset_path):
        from mantidimaging.core.utility.savu_interop.webapi import SERVER_URL, JOB_SUBMIT_URL
        from requests_futures.sessions import FuturesSession

        session: FuturesSession = FuturesSession(executor=ProcessPoolExecutor(max_workers=1))
        files = {"process_list_file": pl_path.read_bytes()}
        data = {"process_list_name": self.stack.name, "dataset": dataset_path}

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

        if response.ok:
            content_json = response.json()
            try:
                content = JobRunResponseContent(content_json["job"]["id"], content_json["queue"])
            except TypeError as e:
                msg = f"Could not parse content from remote server.\nContent: {str(response.content)}\nError: {e}"
                logger.error(msg)
                raise RuntimeError(msg)

            logger.info(content)
            self.presenter.do_job_submission_success(content)
        else:
            logger.error(f"Error code: {response.status_code}, message: {response.content!r}")
            self.presenter.do_job_submission_failure(response)

        # reload changes? what do
        # TODO figure out how to get params like ROI later
        # Get auto parameters
        # exec_kwargs = get_auto_params_from_stack(self.stack_presenter, self.auto_props)
        #
        # self.apply_filter(self.stack_presenter.images, exec_kwargs)
        #
        # Refresh the image in the stack visualiser
        # self.stack_presenter.notify(SVNotification.REFRESH_IMAGE)

    @staticmethod
    def create_plugin_entry_from(current_filter: CurrentFilterData) -> SAVUPluginListEntry:
        plugin = current_filter[0]
        data = {}
        description = {}
        hidden = []
        for index, param in enumerate(plugin.visible_parameters()):
            val = get_value_from_qwidget(current_filter[1][index])
            if param.type == "list" or param.type == "tuple" and val:
                try:
                    val = ast.literal_eval(val)
                except SyntaxError:
                    raise RuntimeError(f"Invalid format for {param.name} parameter")
                except ValueError:
                    raise RuntimeError(f"Invalid value for {param.name} parameter")

            data[param.name] = val
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
