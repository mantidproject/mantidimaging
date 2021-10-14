# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from pathlib import Path

from pyqtgraph import ViewBox
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap


class IndicatorIconView(QGraphicsPixmapItem):
    def __init__(self, parent: ViewBox, icon_path: Path, icon_pos: int):
        """An indicator icon for a pyqtgraph ViewBox

        The icon loaded from icon_path will be displayed in the low right corner of the ViewBox.

        :param parent: ViewBox to place indicator in
        :param icon_path: path to icon
        :param icon_pos: position index. Counting from 0 in lower right.
        """
        super().__init__()

        self.parent = parent
        self.icon_pos = icon_pos
        self.set_icon(icon_path)

        self.parent.scene().addItem(self)

        self.position_icon()
        self.parent.sigResized.connect(self.position_icon)

    def set_icon(self, icon_path: Path):
        image_pm = QPixmap(icon_path)
        self.setPixmap(image_pm)

    def position_icon(self):
        scene_size = self.parent.size()
        img_size = self.pixmap().size()
        self.setOffset(scene_size.width() - img_size.width() * (1 + self.icon_pos) - 10,
                       scene_size.height() - img_size.height() - 30)
