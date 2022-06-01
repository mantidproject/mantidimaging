# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Union, Tuple, Optional

from PyQt5.QtCore import QRect
from pyqtgraph import GraphicsLayout, LineSegmentROI

if TYPE_CHECKING:
    from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
    from mantidimaging.gui.widgets.mi_image_view.view import MIImageView


class LineProfilePlot(GraphicsLayout):
    def __init__(self, image_view: Union['MIMiniImageView', 'MIImageView'], enable_roi_reset: bool = True):
        super().__init__()

        self._line_profile = self.addPlot().plot()
        self._image_view = image_view
        self._roi_line: Optional[MILineSegmentROI] = None
        self._roi_initial_state = None

        self.update_plot()
        if enable_roi_reset:
            self._add_roi_reset_menu_option()

    def update_plot(self):
        if self._roi_line is not None or self._try_add_roi_to_image_view():
            roi_slice = self._roi_line.getArrayRegion(self._image_view.image_data,
                                                      self._image_view.image_item,
                                                      axes=(1, 0))
            self._line_profile.setData(roi_slice)

    def reset_roi_line(self, force_reset: bool = False) -> None:
        if self._roi_initial_state is not None and (force_reset or self._roi_line_needs_resetting()):
            self._roi_initial_state['points'] = self._roi_initial_pos()
            self._roi_line.setState(self._roi_initial_state)
            self._roi_line.maxBounds = self._roi_bounds()

    def _try_add_roi_to_image_view(self) -> bool:
        initial_position = self._roi_initial_pos()
        if initial_position is None:
            return False

        self._roi_line = MILineSegmentROI(positions=initial_position, pen='r', maxBounds=self._roi_bounds())
        self._image_view.viewbox.addItem(self._roi_line)
        self._roi_line.sigRegionChanged.connect(self.update_plot)
        self._roi_initial_state = self._roi_line.saveState()
        return True

    def _add_roi_reset_menu_option(self) -> None:
        self._reset_roi = self._image_view.viewbox.menu.addAction("Reset ROI")
        self._image_view.viewbox.menu.insertSeparator(self._reset_roi)
        self._reset_roi.triggered.connect(lambda: self.reset_roi_line(True))

    def _roi_line_needs_resetting(self) -> bool:
        image_width = self._image_view.image_item.width()
        if image_width is None or self._roi_line is None:
            return False

        roi_bound_width = self._roi_line.maxBounds.width()
        roi_bound_height = self._roi_line.maxBounds.height()
        return roi_bound_width != image_width or roi_bound_height != self._image_view.image_item.height()

    def _roi_initial_pos(self) -> Optional[list[Tuple[int, int]]]:
        image_width = self._image_view.image_item.width()
        return [(0, 0), (image_width, 0)] if image_width is not None else None

    def _roi_bounds(self) -> QRect:
        return QRect(0, 0, self._image_view.image_item.width(), self._image_view.image_item.height())


class MILineSegmentROI(LineSegmentROI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def checkPointMove(self, handle, pos, modifiers) -> bool:
        if self.maxBounds is None:
            return True

        new_point = self.getViewBox().mapSceneToView(pos)
        return self.maxBounds.contains(new_point.x(), new_point.y())
