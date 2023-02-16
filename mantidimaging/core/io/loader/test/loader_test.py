# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from unittest import mock
from pathlib import Path

from mantidimaging.core.io import loader
from mantidimaging.core.io.loader.loader import create_loading_parameters_for_file_path, DEFAULT_PIXEL_DEPTH, \
    DEFAULT_PIXEL_SIZE, DEFAULT_IS_SINOGRAM, new_create_loading_parameters_for_file_path
from pyfakefs.fake_filesystem_unittest import TestCase

from mantidimaging.core.utility.data_containers import FILE_TYPES


class LoaderTest(TestCase):
    def setUp(self) -> None:
        self.setUpPyfakefs()

    def _files_equal(self, file1, file2):
        self.assertIsNotNone(file1)
        self.assertIsNotNone(file2)
        self.assertEqual(Path(file1).absolute(), Path(file2).absolute())

    def _file_list_count_equal(self, list1, list2):
        """Check that 2 lists of paths refer to the same files. Order independent"""
        self.assertCountEqual((Path(s).absolute() for s in list1), (Path(s).absolute() for s in list2))

    def test_raise_on_invalid_format(self):
        self.assertRaises(NotImplementedError, loader.load, "/some/path", file_names=["/somefile"], in_format='txt')

    @mock.patch("mantidimaging.core.io.loader.loader.load_log")
    @mock.patch("mantidimaging.core.io.loader.loader.read_in_file_information")
    def test_create_loading_parameters_for_file_path_new(self, _load_log, _read_in_file_information):
        output_directory = Path("/b")
        for filename in ["Tomo_log.txt", "Flat_After_log.txt", "Flat_Before_log.txt"]:
            self.fs.create_file(output_directory / filename)

        for stack_type in ["Flat_Before", "Flat_After", "Dark_Before", "Dark_After", "Tomo"]:
            for image_number in range(0, 5):
                filename = Path(output_directory / stack_type / f"{stack_type}_{image_number:04d}.tif")
                self.fs.create_file(filename)

        self.fs.create_file(output_directory / "180deg" / "180deg_0000.tif")

        lp = new_create_loading_parameters_for_file_path(output_directory)

        self.assertEqual(DEFAULT_PIXEL_DEPTH, lp.dtype)
        self.assertEqual(DEFAULT_PIXEL_SIZE, lp.pixel_size)
        self.assertEqual(DEFAULT_IS_SINOGRAM, lp.sinograms)

        sample = lp.image_stacks[FILE_TYPES.SAMPLE]
        self.assertIn(Path("/b/Tomo/Tomo_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))
        self._files_equal("/b/Tomo_log.txt", sample.log_file)

        sample = lp.image_stacks[FILE_TYPES.FLAT_BEFORE]
        self.assertIn(Path("/b/Flat_Before/Flat_Before_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))
        self._files_equal("/b/Flat_Before_log.txt", sample.log_file)

        sample = lp.image_stacks[FILE_TYPES.FLAT_AFTER]
        self.assertIn(Path("/b/Flat_After/Flat_After_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))
        self._files_equal("/b/Flat_After_log.txt", sample.log_file)

        sample = lp.image_stacks[FILE_TYPES.DARK_BEFORE]
        self.assertIn(Path("/b/Dark_Before/Dark_Before_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))

        sample = lp.image_stacks[FILE_TYPES.DARK_AFTER]
        self.assertIn(Path("/b/Dark_After/Dark_After_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))

        sample = lp.image_stacks[FILE_TYPES.PROJ_180]
        self.assertIn(Path("/b/180deg/180deg_0000.tif"), sample.file_group.all_files())
        self.assertEqual(1, len(list(sample.file_group.all_files())))

    @mock.patch("mantidimaging.core.io.loader.loader.load_log")
    @mock.patch("mantidimaging.core.io.loader.loader.read_in_file_information")
    def test_create_loading_parameters_for_file_path(self, _load_log, _read_in_file_information):
        output_directory = Path("/b")
        for filename in ["Tomo_log.txt", "Flat_After_log.txt", "Flat_Before_log.txt"]:
            self.fs.create_file(output_directory / filename)

        for stack_type in ["Flat_Before", "Flat_After", "Dark_Before", "Dark_After", "Tomo"]:
            for image_number in range(0, 5):
                filename = Path(output_directory / stack_type / f"{stack_type}_{image_number:04d}.tif")
                self.fs.create_file(filename)

        self.fs.create_file(output_directory / "180deg" / "180deg_000.tif")

        image_format = "tif"

        lp = create_loading_parameters_for_file_path(output_directory)

        self.assertEqual(DEFAULT_PIXEL_DEPTH, lp.dtype)
        self.assertEqual(DEFAULT_PIXEL_SIZE, lp.pixel_size)
        self.assertEqual(DEFAULT_IS_SINOGRAM, lp.sinograms)

        # Sample checking
        sample = lp.sample
        self.assertEqual(image_format, sample.format)
        self.assertEqual(None, sample.indices)
        self._files_equal("/b/Tomo", sample.input_path)
        self._files_equal("/b/Tomo_log.txt", sample.log_file)
        self._files_equal("/b/Tomo/Tomo", sample.prefix)

        # Flat before checking
        flat_before = lp.flat_before
        self.assertEqual(image_format, flat_before.format)
        self.assertEqual(None, flat_before.indices)
        self._files_equal("/b/Flat_Before_log.txt", flat_before.log_file)
        self._files_equal("/b/Flat_Before", flat_before.input_path)
        self._files_equal("/b/Flat_Before/Flat_Before", flat_before.prefix)

        # Flat after checking
        flat_after = lp.flat_after
        self.assertEqual(image_format, flat_after.format)
        self.assertEqual(None, flat_after.indices)
        self._files_equal("/b/Flat_After_log.txt", flat_after.log_file)
        self._files_equal("/b/Flat_After", flat_after.input_path)
        self._files_equal("/b/Flat_After/Flat_After", flat_after.prefix)

        # Dark before checking
        dark_before = lp.dark_before
        self.assertEqual(image_format, dark_before.format)
        self.assertEqual(None, dark_before.indices)
        self._files_equal("/b/Dark_Before", dark_before.input_path)
        self._files_equal("/b/Dark_Before/Dark_Before", dark_before.prefix)

        # Dark after checking
        dark_after = lp.dark_after
        self.assertEqual(image_format, dark_after.format)
        self.assertEqual(None, dark_after.indices)
        self._files_equal("/b/Dark_After", dark_after.input_path)
        self._files_equal("/b/Dark_After/Dark_After", dark_after.prefix)

        # 180 degree checking
        proj180 = lp.proj_180deg
        self.assertEqual(image_format, proj180.format)
        self.assertEqual(None, proj180.indices)
        self._files_equal("/b/180deg/180deg_000.tif", proj180.input_path)
        self.assertEqual(None, proj180.log_file)
        self._files_equal("/b/180deg/180deg", proj180.prefix)
