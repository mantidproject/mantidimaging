# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path
from unittest import mock

import numpy as np

from mantidimaging.core.io.filenames import FilenameGroup
from mantidimaging.core.io.instrument_log import InstrumentLog
from mantidimaging.core.io.loader.loader import (DEFAULT_PIXEL_DEPTH, DEFAULT_PIXEL_SIZE, DEFAULT_IS_SINOGRAM,
                                                 create_loading_parameters_for_file_path, get_loader, load, _imread)

from mantidimaging.core.utility.data_containers import FILE_TYPES, ProjectionAngles
from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase


class LoaderTest(FakeFSTestCase):

    def test_raise_on_invalid_format(self):
        self.assertRaises(NotImplementedError, get_loader, in_format='txt')

    def test_WHEN_tif_file_invalid_THEN_filename_in_exception_message(self):
        filename = "/foo/bar/a.tif"
        self.fs.create_file(filename, contents="BADDATA")

        self.assertRaisesRegex(RuntimeError, filename, _imread, filename=filename)

    def test_create_loading_parameters_for_file_path(self):
        output_directory = Path("/b")
        for filename in ["Tomo_log.txt", "Flat_After_log.txt", "Flat_Before_log.txt"]:
            self.fs.create_file(output_directory / filename)

        for stack_type in ["Flat_Before", "Flat_After", "Dark_Before", "Dark_After", "Tomo"]:
            for image_number in range(0, 5):
                filename = Path(output_directory / stack_type / f"{stack_type}_{image_number:04d}.tif")
                self.fs.create_file(filename)

        self.fs.create_file(output_directory / "180deg" / "180deg_0000.tif")

        lp = create_loading_parameters_for_file_path(output_directory)

        self.assertEqual(DEFAULT_PIXEL_DEPTH, lp.dtype)
        self.assertEqual(DEFAULT_PIXEL_SIZE, lp.pixel_size)
        self.assertEqual(DEFAULT_IS_SINOGRAM, lp.sinograms)

        sample = lp.image_stacks[FILE_TYPES.SAMPLE]
        self._file_in_sequence(Path("/b/Tomo/Tomo_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))
        self._files_equal("/b/Tomo_log.txt", sample.log_file)

        sample = lp.image_stacks[FILE_TYPES.FLAT_BEFORE]
        self._file_in_sequence(Path("/b/Flat_Before/Flat_Before_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))
        self._files_equal("/b/Flat_Before_log.txt", sample.log_file)

        sample = lp.image_stacks[FILE_TYPES.FLAT_AFTER]
        self._file_in_sequence(Path("/b/Flat_After/Flat_After_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))
        self._files_equal("/b/Flat_After_log.txt", sample.log_file)

        sample = lp.image_stacks[FILE_TYPES.DARK_BEFORE]
        self._file_in_sequence(Path("/b/Dark_Before/Dark_Before_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))

        sample = lp.image_stacks[FILE_TYPES.DARK_AFTER]
        self._file_in_sequence(Path("/b/Dark_After/Dark_After_0000.tif"), sample.file_group.all_files())
        self.assertEqual(5, len(list(sample.file_group.all_files())))

        sample = lp.image_stacks[FILE_TYPES.PROJ_180]
        self._file_in_sequence(Path("/b/180deg/180deg_0000.tif"), sample.file_group.all_files())
        self.assertEqual(1, len(list(sample.file_group.all_files())))

    @mock.patch('mantidimaging.core.io.loader.loader.load_log')
    @mock.patch('mantidimaging.core.io.loader.loader.img_loader.execute')
    def test_load_with_golden_angles(self, mock_execute: mock.Mock, mock_load_log: mock.Mock):
        filenames = [Path(f"foo_{n}.tif") for n in range(20)]
        angles = np.array([(n * 137.507764) % 360 for n in range(20)])

        mock_filename_group = mock.create_autospec(FilenameGroup, metadata_path=None)
        mock_filename_group.all_files.return_value = filenames
        mock_filename_group.first_file.return_value = filenames[0]

        mock_log_data = mock.create_autospec(InstrumentLog)
        mock_log_data.has_projection_angles.return_value = True
        mock_log_data.projection_angles.return_value = ProjectionAngles(np.deg2rad(angles))

        mock_load_log.return_value = mock_log_data

        load(mock_filename_group, log_file=Path())

        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        reordered_filenames = call_args[0][1]

        self._file_list_count_equal(filenames, reordered_filenames)
        self.assertListEqual(['foo_0.tif', 'foo_8.tif', 'foo_16.tif', 'foo_3.tif', 'foo_11.tif'],
                             reordered_filenames[:5])
