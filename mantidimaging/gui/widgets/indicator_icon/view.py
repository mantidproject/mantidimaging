# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import List, Optional, Tuple, Callable

import numpy as np
from PIL import Image
from pyqtgraph import ViewBox
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsSimpleTextItem, QMenu, QAction
from PyQt5.QtGui import QPixmap, QImage, QColor


class IndicatorIconView(QGraphicsPixmapItem):  # type: ignore

    def __init__(self,
                 parent: ViewBox,
                 icon_path: str,
                 icon_pos: int,
                 color: Optional[List[int]] = None,
                 message: str = ""):
        """An indicator icon for a pyqtgraph ViewBox

        The icon loaded from icon_path will be displayed in the low right corner of the ViewBox.

        :param parent: ViewBox to place indicator in
        :param icon_path: path to icon
        :param icon_pos: position index. Counting from 0 in lower right.
        """
        super().__init__()

        self.parent = parent
        self.icon_pos = icon_pos

        self.label = QGraphicsSimpleTextItem(message)
        self.label.setVisible(False)
        self.parent.scene().addItem(self.label)

        self.set_icon(icon_path, color)
        self.icon_size = [32, 32]

        self.parent.scene().addItem(self)

        self.position_icon()
        self.parent.sigResized.connect(self.position_icon)
        self.setVisible(False)
        self.setAcceptHoverEvents(True)

        self.connected_overlay = None

        self.actions: List[QAction] = []

    def set_icon(self, icon_path: str, color: Optional[List[int]] = None) -> None:
        if color is not None:
            im = Image.open(icon_path)
            image_data = np.array(im)
            # Set the RGB part to the red channel multiplied by the requested color
            red_channel = image_data[:, :, 0] / 255
            image_data[:, :, 0] = red_channel * color[0]
            image_data[:, :, 1] = red_channel * color[1]
            image_data[:, :, 2] = red_channel * color[2]

            h = image_data.shape[0]
            w = image_data.shape[1]
            image_qi = QImage(image_data.data, w, h, 4 * w, QImage.Format_RGBA8888)

            image_pm = QPixmap.fromImage(image_qi)

            self.label.setBrush(QColor(*color))
        else:
            image_pm = QPixmap(icon_path)
        self.setPixmap(image_pm)

    def position_icon(self) -> None:
        # The size of the imageview we are putting the icon ing
        scene_size = self.parent.size()
        # The position of the image within the scene
        scene_pos = self.parent.scenePos()
        # Lower right corner in scene pixel coordinates
        corner_pos_x = scene_size.width() + scene_pos.x()
        corner_pos_y = scene_size.height() + scene_pos.y()

        icon_pos_x = corner_pos_x - self.icon_size[0] * (1 + self.icon_pos) - 10
        icon_pos_y = corner_pos_y - self.icon_size[1] - 30
        self.setOffset(icon_pos_x, icon_pos_y)

        label_width = self.label.boundingRect().width()
        self.label.setPos(corner_pos_x - label_width, icon_pos_y - self.icon_size[0])

    def hoverEnterEvent(self, event) -> None:
        if self.connected_overlay is not None:
            self.connected_overlay.setVisible(True)
        self.label.setVisible(True)

    def hoverLeaveEvent(self, event) -> None:
        if self.connected_overlay is not None:
            self.connected_overlay.setVisible(False)
        self.label.setVisible(False)

    def add_actions(self, actions: List[Tuple[str, Callable]]) -> None:
        for text, method in actions:
            action = QAction(text)
            action.triggered.connect(method)
            self.actions.append(action)

    def mouseClickEvent(self, event) -> None:
        event.accept()
        if self.actions:
            qm = QMenu()
            for action in self.actions:
                qm.addAction(action)

            qm.exec(event.screenPos().toQPoint())

    def set_message(self, message):
        self.label.setText(message)
        self.position_icon()
