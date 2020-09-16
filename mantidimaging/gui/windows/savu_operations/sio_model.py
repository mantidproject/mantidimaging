import json
from typing import TYPE_CHECKING, Optional

from requests import Response

from mantidimaging.core.net.socket_io import SocketIO
from mantidimaging.gui.windows.savu_operations.job_run_response import JobRunResponseContent

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_operations.remote_presenter import SavuFiltersRemotePresenter  # noqa: F401


class SavuFiltersSIOModel(object):
    """
    Handles remote events
    """
    EVENT_STATUS = "status"
    EVENT_JOB_END = "job_end"

    def __init__(self, presenter: 'SavuFiltersRemotePresenter', namespace: str):
        self.presenter = presenter
        self.namespace = namespace

        self.client = SocketIO()
        self.client.connect()

        self.client.sio_client.on(self.EVENT_STATUS, self.action_event_status, namespace=namespace)
        self.client.sio_client.on(self.EVENT_JOB_END, self.action_event_job_end, namespace=namespace)

        self.job_response: Optional[JobRunResponseContent] = None

    def disconnect(self):
        self.client.disconnect()

    def retrieve_plugins_json(self):
        try:
            response: Response = self.client.request.result(timeout=5)
            if response.status_code == 200:
                return json.loads(response.content)
            else:
                raise ValueError(f"Failed getting plugins from the Savu backend. Error code {response.status_code}")
        except ConnectionError:
            raise RuntimeError("Cannot reach Savu backend. The GUI cannot open.")

    def join(self, job_response: JobRunResponseContent):
        """
        Joins the room for this job
        :param job_response: Parsed response from the remote service
        """
        self.client.sio_client.emit("join",
                                    json.dumps({
                                        "job": job_response.job_id,
                                        "queue": job_response.queue
                                    }),
                                    namespace=self.namespace)

    def action_event_status(self, remote_output):
        self.presenter.update_output_window(remote_output)

    def action_event_job_end(self, remote_output):
        self.presenter.remote_job_end(remote_output)
