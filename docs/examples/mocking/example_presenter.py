from __future__ import (absolute_import, division, print_function)
from enum import IntEnum


class Notification(IntEnum):
    SET_VALUE = 1,
    RESET_VALUE_CLICKED = 2


class ImgpyExamplePresenter(object):
    def __init__(self, view):
        super(ImgpyExamplePresenter, self).__init__()
        self.view = view
        self.model = 'create_the_model_instance_here'

    def notify(self, signal):
        """
        Pass a signal from the view to the presenter.
        In theory this must be the _ONLY_ public function, 
        but this is python, so we can't enforce it, but we can say
        pleaaaaaaase dont use the ones with _
        """
        if signal == Notification.SET_VALUE:
            self._update_view_value()
        elif signal == Notification.RESET_VALUE_CLICKED:
            self._reset_view_value()

    def _reset_view_value(self):
        current_value = self.view.get_value()
        self.view.set_value(current_value)

    def _update_view_value(self):
        # calls the method in the view to update the value
        self.view.set_value(5)
