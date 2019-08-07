from concurrent.futures import Future
from concurrent.futures import ProcessPoolExecutor

from requests_futures.sessions import FuturesSession

from mantidimaging.core.utility.savu_interop.webapi import SERVER_URL, PLUGINS_WITH_DETAILS_URL

data = None


def prepare_data():
    session = FuturesSession(executor=ProcessPoolExecutor(max_workers=1))
    # TODO consider integrating more into the model with the Async requests and stuff
    # TODO consider moving to CORE as this is not a GUI feature really
    response: Future = session.get(f"{SERVER_URL}/{PLUGINS_WITH_DETAILS_URL}")

    global data

    data = response


prepare_data()
