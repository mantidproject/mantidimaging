from __future__ import absolute_import, division, print_function
import unittest
from isis_imaging.core.algorithms import execution_splitter

_global_variable = 0


def func_to_be_executed(increment):
    global _global_variable
    _global_variable += increment


class ExecutionSplitterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ExecutionSplitterTest, self).__init__(*args, **kwargs)

    def test_number_of_runs(self):
        # TODO run the execution a few times and assert that the increment has been correctly processed N number of times

    def test_file_name_indices(self):
        # TODO further tests to assert that the files are correctly named?

    def test_all_files_are_processed(self):
        # TODO uhh?
