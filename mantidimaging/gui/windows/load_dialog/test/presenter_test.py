# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from pathlib import Path
from unittest import mock

from mantidimaging.core.io.loader.loader import FileInformation
from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile
from mantidimaging.gui.windows.load_dialog.presenter import LoadPresenter, Notification, logger


class LoadDialogPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(LoadDialogPresenterTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.v = mock.MagicMock()
        self.p = LoadPresenter(self.v)

    def test_notify_update_all_fields(self):
        self.p.do_update_sample = mock.MagicMock()

        self.p.notify(Notification.UPDATE_ALL_FIELDS)

        self.p.do_update_sample.assert_called_once()

    def test_notify_update_flat_or_dark(self):
        self.p.do_update_flat_or_dark = mock.MagicMock()

        self.p.notify(Notification.UPDATE_FLAT_OR_DARK, alt=1)

        self.p.do_update_flat_or_dark.assert_called_once_with(alt=1)

    def test_notify_update_single_file(self):
        self.p.do_update_single_file = mock.MagicMock()

        self.p.notify(Notification.UPDATE_SINGLE_FILE, alt=1)

        self.p.do_update_single_file.assert_called_once_with(alt=1)

    def test_do_update_sample_with_no_selected_file(self):
        self.v.select_file.return_value = None

        self.assertFalse(self.p.do_update_sample())

        self.v.select_file.assert_called_once_with("Sample")

    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.find_log", return_value=3)
    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.find_180deg_proj", return_value=2)
    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.find_images", return_value=1)
    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.load_log")
    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.read_in_file_information",
                return_value=FileInformation([], (0, 0, 0), True))
    @mock.patch(
        "mantidimaging.gui.windows.load_dialog.presenter.get_file_extension", )
    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.get_prefix")
    def test_do_update_sample(self, get_prefix, get_file_extension, read_in_file_information, mock_load_log,
                              find_images, find_180deg_proj, find_log):
        selected_file = "SelectedFile"
        sample_file_name = "SampleFileName"
        path_text = "PathText"
        image_format = "ImageFormat"
        prefix = "FilePrefix"
        dirname = "/Dirname"

        mock_log = mock.create_autospec(IMATLogFile)
        mock_load_log.return_value = mock_log
        self.v.select_file.return_value = selected_file
        self.v.sample.file.return_value = sample_file_name
        self.v.sample.path_text.return_value = path_text
        self.v.sample.directory.return_value = dirname
        self.v.flat.directory.return_value = dirname + "t"
        get_file_extension.return_value = image_format
        get_prefix.return_value = prefix

        self.p.do_update_sample()

        self.assertEqual(selected_file, self.v.sample.path)
        self.v.sample.widget.setExpanded.assert_called_once_with(True)
        self.assertEqual(image_format, self.p.image_format)
        get_file_extension.assert_called_once_with(sample_file_name)
        get_prefix.assert_called_once_with(path_text)
        read_in_file_information.assert_called_once_with(dirname, in_prefix=prefix, in_format=image_format)
        self.assertEqual((0, 0, 0), self.p.last_file_info.shape)
        self.v.flat_before.set_images.assert_called_once_with(1)
        self.v.dark_before.set_images.assert_called_once_with(1)
        self.v.flat_after.set_images.assert_called_once_with(1)
        self.v.dark_after.set_images.assert_called_once_with(1)
        self.assertEqual(2, self.v.proj_180deg.path)
        find_log.assert_any_call(Path(dirname), dirname, logger)
        find_images.assert_any_call(Path(dirname),
                                    'Flat',
                                    suffix='Before',
                                    look_without_suffix=True,
                                    image_format=image_format,
                                    logger=logger)
        find_images.assert_any_call(Path(dirname), 'Flat', suffix='After', image_format=image_format, logger=logger)
        find_images.assert_any_call(Path(dirname),
                                    'Dark',
                                    suffix='Before',
                                    look_without_suffix=True,
                                    image_format=image_format,
                                    logger=logger)
        find_images.assert_any_call(Path(dirname), 'Dark', suffix='After', image_format=image_format, logger=logger)
        self.assertEqual(4, find_images.call_count)
        find_180deg_proj.assert_called_once_with(Path(dirname), image_format, logger)
        self.assertEqual(self.v.sample_log.path, 3)
        self.assertEqual(self.v.flat_before_log.path, 3)
        self.assertFalse(self.v.flat_before_log.use)
        self.assertFalse(self.v.sample_log.use)
        self.v.images_are_sinograms.setChecked.assert_called_once_with(True)
        self.v.sample.update_indices.assert_called_once_with(0)
        self.v.sample.update_shape.assert_called_once_with((0, 0))
        mock_load_log.assert_called_once()
        mock_log.raise_if_angle_missing.assert_called_once()

    def test_do_update_flat_or_dark_returns_without_setting_anything(self):
        file_name = None
        name = "Name"
        suffix = "testing"
        field = mock.MagicMock()
        self.v.select_file.return_value = file_name

        self.p.do_update_flat_or_dark(field, name, suffix)

        field.set_images.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.find_images")
    def test_do_update_flat_or_dark(self, find_images):
        file_name = "/ExampleFilename"
        name = "Name"
        suffix = "Apples"
        field = mock.MagicMock()
        self.v.select_file.return_value = file_name

        self.p.do_update_flat_or_dark(field, name, suffix)

        find_images.assert_called_once_with(Path('/'), name, suffix, image_format='', logger=logger)
        field.set_images.assert_called_once_with(find_images.return_value)

    def test_do_update_single_file(self):
        file_name = "file_name"
        name = "Name"
        is_image_file = True
        field = mock.MagicMock()
        self.v.select_file.return_value = file_name

        self.p.do_update_single_file(field, name, is_image_file)

        self.v.select_file.assert_called_once_with(name, is_image_file)
        self.assertEqual(field.path, file_name)

    def test_do_update_single_file_no_file_selected(self):
        file_name = "file_name"
        name = "Name"
        is_image_file = True
        field = mock.MagicMock()
        self.v.select_file.return_value = None

        self.p.do_update_single_file(field, name, is_image_file)

        self.v.select_file.assert_called_once_with(name, is_image_file)
        self.assertNotEqual(field.path, file_name)

    def test_do_update_sample_log_no_sample_selected(self):
        name = "Name"
        is_image_file = True
        field = mock.MagicMock()
        self.p.last_file_info = None
        self.assertRaises(RuntimeError, self.p.do_update_sample_log, field, name, is_image_file)

    def test_do_update_sample_log_no_file_selected(self):
        file_name = "file_name"
        name = "Name"
        is_image_file = True
        field = mock.MagicMock()
        self.v.select_file.return_value = None

        self.p.last_file_info = FileInformation([], (0, 0, 0), False)
        self.p.do_update_sample_log(field, name, is_image_file)

        self.v.select_file.assert_called_once_with(name, is_image_file)
        self.assertNotEqual(field.path, file_name)

    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.LoadPresenter.ensure_sample_log_consistency")
    def test_do_update_sample_log(self, mock_ensure):
        file_name = "file_name"
        name = "Name"

        is_image_file = True
        field = mock.MagicMock()
        self.v.select_file.return_value = file_name

        self.p.last_file_info = FileInformation([], (0, 0, 0), False)
        self.p.do_update_sample_log(field, name, is_image_file)

        self.v.select_file.assert_called_once_with(name, is_image_file)
        mock_ensure.assert_called_once_with(field, file_name, [])

    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.load_log")
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

        mock_load_log.assert_called_once_with(file_name)
        mock_log.raise_if_angle_missing.assert_called_once_with(test_filenames)
        self.assertIsNotNone(field.path)
        self.assertIsNotNone(field.use)

    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.load_log")
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

    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.get_prefix", return_value="/path")
    def test_get_parameters(self, get_prefix):
        path_text = "/path/text"
        sample_input_path = "/sample/input/path"
        image_format = ".tif"
        sample_indices = [1, 1]
        sample_file_name = "/path/sample_file_name"
        pixel_size = 24
        flat_file_name = "/path/flat_file_name"
        flat_log_file_name = "/path/flat/log/file_name"
        flat_directory = "/path/directory"
        dark_directory = "/path/dark/directory"
        proj180deg_directory = "/path/proj180/directory"
        proj180deg_file = "/path/proj180/directory/file"
        dtype = "float32"
        sinograms = True
        sample_path_text = "/path/of/sample"
        dark_before_path_text = "/path/of/dark"
        self.v.sample_log.path_text.return_value = path_text
        self.v.sample_log.use.isChecked.return_value = True
        self.v.sample.directory.return_value = sample_input_path
        self.p.image_format = image_format
        self.v.sample.indices = sample_indices
        self.v.sample.file.return_value = sample_file_name
        self.v.pixelSize.value.return_value = pixel_size
        self.v.flat_before.use.isChecked.return_value = True
        self.v.flat_before.path_text.return_value = flat_file_name
        self.v.flat_before_log.path_text.return_value = flat_log_file_name
        self.v.flat_before.directory.return_value = flat_directory
        self.v.flat_after.use.isChecked.return_value = True
        self.v.flat_after.path_text.return_value = flat_file_name
        self.v.flat_after_log.path_text.return_value = flat_log_file_name
        self.v.flat_after.directory.return_value = flat_directory
        self.v.dark_before.directory.return_value = dark_directory
        self.v.dark_after.directory.return_value = dark_directory
        self.v.pixel_bit_depth.currentText.return_value = dtype
        self.v.images_are_sinograms.isChecked.return_value = sinograms
        self.v.proj_180deg.path_text.return_value = proj180deg_file
        self.v.proj_180deg.directory.return_value = proj180deg_directory
        self.v.sample.path_text.return_value = sample_path_text
        self.v.dark_before.path_text.return_value = dark_before_path_text

        lp = self.p.get_parameters()

        self.assertEqual(lp.sample.log_file, path_text)
        self.assertEqual(lp.sample.input_path, sample_input_path)
        self.assertEqual(lp.sample.format, image_format)
        self.assertEqual(lp.sample.prefix, "/path")
        self.assertEqual(lp.sample.indices, sample_indices)
        self.assertEqual(lp.name, sample_file_name)
        self.assertEqual(lp.pixel_size, pixel_size)
        self.assertEqual(lp.flat_before.prefix, "/path")
        self.assertEqual(lp.flat_before.log_file, flat_log_file_name)
        self.assertEqual(lp.flat_before.format, image_format)
        self.assertEqual(lp.flat_before.input_path, flat_directory)
        self.assertEqual(lp.flat_after.prefix, "/path")
        self.assertEqual(lp.flat_after.log_file, flat_log_file_name)
        self.assertEqual(lp.flat_after.format, image_format)
        self.assertEqual(lp.flat_after.input_path, flat_directory)
        self.assertEqual(lp.dark_before.input_path, dark_directory)
        self.assertEqual(lp.dark_before.prefix, "/path")
        self.assertEqual(lp.dark_before.format, image_format)
        self.assertEqual(lp.dark_after.input_path, dark_directory)
        self.assertEqual(lp.dark_after.prefix, "/path")
        self.assertEqual(lp.dark_after.format, image_format)
        self.assertEqual(lp.proj_180deg.input_path, proj180deg_directory)
        self.assertEqual(lp.proj_180deg.prefix, "/path/proj180/directory/file")
        self.assertEqual(lp.proj_180deg.format, image_format)
        self.assertEqual(lp.dtype, dtype)
        self.assertEqual(lp.sinograms, sinograms)
        self.assertEqual(lp.pixel_size, pixel_size)
        self.assertTrue(mock.call(sample_path_text) in get_prefix.call_args_list)
        self.assertTrue(mock.call(flat_file_name) in get_prefix.call_args_list)
        self.assertTrue(mock.call(dark_before_path_text) in get_prefix.call_args_list)
