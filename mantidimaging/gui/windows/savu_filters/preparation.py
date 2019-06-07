from concurrent.futures import Future

from requests_futures.sessions import FuturesSession


class SingleAccessContainer:
    def __init__(self, obj):
        self.__obj = obj

    def get(self):
        if self.__obj is None:
            raise ValueError("This object has been retrieved before.")

        obj = self.__obj
        self.__obj = None
        return obj


data = None  # type: SingleAccessContainer


def prepare_data():
    session = FuturesSession()
    # TODO consider integrating more into the model with the Async requests and stuff
    # TODO consider moving to CORE as this is not a GUI feature really
    response = session.get('http://localhost:5000/plugins?details=true')  # type: Future

    global data

    data = SingleAccessContainer(response)
