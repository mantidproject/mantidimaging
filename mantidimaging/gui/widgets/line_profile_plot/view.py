# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Union, Optional

from PyQt5.QtCore import QRect
from pyqtgraph import GraphicsLayout, LineSegmentROI

from mantidimaging.gui.utility import BlockQtSignals

if TYPE_CHECKING:
    from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
    from mantidimaging.gui.widgets.mi_image_view.view import MIImageView


class LineProfilePlot(GraphicsLayout):
    def __init__(self, image_view: Union['MIMiniImageView', 'MIImageView']):
        super().__init__()

        self._plot = self.addPlot()
        self._line_profile = self._plot.plot()
        self._roi_line = ImageViewLineROI(image_view, reset_menu_name="Reset Profile Line")
        self._roi_line.sigRegionChanged.connect(self.update)

    def update(self) -> None:
        image_region = self._roi_line.get_image_region()
        if image_region is None:
            self.clear_plot()
        else:
            self._line_profile.setData(image_region)

    def reset(self) -> None:
        if self._roi_line.reset_is_needed():
            self._roi_line.reset()
        else:
            # Even if we don't need to move the ROI line, we may have new image data to plot
            self.update()

    def clear_plot(self):
        # Calling self._line_profile.clear() seems to be very slow, so we use this approach instead
        self._plot.clear()
        self._line_profile = self._plot.plot()


class ImageViewLineROI(LineSegmentROI):
    def __init__(self, image_view: Union['MIMiniImageView', 'MIImageView'], reset_menu_name: Optional[str] = None):
        super().__init__(positions=[(0, 0), (0, 0)], pen='r')

        self._image_view = image_view
        self._add_reset_menu_option(reset_menu_name)
        self._initial_state = self.saveState()
        self._roi_line_is_visible = False

        # We can't add the ROI line until we have some image data dimensions to position it
        if self._image_data_exists():
            self._add_roi_to_image()

    def checkPointMove(self, handle, pos, modifiers) -> bool:
        if self.maxBounds is None:
            return True

        new_point = self.getViewBox().mapSceneToView(pos)
        return self.maxBounds.contains(new_point.x(), new_point.y())

    def get_image_region(self):
        if not self._image_data_exists():
            return None

        if not self._roi_line_is_visible:
            self._add_roi_to_image()

        return self.getArrayRegion(self._image_view.image_data, self._image_view.image_item, axes=(1, 0))

    def reset(self) -> None:
        if self._image_data_exists() and self._roi_line_is_visible:
            self._set_initial_state()
            self.sigRegionChanged.emit(self)

    def reset_is_needed(self) -> bool:
        if not self._image_data_exists() or not self._roi_line_is_visible:
            return False

        image_width = self._image_view.image_item.width()
        image_height = self._image_view.image_item.height()
        return self.maxBounds.width() != image_width or self.maxBounds.height() != image_height

    def _image_data_exists(self) -> bool:
        return self._image_view.image_data is not None

    def _set_initial_state(self) -> None:
        # Prevent emitting a RegionChanged signal from setting the state programmatically
        with BlockQtSignals(self):
            self._initial_state['points'] = [(0, 0), (self._image_view.image_item.width(), 0)]
            self.setState(self._initial_state)
            self.maxBounds = QRect(0, 0, self._image_view.image_item.width(), self._image_view.image_item.height())

    def _add_roi_to_image(self) -> None:
        self._set_initial_state()
        self._image_view.viewbox.addItem(self)
        self._roi_line_is_visible = True

    def _add_reset_menu_option(self, reset_menu_name: Optional[str] = None) -> None:
        menu_name = reset_menu_name if reset_menu_name is not None else "Reset ROI line"
        self._reset_option = self._image_view.viewbox.menu.addAction(menu_name)
        self._image_view.viewbox.menu.insertSeparator(self._reset_option)
        self._reset_option.triggered.connect(lambda: self.reset())
