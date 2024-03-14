# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QGraphicsSceneMouseEvent
from pyqtgraph import PlotItem, InfiniteLine


class ZSlider(PlotItem):
    """
    A plot item to draw a z-axis slider mimicking the slider in PyQtGraph's ImageView

    This gives us flexibility to choose what happens when the user move through the z-axis. It can be combined with
    the one or more :py:class:`~mantidimaging.gui.widgets.mi_mini_image_view.view.MIMiniImageView`'s in a
    GraphicsLayoutWidget. It is used in the Operations window to choose the slice to preview a filter with,
    and in the Live Viewer scroll through images.

    Emits a :code:`valueChanged` signal when the user moves the slider
    """

    z_line: InfiniteLine
    valueChanged = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(40)
        self.hideAxis("left")
        self.setXRange(0, 1)
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()

        self.z_line = InfiniteLine(0, movable=True)
        self.z_line.setPen((255, 255, 0, 200))
        self.addItem(self.z_line)

        self.z_line.sigPositionChanged.connect(self.value_changed)

    def set_range(self, min: int, max: int) -> None:
        self.z_line.setValue(min)
        self.setXRange(min, max)
        self.z_line.setBounds([min, max])

    def set_value(self, value: int) -> None:
        self.z_line.setValue(value)

    def value_changed(self) -> None:
        self.valueChanged.emit(int(self.z_line.value()))

    def mousePressEvent(self, ev: QGraphicsSceneMouseEvent) -> None:
        """
        Adjusts built in behaviour to allow user to click anywhere on the line to jump there.
        """
        if ev.button() == Qt.MouseButton.LeftButton:
            x = round(self.vb.mapSceneToView(ev.scenePos()).x())
            self.set_value(x)
        super().mousePressEvent(ev)
