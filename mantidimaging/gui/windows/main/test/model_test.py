# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
import uuid

from unittest import mock
import numpy as np
from numpy.testing import assert_array_equal

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles
from mantidimaging.gui.windows.main import MainWindowModel
from mantidimaging.gui.windows.main.model import _matching_dataset_attribute
from mantidimaging.test_helpers.unit_test_helper import generate_images


def test_matching_dataset_attribute_returns_true_for_matching_ids():
    images = generate_images()
    assert _matching_dataset_attribute(images, images.id)


def test_matching_dataset_attribute_returns_false_for_different_ids():
    images = generate_images()
    assert not _matching_dataset_attribute(images, uuid.uuid4())


def test_matching_dataset_attribute_returns_false_for_none():
    assert not _matching_dataset_attribute(None, uuid.uuid4())


class MainWindowModelTest(unittest.TestCase):
    def setUp(self):
        self.model = MainWindowModel()
        self.model_class_name = f"{self.model.__module__}.{self.model.__class__.__name__}"
        self.stack_list_property = f"{self.model_class_name}.stack_list"

    def _add_mock_image(self):
        dataset_mock = mock.Mock()
        image_mock = mock.Mock()
        dataset_mock.id = "dataset-id"
        image_mock.id = images_id = "images-id"
        dataset_mock.all = [image_mock]
        self.model.datasets[dataset_mock.id] = dataset_mock
        return images_id, image_mock

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
    @mock.patch('mantidimaging.gui.windows.main.model.StrictDataset')
    def test_do_load_stack_sample_and_flat(self, dataset_mock: mock.Mock, load_p_mock: mock.Mock,
                                           load_log_mock: mock.Mock):
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

        ds_mock = dataset_mock.return_value

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

        dataset_mock.assert_called_with(sample_images_mock)
        assert ds_mock.flat_before == flatb_images_mock
        assert ds_mock.flat_after == flata_images_mock

    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_log')
    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_p')
    @mock.patch('mantidimaging.gui.windows.main.model.StrictDataset')
    def test_do_load_stack_sample_and_flat_and_dark_and_180deg(self, dataset_mock: mock.Mock, load_p_mock: mock.Mock,
                                                               load_log_mock: mock.Mock):
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
        load_p_mock.side_effect = [
            sample_images_mock, flatb_images_mock, flata_images_mock, darkb_images_mock, darka_images_mock,
            mock.Mock()
        ]

        ds_mock = dataset_mock.return_value

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

        dataset_mock.assert_called_with(sample_images_mock)

        assert ds_mock.flat_before == flatb_images_mock
        assert ds_mock.flat_after == flata_images_mock
        assert ds_mock.dark_before == darkb_images_mock
        assert ds_mock.dark_after == darka_images_mock

    @mock.patch('mantidimaging.core.io.loader.load_log')
    def test_add_log_to_sample(self, load_log: mock.Mock):
        log_file = "Log file"
        images_id = "id"
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
        images_id = "id"
        stack_mock = mock.MagicMock()
        self.model.get_images_by_uuid = stack_mock
        stack_mock.return_value = None

        self.assertRaises(RuntimeError, self.model.add_log_to_sample, images_id=images_id, log_file=log_file)

        stack_mock.assert_called_with(images_id)

    @mock.patch('mantidimaging.core.io.loader.load')
    def test_add_180_deg_to_dataset(self, load: mock.Mock):
        _180_file = "180 file"
        dataset_id = "id"
        self.model.datasets[dataset_id] = dataset_mock = StrictDataset(generate_images())
        load.return_value.sample = _180_stack = generate_images()
        self.model.add_180_deg_to_dataset(dataset_id=dataset_id, _180_deg_file=_180_file)

        load.assert_called_with(file_names=[_180_file])
        self.assertEqual(_180_stack, dataset_mock.proj180deg)

    @mock.patch('mantidimaging.core.io.loader.load')
    def test_add_180_deg_to_dataset_no_dataset(self, load: mock.Mock):
        """
        Test in add_180_deg_to_stack when get_images_by_uuid returns None
        """
        _180_file = "180 file"
        dataset_id = "id"
        self.assertRaises(RuntimeError,
                          self.model.add_180_deg_to_dataset,
                          dataset_id=dataset_id,
                          _180_deg_file=_180_file)

    def test_add_projection_angles_to_sample_no_stack(self):
        proj_angles = ProjectionAngles(np.arange(0, 10))
        images_id = "id"
        get_images_mock = mock.MagicMock()
        self.model.get_images_by_uuid = get_images_mock
        get_images_mock.return_value = None
        self.assertRaises(RuntimeError, self.model.add_projection_angles_to_sample, images_id, proj_angles)

        get_images_mock.assert_called_with(images_id)

    def test_add_projection_angles_to_sample(self):
        proj_angles = ProjectionAngles(np.arange(0, 10))
        images_id = "id"
        get_images_mock = mock.MagicMock()
        self.model.get_images_by_uuid = get_images_mock

        self.model.add_projection_angles_to_sample(images_id, proj_angles)

        get_images_mock.assert_called_with(images_id)
        get_images_mock.return_value.set_projection_angles.assert_called_once_with(proj_angles)

    @mock.patch("mantidimaging.gui.windows.main.model.loader")
    def test_load_stack(self, loader: mock.MagicMock):
        file_path = "file_path"
        progress = mock.Mock()

        self.model.load_images(file_path, progress)

        loader.load_stack.assert_called_once_with(file_path, progress)

    def test_no_image_with_matching_id(self):
        self.assertIsNone(self.model.get_images_by_uuid(uuid.uuid4()))

    @mock.patch("mantidimaging.gui.windows.main.model.saver.save")
    def test_save_image(self, save_mock: mock.MagicMock):
        images_id, images_mock = self._add_mock_image()
        images_mock.data = generate_images().data

        output_dir = "output"
        name_prefix = "prefix"
        image_format = "image format"
        overwrite = True
        pixel_depth = "depth"
        progress = mock.Mock()

        save_mock.return_value = filenames = ["filename" for _ in range(len(images_mock.data))]

        result = self.model.do_images_saving(images_id, output_dir, name_prefix, image_format, overwrite, pixel_depth,
                                             progress)
        save_mock.assert_called_once_with(images_mock,
                                          output_dir=output_dir,
                                          name_prefix=name_prefix,
                                          overwrite_all=overwrite,
                                          out_format=image_format,
                                          pixel_depth=pixel_depth,
                                          progress=progress)
        self.assertListEqual(images_mock.filenames, filenames)  # type: ignore
        assert result

    @mock.patch("mantidimaging.gui.windows.main.model.saver.save")
    def test_image_save_when_image_not_found(self, save_mock: mock.MagicMock):
        with self.assertRaises(RuntimeError):
            self.model.do_images_saving(uuid.uuid4(), "output", "name_prefix", "image_format", True, "pixel_depth",
                                        mock.Mock())
        save_mock.assert_not_called()

    def test_set_images_by_uuid_success(self):
        prev_images = generate_images()
        new_data = generate_images().data
        ds = StrictDataset(prev_images)
        self.model.datasets[ds.id] = ds

        self.model.set_image_data_by_uuid(prev_images.id, new_data)
        assert_array_equal(ds.sample.data, new_data)

    def test_set_images_by_uuid_failure(self):
        with self.assertRaises(RuntimeError):
            self.model.set_image_data_by_uuid("cant-find-this-id", generate_images())

    def test_remove_dataset_from_model(self):
        images = [generate_images() for _ in range(5)]
        ids = [image_stack.id for image_stack in images]

        ds = StrictDataset(*images)
        self.model.datasets[ds.id] = ds

        stacks_to_close = self.model.remove_container(ds.id)
        self.assertNotIn(ds, self.model.datasets.values())
        self.assertListEqual(stacks_to_close, ids)

    def test_failed_remove_container(self):
        with self.assertRaises(RuntimeError):
            self.model.remove_container(uuid.uuid4())

    def test_remove_images_from_dataset(self):
        images = [generate_images() for _ in range(2)]
        ds = StrictDataset(*images)
        self.model.datasets[ds.id] = ds

        self.assertIsNotNone(ds.flat_before)
        self.model.remove_container(images[-1].id)
        self.assertIsNone(ds.flat_before)

    def test_add_dataset_to_model(self):
        ds = StrictDataset(generate_images())
        self.model.add_dataset_to_model(ds)
        self.assertIn(ds, self.model.datasets.values())

    def test_image_ids(self):
        all_ids = []
        for _ in range(3):
            images = [generate_images() for _ in range(3)]
            all_ids += [image.id for image in images]
            ds = StrictDataset(*images)
            self.model.add_dataset_to_model(ds)
        self.assertListEqual(all_ids, self.model.image_ids)

    def test_add_recon_to_dataset(self):
        sample = generate_images()
        sample_id = sample.id
        ds = StrictDataset(sample)

        recon = generate_images()
        self.model.add_dataset_to_model(ds)
        self.model.add_recon_to_dataset(recon, sample_id)
        self.assertIn(recon, ds.all)
