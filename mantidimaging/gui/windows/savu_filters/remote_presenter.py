from typing import TYPE_CHECKING

from mantidimaging.core.utility.savu_interop.webapi import WS_JOB_STATUS_NAMESPACE
from mantidimaging.gui.windows.savu_filters import preparation
from mantidimaging.gui.windows.savu_filters.job_run_response import JobRunResponseContent
from mantidimaging.gui.windows.savu_filters.sio_model import SavuFiltersSIOModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_filters.view import SavuFiltersWindowView  # noqa:F401


class SavuFiltersRemotePresenter(object):
    def __init__(self, view: 'SavuFiltersWindowView'):
        self.view = view
        self.sio_model = SavuFiltersSIOModel(self, preparation.sio_client, WS_JOB_STATUS_NAMESPACE)

    def do_job_submission_success(self, response_content: JobRunResponseContent):
        self.sio_model.join(response_content)

    def update_output_window(self, remote_output: JobRunResponseContent):
        # TODO update a table view or something
        self.view.new_output.emit(remote_output)

    def remote_job_end(self, remote_output):
        self.view.savu_finished.emit(remote_output["output"])
