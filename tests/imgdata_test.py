from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from tests import test_helper as th


class DataTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DataTest, self).__init__(*args, **kwargs)

        # force silent outputs
        from configs.recon_config import ReconstructionConfig
        self.config = ReconstructionConfig.empty_init()
        self.config.func.verbosity = 0

    def create_saver(self):
        from imgdata.saver import Saver
        return Saver(self.config)

    def assert_files_exist(self,
                           base_name,
                           file_format,
                           stack=True,
                           num_images=1,
                           indices=None):
        import os

        if not stack:
            # generate a list of filenames with 000000 numbers appended
            filenames = []

            # this way we account for only selected indices in the filenames
            if indices:
                start = indices[0]
                end = indices[1]
            else:
                start = 0
                end = num_images

            for i in range(start, end):
                filenames.append(base_name + '00000' + str(i) + '.' +
                                 file_format)

            for f in filenames:
                self.assertTrue(os.path.isfile(f))

        else:
            filename = base_name + '.' + file_format
            self.assertTrue(os.path.isfile(filename))

    def delete_files(self, prefix=''):
        import tempfile
        import os
        import shutil
        with tempfile.NamedTemporaryFile() as f:
            from imgdata.loader import get_file_names
            full_path = os.path.join(os.path.dirname(f.name), prefix)
            shutil.rmtree(full_path)

    def tearDown(self):
        """
        Cleanup, Make sure all files are deleted from tmp
        """
        try:
            self.delete_files(prefix='pre_processed')
        except OSError:
            # no preprocessed images were saved
            pass
        try:
            self.delete_files(prefix='reconstructed')
        except OSError:
            # no reconstructed images were saved
            pass

    def test_preproc_fits_par(self):
        self.do_preproc('fits', parallel=True)

    def test_preproc_fits_par_loader_indices_4_5(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[4, 5], expected_len=1)

    def test_preproc_fits_par_loader_indices_0_7(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[0, 7], expected_len=7)

    def test_preproc_fits_par_loader_indices_3_9(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[3, 9], expected_len=6)

    def test_preproc_fits_par_loader_indices_5_9(self):
        self.do_preproc(
            'fits', parallel=True, loader_indices=[5, 9], expected_len=4)

    def test_preproc_fits_par_saver_indices_0_5(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[0, 5], expected_len=5)

    def test_preproc_fits_par_saver_indices_0_2(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[0, 2], expected_len=2)

    def test_preproc_fits_par_saver_indices_3_10(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[3, 10], expected_len=7)

    def test_preproc_fits_par_saver_indices_7_10(self):
        self.do_preproc(
            'fits', parallel=True, saver_indices=[7, 10], expected_len=3)

    # fits sequential
    def test_preproc_fits_seq(self):
        self.do_preproc('fits', parallel=False)

    # fits sequential loader indices
    def test_preproc_fits_seq_loader_indices_4_5(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[4, 5], expected_len=1)

    def test_preproc_fits_seq_loader_indices_0_7(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[0, 7], expected_len=7)

    def test_preproc_fits_seq_loader_indices_3_9(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[3, 9], expected_len=6)

    def test_preproc_fits_seq_loader_indices_5_9(self):
        self.do_preproc(
            'fits', parallel=False, loader_indices=[5, 9], expected_len=4)

    # fits sequential saver indices
    def test_preproc_fits_seq_saver_indices_0_5(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[0, 5], expected_len=5)

    def test_preproc_fits_seq_saver_indices_0_2(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[0, 2], expected_len=2)

    def test_preproc_fits_seq_saver_indices_3_10(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[3, 10], expected_len=7)

    def test_preproc_fits_seq_saver_indices_7_10(self):
        self.do_preproc(
            'fits', parallel=False, saver_indices=[7, 10], expected_len=3)

    # tiff tests
    def test_preproc_tiff_par(self):
        self.do_preproc('tiff', parallel=True)

    def test_preproc_tiff_par_loader_indices_4_5(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[4, 5], expected_len=1)

    def test_preproc_tiff_par_loader_indices_0_7(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[0, 7], expected_len=7)

    def test_preproc_tiff_par_loader_indices_3_9(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[3, 9], expected_len=6)

    def test_preproc_tiff_par_loader_indices_5_9(self):
        self.do_preproc(
            'tiff', parallel=True, loader_indices=[5, 9], expected_len=4)

    def test_preproc_tiff_par_saver_indices_0_5(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[0, 5], expected_len=5)

    def test_preproc_tiff_par_saver_indices_0_2(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[0, 2], expected_len=2)

    def test_preproc_tiff_par_saver_indices_3_10(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[3, 10], expected_len=7)

    def test_preproc_tiff_par_saver_indices_7_10(self):
        self.do_preproc(
            'tiff', parallel=True, saver_indices=[7, 10], expected_len=3)

    # tiff sequential
    def test_preproc_tiff_seq(self):
        self.do_preproc('tiff', parallel=False)

    # tiff sequential loader indices
    def test_preproc_tiff_seq_loader_indices_4_5(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[4, 5], expected_len=1)

    def test_preproc_tiff_seq_loader_indices_0_7(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[0, 7], expected_len=7)

    def test_preproc_tiff_seq_loader_indices_3_9(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[3, 9], expected_len=6)

    def test_preproc_tiff_seq_loader_indices_5_9(self):
        self.do_preproc(
            'tiff', parallel=False, loader_indices=[5, 9], expected_len=4)

    # tiff sequential saver indices
    def test_preproc_tiff_seq_saver_indices_0_5(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[0, 5], expected_len=5)

    def test_preproc_tiff_seq_saver_indices_0_2(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[0, 2], expected_len=2)

    def test_preproc_tiff_seq_saver_indices_3_10(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[3, 10], expected_len=7)

    def test_preproc_tiff_seq_saver_indices_7_10(self):
        self.do_preproc(
            'tiff', parallel=False, saver_indices=[7, 10], expected_len=3)

    def do_preproc(self,
                   img_format,
                   parallel=False,
                   loader_indices=None,
                   expected_len=None,
                   saver_indices=None):
        images = th.gen_img_shared_array_with_val(42.)
        flat = None
        dark = None
        saver = self.create_saver()
        import tempfile
        import os
        with tempfile.NamedTemporaryFile() as f:
            saver._output_path = os.path.dirname(f.name)
            saver._img_format = img_format
            saver._save_preproc = True
            saver._swap_axes = False
            saver._indices = saver_indices
            data_as_stack = False

            saver.save_preproc_images(images)

            preproc_output_path = saver._output_path + '/pre_processed/'

            from imgdata import loader
            # this does not load any flats or darks as they were not saved out
            sample, flat_loaded, dark_loaded = loader.load(
                preproc_output_path,
                None,
                None,
                saver._img_format,
                cores=1,
                parallel_load=parallel,
                indices=loader_indices)

            if loader_indices or saver_indices:
                assert len(
                    sample
                ) == expected_len, "The length of the loaded data does not match the expected length! Expected: {0}, Actual {1}".format(
                    expected_len, len(sample))

                crop_indices = loader_indices if loader_indices is not None else saver_indices
                # crop the original images to make sure the tests is correct
                images = images[crop_indices[0]:crop_indices[1]]

            th.assert_equals(sample, images)
            th.assert_equals(flat_loaded, flat)
            th.assert_equals(dark_loaded, dark)

            self.assert_files_exist(preproc_output_path + 'out_preproc_image',
                                    saver._img_format, data_as_stack,
                                    images.shape[0], loader_indices or
                                    saver_indices)

    def test_save_nxs_seq(self):
        self.do_preproc_nxs(parallel=False)

    def test_save_nxs_seq_indices_0_4(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[0, 4], expected_len=4)

    def test_save_nxs_seq_saver_indices_0_4(self):
        self.do_preproc_nxs(
            parallel=False, saver_indices=[0, 4], expected_len=4)

    def test_save_nxs_seq_indices_5_9(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[5, 9], expected_len=4)

    def test_save_nxs_seq_saver_indices_5_9(self):
        self.do_preproc_nxs(
            parallel=False, saver_indices=[5, 9], expected_len=4)

    def test_save_nxs_par(self):
        self.do_preproc_nxs(parallel=True)

    def test_save_nxs_par_indices_6_7(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[6, 7], expected_len=1)

    def test_save_nxs_par_saver_indices_6_7(self):
        self.do_preproc_nxs(
            parallel=False, saver_indices=[6, 7], expected_len=1)

    def test_save_nxs_par_indices_3_4(self):
        self.do_preproc_nxs(
            parallel=False, loader_indices=[3, 4], expected_len=1)

    def test_save_nxs_par_saver_indices_3_4(self):
        self.do_preproc_nxs(
            parallel=False, saver_indices=[3, 4], expected_len=1)

    def do_preproc_nxs(self,
                       save_out_img_format='nxs',
                       parallel=False,
                       loader_indices=None,
                       expected_len=None,
                       saver_indices=None):
        images = th.gen_img_shared_array_with_val(42.)
        # this is different from do_preproc as we need to
        # save out flat and dark images, and they will be loaded
        # back in
        flat = None
        dark = None
        saver = self.create_saver()
        import tempfile
        import os

        with tempfile.NamedTemporaryFile() as f:
            saver._output_path = os.path.dirname(f.name)
            saver._save_preproc = True
            saver._img_format = save_out_img_format
            saver._swap_axes = False
            saver._indices = saver_indices
            data_as_stack = True

            saver.save_preproc_images(images)

            preproc_output_path = saver._output_path + '/pre_processed/'

            # this does not load any flats or darks as they were not saved out
            from imgdata import loader
            # this is a race condition versus the saving from the saver
            # when load is executed in parallel, the 8 threads try to 
            # load the data too fast, and the data loaded is corrupted
            sample, flat_loaded, dark_loaded = loader.load(
                preproc_output_path,
                None,
                None,
                saver._img_format,
                cores=1,  # hard coded 1 core to avoid race condition
                parallel_load=parallel,
                indices=loader_indices)

            if loader_indices or saver_indices:
                assert len(
                    sample
                ) == expected_len, "The length of the loaded data does not match the expected length! Expected: {0}, Actual {1}".format(
                    expected_len, len(sample))

                crop_indices = loader_indices if loader_indices is not None else saver_indices
                # crop the original images to make sure the tests is correct
                images = images[crop_indices[0]:crop_indices[1]]

            th.assert_equals(sample, images)
            th.assert_equals(flat_loaded, flat)
            th.assert_equals(dark_loaded, dark)

            self.assert_files_exist(preproc_output_path + 'out_preproc_image',
                                    saver._img_format, data_as_stack,
                                    images.shape[0])

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
            img_format='fits', horiz_slices=False, saver_indices=[0, 8])

    def test_do_recon_tiff_indices_0_4(self):
        self.do_recon(
            img_format='tiff', horiz_slices=False, saver_indices=[0, 4])

    def do_recon(self, img_format, horiz_slices=False, saver_indices=None):
        """
        Note: saver_indices doesn't work with horiz_slices
        """
        images = th.gen_img_shared_array()
        flat = None
        dark = None
        saver = self.create_saver()
        import tempfile
        import os
        with tempfile.NamedTemporaryFile() as f:
            saver._output_path = os.path.dirname(f.name)
            saver._img_format = img_format
            saver._swap_axes = False
            saver._save_horiz_slices = horiz_slices
            saver._indices = saver_indices
            data_as_stack = False

            saver.save_recon_output(images)

            recon_output_path = saver._output_path + '/reconstructed/'

            self.assert_files_exist(recon_output_path + 'recon_slice',
                                    saver._img_format, data_as_stack,
                                    images.shape[0], saver_indices)

            if horiz_slices:
                self.assert_files_exist(
                    recon_output_path + 'horiz_slices/recon_horiz',
                    saver._img_format, data_as_stack, images.shape[1],
                    saver_indices)


if __name__ == '__main__':
    unittest.main()
