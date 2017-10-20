from __future__ import absolute_import, division, print_function

import argparse
import unittest

from mantidimaging.core.configs.functional_config import FunctionalConfig
from mantidimaging.core.utility import registrator


class FunctionalConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = argparse.ArgumentParser()
        cls.func_config = FunctionalConfig()
        cls.parser = cls.func_config._setup_parser(cls.parser)

        registrator.register_into(
                cls.parser, func=registrator.cli_register,
                package='mantidimaging.core.filters')

    def test_config_doctest(self):
        self._compare_dict_to_str(self.func_config.__dict__,
                                  str(self.func_config), FunctionalConfig)

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
