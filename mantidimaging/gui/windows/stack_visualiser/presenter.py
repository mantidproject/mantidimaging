from enum import IntEnum
from logging import getLogger

from mantidimaging.core.data import Images
from mantidimaging.gui.mvp_base import BasePresenter
from .model import SVModel


class SVNotification(IntEnum):
    REFRESH_IMAGE = 0
    TOGGLE_IMAGE_MODE = 1


class SVParameters(IntEnum):
    """
    Stack Visualiser parameters that the Stack Visualiser presenter can retrieve
    """
    ROI = 0


class SVImageMode(IntEnum):
    NORMAL = 0
    AVERAGED = 1


class StackVisualiserPresenter(BasePresenter):
    def __init__(self, view, images: Images):
        super(StackVisualiserPresenter, self).__init__(view)
        self.model = SVModel()
        self.images = images
        self._current_image_index = 0
        self.image_mode: SVImageMode = SVImageMode.NORMAL
        self.averaged_image = None

    def notify(self, signal):
        try:
            if signal == SVNotification.REFRESH_IMAGE:
                self.set_displayed_image()
            if signal == SVNotification.TOGGLE_IMAGE_MODE:
                self.toggle_image_mode()
        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def delete_data(self):
        self.images = None

    def get_image(self, index):
        return self.images.sample[index]

    def set_displayed_image(self):
        if self.image_mode is SVImageMode.NORMAL:
            to_display = self.images.sample
        else:
            to_display = self.averaged_image
        self.view.image = to_display

    def get_parameter_value(self, parameter: SVParameters):
        """
        Gets a parameter from the stack visualiser for use elsewhere (e.g. filters).
        :param parameter: The parameter value to be retrieved
        """
        if parameter == SVParameters.ROI:
            return self.view.current_roi
        else:
            raise ValueError(
                "Invalid parameter name has been requested from the Stack "
                "Visualiser, parameter: {0}".format(parameter))

    def toggle_image_mode(self):
        if self.image_mode is SVImageMode.NORMAL:
            self.image_mode = SVImageMode.AVERAGED
        else:
            self.image_mode = SVImageMode.NORMAL

        if self.image_mode is SVImageMode.AVERAGED and self.averaged_image is None:
            self.averaged_image = self.model.create_averaged_image(self.images.sample)
        self.set_displayed_image()
