# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from mantidimaging.core.utility.savu_interop.webapi import WS_JOB_STATUS_NAMESPACE
from mantidimaging.gui.windows.savu_operations.job_run_response import JobRunResponseContent
from mantidimaging.gui.windows.savu_operations.sio_model import SavuFiltersSIOModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_operations.view import SavuFiltersWindowView  # noqa:F401  # pragma: no cover


class SavuFiltersRemotePresenter(object):
    def __init__(self, view: 'SavuFiltersWindowView'):
        self.view = view
        self.sio_model = SavuFiltersSIOModel(self, WS_JOB_STATUS_NAMESPACE)

    def disconnect(self):
        self.sio_model.disconnect()

    def retrieve_plugins_json(self):
        return self.sio_model.retrieve_plugins_json()

    def do_job_submission_success(self, response_content: JobRunResponseContent):
        self.sio_model.join(response_content)

    def update_output_window(self, remote_output: JobRunResponseContent):
        # TODO update a table view or something
        self.view.new_output.emit(remote_output)

    def remote_job_end(self, remote_output):
        self.view.savu_finished.emit(remote_output["output"])
