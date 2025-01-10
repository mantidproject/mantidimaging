# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import mock

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QColor

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY, SHORT_DELAY
from mantidimaging.test_helpers.qt_test_helpers import wait_until


class TestGuiLiveViewer(GuiSystemBase):

    def setUp(self) -> None:
        patcher_show_error_dialog = mock.patch(
            "mantidimaging.gui.windows.spectrum_viewer.view.SpectrumViewerWindowView.show_error_dialog")
        self.mock_show_error_dialog = patcher_show_error_dialog.start()
        self.addCleanup(patcher_show_error_dialog.stop)
        super().setUp()
        self._close_welcome()

        self._open_live_viewer()
        assert self.main_window.live_viewer_list[-1] is not None
        self.live_viewer_window = self.main_window.live_viewer_list[-1]
        print(f"{self.live_viewer_window=}")

        self.assertTrue(self.live_viewer_window.isVisible())
        QTest.qWait(SHORT_DELAY)

    def tearDown(self) -> None:
        self._close_image_stacks()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    def test_open_intensity_profile(self):
        self.live_viewer_window.spectrum_action.trigger()
        QTest.qWait(SHORT_DELAY)
        wait_until(lambda: self.live_viewer_window.presenter.model.mean is not np.empty(0), max_retry=600)
        self.assertFalse(np.isnan(self.live_viewer_window.presenter.model.mean).any())
