from logging import getLogger


class BasePresenter(object):
    def __init__(self, view):
        self.view = view

    def notify(self, signal):
        raise NotImplementedError("Presenter must implement the notify() method")

    def show_error(self, error):
        if hasattr(self.view, 'show_error_dialog'):
            # If the view knows how to handle an error message
            self.view.show_error_dialog(error)
        else:
            # Otherwise just log the error
            getLogger(__name__).error('Presenter error: {}'.format(error))
