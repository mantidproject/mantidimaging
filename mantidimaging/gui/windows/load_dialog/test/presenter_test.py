import unittest
from pathlib import Path
from unittest import mock

from mantidimaging.gui.windows.load_dialog.presenter import LoadPresenter, Notification


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

    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.read_in_shape", return_value=((0, 0, 0), True))
    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.get_file_extension", )
    @mock.patch("mantidimaging.gui.windows.load_dialog.presenter.get_prefix")
    def test_do_update_sample(self, get_prefix, get_file_extension, read_in_shape):
        selected_file = "SelectedFile"
        sample_file_name = "SampleFileName"
        path_text = "PathText"
        image_format = "ImageFormat"
        prefix = "FilePrefix"
        dirname = "/Dirname"

        self.v.select_file.return_value = selected_file
        self.v.sample.file.return_value = sample_file_name
        self.v.sample.path_text.return_value = path_text
        self.v.sample.directory.return_value = dirname
        self.v.flat.directory.return_value = dirname + "t"
        self.p._find_images = mock.MagicMock(return_value=1)
        self.p._find_180deg_proj = mock.MagicMock(return_value=2)
        self.p._find_log = mock.MagicMock(return_value=3)
        get_file_extension.return_value = image_format
        get_prefix.return_value = prefix

        self.p.do_update_sample()

        self.assertEqual(selected_file, self.v.sample.path)
        self.v.sample.widget.setExpanded.assert_called_once_with(True)
        self.assertEqual(image_format, self.p.image_format)
        get_file_extension.assert_called_once_with(sample_file_name)
        get_prefix.assert_called_once_with(path_text)
        read_in_shape.assert_called_once_with(dirname, in_prefix=prefix, in_format=image_format)
        self.assertEqual((0, 0, 0), self.p.last_shape)
        self.v.flat.set_images.assert_called_once_with(1)
        self.v.dark.set_images.assert_called_once_with(1)
        self.assertEqual(2, self.v.proj_180deg.path)
        self.p._find_log.assert_any_call(Path(dirname), dirname + "t")
        self.p._find_log.assert_any_call(Path(dirname), dirname)
        self.assertEqual(self.v.sample_log.path, 3)
        self.assertEqual(self.v.flat_log.path, 3)
        self.assertFalse(self.v.flat_log.use)
        self.assertFalse(self.v.sample_log.use)
        self.v.images_are_sinograms.setChecked.assert_called_once_with(True)
        self.v.sample.update_indices.assert_called_once_with(0)
        self.v.sample.update_shape.assert_called_once_with((0, 0))

    def test_do_update_flat_or_dark_returns_without_setting_anything(self):
        file_name = None
        name = "Name"
        field = mock.MagicMock()
        self.v.select_file.return_value = file_name

        self.p.do_update_flat_or_dark(field, name)

        field.set_images.assert_not_called()

    def test_do_update_flat_or_dark(self):
        file_name = "/ExampleFilename"
        name = "Name"
        field = mock.MagicMock()
        self.v.select_file.return_value = file_name
        self.p._find_images = mock.MagicMock(return_value=1)

        self.p.do_update_flat_or_dark(field, name)

        self.p._find_images.assert_called_once_with(Path('/'), "Name")
        field.set_images.assert_called_once_with(1)

    def test_do_update_single_file(self):
        file_name = "file_name"
        image_name = "/ExampleImageName"
        name = "Name"
        field = mock.MagicMock()
        self.v.select_file.return_value = file_name

        self.p.do_update_single_file(field, name, image_name)

        self.v.select_file.assert_called_once_with(name, image_name)
        self.assertEqual(field.path, file_name)
