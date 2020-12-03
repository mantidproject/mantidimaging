# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock
import tempfile

from PyQt5.QtCore import QSettings, QCoreApplication

from mantidimaging.gui.windows.welcome_screen.presenter import WelcomeScreenPresenter
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class WelcomeScreenPresenterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        QCoreApplication.setApplicationName("test1")
        QCoreApplication.setOrganizationName("org1")
        cls.settings_dir = tempfile.TemporaryDirectory()
        QSettings.setDefaultFormat(QSettings.IniFormat)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, cls.settings_dir.name)

    def setUp(self):
        self.v = mock.MagicMock()
        self.v.get_show_at_start = mock.Mock(return_value=True)
        self.p = WelcomeScreenPresenter(None, view=self.v)

    def tearDown(self):
        settings = QSettings()
        settings.clear()

    def test_init(self):
        self.v.set_version_label.assert_called_once()

    def test_show_at_start_init(self):
        self.assertTrue(WelcomeScreenPresenter.show_at_start_enabled())

        settings = QSettings()
        settings.setValue("welcome_screen/show_at_start", True)
        self.assertTrue(WelcomeScreenPresenter.show_at_start_enabled())

        settings.setValue("welcome_screen/show_at_start", False)
        self.assertFalse(WelcomeScreenPresenter.show_at_start_enabled())

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


if __name__ == '__main__':
    unittest.main()
