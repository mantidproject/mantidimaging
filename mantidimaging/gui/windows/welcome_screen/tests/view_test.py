# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

from PyQt5.QtWidgets import QLabel

from mantidimaging.gui.windows.welcome_screen.view import WelcomeScreenView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class WelcomeScreenViewTest(unittest.TestCase):

    def setUp(self):
        self.presenter = mock.MagicMock()
        self.view = WelcomeScreenView(None, self.presenter)

    def test_set_version_label(self):
        test_string = "test_string"
        self.view.set_version_label(test_string)
        self.assertEqual(self.view.version_label.text(), test_string)
        self.assertEqual(self.view.version_label.styleSheet(), "QLabel { font-size: 18px; margin-left: 5px; }")

    def test_add_issues(self):
        test_issues = "Test Issue Warning"
        self.view.add_issues(test_issues)
        self.assertEqual(self.view.issues_label.text(), test_issues)
        self.assertIn("color: red", self.view.issues_label.styleSheet())

    def test_banner_is_set_correctly(self):
        self.assertIsInstance(self.view.banner_label, QLabel)
        self.assertTrue(not self.view.banner_label.pixmap().isNull())
        self.assertTrue(self.view.banner_label.hasScaledContents())
        self.assertEqual(self.view.banner_label.minimumSize(), self.view.Banner_container.size())


if __name__ == '__main__':
    unittest.main()
