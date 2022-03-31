# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import unittest

import h5py
import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.core.io import loader
from mantidimaging.core.io import saver
from mantidimaging.helper import initialise_logging
from mantidimaging.test_helpers import FileOutputtingTestCase

NX_CLASS = "NX_class"


def _decode_nexus_class(nexus_data) -> str:
    return nexus_data.attrs[NX_CLASS].decode("utf-8")


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
        dataset = loader.load(self.output_directory, in_format=img_format, indices=loader_indices)
        loaded_images = dataset.sample

        if loader_indices:
            assert len(loaded_images.data) == expected_len, \
                "The length of the loaded data does not " \
                "match the expected length! Expected: {0}, " \
                "Got {1}".format(expected_len, len(
                    loaded_images.data))

            expected_images.data = expected_images.data[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(loaded_images.data, expected_images.data)

    def test_load_sample_flat_and_dark(self,
                                       img_format='tiff',
                                       loader_indices=None,
                                       expected_len=None,
                                       saver_indices=None):
        images = th.generate_images()
        flat_before = th.generate_images()
        dark_before = th.generate_images()
        flat_after = th.generate_images()
        dark_after = th.generate_images()

        # this only affects enumeration
        saver._indices = saver_indices

        # saver indices only affects the enumeration of the data
        if saver_indices:
            # crop the original images to make sure the test is checking the
            # indices that were actually saved out
            images.data = images.data[saver_indices[0]:saver_indices[1]]

        saver.image_save(images, self.output_directory, out_format=img_format)
        flat_before_dir = os.path.join(self.output_directory, "imgIOTest_flat_before")
        saver.image_save(flat_before, flat_before_dir, out_format=img_format)
        flat_after_dir = os.path.join(self.output_directory, "imgIOTest_flat_after")
        saver.image_save(flat_after, flat_after_dir, out_format=img_format)
        dark_before_dir = os.path.join(self.output_directory, "imgIOTest_dark_before")
        saver.image_save(dark_before, dark_before_dir, out_format=img_format)
        dark_after_dir = os.path.join(self.output_directory, "imgIOTest_dark_after")
        saver.image_save(dark_after, dark_after_dir, out_format=img_format)

        data_as_stack = False
        self.assert_files_exist(os.path.join(self.output_directory, saver.DEFAULT_NAME_PREFIX), img_format,
                                data_as_stack, images.data.shape[0])

        flat_before_dir = os.path.join(flat_before_dir, saver.DEFAULT_NAME_PREFIX)
        self.assert_files_exist(flat_before_dir, img_format, data_as_stack, flat_before.data.shape[0])
        flat_after_dir = os.path.join(flat_after_dir, saver.DEFAULT_NAME_PREFIX)
        self.assert_files_exist(flat_after_dir, img_format, data_as_stack, flat_after.data.shape[0])

        dark_before_dir = os.path.join(dark_before_dir, saver.DEFAULT_NAME_PREFIX)
        self.assert_files_exist(dark_before_dir, img_format, data_as_stack, dark_before.data.shape[0])
        dark_after_dir = os.path.join(dark_after_dir, saver.DEFAULT_NAME_PREFIX)
        self.assert_files_exist(dark_after_dir, img_format, data_as_stack, dark_after.data.shape[0])

        flat_before_filename = f"{flat_before_dir}_{''.zfill(saver.DEFAULT_ZFILL_LENGTH)}.{img_format}"
        flat_after_filename = f"{flat_after_dir}_{''.zfill(saver.DEFAULT_ZFILL_LENGTH)}.{img_format}"
        dark_before_filename = f"{dark_before_dir}_{''.zfill(saver.DEFAULT_ZFILL_LENGTH)}.{img_format}"
        dark_after_filename = f"{dark_after_dir}_{''.zfill(saver.DEFAULT_ZFILL_LENGTH)}.{img_format}"

        dataset = loader.load(self.output_directory,
                              input_path_flat_before=flat_before_filename,
                              input_path_flat_after=flat_after_filename,
                              input_path_dark_before=dark_before_filename,
                              input_path_dark_after=dark_after_filename,
                              in_format=img_format,
                              indices=loader_indices)
        loaded_images = dataset.sample

        if loader_indices:
            assert len(loaded_images.data) == expected_len, \
                "The length of the loaded data doesn't " \
                "match the expected length: {0}, " \
                "Got: {1}".format(
                    expected_len, len(loaded_images.data))

            # crop the original images to make sure the tests is correct
            images.data = images.data[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(loaded_images.data, images.data)
        # we only check the first image because they will be
        # averaged out when loaded! The initial images are only 3s
        npt.assert_equal(dataset.flat_before.data, flat_before.data)
        npt.assert_equal(dataset.dark_before.data, dark_before.data)
        npt.assert_equal(dataset.flat_after.data, flat_after.data)
        npt.assert_equal(dataset.dark_after.data, dark_after.data)

    def test_metadata_round_trip(self):
        # Create dummy image stack
        sample = th.gen_img_numpy_rand()
        images = ImageStack(sample)
        images.metadata['message'] = 'hello, world!'

        # Save image stack
        saver.image_save(images, self.output_directory)

        # Load image stack back
        dataset = loader.load(self.output_directory)
        loaded_images = dataset.sample

        # Ensure properties have been preserved
        self.assertEqual(loaded_images.metadata, images.metadata)

    def test_nexus_save(self):
        sd = StrictDataset(th.generate_images())
        path = "nexus/file/path"
        sample_name = "sample-name"

        with h5py.File(path, "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, sample_name)

            assert _decode_nexus_class(nexus_file["entry1"]) == "NXentry"
            assert _decode_nexus_class(nexus_file["entry1"]["tomo_entry"]) == "NXsubentry"

            tomo_entry = nexus_file["entry1"]["tomo_entry"]

            assert np.array(tomo_entry["definition"]).tostring().decode("utf-8") == "NXtomo"
            assert _decode_nexus_class(tomo_entry["instrument"]) == "NXinstrument"

            assert _decode_nexus_class(tomo_entry["instrument"]["detector"]) == "NXdetector"
            npt.assert_array_equal(np.array(tomo_entry["instrument"]["detector"]["data"]), sd.sample.data)
            npt.assert_array_equal(np.array(tomo_entry["instrument"]["detector"]["image_key"]),
                                   [0 for _ in range(sd.sample.data.shape[0])])

            assert _decode_nexus_class(tomo_entry["sample"]) == "NXsample"
            assert np.array(tomo_entry["sample"]["name"]).tostring().decode("utf-8") == sample_name
            npt.assert_array_equal(np.array(tomo_entry["sample"]["rotation_angle"]),
                                   sd.sample.projection_angles().value)

            self.assertEqual(tomo_entry["data"]["data"], tomo_entry["instrument"]["detector"]["data"])
            self.assertEqual(tomo_entry["data"]["rotation_angle"], tomo_entry["sample"]["rotation_angle"])
            self.assertEqual(tomo_entry["data"]["image_key"], tomo_entry["instrument"]["detector"]["image_key"])


if __name__ == '__main__':
    unittest.main()
