from typing import Tuple

import numpy as np
from PyQt5.QtWidgets import QGraphicsLinearLayout
from pyqtgraph import GraphicsLayoutWidget, ImageItem, ViewBox, HistogramLUTItem

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.gui.dialogs.cor_inspection.types import ImageType


class ReconSlicesView(GraphicsLayoutWidget):
    less_img: ImageItem
    current_img: ImageItem
    more_img: ImageItem

    def __init__(self, parent):
        super().__init__(parent)
        self.less_label = self.addLabel("Less")
        self.current_label = self.addLabel("Current")
        self.more_label = self.addLabel("More")

        self.nextRow()
        self.less_img, self.less_img_vb, self.less_hist = self.image_in_vb("less")
        self.current_img, self.current_img_vb, self.current_hist = self.image_in_vb("current")
        self.more_img, self.more_img_vb, self.more_hist = self.image_in_vb("more")

        def on_level_change():
            levels: Tuple[float, float] = self.current_hist.getLevels()
            self.less_hist.setLevels(*levels)
            self.more_hist.setLevels(*levels)

        self.current_hist.sigLevelsChanged.connect(on_level_change)

        for view, view2 in zip([self.less_img_vb, self.current_img_vb], [self.current_img_vb, self.more_img_vb]):
            view.linkView(ViewBox.XAxis, view2)
            view.linkView(ViewBox.YAxis, view2)

        image_layout = QGraphicsLinearLayout()
        image_layout.addItem(self.less_img_vb)
        image_layout.addItem(self.less_hist)
        image_layout.addItem(self.current_img_vb)
        image_layout.addItem(self.current_hist)
        image_layout.addItem(self.more_img_vb)
        image_layout.addItem(self.more_hist)
        #
        # self.histogram = HistogramLUTItem()
        # self.histogram.setImageItem(self.current_img)
        # image_layout.addItem(self.histogram)
        self.addItem(image_layout, colspan=6)

        self.nextRow()

        less_pixel = self.addLabel("")
        current_pixel = self.addLabel("")
        more_pixel = self.addLabel("")

        self.display_formatted_detail = {
            self.less_img: lambda val: less_pixel.setText(f"Value: {val:.6f}"),
            self.current_img: lambda val: current_pixel.setText(f"Value: {val:.6f}"),
            self.more_img: lambda val: more_pixel.setText(f"Value: {val:.6f}"),
        }

        for img in self.less_img, self.current_img, self.more_img:
            img.hoverEvent = lambda ev: self.mouse_over(ev)

        # self.nextRow()

        # hist_label = {'left': 'Count', 'bottom': 'Bin'}
        # self.less_histogram = HistogramLUTWidget(self, self.less_img)
        # self.addItem(self.less_histogram, 4, 0)
        # self.current_histogram = HistogramLUTWidget(self, self.current_img)
        # self.addItem(self.current_histogram, 4, 1)
        # self.more_histogram = HistogramLUTWidget(self, self.more_img)
        # self.addItem(self.more_histogram, 4, 2)
        # self.less_histogram = self.addPlot(row=4, col=0, labels=hist_label)
        # self.current_histogram = self.addPlot(row=4, col=1, labels=hist_label)
        # self.more_histogram = self.addPlot(row=4, col=2, labels=hist_label)

        # self.nextRow()

        # hist_layout = QGraphicsLinearLayout()
        # histogram = HistogramLUTItem()
        # histogram.setImageItem(self.current_img)
        # hist_layout.addItem(histogram)
        # self.addItem(histogram, 4, 0, colspan=3)

    def mouse_over(self, ev):
        # Ignore events triggered by leaving window or right clicking
        if ev.exit:
            return
        pos = CloseEnoughPoint(ev.pos())
        for img in self.less_img, self.current_img, self.more_img:
            if img.image is not None and pos.x < img.image.shape[0] and pos.y < img.image.shape[1]:
                pixel_value = img.image[pos.y, pos.x]
                self.display_formatted_detail[img](pixel_value)

    def image_in_vb(self, name=None) -> Tuple[ImageItem, ViewBox, HistogramLUTItem]:
        im = ImageItem()
        vb = ViewBox(invertY=True, lockAspect=True, name=name)
        vb.addItem(im)
        hist = HistogramLUTItem(im)
        return im, vb, hist

    def set_image(self, image_type: ImageType, recon_data: np.ndarray, title: str):
        if image_type == ImageType.LESS:
            self.less_img.clear()
            self.less_img.setImage(recon_data)
            self.less_label.setText(title)
        elif image_type == ImageType.CURRENT:
            self.current_img.clear()
            self.current_img.setImage(recon_data)
            self.current_label.setText(title)
            self.current_hist.imageChanged(True, True)
            levels = self.current_hist.getLevels()
            self.current_hist.setLevels(min(recon_data.min(), levels[0]),
                                        min(recon_data.max(), levels[1]))
        elif image_type == ImageType.MORE:
            self.more_img.clear()
            self.more_img.setImage(recon_data)
            self.more_label.setText(title)

        self.less_hist.imageChanged(True, True)
        self.more_hist.imageChanged(True, True)
        self.current_hist.sigLevelsChanged.emit(self.current_hist)
