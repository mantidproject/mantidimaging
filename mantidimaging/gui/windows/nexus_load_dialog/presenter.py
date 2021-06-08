# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.gui.windows.nexus_load_dialog.view import NexusLoadDialog  # pragma: no cover


class NexusLoadPresenter:
    view: 'NexusLoadDialog'

    def __init__(self, view: 'NexusLoadDialog'):
        self.view = view
