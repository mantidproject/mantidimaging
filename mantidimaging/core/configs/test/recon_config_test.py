from __future__ import absolute_import, division, print_function

import argparse
import unittest

import numpy.testing as npt

import mantidimaging.core.testing.unit_test_helper as th

from mantidimaging.core.configs.recon_config import ReconstructionConfig
from mantidimaging.core.configs.filter_registration import (
        register_filters_on_cli)
from mantidimaging.core.configs.functional_config import FunctionalConfig


class FunctionalConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = argparse.ArgumentParser()
        cls.func_config = FunctionalConfig()
        cls.parser = cls.func_config._setup_parser(cls.parser)

        register_filters_on_cli(cls.parser)

    def test_no_input_path_error(self):
        # Ignore output to stdout/stderr
        with th.IgnoreOutputStreams():
            # the error is thrown from handle_special_arguments
            try:
                # don't add input path, which is supposed to be mandatory
                fake_args_list = ['--cors', '42']
                fake_args = self.parser.parse_args(fake_args_list)
                self.func_config._update(fake_args)
                ReconstructionConfig(self.func_config, fake_args)
                assert False, "If we reached this point we have failed the test, \
                              because we were supposed to crash without \
                              --input--path specified"
            except SystemExit:
                # it was supposed to fail, it's fine
                pass

    def test_missing_cors_error(self):
        # don't add CORS, which is mandatory if running reconstruction
        fake_args_list = ['--input-path', '23', '--reconstruction']
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        # this was causing troubles, because the state is not refreshed with a
        # global setUpClass
        self.func_config.cors = None
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_cors_success(self):
        fake_args_list = ['--input-path', '23', '--cors', '42']
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        ReconstructionConfig(self.func_config, fake_args)

    def test_save_preproc_no_output_path_error(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--save-preproc'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_convert_no_output_path_error(self):
        fake_args_list = ['--input-path', '23', '--cors', '42', '--convert']
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_aggregate_no_output_path_error(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--aggregate', '10 20'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_successful_parse(self):
        # remove the output path raise
        fake_args_list = [
            '--input-path', '/tmp/', '--cors', '42', '--output-path', '/tmp/'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        # this shouldn't raise anything, if it does the test will crash
        ReconstructionConfig(self.func_config, fake_args)

    def test_region_of_interest_not_int_fail(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--region-of-interest',
            'test', 'boop', 'what', 'why'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_region_of_interest_success(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--region-of-interest', '10',
            '20', '10', '20'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        ReconstructionConfig(self.func_config, fake_args)

    def test_air_region_not_int_fail(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--air-region', 'test',
            'boop', 'what', 'why'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_air_region_success(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--air-region', '10', '20',
            '10', '20'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        ReconstructionConfig(self.func_config, fake_args)

    def test_indices_single(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--indices', '42'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        rc = ReconstructionConfig(self.func_config, fake_args)
        self.assertEqual(rc.func.indices, [0, 42, 1])

    def test_indices_range(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--indices', '10', '42'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        rc = ReconstructionConfig(self.func_config, fake_args)
        self.assertEqual(rc.func.indices, [10, 42, 1])

    def test_indices_step(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--indices', '15', '33', '3'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config._update(fake_args)
        rc = ReconstructionConfig(self.func_config, fake_args)
        self.assertEqual(rc.func.indices, [15, 33, 3])


if __name__ == '__main__':
    unittest.main()
