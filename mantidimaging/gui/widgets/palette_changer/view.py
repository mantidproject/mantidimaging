# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import List

from PyQt5.QtWidgets import QSpinBox, QComboBox
from pyqtgraph.graphicsItems import HistogramLUTItem

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter


class PaletteChangerView(BaseDialogView):

    numMaterialsSpinBox: QSpinBox
    algorithmComboBox: QComboBox
    colourMapComboBox: QComboBox

    def __init__(self, parent, hists):
        super(PaletteChangerView, self).__init__(parent, "gui/ui/palette_changer.ui")
        self.presenter = PaletteChangerPresenter(self, hists)
        self.accepted.connect(self.presenter.change_colour_palette)

    @property
    def num_materials(self) -> int:
        return self.numMaterialsSpinBox.value()

    @property
    def algorithm(self) -> str:
        return self.algorithmComboBox.currentText()

    @property
    def colour_map(self) -> str:
        return self.colourMapComboBox.currentText()
