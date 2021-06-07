# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from mantidimaging.gui.windows.nexus_load_dialog.view import NexusLoadDialog


class NexusLoadPresenter:
    def __init__(self, view: NexusLoadDialog):
        self.view = view
