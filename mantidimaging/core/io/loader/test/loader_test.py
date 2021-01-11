# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
from unittest import mock

from mantidimaging.core.io import loader
from mantidimaging.core.io.loader import load_stack
from mantidimaging.core.io.loader.loader import create_loading_parameters_for_file_path, DEFAULT_PIXEL_DEPTH, \
    DEFAULT_PIXEL_SIZE, DEFAULT_IS_SINOGRAM
from mantidimaging.test_helpers import FileOutputtingTestCase


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

        # Flat
        os.mkdir(os.path.join(self.output_directory, "Flat_Before"))
        os.mkdir(os.path.join(self.output_directory, "Flat_After"))
        for ii in range(0, 10):
            with open(os.path.join(self.output_directory, "Flat_Before", f"Flat_Before_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

            with open(os.path.join(self.output_directory, "Flat_After", f"Flat_After_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

        # Dark
        os.mkdir(os.path.join(self.output_directory, "Dark_Before"))
        os.mkdir(os.path.join(self.output_directory, "Dark_After"))
        for ii in range(0, 10):
            with open(os.path.join(self.output_directory, "Dark_Before", f"Dark_Before_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

            with open(os.path.join(self.output_directory, "Dark_After", f"Dark_After_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

        # Tomo
        os.mkdir(os.path.join(self.output_directory, "Tomo"))
        for ii in range(0, 200):
            with open(os.path.join(self.output_directory, "Tomo", f"Tomo_00{ii}.tif"), "wb") as f:
                f.write(b"\0")

        # 180 degree projection
        os.mkdir(os.path.join(self.output_directory, "180deg"))
        with open(os.path.join(self.output_directory, "180deg", "180deg_000.tif"), "wb") as f:
            f.write(b"\0")

    @mock.patch("mantidimaging.core.io.loader.loader.find_and_verify_sample_log")
    @mock.patch("mantidimaging.core.io.loader.loader.read_in_file_information")
    def test_create_loading_parameters_for_file_path(self, mock_read_in_file_information,
                                                     mock_find_and_verify_sample_log):
        self._create_test_sample()
        tomo_dir = os.path.join(self.output_directory, "Tomo")
        tomo_prefix = os.path.join(tomo_dir, "Tomo")
        image_format = ".tif"
        flat_before_dir = os.path.join(self.output_directory, "Flat_Before")
        flat_before_prefix = os.path.join(flat_before_dir, "Flat_Before")
        flat_before_log = os.path.join(self.output_directory, "Flat_Before_log.txt")

        flat_after_dir = os.path.join(self.output_directory, "Flat_After")
        flat_after_prefix = os.path.join(flat_after_dir, "Flat_After")
        flat_after_log = os.path.join(self.output_directory, "Flat_After_log.txt")

        dark_before_dir = os.path.join(self.output_directory, "Dark_Before")
        dark_before_prefix = os.path.join(dark_before_dir, "Dark_Before")

        dark_after_dir = os.path.join(self.output_directory, "Dark_After")
        dark_after_prefix = os.path.join(dark_after_dir, "Dark_After")

        proj_180_file_prefix = os.path.join(self.output_directory, "180deg", "180deg")
        proj_180_file = proj_180_file_prefix + "_000.tif"

        lp = create_loading_parameters_for_file_path(self.output_directory)

        mock_read_in_file_information.assert_called_once_with(tomo_dir, in_prefix=tomo_prefix, in_format=image_format)
        mock_find_and_verify_sample_log.assert_called_once_with(tomo_dir,
                                                                mock_read_in_file_information.return_value.filenames)
        self.assertEqual(DEFAULT_PIXEL_DEPTH, lp.dtype)
        self.assertEqual(DEFAULT_PIXEL_SIZE, lp.pixel_size)
        self.assertEqual(DEFAULT_IS_SINOGRAM, lp.sinograms)

        # Sample checking
        sample = lp.sample
        self.assertEqual(image_format, sample.format)
        self.assertEqual(None, sample.indices)
        self.assertEqual(tomo_dir, sample.input_path)
        self.assertEqual(mock_find_and_verify_sample_log.return_value, sample.log_file)
        self.assertEqual(tomo_prefix, sample.prefix)

        # Flat before checking
        flat_before = lp.flat_before
        self.assertEqual(image_format, flat_before.format)
        self.assertEqual(None, flat_before.indices)
        self.assertEqual(flat_before_log, flat_before.log_file)
        self.assertEqual(flat_before_dir, flat_before.input_path)
        self.assertEqual(flat_before_prefix, flat_before.prefix)

        # Flat after checking
        flat_after = lp.flat_after
        self.assertEqual(image_format, flat_after.format)
        self.assertEqual(None, flat_after.indices)
        self.assertEqual(flat_after_log, flat_after.log_file)
        self.assertEqual(flat_after_dir, flat_after.input_path)
        self.assertEqual(flat_after_prefix, flat_after.prefix)

        # Dark before checking
        dark_before = lp.dark_before
        self.assertEqual(image_format, dark_before.format)
        self.assertEqual(None, dark_before.indices)
        self.assertEqual(dark_before_dir, dark_before.input_path)
        self.assertEqual(dark_before_prefix, dark_before.prefix)

        # Dark after checking
        dark_after = lp.dark_after
        self.assertEqual(image_format, dark_after.format)
        self.assertEqual(None, dark_after.indices)
        self.assertEqual(dark_after_dir, dark_after.input_path)
        self.assertEqual(dark_after_prefix, dark_after.prefix)

        # 180 degree checking
        proj180 = lp.proj_180deg
        self.assertEqual(image_format, proj180.format)
        self.assertEqual(None, proj180.indices)
        self.assertEqual(proj_180_file, proj180.input_path)
        self.assertEqual(None, proj180.log_file)
        self.assertEqual(proj_180_file_prefix, proj180.prefix)
