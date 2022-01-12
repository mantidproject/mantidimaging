# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY, SHORT_DELAY
from mantidimaging.gui.windows.recon.view import ReconstructWindowView
from mantidimaging.gui.dialogs.cor_inspection.view import CORInspectionDialogView


class TestGuiSystemReconstruction(GuiSystemBase):
    def setUp(self) -> None:
        super().setUp()
        self._close_welcome()
        self._load_data_set()

        self._open_reconstruction()
        self.assertIsNotNone(self.main_window.recon)
        assert isinstance(self.main_window.recon, ReconstructWindowView)  # for yapf
        self.assertTrue(self.main_window.recon.isVisible())
        self.recon_window = self.main_window.recon
        self._wait_until(lambda: self.recon_window.presenter.model.stack is not None, max_retry=600)

    def tearDown(self) -> None:
        self.recon_window.close()
        assert isinstance(self.main_window.recon, ReconstructWindowView)
        self.assertFalse(self.main_window.recon.isVisible())
        self._close_stack_tabs()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    def test_correlate(self):
        for _ in range(5):
            QTest.mouseClick(self.recon_window.correlateBtn, Qt.MouseButton.LeftButton)

            QTest.qWait(SHORT_DELAY)
            self._wait_until(lambda: self.recon_window.correlateBtn.isEnabled())

    def test_minimise(self):
        for i in range(2, 6):
            QTimer.singleShot(SHORT_DELAY, lambda: self._click_InputDialog(set_int=i))
            QTest.mouseClick(self.recon_window.minimiseBtn, Qt.MouseButton.LeftButton)

            QTest.qWait(SHORT_DELAY)
            self._wait_until(lambda: self.recon_window.minimiseBtn.isEnabled(), max_retry=200)
            QTest.qWait(SHORT_DELAY)

    @classmethod
    def _click_cor_inspect(cls):
        cls._wait_for_widget_visible(CORInspectionDialogView)
        for widget in cls.app.topLevelWidgets():
            if isinstance(widget, CORInspectionDialogView):
                QTest.qWait(SHORT_DELAY)
                QTest.mouseClick(widget.finishButton, Qt.MouseButton.LeftButton)

    def test_refine(self):
        QTimer.singleShot(SHORT_DELAY, lambda: self._click_InputDialog(set_int=4))
        QTest.mouseClick(self.recon_window.minimiseBtn, Qt.MouseButton.LeftButton)
        self._wait_until(lambda: self.recon_window.minimiseBtn.isEnabled(), max_retry=200)

        for _ in range(5):
            QTimer.singleShot(SHORT_DELAY, lambda: self._click_cor_inspect())
            QTest.mouseClick(self.recon_window.refineCorBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY * 2)

        QTest.qWait(SHOW_DELAY)

    def test_refine_stress(self):
        for i in range(5):
            print(f"test_refine_stress iteration {i}")
            QTest.mouseClick(self.recon_window.correlateBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY)
            self._wait_until(lambda: self.recon_window.correlateBtn.isEnabled())

            QTimer.singleShot(SHORT_DELAY, lambda: self._click_InputDialog(set_int=3))
            QTest.mouseClick(self.recon_window.minimiseBtn, Qt.MouseButton.LeftButton)
            self._wait_until(lambda: self.recon_window.minimiseBtn.isEnabled(), max_retry=200)

            QTimer.singleShot(SHORT_DELAY, lambda: self._click_cor_inspect())
            QTest.mouseClick(self.recon_window.refineCorBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY * 2)

        QTest.qWait(SHOW_DELAY)
