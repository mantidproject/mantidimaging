from __future__ import (absolute_import, division, print_function)
import unittest


class ConfigsTest(unittest.TestCase):
    """
    There's not much to test on the configs as they are simple containers for the arguments.
    """

    def test_preproc(self):
        from recon.configs.preproc_config import PreProcConfig
        preproc = PreProcConfig()
        self._compare_dict_to_str(preproc.__dict__, str(preproc))

    def test_postproc(self):
        from recon.configs.postproc_config import PostProcConfig
        postproc = PostProcConfig()
        self._compare_dict_to_str(postproc.__dict__, str(postproc))

    def test_functional(self):
        from recon.configs.functional_config import FunctionalConfig
        fc = FunctionalConfig()
        self._compare_dict_to_str(fc.__dict__, str(fc))

    def _compare_dict_to_str(self, class_dict, class_str):
        dictlen = len(class_dict)
        strlen = len(class_str.split('\n'))
        self.assertEquals(
            dictlen, strlen, "Different size of __dict__({0}) and __str__({1}). Some of the attributes are not documented!".format(dictlen, strlen))

if __name__ == '__main__':
    unittest.main()
