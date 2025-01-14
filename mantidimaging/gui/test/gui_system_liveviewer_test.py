# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import mock

import numpy as np
from PyQt5.QtTest import QTest
from numpy.testing import assert_raises

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHORT_DELAY
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
        self.live_viewer_window.intensity_action.trigger()
        QTest.qWait(SHORT_DELAY)
        wait_until(lambda: not np.isnan(self.live_viewer_window.presenter.model.mean).any(), max_retry=600)
        self.assertFalse(np.isnan(self.live_viewer_window.presenter.model.mean).any())

    def test_roi_resized(self):
        self.live_viewer_window.intensity_action.trigger()
        QTest.qWait(SHORT_DELAY)
        wait_until(lambda: not np.isnan(self.live_viewer_window.presenter.model.mean).any(), max_retry=600)
        old_mean = self.live_viewer_window.presenter.model.mean
        roi = self.live_viewer_window.live_viewer.roi_object.roi
        handle_index = 0
        new_position = (10, 20)
        roi.movePoint(handle_index, new_position)
        QTest.qWait(SHORT_DELAY)
        assert_raises(AssertionError, np.testing.assert_array_equal, old_mean,
                      self.live_viewer_window.presenter.model.mean)
