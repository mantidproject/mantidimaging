# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from mantidimaging.core.io.filenames import FilenameGroup
from mantidimaging.core.io.instrument_log import InstrumentLog, NoParserFound
from mantidimaging.gui.windows.image_load_dialog.field import Field
from mantidimaging.gui.windows.image_load_dialog.presenter import LoadPresenter
from mantidimaging.core.utility.data_containers import FILE_TYPES, Indices


class ImageLoadDialogPresenterTest(unittest.TestCase):

    def _files_equal(self, file1, file2):
        self.assertEqual(Path(file1).absolute(), Path(file2).absolute())

    def setUp(self):
        self.fields = {ft.fname: mock.create_autospec(Field, instance=True) for ft in FILE_TYPES}
        self.view = mock.MagicMock(fields=self.fields)
        self.view.sample = self.fields["Sample"]
        self.presenter = LoadPresenter(self.view)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.do_update_flat_or_dark")
    def test_do_update_field(self, mock_do_update_flat_or_dark):
        selected_file = "SelectedFile"
        self.view.select_file.return_value = selected_file
        ft = FILE_TYPES.FLAT_BEFORE
        field = mock.MagicMock(file_info=ft)

        self.presenter.do_update_field(field)

        self.view.select_file.assert_called_once_with(ft.fname, True)
        mock_do_update_flat_or_dark.assert_called_once_with(field, selected_file)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.do_update_flat_or_dark")
    def test_do_update_field_when_no_file_selected(self, mock_do_update_flat_or_dark):
        self.view.select_file.return_value = None
        ft = FILE_TYPES.FLAT_BEFORE
        field = mock.MagicMock(file_info=ft)

        self.presenter.do_update_field(field)

        self.view.select_file.assert_called_once_with(ft.fname, True)
        mock_do_update_flat_or_dark.assert_not_called()

    def test_update_field_with_filegroup_sample(self):
        mock_file_group = mock.create_autospec(FilenameGroup, instance=True)
        file_list = [mock.Mock()]
        file_log_path = mock.Mock()
        mock_file_group.all_files.return_value = file_list
        mock_file_group.log_path = file_log_path
        mock_file_group.shutter_count_path = file_log_path

        mock_field_path = mock.PropertyMock()
        type(self.fields["Sample Log"]).path = mock_field_path

        self.presenter.update_field_with_filegroup(FILE_TYPES.SAMPLE, mock_file_group)

        mock_file_group.find_all_files.assert_called_once_with()
        mock_file_group.find_log_file.assert_called_once_with()
        self.fields["Sample"].set_images.assert_called_once_with(file_list)
        mock_field_path.assert_called_once_with(file_log_path)

    def test_update_field_with_filegroup_dark_before(self):
        mock_file_group = mock.create_autospec(FilenameGroup, instance=True)
        file_list = [mock.Mock()]
        mock_file_group.all_files.return_value = file_list

        self.presenter.update_field_with_filegroup(FILE_TYPES.DARK_BEFORE, mock_file_group)

        mock_file_group.find_all_files.assert_called_once_with()
        mock_file_group.find_log_file.assert_not_called()
        self.fields["Dark Before"].set_images.assert_called_once_with(file_list)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.FilenameGroup")
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.read_image_dimensions")
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.update_field_with_filegroup")
    def test_do_update_sample_no_related(self, mock_update_field, mock_read_image_dimensions, mock_filename_group):
        selected_file = "/a/b/img_000.tif"
        mock_read_image_dimensions.return_value = [10, 11]
        mock_sample_fg = mock.create_autospec(FilenameGroup, instance=True)
        mock_filename_group.from_file.return_value = mock_sample_fg
        mock_sample_fg.all_indexes = [0, 1, 2, 3]
        mock_sample_fg.find_related.return_value = None

        self.presenter.do_update_sample(selected_file)

        mock_update_field.assert_called_once_with(FILE_TYPES.SAMPLE, mock_sample_fg)
        self.fields["Sample"].update_indices.assert_called_once_with(4)
        self.fields["Sample"].update_shape.assert_called_once_with([10, 11])
        self.view.ok_button.setEnabled.assert_called_once_with(True)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.FilenameGroup")
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.read_image_dimensions")
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.update_field_with_filegroup")
    def test_do_update_sample_related_flat_before(self, mock_update_field, mock_read_image_dimensions,
                                                  mock_filename_group):
        selected_file = "/a/b/img_000.tif"
        mock_read_image_dimensions.return_value = [10, 11]
        mock_sample_fg = mock.create_autospec(FilenameGroup, instance=True)
        mock_fb_fg = mock.create_autospec(FilenameGroup, instance=True)
        mock_filename_group.from_file.return_value = mock_sample_fg
        mock_sample_fg.all_indexes = [0, 1, 2, 3]
        mock_sample_fg.find_related.side_effect = lambda ft: mock_fb_fg if ft == FILE_TYPES.FLAT_BEFORE else None

        self.presenter.do_update_sample(selected_file)

        updated_fields = [c.args[0] for c in mock_update_field.mock_calls]
        self.assertIn(FILE_TYPES.SAMPLE, updated_fields)
        self.assertIn(FILE_TYPES.FLAT_BEFORE, updated_fields)
        self.assertNotIn(FILE_TYPES.FLAT_AFTER, updated_fields)
        self.assertNotIn(FILE_TYPES.DARK_BEFORE, updated_fields)
        self.assertNotIn(FILE_TYPES.DARK_AFTER, updated_fields)

    @mock.patch("mantidimaging.core.io.filenames.FilenameGroup.all_files")
    @mock.patch("mantidimaging.core.io.filenames.FilenameGroup.find_all_files")
    def test_do_update_flat_or_dark(self, mock_find_all_files, mock_all_files):
        file_name = "/aaa_0000.tiff"
        ft = FILE_TYPES.FLAT_BEFORE
        field = mock.MagicMock(file_info=ft)
        files_list = [file_name, "aaa_0001.tiff"]
        mock_all_files.return_value = files_list

        self.presenter.do_update_flat_or_dark(field, file_name)

        field.set_images.assert_called_once_with(files_list)

    def test_do_update_single_file(self):
        file_name = "file_name"
        field = mock.MagicMock(file_info=FILE_TYPES.PROJ_180)

        self.presenter._update_field_action(field, file_name)

        self.assertEqual(field.path, Path(file_name))

    def test_do_update_single_file_no_file_selected(self):
        file_name = "file_name"
        field = mock.MagicMock(file_info=FILE_TYPES.PROJ_180)

        self.presenter._update_field_action(field, None)

        self.assertNotEqual(field.path, file_name)

    def test_do_update_sample_log_no_sample_selected(self):
        field = mock.MagicMock()
        self.presenter.sample_fg = None
        self.assertRaises(RuntimeError, self.presenter.do_update_sample_log, field, "")

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.validate_sample_log")
    def test_do_update_sample_log(self, mock_validate):
        file_name = "file_name"

        field = mock.MagicMock(file_info=FILE_TYPES.SAMPLE_LOG)

        self.presenter.sample_fg = mock.create_autospec(FilenameGroup, instance=True)
        self.presenter.do_update_sample_log(field, file_name)

        mock_validate.assert_called_once_with(file_name, [], [])

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.validate_sample_log")
    def test_do_update_sample_log_clears_field_on_failure(self, mock_validate):
        mock_validate.return_value = False
        field = mock.MagicMock(file_info=FILE_TYPES.SAMPLE_LOG)
        self.presenter.sample_fg = mock.create_autospec(FilenameGroup, instance=True)
        self.presenter.do_update_sample_log(field, "log.txt")

        field.clear.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_validate_sample_log_matching(self, mock_load_log):
        """
        Test behaviour when the number of projection angles and files matches (MATCH scenario)
        """
        mock_log = mock.create_autospec(InstrumentLog, instance=True)
        mock_log.length = 2
        mock_load_log.return_value = mock_log
        file_name = "file_name"
        test_filenames = ["file1", "file2"]
        self.presenter.validate_sample_log(file_name, test_filenames, test_filenames)

        mock_load_log.assert_called_once_with(Path(file_name))
        mock_log.raise_if_angle_missing.assert_called_once_with(test_filenames)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_validate_sample_log_exits_when_none_or_empty_str(self, mock_load_log):
        mock_log = mock.create_autospec(InstrumentLog, instance=True)
        mock_load_log.return_value = mock_log
        file_name = None
        test_filenames = ["file1", "file2"]
        self.presenter.validate_sample_log(file_name, test_filenames, test_filenames)

        mock_load_log.assert_not_called()
        mock_log.raise_if_angle_missing.assert_not_called()

        file_name = ""
        self.presenter.validate_sample_log(file_name, test_filenames, test_filenames)

        mock_load_log.assert_not_called()
        mock_log.raise_if_angle_missing.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_validate_sample_log_smaller_than_selection_returns_false(self, mock_load_log):
        mock_log = mock.create_autospec(InstrumentLog, instance=True)
        mock_log.length = 3
        selected_filenames = ["img.tiff"] * 5
        full_stack_filenames = ["img.tiff"] * 10
        mock_load_log.return_value = mock_log
        result = self.presenter.validate_sample_log("log.txt", selected_filenames, full_stack_filenames)

        self.assertFalse(result)
        self.view.show_error_dialog.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_validate_sample_log_larger_than_full_stack_returns_false(self, mock_load_log):
        """log_count > full_count: always reject"""
        mock_log = mock.create_autospec(InstrumentLog, instance=True)
        mock_log.length = 15
        selected_filenames = ["img.tiff"] * 5
        full_stack_filenames = ["img.tiff"] * 10
        mock_load_log.return_value = mock_log
        result = self.presenter.validate_sample_log("log.txt", selected_filenames, full_stack_filenames)

        self.assertFalse(result)
        self.view.show_error_dialog.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_validate_sample_log_partial_match_warns_user(self, mock_load_log):
        """selected_count <= log_count < full_count: warn and defer to user"""
        mock_log = mock.create_autospec(InstrumentLog, instance=True)
        mock_log.length = 7
        selected_filenames = ["img.tiff"] * 5
        full_stack_filenames = ["img.tiff"] * 10
        mock_load_log.return_value = mock_log
        self.view.show_question_dialog.return_value = True
        result = self.presenter.validate_sample_log("log.txt", selected_filenames, full_stack_filenames)

        self.assertTrue(result)
        self.view.show_question_dialog.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_validate_sample_log_unrecognised_format_returns_false(self, mock_load_log):
        """NoParserFound: always reject with specific error"""
        mock_load_log.side_effect = NoParserFound
        result = self.presenter.validate_sample_log("log.txt", [], [])

        self.assertFalse(result)
        self.view.show_unrecognised_log_format_error.assert_called_once()

    def test_warn_partial_log_user_accepts_returns_true(self):
        self.view.show_question_dialog.return_value = True
        result = self.presenter._warn_partial_log(5, 5, 10)

        self.assertTrue(result)

    def test_warn_partial_log_user_declines_returns_false(self):
        self.view.show_question_dialog.return_value = False
        result = self.presenter._warn_partial_log(5, 5, 10)

        self.assertFalse(result)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.FilenameGroup.find_all_files")
    def test_get_parameters(self, _):
        sample_path = Path("/sample/tomo/tomo_0001.tiff")
        sample_log_path = Path("/sample/tomo.log")
        sample_indices = Indices(0, 10, 1)

        type(self.fields["Sample"]).path = mock.PropertyMock(return_value=sample_path)
        self.fields["Sample"].use.isChecked.return_value = True
        type(self.fields["Sample"]).indices = mock.PropertyMock(return_value=sample_indices)
        type(self.fields["Sample Log"]).path = mock.PropertyMock(return_value=sample_log_path)

        flat_before_path = Path("/sample/flat_before/flat_before_0001.tiff")
        flat_before_log = Path("/sample/flat_before.log")
        flat_after_path = Path("/sample/flat_after/flat_after_0001.tiff")
        flat_after_log = Path("/sample/flat_after.log")
        dark_before_path = Path("/sample/dark_before/dark_before_0001.tiff")
        dark_after_path = Path("/sample/dark_after/dark_after_0001.tiff")
        proj_180_path = Path("/sample/180deg/180deg.tiff")
        self.fields["Flat Before"].use.isChecked.return_value = True
        type(self.fields["Flat Before"]).path = mock.PropertyMock(return_value=flat_before_path)
        type(self.fields["Flat Before Log"]).path = mock.PropertyMock(return_value=flat_before_log)
        self.fields["Flat After"].use.isChecked.return_value = True
        type(self.fields["Flat After"]).path = mock.PropertyMock(return_value=flat_after_path)
        type(self.fields["Flat After Log"]).path = mock.PropertyMock(return_value=flat_after_log)
        type(self.fields["Dark Before"]).path = mock.PropertyMock(return_value=dark_before_path)
        type(self.fields["Dark After"]).path = mock.PropertyMock(return_value=dark_after_path)
        type(self.fields["180 degree"]).path = mock.PropertyMock(return_value=proj_180_path)

        pixel_size = 24
        dtype = "float32"
        sinograms = True
        self.view.pixelSize.value.return_value = pixel_size
        self.view.pixel_bit_depth.currentText.return_value = dtype
        self.view.images_are_sinograms.isChecked.return_value = sinograms

        lp = self.presenter.get_parameters()

        lp_sample = lp.image_stacks[FILE_TYPES.SAMPLE]
        lp_flat_before = lp.image_stacks[FILE_TYPES.FLAT_BEFORE]
        lp_flat_after = lp.image_stacks[FILE_TYPES.FLAT_AFTER]
        lp_dark_before = lp.image_stacks[FILE_TYPES.DARK_BEFORE]
        lp_dark_after = lp.image_stacks[FILE_TYPES.DARK_AFTER]
        lp_proj_180deg = lp.image_stacks[FILE_TYPES.PROJ_180]

        self._files_equal(next(lp_sample.file_group.all_files()), sample_path)
        self._files_equal(lp_sample.log_file, sample_log_path)
        self.assertEqual(lp_sample.indices, sample_indices)

        self._files_equal(next(lp_flat_before.file_group.all_files()), flat_before_path)
        self._files_equal(next(lp_flat_after.file_group.all_files()), flat_after_path)
        self._files_equal(next(lp_dark_before.file_group.all_files()), dark_before_path)
        self._files_equal(next(lp_dark_after.file_group.all_files()), dark_after_path)
        self._files_equal(next(lp_proj_180deg.file_group.all_files()), proj_180_path)

        self._files_equal(lp_flat_before.log_file, flat_before_log)
        self._files_equal(lp_flat_after.log_file, flat_after_log)
        self.assertIsNone(lp_dark_before.log_file)
        self.assertIsNone(lp_dark_after.log_file)
        self.assertIsNone(lp_proj_180deg.log_file)

        self.assertEqual(lp.name, sample_path.name)
        self.assertEqual(lp.dtype, dtype)
        self.assertEqual(lp.sinograms, sinograms)
        self.assertEqual(lp.pixel_size, pixel_size)

        self.assertNotIn(FILE_TYPES.SAMPLE_LOG, lp.image_stacks.keys())
        self.assertNotIn(FILE_TYPES.FLAT_BEFORE_LOG, lp.image_stacks.keys())
        self.assertNotIn(FILE_TYPES.FLAT_AFTER_LOG, lp.image_stacks.keys())
