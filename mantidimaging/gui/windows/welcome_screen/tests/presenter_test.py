# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

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
        self.v = mock.MagicMock()
        self.v.get_show_at_start = mock.Mock(return_value=True)
        with mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.WelcomeScreenPresenter.do_set_up"):
            self.p = WelcomeScreenPresenter(None, view=self.v)

    def tearDown(self):
        settings = QSettings()
        settings.clear()

    def test_init(self):
        self.p.do_set_up()
        self.v.set_version_label.assert_called_once()

    def test_show_at_start_init(self):
        self.assertTrue(WelcomeScreenPresenter.show_at_start_enabled())

        settings = QSettings()
        settings.setValue("welcome_screen/show_at_start", True)
        self.assertTrue(WelcomeScreenPresenter.show_at_start_enabled())

        settings.setValue("welcome_screen/show_at_start", False)
        self.assertFalse(WelcomeScreenPresenter.show_at_start_enabled())

    def test_show_today(self):
        settings = QSettings()
        settings.setValue("welcome_screen/show_at_start", True)
        settings.setValue("welcome_screen/last_run_version", "")
        self.assertTrue(WelcomeScreenPresenter.show_today())

        settings.setValue("welcome_screen/show_at_start", False)
        settings.setValue("welcome_screen/last_run_version", "")
        self.assertTrue(WelcomeScreenPresenter.show_today())

        settings.setValue("welcome_screen/show_at_start", False)
        settings.setValue("welcome_screen/last_run_version", "0.0.0_1")
        self.assertTrue(WelcomeScreenPresenter.show_today())

        settings.setValue("welcome_screen/show_at_start", False)
        settings.setValue("welcome_screen/last_run_version", "1.0.0_1")
        self.assertFalse(WelcomeScreenPresenter.show_today())

    def test_show_at_start_change(self):
        settings = QSettings()

        self.v.get_show_at_start = mock.Mock(return_value=True)
        self.p.show_at_start_changed()
        self.assertTrue(settings.value("welcome_screen/show_at_start", type=bool))

        self.v.get_show_at_start = mock.Mock(return_value=True)
        self.p.show_at_start_changed()
        self.assertTrue(settings.value("welcome_screen/show_at_start", type=bool))

    def test_set_up_show_at_start(self):
        self.p.set_up_show_at_start()
        self.v.set_show_at_start.assert_called_with(True)

    def test_add_link(self):
        link_name, url = "test", "https://example.com/"
        label = '<a href="https://example.com/">test</a>'

        self.v.reset_mock()
        self.p.link_count = 0
        self.p.add_link(link_name, url)
        self.p.add_link(link_name, url)
        self.v.add_link.assert_has_calls([mock.call(label, 0), mock.call(label, 1)])

    def test_show(self):
        self.p.show()
        self.v.show.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_check_issues(self, cuda_check_mock, versions_mock):
        issues = []
        log_msgs = []

        for i in range(1, 3):
            num_string = str(i)
            issues.append("issue" + num_string)
            log_msgs.append("msg" + num_string)

        versions_mock.needs_update.return_value = True
        versions_mock.conda_update_message.return_value = (issues[0], log_msgs[0])
        cuda_check_mock.not_found_message.return_value = (issues[1], log_msgs[1])
        cuda_check_mock.CudaChecker.return_value.cuda_is_present.return_value = False

        with self.assertLogs(WelcomeScreenPresenter.__module__, level='INFO') as presenter_log:
            self.p.check_issues()

        self.v.add_issues.assert_called_once_with("\n".join(issues))
        for i in range(2):
            self.assertIn(log_msgs[i], presenter_log.output[i])

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_no_issues_added(self, cuda_check_mock, versions_mock):
        versions_mock.needs_update.return_value = False
        cuda_check_mock.CudaChecker.return_value.cuda_is_present.return_value = True

        self.p.check_issues()
        self.v.add_issues.assert_not_called()


if __name__ == '__main__':
    unittest.main()
