# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Tuple

from pyqtgraph import ImageItem, ViewBox
from pyqtgraph.graphicsItems.GraphicsLayout import GraphicsLayout
from pyqtgraph.graphicsItems.HistogramLUTItem import HistogramLUTItem

graveyard = []


class MIMiniImageView(GraphicsLayout):
    def __init__(self, name: str = "MIMiniImageView"):
        super().__init__()

        self.im = ImageItem()
        self.vb = ViewBox(invertY=True, lockAspect=True, name=name)
        self.vb.addItem(self.im)
        self.hist = HistogramLUTItem(self.im)
        graveyard.append(self.vb)

        self.addItem(self.vb)
        self.addItem(self.hist)

    def get_parts(self) -> Tuple[ImageItem, ViewBox, HistogramLUTItem]:
        return self.im, self.vb, self.hist
