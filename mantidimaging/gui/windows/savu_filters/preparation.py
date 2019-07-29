from concurrent.futures import Future

from requests_futures.sessions import FuturesSession

data = None


def prepare_data():
    session = FuturesSession()
    # TODO consider integrating more into the model with the Async requests and stuff
    # TODO consider moving to CORE as this is not a GUI feature really
    response: Future = session.get("http://localhost:5000/plugins?details=true")

    global data

    data = response
