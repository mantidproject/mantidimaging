# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import atexit
import json
from concurrent.futures import Future, ProcessPoolExecutor
from logging import getLogger

import socketio
from requests import Response
from requests_futures.sessions import FuturesSession

from mantidimaging.core.utility.savu_interop.webapi import (PLUGINS_WITH_DETAILS_URL, SERVER_URL, SERVER_WS_URL,
                                                            WS_JOB_STATUS_NAMESPACE)

LOG = getLogger(__name__)


class SocketIO:
    def __init__(self):
        LOG.debug("Preparing SOCKET IO connection")
        session = FuturesSession(executor=ProcessPoolExecutor(max_workers=1))

        self.request: Future = session.get(f"{SERVER_URL}/{PLUGINS_WITH_DETAILS_URL}")
        self.sio_client = socketio.Client()

    def retrieve_plugins_json(self):
        try:
            response: Response = self.request.result(timeout=5)
            if response.status_code == 200:
                return json.loads(response.content)
            else:
                raise ValueError(f"Failed getting plugins from the Savu backend. Error code {response.status_code}")
        except ConnectionError:
            raise RuntimeError("Cannot reach Savu backend. The GUI cannot open.")

    def connect(self) -> bool:
        """
        Connects to the websocket on the Hebi backend
        :return: True if the socket connection succeeds
        :raises: RuntimeError if the socket connection fails
        """
        atexit.register(lambda sio: sio.disconnect(), self.sio_client)

        # make output from the communication libs a bit less verbose
        getLogger("engineio.client").setLevel("WARNING")
        getLogger("socketio.client").setLevel("WARNING")
        getLogger("urllib3.connectionpool").setLevel("INFO")

        try:
            self.sio_client.connect(SERVER_WS_URL, namespaces=[WS_JOB_STATUS_NAMESPACE])
            return True
        except socketio.exceptions.ConnectionError as err:
            raise RuntimeError(f"Savu backend could not be connected, error {err}")

    def disconnect(self):
        self.sio_client.reconnection = False
        self.sio_client.disconnect()
