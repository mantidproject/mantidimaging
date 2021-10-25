# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
import uuid

from unittest import mock
import numpy as np

from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles
from mantidimaging.gui.windows.main import MainWindowModel


class MainWindowModelTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MainWindowModelTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.model = MainWindowModel()
        self.model_class_name = f"{self.model.__module__}.{self.model.__class__.__name__}"
        self.stack_list_property = f"{self.model_class_name}.stack_list"

    def _add_mock_image(self):
        image_mock = mock.Mock()
        uid = uuid.uuid1()
        self.model.images[uid] = image_mock
        return uid, image_mock

    def test_get_images_by_uuid(self):
        uid, image_mock = self._add_mock_image()
        self.assertIs(image_mock, self.model.get_images_by_uuid(uid))

    @mock.patch('mantidimaging.core.io.loader.load_log')
    @mock.patch('mantidimaging.core.io.loader.load_p')
    def test_do_load_stack_sample_only(self, load_p_mock: mock.Mock, load_log_mock: mock.Mock):
        lp = LoadingParameters()
        sample_mock = mock.Mock()
        sample_mock.log_file = None
        lp.sample = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = True
        lp.pixel_size = 101
        progress_mock = mock.Mock()

        self.model.do_load_dataset(lp, progress_mock)

        load_p_mock.assert_called_once_with(sample_mock, lp.dtype, progress_mock)
        load_log_mock.assert_not_called()

    @mock.patch('mantidimaging.core.io.loader.load_log')
    @mock.patch('mantidimaging.core.io.loader.load_p')
    def test_do_load_stack_sample_and_sample_log(self, load_p_mock: mock.Mock, load_log_mock: mock.Mock):
        lp = LoadingParameters()
        sample_mock = mock.Mock()
        lp.sample = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = False
        lp.pixel_size = 101
        progress_mock = mock.Mock()

        self.model.do_load_dataset(lp, progress_mock)

        load_p_mock.assert_called_once_with(sample_mock, lp.dtype, progress_mock)
        load_log_mock.assert_called_once_with(sample_mock.log_file)

    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_log')
    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_p')
    def test_do_load_stack_sample_and_flat(self, load_p_mock: mock.Mock, load_log_mock: mock.Mock):
        lp = LoadingParameters()
        sample_mock = mock.Mock()
        lp.sample = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = False
        lp.pixel_size = 101

        flat_before_mock = mock.Mock()
        lp.flat_before = flat_before_mock
        flat_after_mock = mock.Mock()
        lp.flat_after = flat_after_mock
        progress_mock = mock.Mock()

        sample_images_mock = mock.Mock()
        flatb_images_mock = mock.Mock()
        flata_images_mock = mock.Mock()
        load_p_mock.side_effect = [sample_images_mock, flatb_images_mock, flata_images_mock]

        self.model.do_load_dataset(lp, progress_mock)

        load_p_mock.assert_has_calls([
            mock.call(sample_mock, lp.dtype, progress_mock),
            mock.call(flat_before_mock, lp.dtype, progress_mock),
            mock.call(flat_after_mock, lp.dtype, progress_mock)
        ])
        load_log_mock.assert_has_calls([
            mock.call(sample_mock.log_file),
            mock.call(flat_before_mock.log_file),
            mock.call(flat_after_mock.log_file)
        ])
        assert self.model.images[sample_images_mock.id] is sample_images_mock
        assert self.model.images[flatb_images_mock.id] is flatb_images_mock
        assert self.model.images[flata_images_mock.id] is flata_images_mock

    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_log')
    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_p')
    def test_do_load_stack_sample_and_flat_and_dark_and_180deg(self, load_p_mock: mock.Mock, load_log_mock: mock.Mock):
        lp = LoadingParameters()
        sample_mock = mock.Mock()
        lp.sample = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = False
        lp.pixel_size = 101

        flat_before_mock = mock.Mock()
        lp.flat_before = flat_before_mock
        flat_after_mock = mock.Mock()
        lp.flat_after = flat_after_mock

        dark_before_mock = mock.Mock()
        lp.dark_before = dark_before_mock
        dark_after_mock = mock.Mock()
        lp.dark_after = dark_after_mock

        proj_180deg_mock = mock.Mock()
        lp.proj_180deg = proj_180deg_mock

        progress_mock = mock.Mock()

        sample_images_mock = mock.Mock()
        flatb_images_mock = mock.Mock()
        flata_images_mock = mock.Mock()
        darkb_images_mock = mock.Mock()
        darka_images_mock = mock.Mock()
        load_p_mock.side_effect = [sample_images_mock, flatb_images_mock, flata_images_mock, darkb_images_mock, darka_images_mock, mock.Mock()]

        self.model.do_load_dataset(lp, progress_mock)

        load_p_mock.assert_has_calls([
            mock.call(sample_mock, lp.dtype, progress_mock),
            mock.call(flat_before_mock, lp.dtype, progress_mock),
            mock.call(flat_after_mock, lp.dtype, progress_mock),
            mock.call(dark_before_mock, lp.dtype, progress_mock),
            mock.call(dark_after_mock, lp.dtype, progress_mock),
            mock.call(proj_180deg_mock, lp.dtype, progress_mock)
        ])

        load_log_mock.assert_has_calls([
            mock.call(sample_mock.log_file),
            mock.call(flat_before_mock.log_file),
            mock.call(flat_after_mock.log_file)
        ])
        assert self.model.images[sample_images_mock.id] is sample_images_mock
        assert self.model.images[flatb_images_mock.id] is flatb_images_mock
        assert self.model.images[flata_images_mock.id] is flata_images_mock
        assert self.model.images[darkb_images_mock.id] is darkb_images_mock
        assert self.model.images[darka_images_mock.id] is darka_images_mock

    @mock.patch('mantidimaging.core.io.loader.load_log')
    def test_add_log_to_sample(self, load_log: mock.Mock):
        log_file = "Log file"
        images_id = uuid.uuid1()
        images_mock = mock.MagicMock()
        self.model.get_images_by_uuid = get_images_mock = mock.Mock(return_value=images_mock)

        self.model.add_log_to_sample(images_id=images_id, log_file=log_file)

        load_log.assert_called_once_with(log_file)
        get_images_mock.assert_called_with(images_id)
        self.assertEqual(load_log.return_value, images_mock.log_file)
        # stack_mock.return_value.widget.return_value.presenter.images.log_file.raise_if_angle_missing \
        #     .assert_called_once_with(stack_mock.return_value.widget.return_value.presenter.images.filenames)

    @mock.patch('mantidimaging.core.io.loader.load_log')
    def test_add_log_to_sample_no_stack(self, load_log: mock.Mock):
        """
        Test in add_log_to_sample when get_stack_by_name returns None
        """
        log_file = "Log file"
        images_id = uuid.uuid1()
        stack_mock = mock.MagicMock()
        self.model.get_images_by_uuid = stack_mock
        stack_mock.return_value = None

        self.assertRaises(RuntimeError, self.model.add_log_to_sample, images_id=images_id, log_file=log_file)

        stack_mock.assert_called_with(images_id)

    @mock.patch('mantidimaging.core.io.loader.load')
    def test_add_180_deg_to_dataset(self, load: mock.Mock):
        _180_file = "180 file"
        images_id = uuid.uuid1()
        self.model.images[images_id] = images_mock = mock.MagicMock()
        self.model.get_images_by_uuid = mock.Mock(return_value=images_mock)

        _180_stack = self.model.add_180_deg_to_dataset(images_id=images_id, _180_deg_file=_180_file)

        load.assert_called_with(file_names=[_180_file])
        self.assertEqual(_180_stack, images_mock.proj180deg)

    @mock.patch('mantidimaging.core.io.loader.load')
    def test_add_180_deg_to_dataset_no_dataset(self, load: mock.Mock):
        """
        Test in add_180_deg_to_stack when get_images_by_uuid returns None
        """
        _180_file = "180 file"
        images_id = uuid.uuid1()
        self.model.get_images_by_uuid = get_images_mock = mock.Mock(return_value = None)
        self.assertRaises(RuntimeError,
                          self.model.add_180_deg_to_dataset,
                          images_id=images_id,
                          _180_deg_file=_180_file)
        get_images_mock.assert_called_with(images_id)

    def test_add_projection_angles_to_sample_no_stack(self):
        proj_angles = ProjectionAngles(np.arange(0, 10))
        images_id = uuid.uuid1()
        get_images_mock = mock.MagicMock()
        self.model.get_images_by_uuid = get_images_mock
        get_images_mock.return_value = None
        self.assertRaises(RuntimeError, self.model.add_projection_angles_to_sample, images_id, proj_angles)

        get_images_mock.assert_called_with(images_id)

    def test_add_projection_angles_to_sample(self):
        proj_angles = ProjectionAngles(np.arange(0, 10))
        images_id = uuid.uuid1()
        get_images_mock = mock.MagicMock()
        self.model.get_images_by_uuid = get_images_mock

        self.model.add_projection_angles_to_sample(images_id, proj_angles)

        get_images_mock.assert_called_with(images_id)
        get_images_mock.return_value.set_projection_angles.assert_called_once_with(
            proj_angles)

    @mock.patch("mantidimaging.gui.windows.main.model.loader")
    def test_load_stack(self, loader: mock.MagicMock):
        file_path = "file_path"
        progress = mock.Mock()

        self.model.load_images(file_path, progress)

        loader.load_stack.assert_called_once_with(file_path, progress)
