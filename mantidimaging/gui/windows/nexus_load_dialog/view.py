# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QDialog

from mantidimaging.gui.utility import compile_ui
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter


class NexusLoadDialog(QDialog):
    def __init__(self, parent):
        super(NexusLoadDialog, self).__init__(parent)
        compile_ui("gui/ui/nexus_load_dialog.ui", self)

        self.parent_view = parent
        self.presenter = NexusLoadPresenter(self)
