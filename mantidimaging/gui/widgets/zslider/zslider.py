# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QGraphicsSceneMouseEvent
from pyqtgraph import PlotItem, InfiniteLine


class ZSlider(PlotItem):
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

    def mousePressEvent(self, ev: 'QGraphicsSceneMouseEvent') -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            x = round(self.vb.mapSceneToView(ev.scenePos()).x())
            self.set_value(x)
        super().mousePressEvent(ev)
