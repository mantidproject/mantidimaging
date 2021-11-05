# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import List, Optional

from pyqtgraph import ViewBox
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage
from skimage import io as skio


class IndicatorIconView(QGraphicsPixmapItem):
    def __init__(self, parent: ViewBox, icon_path: str, icon_pos: int, color: Optional[List[int]] = None):
        """An indicator icon for a pyqtgraph ViewBox

        The icon loaded from icon_path will be displayed in the low right corner of the ViewBox.

        :param parent: ViewBox to place indicator in
        :param icon_path: path to icon
        :param icon_pos: position index. Counting from 0 in lower right.
        """
        super().__init__()

        self.parent = parent
        self.icon_pos = icon_pos
        self.set_icon(icon_path, color)
        self.icon_size = [32, 32]

        self.parent.scene().addItem(self)

        self.position_icon()
        self.parent.sigResized.connect(self.position_icon)
        self.setVisible(False)
        self.setAcceptHoverEvents(True)

        self.connected_overlay = None

    def set_icon(self, icon_path: str, color: Optional[List[int]] = None):
        if color is not None:
            image_data = skio.imread(icon_path, plugin="imageio")
            # Set the RGB part to the red channel multiplied by the requested color
            red_channel = image_data[:, :, 0] / 255
            image_data[:, :, 0] = red_channel * color[0]
            image_data[:, :, 1] = red_channel * color[1]
            image_data[:, :, 2] = red_channel * color[2]

            h = image_data.shape[0]
            w = image_data.shape[1]
            image_qi = QImage(image_data.data, w, h, 4 * w, QImage.Format_RGBA8888)

            image_pm = QPixmap.fromImage(image_qi)
        else:
            image_pm = QPixmap(icon_path)
        self.setPixmap(image_pm)

    def position_icon(self):
        # The size of the imageview we are putting the icon ing
        scene_size = self.parent.size()
        # The position of the image within the scene
        scene_pos = self.parent.scenePos()
        # Lower right corner in scene pixel coordinates
        corner_pos_x = scene_size.width() + scene_pos.x()
        corner_pos_y = scene_size.height() + scene_pos.y()

        self.setOffset(corner_pos_x - self.icon_size[0] * (1 + self.icon_pos) - 10,
                       corner_pos_y - self.icon_size[1] - 30)

    def hoverEnterEvent(self, event):
        if self.connected_overlay is not None:
            self.connected_overlay.setOpacity(1)

    def hoverLeaveEvent(self, event):
        if self.connected_overlay is not None:
            self.connected_overlay.setOpacity(0)
