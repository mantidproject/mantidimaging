from logging import getLogger
from typing import Optional, Tuple, Callable

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel
from pyqtgraph import ImageView, ROI
from pyqtgraph.GraphicsScene.mouseEvents import HoverEvent

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.sensible_roi import SensibleROI


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

    roi_changed_callback: Optional[Callable[[SensibleROI], None]] = None

    def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, levelMode='mono', *args):
        super().__init__(parent, name, view, imageItem, levelMode, *args)
        self.details = QLabel("", self.ui.layoutWidget)
        self.details.setStyleSheet("QLabel { color : white; }")
        self.ui.gridLayout.addWidget(self.details, 1, 0, 1, 1)

        self.imageItem.hoverEvent = self.image_hover_event
        # disconnect the ROI recalculation on every move
        self.roi.sigRegionChanged.disconnect(self.roiChanged)
        self.view.removeItem(self.roi)

        self.roi = UnrotateablePlotROI(300)
        self.roi.setZValue(30)
        self.view.addItem(self.roi)
        self.roi.hide()
        # self.roi.setSize(300)
        self.roi.sigRegionChangeFinished.connect(self.roiChanged)
        self.extend_roi_plot_mouse_press_handler()

    def roiChanged(self):
        """
        Reimplements the roiChanged function to expect only 3D data,
        and uses a faster mean calculation on the ROI view of the data,
        instead of the full sized data.
        """
        roi_pos, roi_size = self.get_roi()

        # image indices are in order [Z, X, Y]
        left, right = roi_pos.x, roi_pos.x + roi_size.x
        top, bottom = roi_pos.y, roi_pos.y + roi_size.y
        self.roiString = f"({left}, {top}, {right}, {bottom})"
        if self.image.ndim == 3:
            data = self.image[:, left:right, top:bottom]
            if data is not None:
                while data.ndim > 1:
                    data = data.mean(axis=1)
                if len(self.roiCurves) == 0:
                    self.roiCurves.append(self.ui.roiPlot.plot())
                self.roiCurves[0].setData(y=data, x=self.tVals)

        if self.roi_changed_callback:
            self.roi_changed_callback(SensibleROI(left, top, right, bottom))

    def extend_roi_plot_mouse_press_handler(self):
        original_handler = self.ui.roiPlot.mousePressEvent

        def extended_handler(ev):
            if ev.button() == QtCore.Qt.LeftButton:
                self.set_timeline_to_tick_nearest(ev.x())
            original_handler(ev)

        self.ui.roiPlot.mousePressEvent = lambda ev: extended_handler(ev)

    def get_roi(self, ensure_in_image=True) -> Tuple[CloseEnoughPoint, CloseEnoughPoint]:
        roi_pos, roi_size = CloseEnoughPoint(self.roi.pos()), CloseEnoughPoint(self.roi.size())

        if ensure_in_image:
            # Don't allow negative point coordinates
            if roi_pos.x < 0 or roi_pos.y < 0:
                getLogger(__name__).info("Region of Interest starts outside the picture! Clipping start to (0, 0)")
                roi_pos.x = max(roi_pos.x, 0)
                roi_pos.y = max(roi_pos.y, 0)
        return roi_pos, roi_size

    def image_hover_event(self, event: HoverEvent):
        if event.exit:
            return
        pt = CloseEnoughPoint(event.pos())
        msg = f"x={pt.x}, y={pt.y}, "
        if self.image.ndim == 3:
            msg += f"z={self.currentIndex}, value={self.image[self.currentIndex, pt.y, pt.x]}"
        else:
            msg += f"value={self.image[pt.y, pt.x]}"

        if self.roiString is not None:
            msg += f" | roi = {self.roiString}"
        self.details.setText(msg)

    def set_timeline_to_tick_nearest(self, x):
        x_axis = self.getRoiPlot().getAxis('bottom')
        frac_pos = (x - x_axis.x()) / x_axis.height()
        view_range = self.getRoiPlot().viewRange()[0]
        domain_pos = (view_range[1] - view_range[0]) * frac_pos
        self.timeLine.setValue(np.round(view_range[0] + domain_pos))
