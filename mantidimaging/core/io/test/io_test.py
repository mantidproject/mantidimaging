# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import datetime
import os
import unittest
from unittest import mock

import h5py
import numpy as np
import numpy.testing as npt
from mantidimaging.core.operation_history.const import TIMESTAMP

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.core.io import loader
from mantidimaging.core.io import saver
from mantidimaging.core.io.saver import _rescale_recon_data, _save_recon_to_nexus
from mantidimaging.core.utility.version_check import CheckVersion
from mantidimaging.helper import initialise_logging
from mantidimaging.test_helpers import FileOutputtingTestCase

NX_CLASS = "NX_class"


def _decode_nexus_class(nexus_data) -> str:
    return nexus_data.attrs[NX_CLASS].decode("utf-8")


def _nexus_dataset_to_string(nexus_dataset) -> str:
    return np.array(nexus_dataset).tostring().decode("utf-8")


def test_rescale_negative_recon_data():

    recon = th.generate_images()
    recon.data -= np.min(recon.data) * 1.2

    assert np.min(_rescale_recon_data(recon.data)) >= 0
    assert int(np.max(_rescale_recon_data(recon.data))) == np.iinfo("uint16").max


class IOTest(FileOutputtingTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # force silent outputs
        initialise_logging()

    def assert_files_exist(self, base_name, file_format, stack=True, num_images=1, indices=None):

        if not stack:
            # this way we account for only selected indices in the filenames
            if not indices:
                indices = [0, num_images, 1]

            filenames = saver.generate_names(base_name, indices, num_images, out_format=file_format)

            for f in filenames:
                self.assertTrue(os.path.isfile(f))

        else:
            filename = base_name + '.' + file_format
            self.assertTrue(os.path.isfile(filename))

    # fits sequential
    def test_preproc_fits_seq(self):
        self.do_preproc('fits')

    # fits sequential loader indices
    def test_preproc_fits_seq_loader_indices_4_5(self):
        self.do_preproc('fits', loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_fits_seq_loader_indices_0_7(self):
        self.do_preproc('fits', loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_fits_seq_loader_indices_3_9(self):
        self.do_preproc('fits', loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_fits_seq_loader_indices_5_9(self):
        self.do_preproc('fits', loader_indices=[5, 9, 1], expected_len=4)

    # fits sequential saver indices
    def test_preproc_fits_seq_saver_indices_0_5(self):
        self.do_preproc('fits', saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_fits_seq_saver_indices_0_2(self):
        self.do_preproc('fits', saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_fits_seq_saver_indices_3_10(self):
        self.do_preproc('fits', saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_fits_seq_saver_indices_7_10(self):
        self.do_preproc('fits', saver_indices=[7, 10, 1], expected_len=3)

    # tiff sequential
    def test_preproc_tiff_seq(self):
        self.do_preproc('tiff')

    # tiff sequential loader indices
    def test_preproc_tiff_seq_loader_indices_4_5(self):
        self.do_preproc('tiff', loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_tiff_seq_loader_indices_0_7(self):
        self.do_preproc('tiff', loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_tiff_seq_loader_indices_3_9(self):
        self.do_preproc('tiff', loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_tiff_seq_loader_indices_5_9(self):
        self.do_preproc('tiff', loader_indices=[5, 9, 1], expected_len=4)

    # tiff sequential saver indices
    def test_preproc_tiff_seq_saver_indices_0_5(self):
        self.do_preproc('tiff', saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_tiff_seq_saver_indices_0_2(self):
        self.do_preproc('tiff', saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_tiff_seq_saver_indices_3_10(self):
        self.do_preproc('tiff', saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_tiff_seq_saver_indices_7_10(self):
        self.do_preproc('tiff', saver_indices=[7, 10, 1], expected_len=3)

    def do_preproc(self, img_format, loader_indices=None, expected_len=None, saver_indices=None, data_as_stack=False):
        expected_images = th.generate_images()

        # saver indices only affects the enumeration of the data
        if saver_indices:
            # crop the original images to make sure the tests is correct
            expected_images.data = expected_images.data[saver_indices[0]:saver_indices[1]]

        # saver.save_preproc_images(expected_images)
        saver.image_save(expected_images, self.output_directory, out_format=img_format, indices=saver_indices)

        self.assert_files_exist(os.path.join(self.output_directory, saver.DEFAULT_NAME_PREFIX), img_format,
                                data_as_stack, expected_images.data.shape[0], saver_indices)

        # this does not load any flats or darks as they were not saved out
        loaded_images = loader.load(self.output_directory, in_format=img_format, indices=loader_indices)

        if loader_indices:
            assert len(loaded_images.data) == expected_len, \
                "The length of the loaded data does not " \
                "match the expected length! Expected: {0}, " \
                "Got {1}".format(expected_len, len(
                    loaded_images.data))

            expected_images.data = expected_images.data[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(loaded_images.data, expected_images.data)

    def test_load_sample(self):
        img_format = 'tiff'
        images = th.generate_images()

        saver.image_save(images, self.output_directory, out_format=img_format)

        data_as_stack = False
        self.assert_files_exist(os.path.join(self.output_directory, saver.DEFAULT_NAME_PREFIX), img_format,
                                data_as_stack, images.data.shape[0])

        loaded_images = loader.load(self.output_directory, in_format=img_format)

        npt.assert_equal(loaded_images.data, images.data)

    def test_metadata_round_trip(self):
        # Create dummy image stack
        sample = th.gen_img_numpy_rand()
        images = ImageStack(sample)
        images.metadata['message'] = 'hello, world!'

        # Save image stack
        saver.image_save(images, self.output_directory)

        # Load image stack back
        loaded_images = loader.load(self.output_directory)

        # Ensure properties have been preserved
        self.assertEqual(loaded_images.metadata, images.metadata)

    def test_nexus_simple_dataset_save(self):
        sample = th.generate_images()
        sample.data *= 12
        sample._projection_angles = sample.projection_angles()

        sd = StrictDataset(sample)
        path = "nexus/file/path"
        sample_name = "sample-name"

        with h5py.File(path, "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, sample_name)

            # test entry field
            self.assertEqual(_decode_nexus_class(nexus_file["entry1"]), "NXentry")
            self.assertEqual(_decode_nexus_class(nexus_file["entry1"]["tomo_entry"]), "NXsubentry")

            tomo_entry = nexus_file["entry1"]["tomo_entry"]

            # test definition field
            self.assertEqual(_nexus_dataset_to_string(tomo_entry["definition"]), "NXtomo")

            # test instrument field
            self.assertEqual(_decode_nexus_class(tomo_entry["instrument"]), "NXinstrument")

            # test instrument/detector fields
            self.assertEqual(_decode_nexus_class(tomo_entry["instrument"]["detector"]), "NXdetector")
            npt.assert_array_equal(np.array(tomo_entry["instrument"]["detector"]["data"]),
                                   sd.sample.data.astype("uint16"))
            npt.assert_array_equal(np.array(tomo_entry["instrument"]["detector"]["image_key"]),
                                   [0 for _ in range(sd.sample.data.shape[0])])

            # test instrument/sample fields
            self.assertEqual(_decode_nexus_class(tomo_entry["sample"]), "NXsample")
            self.assertEqual(_nexus_dataset_to_string(tomo_entry["sample"]["name"]), sample_name)
            npt.assert_array_equal(np.array(tomo_entry["sample"]["rotation_angle"]),
                                   sd.sample.projection_angles().value)

            # test links
            self.assertEqual(tomo_entry["data"]["data"], tomo_entry["instrument"]["detector"]["data"])
            self.assertEqual(tomo_entry["data"]["rotation_angle"], tomo_entry["sample"]["rotation_angle"])
            self.assertEqual(tomo_entry["data"]["image_key"], tomo_entry["instrument"]["detector"]["image_key"])

    def test_nexus_missing_projection_angles_save_as_zeros(self):
        shape = (10, 8, 10)
        sample = th.generate_images(shape)
        flat_before = th.generate_images(shape)
        flat_before._projection_angles = flat_before.projection_angles()

        sd = StrictDataset(sample, flat_before=flat_before)
        path = "nexus/file/path"
        sample_name = "sample-name"

        with h5py.File(path, "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, sample_name)
            tomo_entry = nexus_file["entry1"]["tomo_entry"]
            rotation_angle_entry = tomo_entry["sample"]["rotation_angle"]

            # test rotation angle fields
            expected = np.concatenate([flat_before.projection_angles().value, np.zeros(shape[0])])
            npt.assert_array_equal(expected, np.array(rotation_angle_entry))

            # test rotation angle links
            self.assertEqual(tomo_entry["data"]["rotation_angle"], rotation_angle_entry)

    @staticmethod
    def test_nexus_complex_dataset_save():
        image_stacks = []
        for _ in range(5):
            image_stack = th.generate_images()
            image_stack.data *= 12
            image_stacks.append(image_stack)
            image_stack._projection_angles = image_stack.projection_angles()

        sd = StrictDataset(*image_stacks)

        with h5py.File("nexus/file/path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name")
            tomo_entry = nexus_file["entry1"]["tomo_entry"]

            # test instrument field
            npt.assert_array_equal(
                np.array(tomo_entry["instrument"]["detector"]["data"]),
                np.concatenate(
                    [sd.dark_before.data, sd.flat_before.data, sd.sample.data, sd.flat_after.data,
                     sd.dark_after.data]).astype("uint16"))
            npt.assert_array_equal(
                np.array(tomo_entry["instrument"]["detector"]["image_key"]),
                [2 for _ in range(sd.dark_before.data.shape[0])] + [1 for _ in range(sd.flat_before.data.shape[0])] +
                [0 for _ in range(sd.sample.data.shape[0])] + [1 for _ in range(sd.flat_after.data.shape[0])] +
                [2 for _ in range(sd.dark_after.data.shape[0])])

            # test instrument/sample fields
            npt.assert_array_equal(np.array(tomo_entry["sample"]["rotation_angle"]),
                                   np.concatenate([images.projection_angles().value for images in image_stacks]))

    @mock.patch("mantidimaging.core.io.saver.h5py.File")
    @mock.patch("mantidimaging.core.io.saver._nexus_save")
    def test_h5py_os_error_returns(self, nexus_save_mock: mock.Mock, file_mock: mock.Mock):
        file_mock.side_effect = OSError
        with self.assertRaises(RuntimeError):
            saver.nexus_save(StrictDataset(th.generate_images()), "path", "sample-name")
        nexus_save_mock.assert_not_called()

    @mock.patch("mantidimaging.core.io.saver.h5py.File")
    @mock.patch("mantidimaging.core.io.saver._nexus_save")
    @mock.patch("mantidimaging.core.io.saver.os")
    def test_failed_nexus_save_deletes_file(self, os_mock: mock.Mock, nexus_save_mock: mock.Mock, file_mock: mock.Mock):
        nexus_save_mock.side_effect = OSError
        save_path = "failed/save/path"
        with self.assertRaises(RuntimeError):
            saver.nexus_save(StrictDataset(th.generate_images()), save_path, "sample-name")
        file_mock.return_value.close.assert_called_once()
        os_mock.remove.assert_called_once_with(save_path)

    @mock.patch("mantidimaging.core.io.saver.h5py.File")
    @mock.patch("mantidimaging.core.io.saver._nexus_save")
    def test_successful_nexus_save_closes_file(self, nexus_save_mock: mock.Mock, file_mock: mock.Mock):
        saver.nexus_save(StrictDataset(th.generate_images()), "path", "sample-name")
        file_mock.return_value.close.assert_called_once()

    @mock.patch("mantidimaging.core.io.saver._save_recon_to_nexus")
    def test_save_recons_if_present(self, recon_save_mock: mock.Mock):
        sample = th.generate_images()
        sample._projection_angles = sample.projection_angles()

        sd = StrictDataset(sample)
        sd.recons.data = [th.generate_images(), th.generate_images()]

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name")

        self.assertEqual(recon_save_mock.call_count, len(sd.recons))

    @mock.patch("mantidimaging.core.io.saver._save_recon_to_nexus")
    def test_dont_save_recons_if_none_present(self, recon_save_mock: mock.Mock):

        sample = th.generate_images()
        sample._projection_angles = sample.projection_angles()

        sd = StrictDataset(sample)

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name")

        recon_save_mock.assert_not_called()

    def test_save_recon_to_nexus(self):

        sample = th.generate_images()
        sample._projection_angles = sample.projection_angles()

        sd = StrictDataset(sample)

        recon = th.generate_images(seed=2)
        recon.metadata[TIMESTAMP] = None
        recon.name = recon_name = "Recon"
        sd.recons.append(recon)

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name")

            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]), "NXentry")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["title"]), recon_name)
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["definition"]), "NXtomoproc")

            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]["INSTRUMENT"]), "NXinstrument")
            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]), "NXsource")

            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]["type"]),
                             "Neutron source")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]["name"]), "ISIS")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]["probe"]),
                             "neutron")

            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]["SAMPLE"]), "NXsample")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["SAMPLE"]["name"]), recon_name)

            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["program"]),
                             "Mantid Imaging")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["version"]),
                             CheckVersion().get_version())
            self.assertIn(str(datetime.date.today()),
                          _nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["date"]))

            assert abs(
                np.max(
                    np.array(nexus_file[recon_name]["data"]["data"]) -
                    _rescale_recon_data(recon.data).astype("uint16"))) <= 1

    def test_use_recon_date_from_image_stack(self):
        sample = th.generate_images()
        sample._projection_angles = sample.projection_angles()

        sd = StrictDataset(sample)

        recon = th.generate_images(seed=2)
        recon.name = recon_name = "Recon"
        gemini = "2022-06-18"
        recon.metadata[TIMESTAMP] = datetime.date.fromisoformat(gemini)
        sd.recons.append(recon)

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name")
            self.assertIn(str(datetime.date.fromisoformat(gemini)),
                          _nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["date"]))

    @staticmethod
    def test_save_recon_xyz_data():
        recon = th.generate_images()
        recon.name = recon_name = "Recon"
        recon.pixel_size = pixel_size = 3

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            _save_recon_to_nexus(nexus_file, recon)
            npt.assert_array_equal(np.array(nexus_file[recon_name]["data"]["x"]),
                                   np.array([pixel_size * i for i in range(recon.data.shape[0])]))
            npt.assert_array_equal(np.array(nexus_file[recon_name]["data"]["y"]),
                                   np.array([pixel_size * i for i in range(recon.data.shape[1])]))
            npt.assert_array_equal(np.array(nexus_file[recon_name]["data"]["z"]),
                                   np.array([pixel_size * i for i in range(recon.data.shape[2])]))


if __name__ == '__main__':
    unittest.main()
