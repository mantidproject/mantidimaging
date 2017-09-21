from __future__ import absolute_import, division, print_function

import logging
import os
import unittest

import numpy as np

from mantidimaging.core.aggregate import aggregate
from mantidimaging.core.configs.recon_config import ReconstructionConfig
from mantidimaging.core.io import loader
from mantidimaging.core.io.saver import Saver
from mantidimaging.tests.file_outputting_test_case import (
        FileOutputtingTestCase)
from mantidimaging.tests import test_helper as th


class AggregateTest(FileOutputtingTestCase):
    def __init__(self, *args, **kwargs):
        super(AggregateTest, self).__init__(*args, **kwargs)

        # force silent outputs
        self.config = ReconstructionConfig.empty_init()
        self.config.func.verbosity = logging.CRITICAL

    def create_saver(self):
        return Saver(self.config)

    def test_aggregate_single_folder_sum_fits(self):
        self.do_aggregate_single_folder('fits', 'fits', 'sum')

    def test_aggregate_single_folder_sum_tif(self):
        self.do_aggregate_single_folder('tif', 'tif', 'sum')

    def test_aggregate_single_folder_avg_fits(self):
        self.do_aggregate_single_folder('fits', 'fits', 'avg')

    def test_aggregate_single_folder_avg_tif(self):
        self.do_aggregate_single_folder('tif', 'tif', 'avg')

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

        aggregate_path = os.path.join(self.output_directory, 'aggregate')
        # save out 5 'angles'
        for i in range(aggregate_angles):
            angle_path = aggregate_path + '/angle' + str(i)
            saver._output_path = angle_path
            saver._out_format = img_format
            saver._data_as_stack = stack
            # do the actual saving out, directories will be created here
            saver.save(
                images,
                angle_path,
                'out_angle',
                out_format=saver._out_format)

        # aggregate them
        conf = self.config
        conf.func.aggregate = ['0', '10', mode]
        # select angles 0 - 4 (aggregate_angles is 5 so we subtract 1)
        conf.func.aggregate_angles = ['0', str(aggregate_angles - 1)]
        conf.func.aggregate_single_folder_output = True
        conf.func.input_path = aggregate_path
        conf.func.in_format = saver._out_format
        conf.func.out_format = convert_format
        aggregate_output_path = os.path.join(self.output_directory,
                                             'aggregated')
        conf.func.output_path = aggregate_output_path
        # because we need to write in the same folder
        conf.func.overwrite_all = True
        conf.func.convert_prefix = 'aggregated'
        aggregate.execute(conf)

        # load them back
        # compare data to original
        # this does not load any flats or darks as they were not saved out
        images = loader.load(
            aggregate_output_path,
            in_format=saver._out_format,
            parallel_load=parallel)

        for i in images.get_sample():
            th.assert_equals(i, expected)

    def test_aggregate_not_single_folder_sum_fits(self):
        self.do_aggregate_not_single_folder('fits', 'fits', 'sum')

    def test_aggregate_not_single_folder_sum_tif(self):
        self.do_aggregate_not_single_folder('tif', 'tif', 'sum')

    def test_aggregate_not_single_folder_avg_fits(self):
        self.do_aggregate_not_single_folder('fits', 'fits', 'avg')

    def test_aggregate_not_single_folder_avg_tif(self):
        self.do_aggregate_not_single_folder('tif', 'tif', 'avg')

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

        aggregate_path = os.path.join(self.output_directory, 'aggregate')
        # keep the angle paths for the load later
        angle_paths = []
        # save out 5 'angles'
        for i in range(aggregate_angles):
            angle_paths.append(aggregate_path + '/angle' + str(i))
            saver._output_path = angle_paths[i]
            saver._out_format = img_format
            saver._data_as_stack = stack
            saver._overwrite_all = True
            # do the actual saving out, directories will be created here
            saver.save(
                images,
                angle_paths[i],
                'out_angle',
                swap_axes=False,
                out_format=saver._out_format)

        # aggregate them
        conf = self.config
        conf.func.aggregate = ['0', '10', mode]
        # select angles 0 - 4 (starts from 0 so -1)
        conf.func.aggregate_angles = ['0', str(aggregate_angles - 1)]
        conf.func.aggregate_single_folder_output = False
        conf.func.input_path = aggregate_path
        conf.func.in_format = saver._out_format
        conf.func.out_format = convert_format
        aggregate_output_path = os.path.join(self.output_directory,
                                             'aggregated')
        conf.func.output_path = aggregate_output_path
        conf.func.overwrite_all = True
        conf.func.convert_prefix = 'aggregated'
        aggregate.execute(conf)

        # load them back
        # compare data to original
        # this does not load any flats or darks as they were not saved out
        for i in range(aggregate_angles):
            angle_path = os.path.join(self.output_directory,
                                      'aggregated/angle_' + mode + str(i))

            images = loader.load(
                angle_path,
                in_format=saver._out_format,
                parallel_load=parallel)

            for i in images.get_sample():
                th.assert_equals(i, expected)


if __name__ == '__main__':
    unittest.main()
