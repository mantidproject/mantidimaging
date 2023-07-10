# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowPresenter


class LiveViewerWindowModel:
    """
    The model for the spectrum viewer window.
    """

    def __init__(self, presenter: 'LiveViewerWindowPresenter'):
        self.presenter = presenter
