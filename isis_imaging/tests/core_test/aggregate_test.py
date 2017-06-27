from __future__ import absolute_import, division, print_function

import os
import tempfile
import unittest

import numpy as np

from isis_imaging.core.aggregate import aggregate
from isis_imaging.core.configs.recon_config import ReconstructionConfig
from isis_imaging.core.io import loader
from isis_imaging.core.io.saver import Saver
from isis_imaging.tests import test_helper as th


class AggregateTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AggregateTest, self).__init__(*args, **kwargs)

        # force silent outputs
        self.config = ReconstructionConfig.empty_init()
        self.config.func.verbosity = 0

    def create_saver(self):
        return Saver(self.config)

    def tearDown(self):
        """
        Cleanup, Make sure all files are deleted from tmp
        """
        try:
            th.delete_files(folder='pre_processed')
        except OSError:
            # no preprocessed images were saved
            pass
        try:
            th.delete_files(folder='reconstructed')
        except OSError:
            # no reconstructed images were saved
            pass

        try:
            th.delete_files(folder='converted')
        except OSError:
            # no reconstructed images were saved
            pass

        try:
            th.delete_files(folder='aggregated')
        except OSError:
            # no reconstructed images were saved
            pass

        try:
            th.delete_files(folder='aggregate')
        except OSError:
            # no reconstructed images were saved
            pass

    def test_aggregate_single_folder_sum_fits(self):
        self.do_aggregate_single_folder('fits', 'fits', 'sum')

    def test_aggregate_single_folder_sum_tiff(self):
        self.do_aggregate_single_folder('tiff', 'tiff', 'sum')

    def test_aggregate_single_folder_avg_fits(self):
        self.do_aggregate_single_folder('fits', 'fits', 'avg')

    def test_aggregate_single_folder_avg_tiff(self):
        self.do_aggregate_single_folder('tiff', 'tiff', 'avg')

    def do_aggregate_single_folder(self,
                                   img_format,
                                   convert_format,
                                   mode='sum'):
        # this just converts between the formats, but not NXS!
        # create some images
        images = th.gen_img_shared_array()
        if 'sum' == mode:
            expected = images.sum(axis=0, dtype=np.float32)
        else:
            expected = images.mean(axis=0, dtype=np.float32)
        aggregate_angles = 7
        stack = False
        parallel = False
        saver = self.create_saver()

        with tempfile.NamedTemporaryFile() as f:
            aggregate_path = os.path.dirname(f.name) + '/aggregate'
            # save out 5 'angles'
            for i in range(aggregate_angles):
                angle_path = aggregate_path + '/angle' + str(i)
                saver._output_path = angle_path
                saver._img_format = img_format
                saver._data_as_stack = stack
                # do the actual saving out, directories will be created here
                saver.save(
                    images,
                    angle_path,
                    'out_angle',
                    img_format=saver._img_format)

            # aggregate them
            conf = self.config
            conf.func.aggregate = ['0', '10', mode]
            # select angles 0 - 4 (aggregate_angles is 5 so we subtract 1)
            conf.func.aggregate_angles = ['0', str(aggregate_angles - 1)]
            conf.func.aggregate_single_folder_output = True
            conf.func.input_path = aggregate_path
            conf.func.in_format = saver._img_format
            conf.func.out_format = convert_format
            aggregate_output_path = os.path.dirname(f.name) + '/aggregated'
            conf.func.output_path = aggregate_output_path
            # because we need to write in the same folder
            conf.func.overwrite_all = True
            conf.func.convert_prefix = 'aggregated'
            aggregate.execute(conf)

            # load them back
            # compare data to original
            # this does not load any flats or darks as they were not saved out
            sample = loader.load(
                aggregate_output_path,
                img_format=saver._img_format,
                parallel_load=parallel)

            for i in sample:
                th.assert_equals(i, expected)

            th.assert_files_exist(self,
                                  aggregate_output_path + '/out_' + mode + '_0_10_',
                                  saver._img_format, single_file=saver._data_as_stack, num_images=aggregate_angles)

    def test_aggregate_not_single_folder_sum_fits(self):
        self.do_aggregate_not_single_folder('fits', 'fits', 'sum')

    def test_aggregate_not_single_folder_sum_tiff(self):
        self.do_aggregate_not_single_folder('tiff', 'tiff', 'sum')

    def test_aggregate_not_single_folder_avg_fits(self):
        self.do_aggregate_not_single_folder('fits', 'fits', 'avg')

    def test_aggregate_not_single_folder_avg_tiff(self):
        self.do_aggregate_not_single_folder('tiff', 'tiff', 'avg')

    def do_aggregate_not_single_folder(self,
                                       img_format,
                                       convert_format,
                                       mode='sum'):
        # this just converts between the formats, but not NXS!
        # create some images
        images = th.gen_img_shared_array()
        if 'sum' == mode:
            expected = images.sum(axis=0, dtype=np.float32)
        else:
            expected = images.mean(axis=0, dtype=np.float32)
        aggregate_angles = 7
        stack = False
        parallel = False
        saver = self.create_saver()

        with tempfile.NamedTemporaryFile() as f:
            aggregate_path = os.path.dirname(f.name) + '/aggregate'
            # keep the angle paths for the load later
            angle_paths = []
            # save out 5 'angles'
            for i in range(aggregate_angles):
                angle_paths.append(aggregate_path + '/angle' + str(i))
                saver._output_path = angle_paths[i]
                saver._img_format = img_format
                saver._data_as_stack = stack
                saver._overwrite_all = True
                # do the actual saving out, directories will be created here
                saver.save(
                    images,
                    angle_paths[i],
                    'out_angle',
                    swap_axes=False,
                    img_format=saver._img_format)

            # aggregate them
            conf = self.config
            conf.func.aggregate = ['0', '10', mode]
            # select angles 0 - 4 (starts from 0 so -1)
            conf.func.aggregate_angles = ['0', str(aggregate_angles - 1)]
            conf.func.aggregate_single_folder_output = False
            conf.func.input_path = aggregate_path
            conf.func.in_format = saver._img_format
            conf.func.out_format = convert_format
            aggregate_output_path = os.path.dirname(f.name) + '/aggregated'
            conf.func.output_path = aggregate_output_path
            conf.func.overwrite_all = True
            conf.func.convert_prefix = 'aggregated'
            aggregate.execute(conf)

            # load them back
            # compare data to original
            # this does not load any flats or darks as they were not saved out
            for i in range(aggregate_angles):
                angle_path = os.path.dirname(
                    f.name) + '/aggregated/angle_' + mode + str(i)

                sample = loader.load(
                    angle_path,
                    img_format=saver._img_format,
                    parallel_load=parallel)

                for i in sample:
                    th.assert_equals(i, expected)

                # we leave it as '00_1' here and leave the num_images parameter
                # this means that an additional 0 will be appended to the
                # filename: out_...00_10 and will get the correct file name.
                # This is a cheat to avoid an additional if statement
                th.assert_files_exist(self,
                                      angle_path + '/out_' + mode + '00_1',
                                      saver._img_format,
                                      single_file=saver._data_as_stack,
                                      num_images=1)


if __name__ == '__main__':
    unittest.main()
