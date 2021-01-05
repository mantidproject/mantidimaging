# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.core.io.loader import load_stack
from mantidimaging.core.io import loader


class LoaderTest(unittest.TestCase):
    def test_raise_on_invalid_format(self):
        self.assertRaises(ValueError, loader.load, "/some/path", file_names=["/somefile"], in_format='txt')

    @mock.patch("mantidimaging.core.io.loader.loader.load")
    @mock.patch("mantidimaging.core.io.loader.loader.get_file_names")
    def test_load_stack(self, get_file_names_mock: mock.Mock, load_mock: mock.Mock):
        file_names = mock.Mock()
        progress = mock.Mock()
        file_path = "/path/to/file/that/is/fake.tif"
        get_file_names_mock.return_value = file_names

        load_stack(file_path, progress)

        load_mock.assert_called_once_with(file_names=file_names, progress=progress)
        get_file_names_mock.assert_called_once_with(path="/path/to/file/that/is",
                                                    img_format="tif",
                                                    prefix="/path/to/file/that/is/fake.ti")
