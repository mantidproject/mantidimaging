# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtWidgets import QSpinBox, QComboBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter


class PaletteChangerView(BaseDialogView):

    numMaterialsSpinBox: QSpinBox
    algorithmComboBox: QComboBox
    colourMapComboBox: QComboBox

    def __init__(self, parent, hists, recon_image):
        super(PaletteChangerView, self).__init__(parent, "gui/ui/palette_changer.ui")
        self.presenter = PaletteChangerPresenter(self, hists, recon_image)
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
