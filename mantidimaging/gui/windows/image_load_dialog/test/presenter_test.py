# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from mantidimaging.core.io.loader.loader import FileInformation
from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile
from mantidimaging.gui.windows.image_load_dialog.field import Field
from mantidimaging.gui.windows.image_load_dialog.presenter import LoadPresenter
from mantidimaging.core.utility.data_containers import FILE_TYPES


class ImageLoadDialogPresenterTest(unittest.TestCase):
    def _files_equal(self, file1, file2):
        self.assertEqual(Path(file1).absolute(), Path(file2).absolute())

    def setUp(self):
        self.fields = {ft.fname: mock.create_autospec(Field) for ft in FILE_TYPES}
        self.v = mock.MagicMock(fields=self.fields)
        self.v.sample = self.fields["Sample"]
        self.p = LoadPresenter(self.v)

    def test_do_update_sample_with_no_selected_file(self):
        self.p.do_update_sample(None)

        self.v.ok_button.setEnabled.assert_called_once_with(False)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.do_update_flat_or_dark")
    def test_do_update_field(self, mock_do_update_flat_or_dark):
        selected_file = "SelectedFile"
        self.v.select_file.return_value = selected_file
        ft = FILE_TYPES.FLAT_BEFORE
        field = mock.MagicMock(file_info=ft)

        self.p.do_update_field(field)

        self.v.select_file.assert_called_once_with(ft.fname, True)
        mock_do_update_flat_or_dark.assert_called_once_with(field, selected_file)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.find_log_for_image", return_value=3)
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.find_180deg_proj", return_value=2)
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.find_images", return_value=1)
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.read_in_file_information",
                return_value=FileInformation(["a"], (0, 0, 0), True))
    @mock.patch(
        "mantidimaging.gui.windows.image_load_dialog.presenter.get_file_extension", )
    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.get_prefix")
    def test_do_update_sample(self, get_prefix, get_file_extension, read_in_file_information, mock_load_log,
                              find_images, find_180deg_proj, find_log_for_image):
        selected_file = "SelectedFile"
        sample_file_name = "SampleFileName"
        path_text = "PathText"
        image_format = "ImageFormat"
        prefix = "FilePrefix"
        dirname = "/Dirname"

        mock_log = mock.create_autospec(IMATLogFile)
        mock_load_log.return_value = mock_log
        self.v.sample.file.return_value = sample_file_name
        self.v.sample.path_text.return_value = path_text
        self.v.sample.directory.return_value = dirname

        self.fields["Flat Before"].path_text.return_value = path_text
        self.fields["Flat After"].path_text.return_value = path_text

        get_file_extension.return_value = image_format
        get_prefix.return_value = prefix

        self.p.do_update_sample(selected_file)

        self.assertEqual(selected_file, self.v.sample.path)
        self.v.sample.widget.setExpanded.assert_called_once_with(True)
        self.assertEqual(image_format, self.p.image_format)
        get_file_extension.assert_called_once_with(sample_file_name)
        get_prefix.assert_called_once_with(path_text)
        read_in_file_information.assert_called_once_with(dirname, in_prefix=prefix, in_format=image_format)
        self.assertEqual((0, 0, 0), self.p.last_file_info.shape)
        for name in ["Flat Before", "Flat After", "Dark Before", "Dark After"]:
            self.fields[name].set_images.assert_called_once_with(1)
        self.assertEqual(2, self.fields["180 degree"].path)
        find_log_for_image.assert_any_call(Path("a"))
        find_images.assert_any_call(Path(dirname),
                                    'Flat',
                                    suffix='Before',
                                    look_without_suffix=True,
                                    image_format=image_format)
        find_images.assert_any_call(Path(dirname),
                                    'Flat',
                                    suffix='After',
                                    look_without_suffix=False,
                                    image_format=image_format)
        find_images.assert_any_call(Path(dirname),
                                    'Dark',
                                    suffix='Before',
                                    look_without_suffix=True,
                                    image_format=image_format)
        find_images.assert_any_call(Path(dirname),
                                    'Dark',
                                    suffix='After',
                                    look_without_suffix=False,
                                    image_format=image_format)
        self.assertEqual(4, find_images.call_count)
        find_180deg_proj.assert_called_once_with(Path(dirname), image_format)
        self.assertEqual(self.fields["Sample Log"].path, 3)
        self.assertEqual(self.fields["Flat Before Log"].path, 3)
        self.assertFalse(self.fields["Flat Before Log"].use)
        self.assertFalse(self.fields["Sample Log"].use)
        self.v.images_are_sinograms.setChecked.assert_called_once_with(True)
        self.v.sample.update_indices.assert_called_once_with(0)
        self.v.sample.update_shape.assert_called_once_with((0, 0))
        mock_load_log.assert_called_once()
        mock_log.raise_if_angle_missing.assert_called_once()

    def test_do_update_flat_or_dark_returns_without_setting_anything(self):
        file_name = None
        field = mock.MagicMock()

        self.p.do_update_flat_or_dark(field, file_name)

        field.set_images.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.find_images")
    def test_do_update_flat_or_dark(self, find_images):
        file_name = "/ExampleFilename"
        ft = FILE_TYPES.FLAT_BEFORE
        field = mock.MagicMock(file_info=ft)

        self.p.do_update_flat_or_dark(field, file_name)

        find_images.assert_called_once_with(Path('/'), ft.fname, ft.suffix, image_format='')
        field.set_images.assert_called_once_with(find_images.return_value)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.find_images")
    def test_do_update_flat_or_dark_second_attempt(self, find_images):
        file_name = "/aaa_0000.tiff"
        ft = FILE_TYPES.FLAT_BEFORE
        field = mock.MagicMock(file_info=ft)
        files_list = [file_name, "aaa_0001.tiff"]
        find_images.side_effect = [[], files_list]

        self.p.do_update_flat_or_dark(field, file_name)

        calls = [
            mock.call(Path('/'), ft.fname, ft.suffix, image_format=''),
            mock.call(Path('/'), "aaa", "", image_format='')
        ]
        find_images.assert_has_calls(calls)
        field.set_images.assert_called_once_with(files_list)

    def test_do_update_single_file(self):
        file_name = "file_name"
        field = mock.MagicMock(file_info=FILE_TYPES.PROJ_180)

        self.p.do_update_single_file(field, file_name)

        self.assertEqual(field.path, file_name)

    def test_do_update_single_file_no_file_selected(self):
        file_name = "file_name"
        field = mock.MagicMock(file_info=FILE_TYPES.PROJ_180)

        self.p.do_update_single_file(field, None)

        self.assertNotEqual(field.path, file_name)

    def test_do_update_sample_log_no_sample_selected(self):
        field = mock.MagicMock()
        self.p.last_file_info = None
        self.assertRaises(RuntimeError, self.p.do_update_sample_log, field, "")

    def test_do_update_sample_log_no_file_selected(self):
        file_name = "file_name"
        field = mock.MagicMock(file_info=FILE_TYPES.SAMPLE_LOG)

        self.p.last_file_info = FileInformation([], (0, 0, 0), False)
        self.p.do_update_sample_log(field, None)

        self.assertNotEqual(field.path, file_name)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.LoadPresenter.ensure_sample_log_consistency")
    def test_do_update_sample_log(self, mock_ensure):
        file_name = "file_name"

        field = mock.MagicMock(file_info=FILE_TYPES.SAMPLE_LOG)

        self.p.last_file_info = FileInformation([], (0, 0, 0), False)
        self.p.do_update_sample_log(field, file_name)

        mock_ensure.assert_called_once_with(field, file_name, [])

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_ensure_sample_log_consistency_matching(self, mock_load_log):
        """
        Test behaviour when the number of projection angles and files matches
        """
        mock_log = mock.create_autospec(IMATLogFile)
        mock_load_log.return_value = mock_log
        file_name = "file_name"
        field = mock.MagicMock()
        field.path = None
        field.use = None
        test_filenames = ["file1", "file2"]

        self.p.last_file_info = FileInformation(test_filenames, (2, 10, 10), False)

        self.p.ensure_sample_log_consistency(field, file_name, test_filenames)

        mock_load_log.assert_called_once_with(Path(file_name))
        mock_log.raise_if_angle_missing.assert_called_once_with(test_filenames)
        self.assertIsNotNone(field.path)
        self.assertIsNotNone(field.use)

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.load_log")
    def test_ensure_sample_log_consistency_exits_when_none_or_empty_str(self, mock_load_log):
        mock_log = mock.create_autospec(IMATLogFile)
        mock_load_log.return_value = mock_log
        file_name = None
        field = mock.MagicMock()
        test_filenames = ["file1", "file2"]

        self.p.ensure_sample_log_consistency(field, file_name, test_filenames)

        mock_load_log.assert_not_called()
        mock_log.raise_if_angle_missing.assert_not_called()

        file_name = ""
        self.p.ensure_sample_log_consistency(field, file_name, test_filenames)

        mock_load_log.assert_not_called()
        mock_log.raise_if_angle_missing.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.image_load_dialog.presenter.FilenameGroup.find_all_files")
    def test_get_parameters(self, _):
        sample_path = "/sample/tomo/tomo_0001.tiff"
        sample_file = "tomo_0001.tiff"
        sample_log_path = "/sample/tomo.log"

        self.fields["Sample"].path_text.return_value = sample_path
        self.fields["Sample"].file.return_value = sample_file
        self.fields["Sample"].use.isChecked.return_value = True
        self.fields["Sample Log"].path_text.return_value = sample_log_path

        # sample_indices = [1, 1] #TODO

        flat_before_path = "/sample/flat_before/flat_before_0001.tiff"
        flat_before_log = "/sample/flat_before.log"
        flat_after_path = "/sample/flat_after/flat_after_0001.tiff"
        flat_after_log = "/sample/flat_after.log"
        dark_before_path = "/sample/dark_before/dark_before_0001.tiff"
        dark_after_path = "/sample/dark_after/dark_after_0001.tiff"
        proj_180_path = "/sample/180deg/180deg.tiff"
        self.fields["Flat Before"].use.isChecked.return_value = True
        self.fields["Flat Before"].path_text.return_value = flat_before_path
        self.fields["Flat Before Log"].path_text.return_value = flat_before_log
        self.fields["Flat After"].use.isChecked.return_value = True
        self.fields["Flat After"].path_text.return_value = flat_after_path
        self.fields["Flat After Log"].path_text.return_value = flat_after_log
        self.fields["Dark Before"].path_text.return_value = dark_before_path
        self.fields["Dark After"].path_text.return_value = dark_after_path
        self.fields["180 degree"].path_text.return_value = proj_180_path

        pixel_size = 24
        dtype = "float32"
        sinograms = True
        self.v.pixelSize.value.return_value = pixel_size
        self.v.pixel_bit_depth.currentText.return_value = dtype
        self.v.images_are_sinograms.isChecked.return_value = sinograms

        lp = self.p.get_parameters()

        lp_sample = lp.image_stacks[FILE_TYPES.SAMPLE]
        lp_flat_before = lp.image_stacks[FILE_TYPES.FLAT_BEFORE]
        lp_flat_after = lp.image_stacks[FILE_TYPES.FLAT_AFTER]
        lp_dark_before = lp.image_stacks[FILE_TYPES.DARK_BEFORE]
        lp_dark_after = lp.image_stacks[FILE_TYPES.DARK_AFTER]
        lp_proj_180deg = lp.image_stacks[FILE_TYPES.PROJ_180]

        self._files_equal(next(lp_sample.file_group.all_files()), sample_path)
        self._files_equal(lp_sample.log_file, sample_log_path)

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

        self.assertEqual(lp.name, sample_file)
        self.assertEqual(lp.dtype, dtype)
        self.assertEqual(lp.sinograms, sinograms)
        self.assertEqual(lp.pixel_size, pixel_size)
