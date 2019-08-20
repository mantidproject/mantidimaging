import json
from typing import TYPE_CHECKING, Optional

import socketio

from mantidimaging.gui.windows.savu_filters.job_run_response import JobRunResponseContent

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_filters.remote_presenter import SavuFiltersRemotePresenter  # noqa: F401


class SavuFiltersSIOModel(object):
    """
    Handles remote events
    """
    EVENT_STATUS = "status"
    EVENT_JOB_END = "job_end"

    def __init__(self, presenter: 'SavuFiltersRemotePresenter', sio_client: socketio.Client, namespace: str):
        self.presenter = presenter
        self.namespace = namespace

        self.sio_client = sio_client

        self.sio_client.on(self.EVENT_STATUS, self.action_event_status, namespace=namespace)
        self.sio_client.on(self.EVENT_JOB_END, self.action_event_job_end, namespace=namespace)

        self.job_response: Optional[JobRunResponseContent] = None

    def join(self, job_response: JobRunResponseContent):
        """
        Joins the room for this job
        :param job_response: Parsed response from the remote service
        """
        self.sio_client.emit("join",
                             json.dumps({
                                 "job": job_response.job_id,
                                 "queue": job_response.queue
                             }),
                             namespace=self.namespace)

    def action_event_status(self, remote_output):
        self.presenter.update_output_window(remote_output)

    def action_event_job_end(self, remote_output):
        self.presenter.remote_job_end(remote_output)
