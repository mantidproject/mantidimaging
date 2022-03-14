# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtTest import QTest

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY


class TestGuiSystemWindows(GuiSystemBase):
    def tearDown(self) -> None:
        self._close_image_stacks()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    def test_main_window_shows(self):
        self.assertTrue(self.main_window.isVisible())
        self.assertTrue(self.main_window.welcome_window.view.isVisible())
        QTest.qWait(SHOW_DELAY)
        self._close_welcome()
        self.assertFalse(self.main_window.welcome_window.view.isVisible())
        QTest.qWait(SHOW_DELAY)

    def test_loaded_data(self):
        self._close_welcome()
        self._load_data_set()

    def test_open_operations(self):
        self._close_welcome()
        self._load_data_set()

        self._open_operations()

        self.assertIsNotNone(self.main_window.filters)
        self.assertTrue(self.main_window.filters.isVisible())
        QTest.qWait(SHOW_DELAY)
        self.main_window.filters.close()
        QTest.qWait(SHOW_DELAY)

    def test_open_reconstruction(self):
        self._close_welcome()
        self._load_data_set()

        self._open_reconstruction()

        self.assertIsNotNone(self.main_window.recon)
        self.assertTrue(self.main_window.recon.isVisible())
        QTest.qWait(SHOW_DELAY)
        self._wait_until(lambda: len(self.main_window.recon.presenter.async_tracker) == 0)
        self.main_window.recon.close()
        QTest.qWait(SHOW_DELAY)
        self._close_image_stacks()
        QTest.qWait(SHOW_DELAY)
