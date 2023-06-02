# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from unittest import mock

from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY, SHORT_DELAY
from mantidimaging.gui.windows.recon.view import ReconstructWindowView
from mantidimaging.gui.dialogs.cor_inspection.view import CORInspectionDialogView
from mantidimaging.test_helpers.qt_test_helpers import wait_until
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool


@start_multiprocessing_pool
class TestGuiSystemReconstruction(GuiSystemBase):

    def setUp(self) -> None:
        patcher_show_error_dialog = mock.patch(
            "mantidimaging.gui.windows.recon.view.ReconstructWindowView.show_error_dialog")
        self.mock_show_error_dialog = patcher_show_error_dialog.start()
        self.addCleanup(patcher_show_error_dialog.stop)
        super().setUp()
        self._close_welcome()
        self._load_data_set()

        self._open_reconstruction()
        self.assertIsNotNone(self.main_window.recon)
        assert isinstance(self.main_window.recon, ReconstructWindowView)  # for yapf
        self.assertTrue(self.main_window.recon.isVisible())
        self.recon_window = self.main_window.recon
        wait_until(lambda: self.recon_window.presenter.model.images is not None, max_retry=600)

    def tearDown(self) -> None:
        wait_until(lambda: len(self.recon_window.presenter.async_tracker) == 0)
        self.recon_window.close()
        assert isinstance(self.main_window.recon, ReconstructWindowView)
        self.assertFalse(self.main_window.recon.isVisible())
        self._close_image_stacks()
        self.mock_show_error_dialog.assert_not_called()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    def test_correlate(self):
        for _ in range(5):
            QTest.mouseClick(self.recon_window.correlateBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY)
            wait_until(lambda: self.recon_window.correlateBtn.isEnabled())
            wait_until(lambda: len(self.recon_window.presenter.async_tracker) == 0)

    def test_minimise(self):
        for i in range(2, 6):
            QTimer.singleShot(SHORT_DELAY, lambda i=i: self._click_InputDialog(set_int=i))
            QTest.mouseClick(self.recon_window.minimiseBtn, Qt.MouseButton.LeftButton)

            QTest.qWait(SHORT_DELAY)
            wait_until(lambda: self.recon_window.minimiseBtn.isEnabled(), max_retry=500)
            wait_until(lambda: len(self.recon_window.presenter.async_tracker) == 0)
            QTest.qWait(SHORT_DELAY)

    @classmethod
    def _click_cor_inspect(cls):
        """
        Needs to be queued with QTimer.singleShot before triggering the message box
        Will raise a RuntimeError if a CORInspectionDialogView is not found
        """
        cls._wait_for_widget_visible(CORInspectionDialogView)
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, CORInspectionDialogView):
                QTest.qWait(SHORT_DELAY)
                QTest.mouseClick(widget.finishButton, Qt.MouseButton.LeftButton)
                return
        raise RuntimeError("_click_InputDialog did not find CORInspectionDialogView")

    def test_refine(self):
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_InputDialog(set_int=4))
        QTest.mouseClick(self.recon_window.minimiseBtn, Qt.MouseButton.LeftButton)
        wait_until(lambda: self.recon_window.minimiseBtn.isEnabled(), max_retry=200)

        for _ in range(5):
            QTimer.singleShot(SHORT_DELAY, lambda: self._click_cor_inspect())
            QTest.mouseClick(self.recon_window.refineCorBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY * 2)
            wait_until(lambda: len(self.recon_window.presenter.async_tracker) == 0)

        QTest.qWait(SHOW_DELAY)

    def test_refine_stress(self):
        for i in range(5):
            print(f"test_refine_stress iteration {i}")
            QTest.mouseClick(self.recon_window.correlateBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY)
            wait_until(lambda: self.recon_window.correlateBtn.isEnabled())

            QTimer.singleShot(SHORT_DELAY, lambda: self._click_InputDialog(set_int=3))
            QTest.mouseClick(self.recon_window.minimiseBtn, Qt.MouseButton.LeftButton)
            wait_until(lambda: self.recon_window.minimiseBtn.isEnabled(), max_retry=200)

            QTimer.singleShot(SHORT_DELAY, lambda: self._click_cor_inspect())
            QTest.mouseClick(self.recon_window.refineCorBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY * 2)
            wait_until(lambda: len(self.recon_window.presenter.async_tracker) == 0)

        QTest.qWait(SHOW_DELAY)

    @mock.patch("mantidimaging.gui.windows.recon.presenter.ReconstructWindowPresenter.do_preview_reconstruct_slice")
    def test_selecting_auto_update_triggers_preview(self, mock_do_preview_reconstruct_slice):
        self.recon_window.previewAutoUpdate.setCheckState(Qt.CheckState.Unchecked)

        QTest.mouseClick(self.recon_window.previewAutoUpdate, Qt.MouseButton.LeftButton)
        wait_until(lambda: mock_do_preview_reconstruct_slice.call_count == 1)

    @mock.patch("mantidimaging.gui.windows.recon.presenter.ReconstructWindowPresenter._get_reconstruct_slice")
    def test_clicking_update_now_btn_triggers_preview(self, mock_get_reconstruct_slice):
        self.recon_window.previewAutoUpdate.setCheckState(Qt.CheckState.Unchecked)

        QTest.mouseClick(self.recon_window.updatePreviewButton, Qt.MouseButton.LeftButton)
        wait_until(lambda: mock_get_reconstruct_slice.call_count == 1)
