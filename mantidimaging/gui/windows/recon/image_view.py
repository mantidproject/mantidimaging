from math import isnan
from typing import Tuple

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QGraphicsGridLayout
from pyqtgraph import GraphicsLayoutWidget, ImageItem, ViewBox, HistogramLUTItem, LabelItem, InfiniteLine

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.data_containers import Degrees


class ReconImagesView(GraphicsLayoutWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.projection, self.projection_vb, self.projection_hist = self.image_in_vb("Projection")
        self.recon, self.recon_vb, self.recon_hist = self.image_in_vb("Recon")

        self.slice_line = InfiniteLine(pos=1024, angle=0, movable=True)
        self.projection_vb.addItem(self.slice_line)
        self.tilt_line = InfiniteLine(pos=1024, angle=90, pen=((255, 0, 0, 255)), movable=True)

        image_layout = QGraphicsGridLayout()
        image_layout.addItem(self.projection_vb, 0, 0)
        image_layout.addItem(self.projection_hist, 0, 1)
        image_layout.addItem(self.recon_vb, 0, 2)
        image_layout.addItem(self.recon_hist, 0, 3)
        projection_details = LabelItem("Value")
        recon_details = LabelItem("Value")
        image_layout.addItem(projection_details, 1, 0, 1, 2)
        image_layout.addItem(recon_details, 1, 2, 1, 2)

        self.addItem(image_layout)
        self.nextRow()

        self.display_formatted_detail = {
            self.projection: lambda val: projection_details.setText(f"Value: {val:.6f}"),
            self.recon: lambda val: recon_details.setText(f"Value: {val:.6f}")
        }
        self.projection.hoverEvent = lambda ev: self.mouse_over(ev, self.projection)
        self.projection.mouseClickEvent = lambda ev: self.mouse_click(ev, self.slice_line)
        self.recon.hoverEvent = lambda ev: self.mouse_over(ev, self.recon)

    @staticmethod
    def image_in_vb(name=None) -> Tuple[ImageItem, ViewBox, HistogramLUTItem]:
        im = ImageItem()
        vb = ViewBox(invertY=True, lockAspect=True, name=name)
        vb.addItem(im)
        hist = HistogramLUTItem(im)
        return im, vb, hist

    def update_projection(self, image_data, preview_slice_index, tilt_line_points, roi):
        self.projection.setImage(image_data)
        if roi:
            self.projection.setRect(QRect(*roi))
        self.projection_hist.imageChanged(autoLevel=True, autoRange=True)
        self.slice_line.setPos(preview_slice_index)
        # self.tilt_line.setAngle()

    def update_recon(self, image_data):
        self.recon.setImage(image_data)
        self.recon_hist.imageChanged(autoLevel=True, autoRange=True)

    def mouse_over(self, ev, img):
        # Ignore events triggered by leaving window or right clicking
        if ev.exit:
            return
        pos = CloseEnoughPoint(ev.pos())
        if img.image is not None and pos.x < img.image.shape[0] and pos.y < img.image.shape[1]:
            pixel_value = img.image[pos.y, pos.x]
            self.display_formatted_detail[img](pixel_value)

    def mouse_click(self, ev, line: InfiniteLine):
        line.setPos(ev.pos())
        self.parent.presenter.do_user_click_recon(CloseEnoughPoint(ev.pos()).y)

    def clear_recon(self):
        self.recon.clear()

    def reset_slice_and_tilt(self, slice_index):
        self.slice_line.setPos(slice_index)
        self.projection_vb.removeItem(self.tilt_line)

    def set_tilt(self, tilt: Degrees):
        if not isnan(tilt.value): # is isnan it means there is no tilt, i.e. the line is vertical
            self.tilt_line.setAngle(90 + tilt.value)
        self.projection_vb.addItem(self.tilt_line)
