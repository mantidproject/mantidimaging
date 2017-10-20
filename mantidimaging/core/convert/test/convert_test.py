from __future__ import absolute_import, division, print_function

import logging
import unittest

import numpy.testing as npt

from mantidimaging.core.convert import convert
from mantidimaging.core.io import loader
from mantidimaging.test.file_outputting_test_case import (
        FileOutputtingTestCase)
from mantidimaging.test import test_helper as th


class ConvertTest(FileOutputtingTestCase):
    """
    This test actually tests the saver and loader modules too, but
    it isn't focussed on them
    """

    def __init__(self, *args, **kwargs):
        super(ConvertTest, self).__init__(*args, **kwargs)

        # force silent outputs
        from mantidimaging.core.configs.recon_config import (
                ReconstructionConfig)
        self.config = ReconstructionConfig.empty_init()
        self.config.func.log_level = logging.CRITICAL

    def create_saver(self):
        from mantidimaging.core.io.saver import Saver
        return Saver(self.config)

    def test_convert_fits_fits_nostack(self):
        self.do_convert(
            img_format='fits',
            convert_format='fits',
            stack=False,
            parallel=False)

    def test_convert_fits_tiff_nostack(self):
        self.do_convert(
            img_format='fits',
            convert_format='tiff',
            stack=False,
            parallel=False)

    def do_convert(self, img_format, convert_format, stack, parallel=False):
        # this just converts between the formats, but not NXS!
        # create some images
        expected_images = th.gen_img_shared_array()
        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = img_format
        saver._save_preproc = True
        saver._data_as_stack = stack
        saver._overwrite_all = True

        # save them out
        saver.save_preproc_images(expected_images)

        preproc_output_path = saver._output_path + '/pre_processed'

        # convert them
        conf = self.config
        conf.func.input_path = preproc_output_path
        conf.func.in_format = saver._out_format
        converted_output_path = saver._output_path + '/converted'
        conf.func.output_path = converted_output_path
        conf.func.out_format = convert_format
        conf.func.data_as_stack = stack
        conf.func.convert_prefix = 'converted'
        convert.execute(conf)

        # load them back
        # compare data to original
        # this odes not load any flats or darks as they were not saved out
        loaded_images = loader.load(
            converted_output_path,
            in_format=convert_format,
            parallel_load=parallel)

        npt.assert_equal(loaded_images.get_sample(), expected_images)

    def test_convert_fits_nxs_stack(self):
        # NXS is only supported for stack
        self.do_convert_to_nxs(
            img_format='fits', convert_format='nxs', stack=True)

    def test_convert_tiff_nxs_stack(self):
        # NXS is only supported for stack
        self.do_convert_to_nxs(
            img_format='tiff', convert_format='nxs', stack=True)

    def do_convert_to_nxs(self, img_format, convert_format, stack):
        # this saves out different formats to a nxs stack
        # create some images
        parallel = False
        expected_images = th.gen_img_shared_array()
        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = img_format
        saver._data_as_stack = stack
        saver._save_preproc = True
        saver._overwrite_all = True

        # save them out
        saver.save_preproc_images(expected_images)
        preproc_output_path = saver._output_path + '/pre_processed'

        # convert them
        conf = self.config
        conf.func.input_path = preproc_output_path
        conf.func.in_format = saver._out_format
        converted_output_path = saver._output_path + '/converted'
        conf.func.output_path = converted_output_path
        conf.func.out_format = convert_format
        conf.func.data_as_stack = stack
        conf.func.convert_prefix = 'converted'
        convert.execute(conf)

        # load them back
        # compare data to original
        # this odes not load any flats or darks as they were not saved out
        loaded_images = loader.load(
            converted_output_path,
            in_format=convert_format,
            parallel_load=parallel)

        npt.assert_equal(loaded_images.get_sample(), expected_images)

    def test_convert_nxs_fits_nostack(self):
        self.do_convert_from_nxs(
            img_format='nxs', convert_format='fits', stack=False)

    def test_convert_nxs_tiff_nostack(self):
        self.do_convert_from_nxs(
            img_format='nxs', convert_format='tiff', stack=False)

    def do_convert_from_nxs(self, img_format, convert_format, stack):
        # this saves out a nexus stack and then loads it in different formats
        # create some images
        parallel = False
        expected_images = th.gen_img_shared_array()
        # expected none, because NXS doesn't currently save
        # out flat or dark image
        saver = self.create_saver()
        saver._output_path = self.output_directory
        saver._out_format = img_format
        # force saving out as STACK because we're saving NXS files
        saver._data_as_stack = True
        saver._save_preproc = True
        saver._overwrite_all = True

        # save them out
        saver.save_preproc_images(expected_images)
        preproc_output_path = saver._output_path + '/pre_processed'

        # convert them
        conf = self.config
        conf.func.input_path = preproc_output_path
        conf.func.in_format = saver._out_format
        converted_output_path = saver._output_path + '/converted'
        conf.func.output_path = converted_output_path
        conf.func.out_format = convert_format
        conf.func.data_as_stack = stack
        conf.func.convert_prefix = 'converted'
        convert.execute(conf)

        # load them back and compare data to original
        # this does not load any flats or darks as they were not saved out
        loaded_images = loader.load(converted_output_path,
                                    in_format=convert_format,
                                    parallel_load=parallel)

        npt.assert_equal(loaded_images.get_sample(), expected_images)


if __name__ == '__main__':
    unittest.main()
