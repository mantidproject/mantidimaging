from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from tests import test_helper as test_helper


class ConfigsTest(unittest.TestCase):
    """
    There's not much to test on the configs as they are simple containers for the arguments.
    """

    def test_preproc(self):
        from configs.preproc_config import PreProcConfig
        preproc = PreProcConfig()
        self._compare_dict_to_str(preproc.__dict__,
                                  str(preproc), "Pre-processing config")

    def test_postproc(self):
        from configs.postproc_config import PostProcConfig
        postproc = PostProcConfig()
        self._compare_dict_to_str(postproc.__dict__,
                                  str(postproc), "Post-processing config")

    def test_functional(self):
        from configs.functional_config import FunctionalConfig
        from configs.postproc_config import PostProcConfig
        from configs.preproc_config import PreProcConfig

        postproc = PostProcConfig()
        preproc = PreProcConfig()
        fc = FunctionalConfig()
        self._compare_dict_to_str(fc.__dict__, str(fc), "Functional config")

        from configs.recon_config import ReconstructionConfig as RC
        # running without --input-path
        fc.input_path = None

        # the error is thrown when constructing a ReconstructionConfig
        npt.assert_raises(ValueError, RC, fc, preproc, postproc)

        # set some input path
        fc.input_path = '23'
        # running --save-preproc without output path
        fc.save_preproc = True
        fc.output_path = None
        npt.assert_raises(ValueError, RC, fc, preproc, postproc)
        # remove the output path raise
        fc.output_path = 'some/dir'
        # running recon without COR
        npt.assert_raises(ValueError, RC, fc, preproc, postproc)
        fc.cors = [42]
        # this shouldn't raise anything, if it does the test will crash
        rc = RC(fc, preproc, postproc)

    def _compare_dict_to_str(self, class_dict, class_str, this_config):
        dictlen = len(class_dict)
        strlen = len(class_str.split('\n'))

        # to be printed if error, we need to evaluate this first because for some reason
        # it's not evaluated in the assert, so we just print {0} and {1} instead of replacing 
        # them with the correct values
        self.assertEquals(
            dictlen, strlen,
            "Different size of __dict__({0}) and __str__({1}). Some of the attributes in the {2} are not documented!".
            format(dictlen, strlen, this_config))


if __name__ == '__main__':
    unittest.main()
