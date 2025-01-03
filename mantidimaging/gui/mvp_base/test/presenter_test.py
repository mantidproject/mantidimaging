# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from unittest import mock
from testfixtures import LogCapture

from mantidimaging.gui.mvp_base import BaseDialogView, BaseMainWindowView, BasePresenter


class MainWindowPresenterTest(unittest.TestCase):

    def test_default_notify_method_raises_exception(self):
        view = mock.create_autospec(BaseMainWindowView, instance=True)
        presenter = BasePresenter(view)

        with self.assertRaises(NotImplementedError):
            presenter.notify(0)

    def test_show_error_message_forwarded_to_main_window_view(self):
        view = mock.create_autospec(BaseMainWindowView, instance=True)
        presenter = BasePresenter(view)

        presenter.show_error("test message", traceback="")
        view.show_error_dialog.assert_called_once_with("test message")

    def test_show_error_message_forwarded_to_dialog_view(self):
        view = mock.create_autospec(BaseDialogView, instance=True)
        presenter = BasePresenter(view)

        presenter.show_error("test message", traceback="")
        view.show_error_dialog.assert_called_once_with("test message")

    def test_bad_view_causes_errors_to_be_logged(self):

        class V:
            pass

        view = V()
        presenter = BasePresenter(view)

        with LogCapture() as lc:
            presenter.show_error("test message", traceback="logged traceback")

        lc.check(('mantidimaging.gui.mvp_base.presenter', 'ERROR', 'Presenter error: test message\nlogged traceback'))


if __name__ == '__main__':
    unittest.main()
