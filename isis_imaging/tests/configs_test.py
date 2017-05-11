from __future__ import absolute_import, division, print_function

import argparse
import unittest

import numpy.testing as npt

from core.configs.functional_config import FunctionalConfig
from core.configs.recon_config import ReconstructionConfig
from core.algorithms import cli_registrator


class ConfigsTest(unittest.TestCase):
    def setUp(self):
        self.parser = argparse.ArgumentParser()
        self.func_config = FunctionalConfig()
        self.parser = self.func_config.setup_parser(self.parser)
        self.grp_filters = self.parser.add_argument_group("Filter options")
        cli_registrator.register_into(self.grp_filters)

    def test_functional_config_doctest(self):
        self._compare_dict_to_str(self.func_config.__dict__,
                                  str(self.func_config), FunctionalConfig)

    def test_cli_registering(self):
        parser = argparse.ArgumentParser()
        self.func_config = FunctionalConfig()
        parser = self.func_config.setup_parser(parser)

        grp_filters = parser.add_argument_group("Filter options")
        cli_registrator.register_into(grp_filters)

        assert grp_filters is not None, "The parser object is None! \
        It was lost somewhere in cli_registrator!"

    def test_no_input_path_error(self):
        # the error is thrown from handle_special_arguments
        try:
            # don't add input path, which is supposed to be mandatory
            fake_args_list = ['--cors', '42']
            fake_args = self.parser.parse_args(fake_args_list)
            self.func_config.update(fake_args)
            ReconstructionConfig(self.func_config, fake_args)
        except SystemExit:
            # it was supposed to fail, it's fine
            pass

    def test_missing_cors_error(self):
        # don't add CORS, which is mandatory if running reconstruction
        fake_args_list = ['--input-path', '23']
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_cors_success(self):
        fake_args_list = ['--input-path', '23', '--cors', '42']
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        ReconstructionConfig(self.func_config, fake_args)

    def test_save_preproc_no_output_path_error(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--save-preproc'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_convert_no_output_path_error(self):
        fake_args_list = ['--input-path', '23', '--cors', '42', '--convert']
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_aggregate_no_output_path_error(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--aggregate', '10 20'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_successful_parse(self):
        # remove the output path raise
        fake_args_list = [
            '--input-path', '/tmp/', '--cors', '42', '--output-path', '/tmp/'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        # this shouldn't raise anything, if it does the test will crash
        ReconstructionConfig(self.func_config, fake_args)

    def test_region_of_interest_not_int_fail(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--region-of-interest',
            'test', 'boop', 'what', 'why'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_region_of_interest_success(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--region-of-interest', '10',
            '20', '10', '20'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        ReconstructionConfig(self.func_config, fake_args)

    def test_air_region_not_int_fail(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--air-region', 'test',
            'boop', 'what', 'why'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        npt.assert_raises(ValueError, ReconstructionConfig, self.func_config,
                          fake_args)

    def test_air_region_success(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--air-region', '10', '20',
            '10', '20'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        ReconstructionConfig(self.func_config, fake_args)

    def test_indices_single(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--indices', '42'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        rc = ReconstructionConfig(self.func_config, fake_args)
        self.assertEqual(rc.func.indices, [0, 42, 1])

    def test_indices_range(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--indices', '10', '42'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        rc = ReconstructionConfig(self.func_config, fake_args)
        self.assertEqual(rc.func.indices, [10, 42, 1])

    def test_indices_step(self):
        fake_args_list = [
            '--input-path', '23', '--cors', '42', '--indices', '15', '33', '3'
        ]
        fake_args = self.parser.parse_args(fake_args_list)
        self.func_config.update(fake_args)
        rc = ReconstructionConfig(self.func_config, fake_args)
        self.assertEqual(rc.func.indices, [15, 33, 3])

    def _compare_dict_to_str(self, class_dict, class_str, this_config):
        dictlen = len(class_dict)
        strlen = len(class_str.split('\n'))

        self.assertEquals(
            dictlen, strlen,
            "Different size of __dict__({0}) and __str__({1}). "
            "Some of the attributes in the {2} are not documented!".format(
                dictlen, strlen, this_config))


if __name__ == '__main__':
    unittest.main()
