# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock
from PyQt5.QtCore import QUrl

from mantidimaging.core.net.help_pages import open_user_operation_docs, open_help_webpage, SECTION_USER_GUIDE


class HelpPagesTest(unittest.TestCase):
    @mock.patch("mantidimaging.core.net.help_pages.open_help_webpage")
    def test_open_user_operation_docs(self, open_func: mock.Mock):
        open_user_operation_docs("Crop Coordinates")
        open_func.assert_called_with(SECTION_USER_GUIDE, "operations/index", "crop-coordinates")

    @mock.patch("mantidimaging.core.net.help_pages.QDesktopServices.openUrl")
    def test_open_help_webpage(self, open_url: mock.Mock):
        open_help_webpage(SECTION_USER_GUIDE, "reconstructions/center_of_rotation")
        expected = QUrl(
            "https://mantidproject.github.io/mantidimaging/user_guide/reconstructions/center_of_rotation.html")
        open_url.assert_called_with(expected)

    @mock.patch("mantidimaging.core.net.help_pages.QDesktopServices.openUrl")
    def test_open_help_webpage_with_section(self, open_url: mock.Mock):
        open_help_webpage(SECTION_USER_GUIDE, "operations/index", "crop-coordinates")
        expected = QUrl(
            "https://mantidproject.github.io/mantidimaging/user_guide/operations/index.html#crop-coordinates")
        open_url.assert_called_with(expected)

    @mock.patch("mantidimaging.core.net.help_pages.QDesktopServices.openUrl")
    def test_open_help_webpage_error(self, open_url: mock.Mock):
        open_url.return_value = False
        self.assertRaises(RuntimeError, open_help_webpage, SECTION_USER_GUIDE, "reconstructions/center_of_rotation")
