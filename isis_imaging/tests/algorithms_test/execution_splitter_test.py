from __future__ import absolute_import, division, print_function
import unittest
from isis_imaging.core.algorithms import execution_splitter
from functools import partial
from isis_imaging.core.configs.recon_config import ReconstructionConfig
_global_variable = 0


def _func_to_be_executed(config):
    """
    :param config: Only added to conform to the standard interface
    """
    global _global_variable
    _global_variable += 1


def _indices_check(cls, splits, iteration, config):
    """
    :param cls: The unittest.TestCase class to use for assertions
    :param splits: The custom-made splits
    :param iteration: List of length 1, containing an integer that server as an internal counter
    :param config: The reconstruction config that has been modified by the execution_splitter
    """
    indices = config.func.indices

    cls.assertEquals(len(indices), 3)

    # assert the starting index is what we expect
    cls.assertEquals(splits[iteration[0]], indices[0])

    # assert the end index is what we expect
    cls.assertEquals(splits[iteration[0] + 1], indices[1])

    # assert the step is 1
    cls.assertEquals(indices[2], 1)

    # modify the member, we use a list because the change will persist through iterations
    iteration[0] += 1


class ExecutionSplitterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ExecutionSplitterTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.rconfig = ReconstructionConfig.empty_init()
        self.recon = False
        self.data_shape = (1000, 100, 100)
        self.split = [0, 200, 400, 600, 800, 1000, 1200, 1400]
        self.expected_iterations = len(self.split) - 1
        self.step = 200

        # define our own custom function that will replace the original _split_data
        # this way we do not have to load data, and we can directly control the returns
        def override_split_data(config):
            return self.recon, self.data_shape, self.split, self.step

        # override the function for the tests, this is restored in tearDown()
        self.backup, execution_splitter._split_data = execution_splitter._split_data, override_split_data

    def tearDown(self):
        # restore the function for the next test
        execution_splitter._split_data = self.backup

    def test_number_of_runs(self):
        execution_splitter.execute(self.rconfig, _func_to_be_executed)

        self.assertEquals(_global_variable, self.expected_iterations)

        # restore the function for other tests

    def test_indices(self):
        # we pass a list of [0] so that we can mutate it inside the function
        modified_indices_check = partial(_indices_check, self, self.split, [0])
        execution_splitter.execute(self.rconfig, modified_indices_check)
