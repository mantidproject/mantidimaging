from __future__ import absolute_import, division, print_function


class BasePresenter(object):

    def __init__(self, view):
        self.view = view

    def notify(self, signal):
        raise NotImplementedError(
                "Presenter must implement the notify() method")

    def show_error(self, error):
        self.view.show_error_dialog(error)
