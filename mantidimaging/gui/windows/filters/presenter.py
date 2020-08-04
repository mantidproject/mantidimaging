import traceback
from enum import Enum, auto
from logging import getLogger
from typing import Callable, Any, Optional
from typing import TYPE_CHECKING

import numpy as np
from pyqtgraph import ImageItem

from mantidimaging.core.data import Images
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import (BlockQtSignals, get_parameters_from_stack)
from mantidimaging.gui.windows.stack_visualiser import SVParameters
from .model import FiltersWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView
    from mantidimaging.gui.windows.filters import FiltersWindowView


class Notification(Enum):
    REGISTER_ACTIVE_FILTER = auto()
    APPLY_FILTER = auto()
    UPDATE_PREVIEWS = auto()
    SCROLL_PREVIEW_UP = auto()
    SCROLL_PREVIEW_DOWN = auto()


class FiltersWindowPresenter(BasePresenter):
    view: 'FiltersWindowView'

    def __init__(self, view: 'FiltersWindowView', main_window: 'MainWindowView'):
        super(FiltersWindowPresenter, self).__init__(view)

        self.model = FiltersWindowModel(self)
        self.main_window = main_window

    def notify(self, signal):
        try:
            if signal == Notification.REGISTER_ACTIVE_FILTER:
                self.do_register_active_filter()
            elif signal == Notification.APPLY_FILTER:
                self.do_apply_filter()
            elif signal == Notification.UPDATE_PREVIEWS:
                self.do_update_previews()
            elif signal == Notification.SCROLL_PREVIEW_UP:
                self.do_scroll_preview(1)
            elif signal == Notification.SCROLL_PREVIEW_DOWN:
                self.do_scroll_preview(-1)

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    @property
    def max_preview_image_idx(self):
        return max(self.model.num_images_in_stack - 1, 0)

    def set_stack_uuid(self, uuid):
        self.set_stack(self.main_window.get_stack_visualiser(uuid) if uuid is not None else None)

    def set_stack(self, stack):
        # Disconnect ROI update signal from previous stack
        self.disconnect_current_stack_roi()

        # Connect ROI update signal to newly selected stack
        if stack:
            stack.roi_updated.connect(self.handle_roi_selection)

        self.model.stack = stack

        # Update the preview image index
        with BlockQtSignals([self.view]):
            self.set_preview_image_index(0)
            self.view.previewImageIndex.setMaximum(self.max_preview_image_idx)

        self.do_update_previews()

    def disconnect_current_stack_roi(self):
        if self.model.stack:
            self.model.stack.roi_updated.disconnect(self.handle_roi_selection)

    def handle_roi_selection(self, roi: SensibleROI):
        if roi and self.filter_uses_parameter(SVParameters.ROI):
            self.view.auto_update_triggered.emit()

    def set_preview_image_index(self, image_idx):
        """
        Sets the current preview image index.
        """
        self.model.preview_image_idx = image_idx

        # Set preview index spin box to new index
        preview_idx_spin = self.view.previewImageIndex
        with BlockQtSignals([preview_idx_spin]):
            preview_idx_spin.setValue(self.model.preview_image_idx)

        # Trigger preview updating
        self.view.auto_update_triggered.emit()

    def do_register_active_filter(self):
        filter_idx = self.view.filterSelector.currentIndex()

        # Get registration function for new filter
        register_func = self.model.filter_registration_func(filter_idx)

        # Register new filter (adding it's property widgets to the properties layout)
        filter_widget_kwargs = register_func(self.view.filterPropertiesLayout, self.view.auto_update_triggered.emit,
                                             self.view)
        self.model.setup_filter(filter_idx, filter_widget_kwargs)
        self.view.clear_error_dialog()

    def filter_uses_parameter(self, parameter):
        return parameter in self.model.params_needed_from_stack.values() if \
            self.model.params_needed_from_stack is not None else False

    def do_apply_filter(self):
        self.view.clear_previews()
        self.model.do_apply_filter()

    def do_update_previews(self):
        stack = self.model.stack_presenter

        self.view.clear_previews()
        if stack is not None:
            subset: Images = stack.get_image(self.model.preview_image_idx)
            before_image = np.copy(subset.data[0])
            # Update image before
            self._update_preview_image(before_image, self.view.preview_image_before,
                                       self.view.previews.set_before_histogram)

            # Generate sub-stack and run filter
            exec_kwargs = get_parameters_from_stack(stack, self.model.params_needed_from_stack)

            filtered_image_data = None
            try:
                self.model.apply_filter(subset, exec_kwargs)
                filtered_image_data = subset.data[0]
            except Exception as e:
                msg = f"Error applying filter for preview: {e}"
                self.show_error(msg, traceback.format_exc())

            # Update image after and difference
            if filtered_image_data is not None:
                self._update_preview_image(filtered_image_data, self.view.preview_image_after,
                                           self.view.previews.set_after_histogram)

                if filtered_image_data.shape == before_image.shape:
                    diff = np.subtract(filtered_image_data, before_image)
                    if self.view.invertDifference.isChecked():
                        diff = np.negative(diff, out=diff)
                    self._update_preview_image(diff, self.view.preview_image_difference, None)

    @staticmethod
    def _update_preview_image(image_data: Optional[np.ndarray], image: ImageItem,
                              redraw_histogram: Optional[Callable[[Any], None]]):
        image.clear()
        image.setImage(image_data)

        if redraw_histogram:
            # Update histogram
            redraw_histogram(image.getHistogram())

    def do_scroll_preview(self, offset):
        idx = self.model.preview_image_idx + offset
        idx = max(min(idx, self.max_preview_image_idx), 0)
        self.set_preview_image_index(idx)
