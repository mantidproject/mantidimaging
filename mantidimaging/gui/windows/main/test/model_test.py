# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
import uuid

from unittest import mock
import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.core.data.reconlist import ReconList
from mantidimaging.core.io.loader.loader import LoadingParameters, ImageParameters
from mantidimaging.core.utility.data_containers import ProjectionAngles, FILE_TYPES, Indices
from mantidimaging.gui.windows.main import MainWindowModel
from mantidimaging.gui.windows.main.model import _matching_dataset_attribute
from mantidimaging.test_helpers.unit_test_helper import generate_images


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
    @mock.patch('mantidimaging.core.io.loader.load_stack_from_image_params')
    def test_do_load_stack_sample_only(self, load_mock: mock.Mock, load_log_mock: mock.Mock):
        lp = LoadingParameters()
        sample_mock = ImageParameters(mock.Mock())
        lp.image_stacks[FILE_TYPES.SAMPLE] = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = True
        lp.pixel_size = 101
        progress_mock = mock.Mock()

        self.model.new_do_load_dataset(lp, progress_mock)

        load_mock.assert_called_once_with(sample_mock, progress_mock, dtype=lp.dtype)
        load_log_mock.assert_not_called()

    @mock.patch('mantidimaging.core.io.loader.load_log')
    @mock.patch('mantidimaging.core.io.loader.load_stack_from_image_params')
    def test_do_load_stack_sample_and_sample_log(self, load_mock: mock.Mock, load_log_mock: mock.Mock):
        lp = LoadingParameters()
        log_file_mock = mock.Mock()
        sample_mock = ImageParameters(mock.Mock(), log_file_mock)
        lp.image_stacks[FILE_TYPES.SAMPLE] = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = False
        lp.pixel_size = 101
        progress_mock = mock.Mock()

        self.model.new_do_load_dataset(lp, progress_mock)

        load_mock.assert_called_once_with(sample_mock, progress_mock, dtype=lp.dtype)
        load_log_mock.assert_called_once_with(log_file_mock)

    @mock.patch('mantidimaging.core.io.loader.load_log')
    @mock.patch('mantidimaging.core.io.loader.loader.load')
    def test_do_load_stack_sample_indicies(self, load_mock: mock.Mock, load_log_mock: mock.Mock):
        lp = LoadingParameters()
        all_files = ["filename"] * 10
        mock_filename_group = mock.Mock()
        mock_filename_group.all_files.return_value = all_files
        sample_mock = ImageParameters(mock_filename_group)
        indices = Indices(0, 100, 2)
        sample_mock.indices = indices
        lp.image_stacks[FILE_TYPES.SAMPLE] = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = True
        lp.pixel_size = 101
        progress_mock = mock.Mock()

        self.model.new_do_load_dataset(lp, progress_mock)

        load_mock.assert_called_once_with(file_names=all_files, progress=progress_mock, dtype=lp.dtype, indices=indices)
        load_log_mock.assert_not_called()

    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_log')
    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_stack_from_image_params')
    @mock.patch('mantidimaging.gui.windows.main.model.StrictDataset')
    def test_do_load_stack_sample_and_flat(self, dataset_mock: mock.Mock, load_mock: mock.Mock,
                                           load_log_mock: mock.Mock):
        lp = LoadingParameters()
        log_file_mock = mock.Mock()
        sample_mock = ImageParameters(mock.Mock(), log_file_mock)
        lp.image_stacks[FILE_TYPES.SAMPLE] = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = False
        lp.pixel_size = 101

        flat_before_log_mock = mock.Mock()
        flat_before_mock = ImageParameters(mock.Mock(), flat_before_log_mock)
        lp.image_stacks[FILE_TYPES.FLAT_BEFORE] = flat_before_mock
        flat_after_log_mock = mock.Mock()
        flat_after_mock = ImageParameters(mock.Mock(), flat_after_log_mock)
        lp.image_stacks[FILE_TYPES.FLAT_AFTER] = flat_after_mock
        progress_mock = mock.Mock()

        sample_images_mock = mock.Mock()
        flatb_images_mock = mock.Mock()
        flata_images_mock = mock.Mock()
        load_mock.side_effect = [sample_images_mock, flatb_images_mock, flata_images_mock]

        ds_mock = dataset_mock.return_value

        self.model.new_do_load_dataset(lp, progress_mock)

        load_mock.assert_has_calls([
            mock.call(sample_mock, progress_mock, dtype=lp.dtype),
            mock.call(flat_before_mock, progress_mock, dtype=lp.dtype),
            mock.call(flat_after_mock, progress_mock, dtype=lp.dtype)
        ])
        load_log_mock.assert_has_calls(
            [mock.call(log_file_mock),
             mock.call(flat_before_log_mock),
             mock.call(flat_after_log_mock)])

        dataset_mock.assert_called_with(sample_images_mock)

        ds_mock.set_stack.assert_has_calls([
            mock.call(FILE_TYPES.FLAT_BEFORE, flatb_images_mock),
            mock.call(FILE_TYPES.FLAT_AFTER, flata_images_mock),
        ])

    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_log')
    @mock.patch('mantidimaging.gui.windows.main.model.loader.load_stack_from_image_params')
    @mock.patch('mantidimaging.gui.windows.main.model.StrictDataset')
    def test_do_load_stack_sample_and_dark_and_180deg(self, dataset_mock: mock.Mock, load_mock: mock.Mock,
                                                      load_log_mock: mock.Mock):
        lp = LoadingParameters()
        log_file_mock = mock.Mock()
        sample_mock = ImageParameters(mock.Mock(), log_file_mock)
        lp.image_stacks[FILE_TYPES.SAMPLE] = sample_mock
        lp.dtype = "dtype_test"
        lp.sinograms = False
        lp.pixel_size = 101

        dark_before_mock = ImageParameters(mock.Mock())
        lp.image_stacks[FILE_TYPES.DARK_BEFORE] = dark_before_mock
        dark_after_mock = ImageParameters(mock.Mock())
        lp.image_stacks[FILE_TYPES.DARK_AFTER] = dark_after_mock

        proj_180deg_mock = ImageParameters(mock.Mock())
        lp.image_stacks[FILE_TYPES.PROJ_180] = proj_180deg_mock

        progress_mock = mock.Mock()

        sample_images_mock = mock.Mock()
        darkb_images_mock = mock.Mock()
        darka_images_mock = mock.Mock()
        proj180_images_mock = mock.Mock()
        load_mock.side_effect = [sample_images_mock, darkb_images_mock, darka_images_mock, proj180_images_mock]

        ds_mock = dataset_mock.return_value

        self.model.new_do_load_dataset(lp, progress_mock)

        load_mock.assert_has_calls([
            mock.call(sample_mock, progress_mock, dtype=lp.dtype),
            mock.call(dark_before_mock, progress_mock, dtype=lp.dtype),
            mock.call(dark_after_mock, progress_mock, dtype=lp.dtype),
            mock.call(proj_180deg_mock, progress_mock, dtype=lp.dtype),
        ])

        load_log_mock.assert_has_calls([
            mock.call(log_file_mock),
        ])

        dataset_mock.assert_called_with(sample_images_mock)

        ds_mock.set_stack.assert_has_calls([
            mock.call(FILE_TYPES.DARK_BEFORE, darkb_images_mock),
            mock.call(FILE_TYPES.DARK_AFTER, darka_images_mock),
            mock.call(FILE_TYPES.PROJ_180, proj180_images_mock),
        ])

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
        load.return_value = _180_stack = generate_images()
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
    @mock.patch("mantidimaging.gui.windows.main.model.FilenameGroup")
    def test_load_stack(self, fng_mock: mock.MagicMock, loader: mock.MagicMock):
        file_path = "file_path"
        progress = mock.Mock()
        group = mock.Mock()
        fng_mock.from_file.return_value = group

        self.model.load_images_into_mixed_dataset(file_path, progress)

        loader.load_stack_from_group.assert_called_once_with(group, progress)

    def test_no_image_with_matching_id(self):
        self.assertIsNone(self.model.get_images_by_uuid(uuid.uuid4()))

    @mock.patch("mantidimaging.gui.windows.main.model.saver.image_save")
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

    @mock.patch("mantidimaging.gui.windows.main.model.saver.image_save")
    def test_image_save_when_image_not_found(self, save_mock: mock.MagicMock):
        with self.assertRaises(RuntimeError):
            self.model.do_images_saving(uuid.uuid4(), "output", "name_prefix", "image_format", True, "pixel_depth",
                                        mock.Mock())
        save_mock.assert_not_called()

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

    def test_remove_empty_dataset_from_model(self):
        sample = generate_images()
        ds = StrictDataset(sample)
        self.model.datasets[ds.id] = ds

        self.model.remove_container(sample.id)
        self.assertEqual(len(ds.all), 0)

        self.model.remove_container(ds.id)
        self.assertEqual(len(self.model.datasets), 0)

    def test_remove_non_sample_images_from_dataset_with_sample(self):
        images = [generate_images() for _ in range(2)]
        # Set the sample 180 to check this isn't removed
        images[0].proj180deg = generate_images()
        ds = StrictDataset(*images)
        self.model.datasets[ds.id] = ds
        id_to_remove = images[-1].id

        self.assertIsNotNone(ds.flat_before)
        deleted_stacks = self.model.remove_container(id_to_remove)
        self.assertIsNone(ds.flat_before)
        self.assertEqual([id_to_remove], deleted_stacks)

    def test_remove_non_sample_images_from_dataset_without_sample(self):
        images = [generate_images() for _ in range(2)]
        ds = StrictDataset(*images)
        ds.sample = None
        self.model.datasets[ds.id] = ds
        id_to_remove = images[-1].id

        self.assertIsNotNone(ds.flat_before)
        deleted_stacks = self.model.remove_container(id_to_remove)
        self.assertIsNone(ds.flat_before)
        self.assertEqual([id_to_remove], deleted_stacks)

    def test_remove_sample_with_180_from_dataset(self):
        sample = generate_images()
        sample.proj180deg = generate_images()
        ds = StrictDataset(sample)
        self.model.datasets[ds.id] = ds

        expected_result = [sample.id, sample.proj180deg.id]
        self.assertIsNotNone(ds.sample)
        deleted_stacks = self.model.remove_container(sample.id)
        self.assertIsNone(ds.sample)
        self.assertEqual(expected_result, deleted_stacks)

    def test_remove_sample_without_180_from_dataset(self):
        sample = generate_images()
        ds = StrictDataset(sample)
        self.model.datasets[ds.id] = ds

        expected_result = [sample.id]
        self.assertIsNotNone(ds.sample)
        deleted_stacks = self.model.remove_container(sample.id)
        self.assertIsNone(ds.sample)
        self.assertEqual(expected_result, deleted_stacks)

    def test_remove_images_from_mixed_dataset(self):
        images = [generate_images() for _ in range(5)]
        ids = [image_stack.id for image_stack in images]
        id_to_remove = ids[0]

        ds = MixedDataset(images)
        self.model.datasets[ds.id] = ds

        deleted_stacks = self.model.remove_container(id_to_remove)
        self.assertNotIn(id_to_remove, ds.all_image_ids)
        self.assertListEqual([id_to_remove], deleted_stacks)

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
        parent_id = self.model.add_recon_to_dataset(recon, sample_id)
        self.assertIn(recon, ds.all)
        assert parent_id == ds.id

    def test_proj180s(self):

        ds1 = StrictDataset(generate_images())
        ds2 = StrictDataset(generate_images())
        ds3 = MixedDataset([generate_images()])

        proj180s = [ImageStack(ds1.sample.data[0]), ImageStack(ds2.sample.data[0])]
        ds1.proj180deg = proj180s[0]
        ds2.proj180deg = proj180s[1]

        self.model.add_dataset_to_model(ds1)
        self.model.add_dataset_to_model(ds2)
        self.model.add_dataset_to_model(ds3)

        self.assertListEqual(self.model.proj180s, proj180s)

    def test_exception_when_dataset_for_recons_not_found(self):
        with self.assertRaises(RuntimeError):
            self.model.add_recon_to_dataset(generate_images(), "bad-id")

    def test_get_parent_strict_dataset_success(self):
        ds = StrictDataset(generate_images())
        self.model.add_dataset_to_model(ds)
        self.assertIs(self.model.get_parent_dataset(ds.sample.id), ds.id)

    def test_get_parent_dataset_doesnt_find_any_parent(self):
        ds = StrictDataset(generate_images())
        self.model.add_dataset_to_model(ds)
        with self.assertRaises(RuntimeError):
            self.model.get_parent_dataset("unrecognised-id")

    def test_delete_all_recons_in_dataset(self):
        ds = StrictDataset(generate_images())
        ds.recons = ReconList([generate_images() for _ in range(3)])
        recon_ids = ds.recons.ids
        self.model.add_dataset_to_model(ds)

        self.assertListEqual(self.model.remove_container(ds.recons.id), recon_ids)
        self.assertListEqual(ds.recons.stacks, [])

    def test_get_all_recon_list_ids(self):
        ds1 = MixedDataset()
        ds2 = MixedDataset()

        self.model.add_dataset_to_model(ds1)
        self.model.add_dataset_to_model(ds2)

        self.assertListEqual(self.model.recon_list_ids, [ds1.recons.id, ds2.recons.id])

    def test_get_recon_list_id(self):
        ds = MixedDataset()
        self.model.add_dataset_to_model(ds)

        assert self.model.get_recon_list_id(ds.id) == ds.recons.id

    def test_no_dataset_with_180_raises(self):
        with self.assertRaises(RuntimeError):
            self.model.get_existing_180_id("bad-id")

    def test_wrong_dataset_type_for_180_raises(self):
        md = MixedDataset()
        self.model.add_dataset_to_model(md)

        with self.assertRaises(RuntimeError):
            self.model.get_existing_180_id(md.id)

    def test_get_existing_180_id_finds_id(self):
        sd = StrictDataset(generate_images((5, 20, 20)))
        sd.proj180deg = _180 = generate_images((1, 20, 20))
        self.model.add_dataset_to_model(sd)

        assert self.model.get_existing_180_id(sd.id) == _180.id

    def test_get_existing_id_returns_none_for_dataset_without_180(self):
        sd = StrictDataset(generate_images((5, 20, 20)))
        self.model.add_dataset_to_model(sd)

        self.assertIsNone(self.model.get_existing_180_id(sd.id))

    def test_matching_dataset_attribute_returns_true_for_matching_ids(self):
        images = generate_images()
        assert _matching_dataset_attribute(images, images.id)

    def test_matching_dataset_attribute_returns_false_for_different_ids(self):
        images = generate_images()
        assert not _matching_dataset_attribute(images, uuid.uuid4())

    def test_matching_dataset_attribute_returns_false_for_none(self):
        assert not _matching_dataset_attribute(None, uuid.uuid4())

    def test_do_nexus_saving_fails_from_no_dataset(self):
        with self.assertRaises(RuntimeError):
            self.model.do_nexus_saving("bad-dataset-id", "path", "sample-name")

    def test_do_nexus_saving_fails_from_wrong_dataset(self):
        md = MixedDataset()
        self.model.add_dataset_to_model(md)

        with self.assertRaises(RuntimeError):
            self.model.do_nexus_saving(md.id, "path", "sample-name")

    @mock.patch("mantidimaging.gui.windows.main.model.saver.nexus_save")
    def test_do_nexus_save_success(self, nexus_save):
        sd = StrictDataset(generate_images())
        self.model.add_dataset_to_model(sd)
        path = "path"
        sample_name = "sample-name"

        self.model.do_nexus_saving(sd.id, path, sample_name)
        nexus_save.assert_called_once_with(sd, path, sample_name)

    def test_is_dataset_strict_returns_true(self):
        strict_ds = StrictDataset(generate_images())
        self.model.add_dataset_to_model(strict_ds)
        self.assertTrue(self.model.is_dataset_strict(strict_ds.id))

    def test_is_dataset_strict_returns_false(self):
        mixed_ds = MixedDataset([generate_images()])
        self.model.add_dataset_to_model(mixed_ds)
        self.assertFalse(self.model.is_dataset_strict(mixed_ds.id))

    def test_is_dataset_strict_raises(self):
        with self.assertRaises(RuntimeError):
            self.model.is_dataset_strict(uuid.uuid4())
