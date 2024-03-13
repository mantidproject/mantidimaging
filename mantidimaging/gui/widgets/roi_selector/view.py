# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np
from PyQt5.QtWidgets import QMainWindow, QMenu, QAction, QPushButton

from mantidimaging.gui.widgets.mi_image_view.view import MIImageView

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class ROISelectorView(QMainWindow):

    def __init__(self,
                 parent,
                 image_stack: ImageStack,
                 slice_idx: int,
                 roi_values: list[int] | None = None,
                 roi_changed_callback=None) -> None:
        super().__init__(parent)

        self.main_image = image_stack.slice_as_array(slice_idx)
        averaged_images = np.sum(image_stack.data, axis=0)
        self.averaged_image = averaged_images.reshape((1, averaged_images.shape[0], averaged_images.shape[1]))

        self.setWindowTitle("Select ROI")
        self.setMinimumHeight(600)
        self.setMinimumWidth(600)
        self.roi_view = MIImageView(self)
        self.setCentralWidget(self.roi_view)

        # Add context menu bits:
        menu = QMenu(self.roi_view)
        toggle_show_averaged_image = QAction("Toggle show averaged image", menu)
        toggle_show_averaged_image.triggered.connect(lambda: self.toggle_average_images())
        menu.addAction(toggle_show_averaged_image)
        menu.addSeparator()
        self.roi_view.imageItem.menu = menu

        self.roi_view.setImage(self.averaged_image)
        self.roi_view_averaged = True

        if roi_changed_callback:
            self.roi_view.roi_changed_callback = lambda callback: roi_changed_callback(callback)

        # prep the MIImageView to display in this context
        self.roi_view.ui.roiBtn.hide()
        self.roi_view.ui.histogram.hide()
        self.roi_view.ui.menuBtn.hide()
        self.roi_view.ui.roiPlot.hide()
        self.roi_view.set_roi(roi_values if roi_values and len(roi_values) == 4 else self.roi_view.default_roi())
        self.roi_view.roi.show()
        self.roi_view.ui.gridLayout.setRowStretch(1, 5)
        self.roi_view.ui.gridLayout.setRowStretch(0, 95)
        self.roi_view.button_stack_right.hide()
        self.roi_view.button_stack_left.hide()

        button = QPushButton("OK", self)
        button.clicked.connect(lambda: self.close())
        self.roi_view.ui.gridLayout.addWidget(button)

        self.roi_view.roiChanged()

    def toggle_average_images(self) -> None:
        self.roi_view.setImage(self.main_image if self.roi_view_averaged else self.averaged_image)
        self.roi_view_averaged = not self.roi_view_averaged
        self.roi_view.roi.show()
        self.roi_view.ui.roiPlot.hide()
