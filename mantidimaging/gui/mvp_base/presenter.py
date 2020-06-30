from logging import getLogger
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from mantidimaging.gui.mvp_base import BaseMainWindowView, BaseDialogView


class BasePresenter(object):
    view: Union['BaseMainWindowView', 'BaseDialogView']

    def __init__(self, view: 'BaseMainWindowView'):
        self.view = view

    def notify(self, signal):
        raise NotImplementedError("Presenter must implement the notify() method")

    def show_error(self, error, traceback):
        if hasattr(self.view, 'show_error_dialog'):
            # If the view knows how to handle an error message
            self.view.show_error_dialog(str(error))
        getLogger(__name__).error(f'Presenter error: {error}\n{traceback}')
