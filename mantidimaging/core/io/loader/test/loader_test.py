# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import unittest
from unittest import mock

from mantidimaging.core.io.loader import load_stack
from mantidimaging.core.io import loader
from test_helpers import FileOutputtingTestCase


class LoaderTest(FileOutputtingTestCase):
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

    def _create_test_sample(self):
        # Logs
        with open(os.path.join(self.output_directory, "Tomo_log.txt"), "w") as f:
            f.write("log")
        with open(os.path.join(self.output_directory, "Flat_After_log.txt"), "w") as f:
            f.write("log")
        with open(os.path.join(self.output_directory, "Flat_Before_log.txt"), "w") as f:
            f.write("log")
        with open(os.path.join(self.output_directory, "180deg_log.txt"), "w") as f:
            f.write("log")

        # Flat
        for ii in range(0, 10):
            with open(os.path.join(self.output_directory, "Flat_Before", f"Flat_Before_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

            with open(os.path.join(self.output_directory, "Flat_After", f"Flat_After_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

        # Dark
        for ii in range(0, 10):
            with open(os.path.join(self.output_directory, "Dark_Before", f"Dark_Before_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

            with open(os.path.join(self.output_directory, "Dark_After", f"Dark_After_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

        # Tomo
        for ii in range (0, 200):
            with open(os.path.join(self.output_directory, "Tomo", f"Tomo_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

        # 180 degree projection
        with open(os.path.join(self.output_directory, "180deg", "180deg_000.tif"), "wb") as f:
            f.write(b"\0")

    def test_create_loading_parameters_for_file_path(self):
        self._create_test_sample()