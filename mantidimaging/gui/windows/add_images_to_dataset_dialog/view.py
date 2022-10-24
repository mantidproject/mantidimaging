# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QComboBox

from mantidimaging.gui.mvp_base import BaseDialogView


class AddImagesToDatasetDialog(BaseDialogView):
    imageTypeComboBox: QComboBox

    def __init__(self, parent, strict_dataset: bool):
        super().__init__(parent, 'gui/ui/add_to_dataset.ui')

        self.imageTypeComboBox.setEnabled(strict_dataset)
