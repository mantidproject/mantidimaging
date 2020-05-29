import os
import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import Images
from mantidimaging.core.io import loader
from mantidimaging.core.io import saver
from mantidimaging.helper import initialise_logging
from mantidimaging.test_helpers import FileOutputtingTestCase


class IOTest(FileOutputtingTestCase):
    def __init__(self, *args, **kwargs):
        super(IOTest, self).__init__(*args, **kwargs)

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

    def test_preproc_fits_par(self):
        self.do_preproc('fits', parallel=True)

    def test_preproc_fits_par_loader_indices_4_5(self):
        self.do_preproc('fits', parallel=True, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_fits_par_loader_indices_0_7(self):
        self.do_preproc('fits', parallel=True, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_fits_par_loader_indices_3_9(self):
        self.do_preproc('fits', parallel=True, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_fits_par_loader_indices_5_9(self):
        self.do_preproc('fits', parallel=True, loader_indices=[5, 9, 1], expected_len=4)

    def test_preproc_fits_par_saver_indices_0_5(self):
        self.do_preproc('fits', parallel=True, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_fits_par_saver_indices_0_2(self):
        self.do_preproc('fits', parallel=True, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_fits_par_saver_indices_3_10(self):
        self.do_preproc('fits', parallel=True, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_fits_par_saver_indices_7_10(self):
        self.do_preproc('fits', parallel=True, saver_indices=[7, 10, 1], expected_len=3)

    # fits sequential
    def test_preproc_fits_seq(self):
        self.do_preproc('fits', parallel=False)

    # fits sequential loader indices
    def test_preproc_fits_seq_loader_indices_4_5(self):
        self.do_preproc('fits', parallel=False, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_fits_seq_loader_indices_0_7(self):
        self.do_preproc('fits', parallel=False, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_fits_seq_loader_indices_3_9(self):
        self.do_preproc('fits', parallel=False, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_fits_seq_loader_indices_5_9(self):
        self.do_preproc('fits', parallel=False, loader_indices=[5, 9, 1], expected_len=4)

    # fits sequential saver indices
    def test_preproc_fits_seq_saver_indices_0_5(self):
        self.do_preproc('fits', parallel=False, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_fits_seq_saver_indices_0_2(self):
        self.do_preproc('fits', parallel=False, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_fits_seq_saver_indices_3_10(self):
        self.do_preproc('fits', parallel=False, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_fits_seq_saver_indices_7_10(self):
        self.do_preproc('fits', parallel=False, saver_indices=[7, 10, 1], expected_len=3)

    # tiff tests
    def test_preproc_tiff_par(self):
        self.do_preproc('tiff', parallel=True)

    def test_preproc_tiff_par_loader_indices_4_5(self):
        self.do_preproc('tiff', parallel=True, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_tiff_par_loader_indices_0_7(self):
        self.do_preproc('tiff', parallel=True, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_tiff_par_loader_indices_3_9(self):
        self.do_preproc('tiff', parallel=True, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_tiff_par_loader_indices_5_9(self):
        self.do_preproc('tiff', parallel=True, loader_indices=[5, 9, 1], expected_len=4)

    def test_preproc_tiff_par_saver_indices_0_5(self):
        self.do_preproc('tiff', parallel=True, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_tiff_par_saver_indices_0_2(self):
        self.do_preproc('tiff', parallel=True, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_tiff_par_saver_indices_3_10(self):
        self.do_preproc('tiff', parallel=True, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_tiff_par_saver_indices_7_10(self):
        self.do_preproc('tiff', parallel=True, saver_indices=[7, 10, 1], expected_len=3)

    # tiff sequential
    def test_preproc_tiff_seq(self):
        self.do_preproc('tiff', parallel=False)

    # tiff sequential loader indices
    def test_preproc_tiff_seq_loader_indices_4_5(self):
        self.do_preproc('tiff', parallel=False, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_tiff_seq_loader_indices_0_7(self):
        self.do_preproc('tiff', parallel=False, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_tiff_seq_loader_indices_3_9(self):
        self.do_preproc('tiff', parallel=False, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_tiff_seq_loader_indices_5_9(self):
        self.do_preproc('tiff', parallel=False, loader_indices=[5, 9, 1], expected_len=4)

    # tiff sequential saver indices
    def test_preproc_tiff_seq_saver_indices_0_5(self):
        self.do_preproc('tiff', parallel=False, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_tiff_seq_saver_indices_0_2(self):
        self.do_preproc('tiff', parallel=False, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_tiff_seq_saver_indices_3_10(self):
        self.do_preproc('tiff', parallel=False, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_tiff_seq_saver_indices_7_10(self):
        self.do_preproc('tiff', parallel=False, saver_indices=[7, 10, 1], expected_len=3)

    def do_preproc(self,
                   img_format,
                   parallel=False,
                   loader_indices=None,
                   expected_len=None,
                   saver_indices=None,
                   data_as_stack=False):
        expected_images = th.gen_img_shared_array_with_val(42.)

        # saver indices only affects the enumeration of the data
        if saver_indices:
            # crop the original images to make sure the tests is correct
            expected_images = \
                expected_images[saver_indices[0]:saver_indices[1]]

        # saver.save_preproc_images(expected_images)
        saver.save(expected_images, self.output_directory, out_format=img_format, indices=saver_indices)

        self.assert_files_exist(os.path.join(self.output_directory, saver.DEFAULT_NAME_PREFIX), img_format,
                                data_as_stack, expected_images.shape[0], saver_indices)

        # this does not load any flats or darks as they were not saved out
        loaded_images = loader.load(self.output_directory, in_format=img_format, indices=loader_indices)

        if loader_indices:
            assert len(loaded_images.sample) == expected_len, \
                "The length of the loaded data does not " \
                "match the expected length! Expected: {0}, " \
                "Got {1}".format(expected_len, len(
                    loaded_images.sample))

            expected_images = expected_images[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(loaded_images.sample, expected_images)

    def test_save_nxs_seq(self):
        # self.do_preproc_nxs(parallel=False)
        self.do_preproc('nxs', data_as_stack=True)

    def test_save_nxs_seq_indices_0_4(self):
        # self.do_preproc_nxs(parallel=False, loader_indices=[0, 4, 1], expected_len=4)
        self.do_preproc('nxs', data_as_stack=True, parallel=False, loader_indices=[0, 4, 1], expected_len=4)

    def test_save_nxs_seq_indices_5_9(self):
        self.do_preproc('nxs', data_as_stack=True, parallel=False, loader_indices=[5, 9, 1], expected_len=4)

    def test_save_nxs_par(self):
        self.do_preproc('nxs', parallel=True, data_as_stack=True)

    def test_save_nxs_par_indices_6_7(self):
        self.do_preproc('nxs', parallel=True, data_as_stack=True, loader_indices=[6, 7, 1], expected_len=1)

    def test_save_nxs_par_indices_3_4(self):
        self.do_preproc('nxs', parallel=True, data_as_stack=True, loader_indices=[6, 7, 1], expected_len=1)

    def test_load_sample_flat_and_dark(self,
                                       img_format='tiff',
                                       loader_indices=None,
                                       expected_len=None,
                                       saver_indices=None):
        images = th.gen_img_shared_array_with_val(42.)
        flat = th.gen_img_shared_array_with_val(42.)
        dark = th.gen_img_shared_array_with_val(42.)

        flat[:] = 3
        dark[:] = 3

        # this only affects enumeration
        saver._indices = saver_indices
        data_as_stack = False

        # saver indices only affects the enumeration of the data
        if saver_indices:
            # crop the original images to make sure the test is checking the
            # indices that were actually saved out
            images = images[saver_indices[0]:saver_indices[1]]

        saver.save(images, self.output_directory, out_format=img_format)
        flat_dir = os.path.join(self.output_directory, "imgIOTest_flat")
        saver.save(flat, flat_dir, out_format=img_format)
        dark_dir = os.path.join(self.output_directory, "imgIOTest_dark")
        saver.save(dark, dark_dir, out_format=img_format)

        self.assert_files_exist(os.path.join(self.output_directory, saver.DEFAULT_NAME_PREFIX), img_format,
                                data_as_stack, images.shape[0])

        self.assert_files_exist(os.path.join(flat_dir, saver.DEFAULT_NAME_PREFIX), img_format, data_as_stack,
                                flat.shape[0])

        self.assert_files_exist(os.path.join(dark_dir, saver.DEFAULT_NAME_PREFIX), img_format, data_as_stack,
                                dark.shape[0])

        loaded_images = loader.load(self.output_directory,
                                    flat_dir,
                                    dark_dir,
                                    in_format=img_format,
                                    indices=loader_indices)

        if loader_indices:
            assert len(loaded_images.sample) == expected_len, \
                "The length of the loaded data doesn't " \
                "match the expected length: {0}, " \
                "Got: {1}".format(
                    expected_len, len(loaded_images.sample))

            # crop the original images to make sure the tests is correct
            images = images[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(loaded_images.sample, images)
        # we only check the first image because they will be
        # averaged out when loaded! The initial images are only 3s
        npt.assert_equal(loaded_images.flat, flat[0])
        npt.assert_equal(loaded_images.dark, dark[0])

    def test_metadata_round_trip(self):
        # Create dummy image stack
        sample = th.gen_img_shared_array_with_val(42.)
        images = Images(sample)
        images.metadata['message'] = 'hello, world!'

        # Save image stack
        saver.save(images, self.output_directory)

        # Load image stack back
        loaded_images = loader.load(self.output_directory)

        # Ensure properties have been preserved
        self.assertEquals(loaded_images.metadata, images.metadata)


if __name__ == '__main__':
    unittest.main()
