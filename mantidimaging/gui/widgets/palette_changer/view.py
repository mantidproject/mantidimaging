# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtWidgets import QSpinBox, QComboBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter


class PaletteChangerView(BaseDialogView):

    numMaterialsSpinBox: QSpinBox
    algorithmComboBox: QComboBox
    colourMapComboBox: QComboBox

    def __init__(self, parent, hists, projection_image_view):
        super(PaletteChangerView, self).__init__(parent, "gui/ui/palette_changer.ui")
        self.presenter = PaletteChangerPresenter(self, hists, projection_image_view)
        self.accepted.connect(self.presenter.change_colour_palette)
        # self.algorithmComboBox.currentTextChanged.connect(self.set_spin_box_enabled)

    @property
    def num_materials(self) -> int:
        return self.numMaterialsSpinBox.value()

    @property
    def algorithm(self) -> str:
        return self.algorithmComboBox.currentText()

    @property
    def colour_map(self) -> str:
        return self.colourMapComboBox.currentText()

    def set_spin_box_enabled(self):
        """
        Disable the number of materials spin box when the Otsu algorithm has been selected.
        """
        self.numMaterialsSpinBox.setEnabled(self.algorithmComboBox.currentText() == "Jenks")
