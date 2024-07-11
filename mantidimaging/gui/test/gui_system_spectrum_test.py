# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import mock

from PyQt5.QtTest import QTest

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY
from mantidimaging.test_helpers.qt_test_helpers import wait_until


class TestGuiSpectrumViewer(GuiSystemBase):

    def setUp(self) -> None:
        patcher_show_error_dialog = mock.patch(
            "mantidimaging.gui.windows.spectrum_viewer.view.SpectrumViewerWindowView.show_error_dialog")
        self.mock_show_error_dialog = patcher_show_error_dialog.start()
        self.addCleanup(patcher_show_error_dialog.stop)
        super().setUp()
        self._close_welcome()
        self._load_data_set()

        self._open_spectrum_viewer()
        assert self.main_window.spectrum_viewer is not None
        self.spectrum_window = self.main_window.spectrum_viewer

        self.assertTrue(self.spectrum_window.isVisible())

        wait_until(lambda: self.spectrum_window.presenter.model._stack is not None, max_retry=600)

    def tearDown(self) -> None:
        self._close_image_stacks()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    def test_spectrum_window_opens_with_data(self):
        QTest.qWait(SHOW_DELAY * 5)
