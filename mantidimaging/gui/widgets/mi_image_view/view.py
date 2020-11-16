# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Optional, Tuple, Callable

from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel
from pyqtgraph import ImageView, ROI, ImageItem
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.widgets.mi_image_view.presenter import MIImagePresenter


class UnrotateablePlotROI(ROI):
    """
    Like PlotROI but does not add a rotation handle.
    """
    def __init__(self, size):
        ROI.__init__(self, pos=[0, 0], size=size)
        self.addScaleHandle([1, 1], [0, 0])


class MIImageView(ImageView):
    details: QLabel
    roiString = None
    imageItem: ImageItem

    roi_changed_callback: Optional[Callable[[SensibleROI], None]] = None

    def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, levelMode='mono', *args):
        super().__init__(parent, name, view, imageItem, levelMode, *args)
        self.presenter = MIImagePresenter()
        self.details = QLabel("", self.ui.layoutWidget)
        self.details.setStyleSheet("QLabel { color : white; background-color: black}")
        self.ui.gridLayout.addWidget(self.details, 1, 0, 1, 1)

        self.imageItem.hoverEvent = self.image_hover_event
        # disconnect the ROI recalculation on every move
        self.roi.sigRegionChanged.disconnect(self.roiChanged)
        self.view.removeItem(self.roi)

        self.roi = UnrotateablePlotROI(300)
        self.roi.setZValue(30)
        # make ROI red
        self.roi.setPen((255, 0, 0))
        self.view.addItem(self.roi)
        self.roi.hide()
        self.roi.sigRegionChangeFinished.connect(self.roiChanged)
        self.extend_roi_plot_mouse_press_handler()
        self.imageItem.setAutoDownsample(False)

        self._last_mouse_hover_location = CloseEnoughPoint([0, 0])

        self.imageItem.sigImageChanged.connect(self._refresh_message)

    def _refresh_message(self):
        # updates the ROI average value
        self._update_roi_region_avg()
        try:
            self._update_message(self._last_mouse_hover_location)
        except IndexError:
            # this happens after the image is cropped, and the last location
            # is outside of the new bounds. To prevent this happening again just reset back to 0, 0
            self._last_mouse_hover_location = CloseEnoughPoint([0, 0])

    def roiChanged(self):
        """
        Re-implements the roiChanged function to expect only 3D data,
        and uses a faster mean calculation on the ROI view of the data,
        instead of the full sized data.
        """
        # if the data isn't 3D the following code can't handle it correctly
        # so defer back to the original implementation which can handle 2D (any maybe ND)
        # more sensibly, albeit slower
        if self.image.ndim != 3:
            return super().roiChanged()

        roi = self._update_roi_region_avg()
        if self.roi_changed_callback and roi is not None:
            self.roi_changed_callback(roi)

    def _update_roi_region_avg(self) -> Optional[SensibleROI]:
        if self.image.ndim != 3:
            return None
        roi_pos, roi_size = self.get_roi()
        # image indices are in order [Z, X, Y]
        left, right = roi_pos.x, roi_pos.x + roi_size.x
        top, bottom = roi_pos.y, roi_pos.y + roi_size.y
        data = self.image[:, top:bottom, left:right]
        if data is not None:
            while data.ndim > 1:
                data = data.mean(axis=1)
            if len(self.roiCurves) == 0:
                self.roiCurves.append(self.ui.roiPlot.plot())
            self.roiCurves[0].setData(y=data, x=self.tVals)
        self.roiString = f"({left}, {top}, {right}, {bottom}) | " \
                         f"region avg={data[int(self.timeLine.value())].mean():.6f}"
        return SensibleROI(left, top, right, bottom)

    def extend_roi_plot_mouse_press_handler(self):
        original_handler = self.ui.roiPlot.mousePressEvent

        def extended_handler(ev):
            if ev.button() == QtCore.Qt.LeftButton:
                self.set_timeline_to_tick_nearest(ev.x())
            original_handler(ev)

        self.ui.roiPlot.mousePressEvent = lambda ev: extended_handler(ev)

    def get_roi(self) -> Tuple[CloseEnoughPoint, CloseEnoughPoint]:
        return self.presenter.get_roi(self.image,
                                      roi_pos=CloseEnoughPoint(self.roi.pos()),
                                      roi_size=CloseEnoughPoint(self.roi.size()))

    def image_hover_event(self, event: HoverEvent):
        if event.exit:
            return
        pt = CloseEnoughPoint(event.pos())
        self._last_mouse_hover_location = pt
        self._update_message(pt)

    def _update_message(self, pt):
        # event holds the coordinates in column-major coordinate
        # while the data is in row-major coordinate, hence why
        # the data access below is [y, x]
        msg = f"x={pt.y}, y={pt.x}, "
        if self.image.ndim == 3:
            msg += f"z={self.currentIndex}, value={self.image[self.currentIndex, pt.y, pt.x]:.6f}"
        else:
            msg += f"value={self.image[pt.y, pt.x]}"
        if self.roiString is not None:
            msg += f" | roi = {self.roiString}"
        self.details.setText(msg)

    def set_timeline_to_tick_nearest(self, x_pos_clicked):
        x_axis = self.getRoiPlot().getAxis('bottom')
        view_range = self.getRoiPlot().viewRange()[0]
        nearest = self.presenter.get_nearest_timeline_tick(x_pos_clicked, x_axis, view_range)
        self.timeLine.setValue(nearest)

    def set_selected_image(self, image_index: int):
        self.timeLine.setValue(image_index)
