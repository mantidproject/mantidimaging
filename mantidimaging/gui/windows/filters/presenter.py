from enum import Enum
from logging import getLogger

import numpy as np
from pyqtgraph import ImageItem, PlotItem

from mantidimaging.core.data import Images
from mantidimaging.core.utility.histogram import (
    generate_histogram_from_image)
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import (
    BlockQtSignals, get_parameters_from_stack)
from mantidimaging.gui.windows.stack_visualiser import SVParameters
from .model import FiltersWindowModel


class Notification(Enum):
    REGISTER_ACTIVE_FILTER = 1
    APPLY_FILTER = 2
    UPDATE_PREVIEWS = 3
    SCROLL_PREVIEW_UP = 4
    SCROLL_PREVIEW_DOWN = 5


class FiltersWindowPresenter(BasePresenter):

    def __init__(self, view, main_window):
        super(FiltersWindowPresenter, self).__init__(view)

        self.model = FiltersWindowModel()
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
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    @property
    def max_preview_image_idx(self):
        return max(self.model.num_images_in_stack - 1, 0)

    def set_stack_uuid(self, uuid):
        self.set_stack(
            self.main_window.get_stack_visualiser(uuid)
            if uuid is not None else None)

    def set_stack(self, stack):
        # Disconnect ROI update signal from previous stack
        if self.model.stack:
            self.model.stack.roi_updated.disconnect(self.handle_roi_selection)

        # Connect ROI update signal to newly selected stack
        if stack:
            stack.roi_updated.connect(self.handle_roi_selection)

        self.model.stack = stack

        # Update the preview image index
        with BlockQtSignals([self.view]):
            self.set_preview_image_index(0)
            self.view.previewImageIndex.setMaximum(self.max_preview_image_idx)

        self.do_update_previews()

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

        # Register new filter (adding it's property widgets to the properties
        # layout)
        self.model.setup_filter(
            register_func(self.view.filterPropertiesLayout,
                          self.view.auto_update_triggered.emit))

    def filter_uses_parameter(self, parameter):
        return parameter in self.model.parameters_from_stack.values() if \
            self.model.parameters_from_stack is not None else False

    def do_apply_filter(self):
        self.model.do_apply_filter()

    def do_update_previews(self):
        log = getLogger(__name__)

        progress = Progress.ensure_instance()
        progress.task_name = 'Filter preview'
        progress.add_estimated_steps(1)

        with progress:
            progress.update(msg='Getting stack')
            stack = self.model.stack_presenter

            # If there is no stack then clear the preview area
            if stack is None:
                self.view.clear_preview_plots()

            else:
                # Add the remaining steps for calculating the preview
                progress.add_estimated_steps(8)

                before_image_data = stack.get_image(self.model.preview_image_idx)

                # Update image before
                self._update_preview_image(
                    before_image_data,
                    self.view.preview_image_before,
                    self.view.preview_histogram_before,
                    progress)

                # Generate sub-stack and run filter
                progress.update(msg='Running preview filter')
                exec_kwargs = get_parameters_from_stack(stack, self.model.parameters_from_stack)

                filtered_image_data = None
                try:
                    sub_images = Images(np.asarray([before_image_data]))
                    self.model.apply_filter(sub_images, exec_kwargs)
                    filtered_image_data = sub_images.sample[0]
                except Exception as e:
                    log.debug("Error applying filter for preview: {}".format(e))

                # Update image after
                if filtered_image_data is not None:
                    self._update_preview_image(
                        filtered_image_data,
                        self.view.preview_image_after,
                        self.view.preview_histogram_after,
                        progress)

            # Redraw
            progress.update(msg='Redraw canvas')

    def _update_preview_image(self, image_data: np.ndarray, image: ImageItem, histogram: PlotItem, progress):
        # Generate histogram data
        progress.update(msg='Generating histogram')
        center, hist, _ = generate_histogram_from_image(image_data)

        # Update image
        progress.update(msg='Updating image')
        image.setImage(image_data)

        # Update histogram
        progress.update(msg='Updating histogram')
        histogram.clearPlots()
        histogram.plot(hist)

    def do_scroll_preview(self, offset):
        idx = self.model.preview_image_idx + offset
        idx = max(min(idx, self.max_preview_image_idx), 0)
        self.set_preview_image_index(idx)
