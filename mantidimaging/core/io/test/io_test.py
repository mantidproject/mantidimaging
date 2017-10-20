from __future__ import absolute_import, division, print_function

import logging
import os
import unittest

import numpy as np
import numpy.testing as npt

from mantidimaging.helper import initialise_logging
from mantidimaging.core.configs.recon_config import ReconstructionConfig
from mantidimaging.core.io import loader
from mantidimaging.core.io.saver import Saver, generate_names
from mantidimaging.test.file_outputting_test_case import (
        FileOutputtingTestCase)
from mantidimaging.test import test_helper as th


class IOTest(FileOutputtingTestCase):
    def __init__(self, *args, **kwargs):
        super(IOTest, self).__init__(*args, **kwargs)

        # force silent outputs
        initialise_logging()
        self.config = ReconstructionConfig.empty_init()
        self.config.func.log_level = logging.CRITICAL

    def create_saver(self):
        return Saver(self.config)

    def assert_files_exist(self,
                           base_name,
                           file_format,
                           stack=True,
                           num_images=1,
                           indices=None):

        if not stack:
            # this way we account for only selected indices in the filenames
            if not indices:
                indices = [0, num_images, 1]

            filenames = generate_names(
                base_name, indices, num_images, out_format=file_format)

            for f in filenames:
                self.assertTrue(os.path.isfile(f))

        else:
            filename = base_name + '.' + file_format
            self.assertTrue(os.path.isfile(filename))

    def test_preproc_fits_par(self):
        self.do_preproc('fits', parallel=True)

    def test_preproc_fits_par_loader_indices_4_5(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_fits_par_loader_indices_0_7(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_fits_par_loader_indices_3_9(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_fits_par_loader_indices_5_9(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[5, 9, 1], expected_len=4)

    def test_preproc_fits_par_saver_indices_0_5(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_fits_par_saver_indices_0_2(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_fits_par_saver_indices_3_10(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_fits_par_saver_indices_7_10(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[7, 10, 1], expected_len=3)

    # fits sequential
    def test_preproc_fits_seq(self):
        self.do_preproc('fits', parallel=False)

    # fits sequential loader indices
    def test_preproc_fits_seq_loader_indices_4_5(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_fits_seq_loader_indices_0_7(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_fits_seq_loader_indices_3_9(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_fits_seq_loader_indices_5_9(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[5, 9, 1], expected_len=4)

    # fits sequential saver indices
    def test_preproc_fits_seq_saver_indices_0_5(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_fits_seq_saver_indices_0_2(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_fits_seq_saver_indices_3_10(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_fits_seq_saver_indices_7_10(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[7, 10, 1], expected_len=3)

    # tiff tests
    def test_preproc_tiff_par(self):
        self.do_preproc('tiff', parallel=True)

    def test_preproc_tiff_par_loader_indices_4_5(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_tiff_par_loader_indices_0_7(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_tiff_par_loader_indices_3_9(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_tiff_par_loader_indices_5_9(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[5, 9, 1], expected_len=4)

    def test_preproc_tiff_par_saver_indices_0_5(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_tiff_par_saver_indices_0_2(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_tiff_par_saver_indices_3_10(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_tiff_par_saver_indices_7_10(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[7, 10, 1], expected_len=3)

    # tiff sequential
    def test_preproc_tiff_seq(self):
        self.do_preproc('tiff', parallel=False)

    # tiff sequential loader indices
    def test_preproc_tiff_seq_loader_indices_4_5(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_tiff_seq_loader_indices_0_7(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_tiff_seq_loader_indices_3_9(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_tiff_seq_loader_indices_5_9(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[5, 9, 1], expected_len=4)

    # tiff sequential saver indices
    def test_preproc_tiff_seq_saver_indices_0_5(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_tiff_seq_saver_indices_0_2(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_tiff_seq_saver_indices_3_10(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_tiff_seq_saver_indices_7_10(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[7, 10, 1], expected_len=3)

    def do_preproc(self,
                   img_format,
                   parallel=False,
                   loader_indices=None,
                   expected_len=None,
                   saver_indices=None):
        expected_images = th.gen_img_shared_array_with_val(42.)
        saver = self.create_saver()
        saver._output_path = self. output_directory
        saver._out_format = img_format
        saver._save_preproc = True
        saver._swap_axes = False
        # this only affects enumeration
        saver._indices = saver_indices
        data_as_stack = False

        # saver indices only affects the enumeration of the data
        if saver_indices:
            # crop the original images to make sure the tests is correct
            expected_images = expected_images[saver_indices[0]:saver_indices[1]]

        saver.save_preproc_images(expected_images)

        # create the same path as the saved out preproc images
        preproc_output_path = saver._output_path + '/pre_processed/'

        self.assert_files_exist(os.path.join(preproc_output_path, 'out_preproc_image'),
                                saver._out_format, data_as_stack,
                                expected_images.shape[0], saver_indices)

        # this does not load any flats or darks as they were not saved out
        loaded_images = loader.load(preproc_output_path, in_format=saver._out_format,
                                    cores=1, parallel_load=parallel, indices=loader_indices)

        if loader_indices:
            assert len(loaded_images.get_sample()) == expected_len, "The length of the loaded data does not " \
                "match the expected length! Expected: {0}, " \
                "Got {1}".format(expected_len, len(
                    loaded_images.get_sample()))

            # crop the original images to make sure the tests is correct
            expected_images = expected_images[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(loaded_images.get_sample(), expected_images)

    def test_save_nxs_seq(self):
        self.do_preproc_nxs(parallel=False)

    def test_save_nxs_seq_indices_0_4(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[0, 4, 1], expected_len=4)

    def test_save_nxs_seq_indices_5_9(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[5, 9, 1], expected_len=4)

    def test_save_nxs_par(self):
        self.do_preproc_nxs(parallel=True)

    def test_save_nxs_par_indices_6_7(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[6, 7, 1], expected_len=1)

    def test_save_nxs_par_indices_3_4(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[3, 4, 1], expected_len=1)

    def do_preproc_nxs(self,
                       save_out_img_format='nxs',
                       parallel=False,
                       loader_indices=None,
                       expected_len=None):
        """
        There are no tests with saver indices, because
        this only saves out one file,
        and the saver indices are only used for enumeration,
        so it doesn't make sense to test it
        """
        expected_images = th.gen_img_shared_array_with_val(42.)
        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._save_preproc = True
        saver._out_format = save_out_img_format
        saver._swap_axes = False
        data_as_stack = True

        saver.save_preproc_images(expected_images)

        # create the same path as the saved out preproc images
        preproc_output_path = os.path.join(
            saver._output_path, 'pre_processed/')

        self.assert_files_exist(os.path.join(preproc_output_path, 'out_preproc_image'),
                                saver._out_format, data_as_stack,
                                expected_images.shape[0])

        # this does not load any flats or darks as they were not saved out!
        # this is a race condition versus the saving from the saver
        # when load is executed in parallel, the 8 threads try to
        # load the data too fast, and the data loaded is corrupted
        # hard coded 1 core to avoid race condition
        images = loader.load(preproc_output_path, in_format=saver._out_format, cores=1,
                             parallel_load=parallel, indices=loader_indices)

        if loader_indices:
            assert len(
                images.get_sample()
            ) == expected_len, "The length of the loaded data does not " \
                               "match the expected length! Expected: {0}, " \
                               "Got {1}".format(
                expected_len, len(images.get_sample()))

            # crop the original images to make sure the tests is correct
            expected_images = expected_images[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(images.get_sample(), expected_images)

        self.assert_files_exist(os.path.join(preproc_output_path, 'out_preproc_image'),
                                saver._out_format, data_as_stack,
                                expected_images.shape[0])

    def test_do_recon_fits(self):
        self.do_recon(img_format='fits', horiz_slices=False)

    def test_do_recon_tiff(self):
        self.do_recon(img_format='tiff', horiz_slices=False)

    def test_do_recon_fits_horiz(self):
        self.do_recon(img_format='fits', horiz_slices=True)

    def test_do_recon_tiff_horiz(self):
        self.do_recon(img_format='tiff', horiz_slices=True)

    def test_do_recon_fits_indices_0_8(self):
        self.do_recon(
            img_format='fits', horiz_slices=False, saver_indices=[0, 8, 1])

    def test_do_recon_tiff_indices_0_4(self):
        self.do_recon(
            img_format='tiff', horiz_slices=False, saver_indices=[0, 4, 1])

    def do_recon(self, img_format, horiz_slices=False, saver_indices=None):
        """
        Note: saver_indices doesn't work with horiz_slices
        """
        images = th.gen_img_shared_array()
        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = img_format
        saver._swap_axes = False
        saver._save_horiz_slices = horiz_slices
        # this only affects enumeration
        saver._indices = saver_indices
        data_as_stack = False

        saver.save_recon_output(images)

        recon_output_path = os.path.join(
            saver._output_path, 'reconstructed/')

        self.assert_files_exist(os.path.join(recon_output_path, 'recon_slice'),
                                saver._out_format, data_as_stack,
                                images.shape[0], saver_indices)

        if horiz_slices:
            self.assert_files_exist(
                os.path.join(recon_output_path,
                             'horiz_slices/recon_horiz'),
                saver._out_format, data_as_stack, images.shape[1],
                saver_indices)

    def test_load_sample_flat_and_dark(self,
                                       img_format='tiff',
                                       parallel=False,
                                       loader_indices=None,
                                       expected_len=None,
                                       saver_indices=None):
        images = th.gen_img_shared_array_with_val(42.)
        flat = th.gen_img_shared_array_with_val(42.)
        dark = th.gen_img_shared_array_with_val(42.)

        flat[:] = 3
        dark[:] = 3

        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = img_format
        saver._save_preproc = True
        saver._swap_axes = False
        # this only affects enumeration
        saver._indices = saver_indices
        data_as_stack = False

        # saver indices only affects the enumeration of the data
        if saver_indices:
            # crop the original images to make sure the tests is correct
            images = images[saver_indices[0]:saver_indices[1]]

        saver.save_preproc_images(images)
        saver._preproc_dir = "imgIOTest_flat"
        saver.save_preproc_images(flat)
        saver._preproc_dir = "imgIOTest_dark"
        saver.save_preproc_images(dark)

        # create the same path as the saved out preproc images
        sample_output_path = os.path.join(
            saver._output_path, 'pre_processed')
        flat_output_path = os.path.join(
            saver._output_path, 'imgIOTest_flat')
        dark_output_path = os.path.join(
            saver._output_path, 'imgIOTest_dark')

        self.assert_files_exist(os.path.join(sample_output_path, 'out_preproc_image'),
                                saver._out_format, data_as_stack,
                                images.shape[0], loader_indices or
                                saver_indices)

        self.assert_files_exist(
            os.path.join(flat_output_path,
                         'out_preproc_image'), saver._out_format,
            data_as_stack, flat.shape[0], loader_indices or saver_indices)

        self.assert_files_exist(
            os.path.join(dark_output_path,
                         'out_preproc_image'), saver._out_format,
            data_as_stack, dark.shape[0], loader_indices or saver_indices)

        loaded_images = loader.load(
                sample_output_path, flat_output_path, dark_output_path,
                in_format=saver._out_format, cores=1, parallel_load=parallel,
                indices=loader_indices)

        if loader_indices:
            assert len(loaded_images.get_sample()) == expected_len, "The length of the loaded data doesn't " \
                "match the expected length: {0}, " \
                "Got: {1}".format(expected_len, len(loaded_images.get_sample()))

            # crop the original images to make sure the tests is correct
            images = images[loader_indices[0]:loader_indices[1]]

        npt.assert_equal(loaded_images.get_sample(), images)
        # we only check the first image because they will be
        # averaged out when loaded! The initial images are only 3s
        npt.assert_equal(loaded_images.get_flat(), flat[0])
        npt.assert_equal(loaded_images.get_dark(), dark[0])

    def test_read_in_shape_from_config(self):
        images = th.gen_img_shared_array_with_val(42.)

        expected_shape = images.shape
        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = "tiff"
        saver._save_preproc = True
        saver._swap_axes = False

        config = ReconstructionConfig.empty_init()
        config.func.input_path = os.path.join(
            saver._output_path, saver._preproc_dir)
        config.func.in_format = saver._out_format
        saver.save_preproc_images(images)

        shape = loader.read_in_shape_from_config(config)

        self.assertEqual(shape, expected_shape)

    def test_load_from_config(self):
        images = th.gen_img_shared_array_with_val(42.)

        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = "tiff"
        saver._save_preproc = True
        saver._swap_axes = False

        config = ReconstructionConfig.empty_init()
        config.func.input_path = os.path.join(
            saver._output_path, saver._preproc_dir)
        config.func.in_format = saver._out_format
        saver.save_preproc_images(images)

        loaded_images = loader.load_from_config(config)

        npt.assert_equal(images, loaded_images.get_sample())

    def test_construct_sinograms(self):
        images = th.gen_img_shared_array_with_val(42.)
        exp_sinograms = np.swapaxes(images, 0, 1)

        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = "tiff"
        saver._save_preproc = True
        saver._swap_axes = False

        config = ReconstructionConfig.empty_init()
        config.func.input_path = os.path.join(
            saver._output_path, saver._preproc_dir)
        config.func.in_format = saver._out_format
        saver.save_preproc_images(images)

        config.func.construct_sinograms = True
        loaded_images = loader.load_from_config(config)

        npt.assert_equal(exp_sinograms, loaded_images.get_sample())


if __name__ == '__main__':
    unittest.main()
