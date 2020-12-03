# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.gui.windows.welcome_screen.view import WelcomeScreenView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class WelcomeScreenViewTest(unittest.TestCase):
    def setUp(self):
        self.p = mock.MagicMock()
        self.v = WelcomeScreenView(None, self.p)

    def test_set_version_label(self):
        test_string = "test_string"
        self.v.set_version_label(test_string)
        self.assertEqual(self.v.version_label.text(), test_string)


if __name__ == '__main__':
    unittest.main()
