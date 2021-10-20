# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import List, Tuple
from weakref import WeakSet

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

        self.siblings: "WeakSet[MIMiniImageView]" = WeakSet()

    @staticmethod
    def set_siblings(sibling_views: List["MIMiniImageView"]):
        for view1 in sibling_views:
            for view2 in sibling_views:
                if view2 is not view1:
                    view1.add_sibling(view2)

    def add_sibling(self, sibling: "MIMiniImageView"):
        self.siblings.add(sibling)

    def get_parts(self) -> Tuple[ImageItem, ViewBox, HistogramLUTItem]:
        return self.im, self.vb, self.hist
