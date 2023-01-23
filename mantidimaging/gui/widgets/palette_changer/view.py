# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtWidgets import QSpinBox, QComboBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter


class PaletteChangerView(BaseDialogView):

    numMaterialsSpinBox: QSpinBox
    algorithmComboBox: QComboBox
    colourMapComboBox: QComboBox

    def __init__(self, parent, main_hist, image, other_hists=None, recon_mode=False):
        super().__init__(parent, "gui/ui/palette_changer.ui")
        other_hists = [] if other_hists is None else other_hists
        self.presenter = PaletteChangerPresenter(self, other_hists, main_hist, image, recon_mode)
        self.accepted.connect(self.presenter.change_colour_palette)
        self.colourMapComboBox.setCurrentText("spectrum")

    @property
    def num_materials(self) -> int:
        return self.numMaterialsSpinBox.value()

    @property
    def algorithm(self) -> str:
        return self.algorithmComboBox.currentText()

    @property
    def colour_map(self) -> str:
        return self.colourMapComboBox.currentText()
