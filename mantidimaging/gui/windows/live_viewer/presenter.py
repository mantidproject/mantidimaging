# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.live_viewer.model import LiveViewerWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover

logger = getLogger(__name__)


class LiveViewerWindowPresenter(BasePresenter):
    """
    The presenter for the Live Viewer window.

    This presenter is responsible for handling user interaction with the view and
    updating the model and view accordingly to look after the state of the window.
    """
    view: LiveViewerWindowView
    model: LiveViewerWindowModel

    def __init__(self, view: LiveViewerWindowView, main_window: MainWindowView):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = LiveViewerWindowModel(self)
