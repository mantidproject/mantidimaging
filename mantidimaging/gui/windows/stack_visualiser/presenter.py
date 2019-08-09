from enum import IntEnum
from logging import getLogger

from mantidimaging.core.data import Images
from mantidimaging.gui.mvp_base import BasePresenter


class SVNotification(IntEnum):
    REFRESH_IMAGE = 0


class SVParameters(IntEnum):
    """
    Stack Visualiser parameters that the Stack Visualiser presenter can retrieve
    """
    ROI = 0


class StackVisualiserPresenter(BasePresenter):
    def __init__(self, view, images: Images, data_traversal_axis):
        super(StackVisualiserPresenter, self).__init__(view)
        self.images = images
        self.axis = data_traversal_axis
        self._current_image_index = 0

    def notify(self, signal):
        try:
            if signal == SVNotification.REFRESH_IMAGE:
                self.view.show_current_image()
        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def delete_data(self):
        self.images = None

    def get_image(self, index):
        return self.images.sample[index]

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
