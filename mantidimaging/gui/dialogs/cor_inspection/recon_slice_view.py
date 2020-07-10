from typing import Tuple, List, TYPE_CHECKING

import numpy as np
from PyQt5.QtWidgets import QPushButton
from pyqtgraph import GraphicsLayoutWidget, ImageItem, ViewBox, HistogramLUTItem, LabelItem

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.gui.dialogs.cor_inspection.types import ImageType

if TYPE_CHECKING:
    from mantidimaging.gui.dialogs.cor_inspection import CORInspectionDialogView


class CompareSlicesView(GraphicsLayoutWidget):
    less_img: ImageItem
    current_img: ImageItem
    more_img: ImageItem

    lessButton: QPushButton
    currentButton: QPushButton
    moreButton: QPushButton

    def __init__(self, parent: 'CORInspectionDialogView'):
        super().__init__(parent)
        self.parent = parent

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

        image_layout = self.addLayout(colspan=6)

        self.less_label = LabelItem("")
        image_layout.addItem(self.less_label, 0, 0, 1, 2)
        self.current_label = LabelItem("")
        image_layout.addItem(self.current_label, 0, 2, 1, 2)
        self.more_label = LabelItem("Value")
        image_layout.addItem(self.more_label, 0, 4, 1, 2)

        image_layout.addItem(self.less_img_vb, 1, 0)
        image_layout.addItem(self.less_hist, 1, 1)
        image_layout.addItem(self.current_img_vb, 1, 2)
        image_layout.addItem(self.current_hist, 1, 3)
        image_layout.addItem(self.more_img_vb, 1, 4)
        image_layout.addItem(self.more_hist, 1, 5)

        less_pixel = LabelItem("Value")
        image_layout.addItem(less_pixel, 2, 0, 1, 2)
        current_pixel = LabelItem("Value")
        image_layout.addItem(current_pixel, 2, 2, 1, 2)
        more_pixel = LabelItem("Value")
        image_layout.addItem(more_pixel, 2, 4, 1, 2)

        less_sumsq = LabelItem("Value")
        image_layout.addItem(less_sumsq, 3, 0, 1, 2)
        current_sumsq = LabelItem("Value")
        image_layout.addItem(current_sumsq, 3, 2, 1, 2)
        more_sumsq = LabelItem("Value")
        image_layout.addItem(more_sumsq, 3, 4, 1, 2)

        def update_text(val: float, sqsum: float, pixel_label: LabelItem, sqsum_label: LabelItem):
            pixel_label.setText(f"Value: {val:.6f}")
            sqsum_label.setText(f"Sum of SQ: {sqsum:.6f}")

        self.display_formatted_detail = {
            # '' if val < 0 else ' ' pads out the line
            self.less_img: lambda val, sumsq: update_text(val, sumsq, less_pixel, less_sumsq),
            self.current_img: lambda val, sumsq: update_text(val, sumsq, current_pixel, current_sumsq),
            self.more_img: lambda val, sumsq: update_text(val, sumsq, more_pixel, more_sumsq),
        }

        for img in self.less_img, self.current_img, self.more_img:
            img.hoverEvent = lambda ev: self.mouse_over(ev)

    def mouse_over(self, ev):
        # Ignore events triggered by leaving window or right clicking
        if ev.exit:
            return
        pos = CloseEnoughPoint(ev.pos())
        self._refresh_value_labels(pos)

    def _refresh_value_labels(self, pos: CloseEnoughPoint):
        diffs = []
        for img in self.less_img, self.current_img, self.more_img:
            if img.image is not None and pos.x < img.image.shape[0] and pos.y < img.image.shape[1]:
                pixel_value = img.image[pos.y, pos.x]
                diff = np.sum(img.image ** 2)
                self.display_formatted_detail[img](pixel_value, diff)
                diffs.append(diff)
        return diffs

    @staticmethod
    def image_in_vb(name=None) -> Tuple[ImageItem, ViewBox, HistogramLUTItem]:
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
            self.current_img.setImage(recon_data, autoLevels=False)
            self.current_label.setText(title)
        elif image_type == ImageType.MORE:
            self.more_img.clear()
            self.more_img.setImage(recon_data)
            self.more_label.setText(title)

        self.less_hist.imageChanged(True, True)
        self.more_hist.imageChanged(True, True)
        self.current_hist.sigLevelsChanged.emit(self.current_hist)
        diffs = self._refresh_value_labels(CloseEnoughPoint([0, 0]))
        self.parent.mark_best_recon(diffs)

