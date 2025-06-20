# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock
import tempfile

from PyQt5.QtCore import QSettings, QCoreApplication

from mantidimaging.gui.windows.welcome_screen.presenter import WelcomeScreenPresenter
from mantidimaging.test_helpers import start_qapplication, mock_versions


@mock_versions
@start_qapplication
class WelcomeScreenPresenterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        QCoreApplication.setApplicationName("test1")
        QCoreApplication.setOrganizationName("org1")
        cls.settings_dir = tempfile.TemporaryDirectory()
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, cls.settings_dir.name)

    def setUp(self):
        self.presenter = WelcomeScreenPresenter(parent=None)
        self.presenter.view = mock.MagicMock()

    def tearDown(self):
        settings = QSettings()
        settings.clear()

    def test_init(self):
        """
        Ensure do_set_up() calls set_version_label(...), set_up_links(), and check_issues().
        """
        self.presenter.do_set_up()
        self.presenter.view.set_version_label.assert_called_once()

    def test_add_link(self):
        """
        Test that add_link(...) calls view.add_link(...) with correct HTML and increments link_count.
        """
        self.presenter.link_count = 0

        # Suppose we add one link
        self.presenter.add_link("some <b>rich</b> text")
        self.presenter.view.add_link.assert_called_with("some <b>rich</b> text", 0)

        # Suppose we add another
        self.presenter.add_link("another link")
        calls = [
            mock.call("some <b>rich</b> text", 0),
            mock.call("another link", 1),
        ]
        self.presenter.view.add_link.assert_has_calls(calls)

    def test_show(self):
        """
        Ensure the presenter's show() method calls the view's show().
        """
        self.presenter.show()
        self.presenter.view.show.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_check_issues(self, cuda_check_mock, versions_mock):
        """
        If there's a needed update and no CUDA, we expect two lines of issues.
        """
        issues = []
        log_msgs = []

        issues.append("issue1")
        log_msgs.append("details1")

        issues.append("issue2")
        log_msgs.append("details2")

        versions_mock.needs_update.return_value = True
        versions_mock.conda_update_message.return_value = (issues[0], log_msgs[0])
        cuda_check_mock.CudaChecker.return_value.cuda_is_present.return_value = False
        cuda_check_mock.not_found_message.return_value = (issues[1], log_msgs[1])

        with self.assertLogs(self.presenter.__module__, level='INFO') as captured_logs:
            self.presenter.check_issues()

        self.presenter.view.add_issues.assert_called_once_with("\n".join(issues))
        self.assertIn(log_msgs[0], captured_logs.output[0])
        self.assertIn(log_msgs[1], captured_logs.output[1])

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_no_issues_added(self, cuda_check_mock, versions_mock):
        """
        If there's no needed update and CUDA is present, no issues are reported to the view.
        """
        versions_mock.needs_update.return_value = False
        cuda_check_mock.CudaChecker.return_value.cuda_is_present.return_value = True

        self.presenter.check_issues()
        self.presenter.view.add_issues.assert_not_called()


if __name__ == '__main__':
    unittest.main()
