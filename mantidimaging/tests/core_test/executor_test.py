from unittest import TestCase

import numpy.testing as npt

from mantidimaging.core import process_list
from mantidimaging.core.filters import median_filter
from mantidimaging.tests import test_helper as th

# global var that will be incremented when the executor successfully executes
# the function
global_variable = 0

MEDIAN_SIZE = 3
MEDIAN_MODE = 'nearest'


class ExecutorTest(TestCase):
    def do_set_up(self, *args):
        shape = (1, 10, 10)

        random = th.gen_img_numpy_rand(shape[1:])

        # set one of the rows to a high value to make sure the median will have
        # a large effect
        random[3] = 411.0

        self.expected_data = th.gen_empty_shared_array(shape)

        # deep copy
        self.expected_data[:] = random

        self.init_data = th.gen_empty_shared_array(shape)

        # copy the expected data values
        self.init_data[:] = self.expected_data

        self.expected_data = median_filter.execute(self.expected_data, *args)

        # sanity check
        th.assert_not_equals(self.init_data, self.expected_data)

        self.pl = process_list.ProcessList()
        self.pl.store(median_filter.execute, MEDIAN_SIZE)

    def test_execute(self):
        self.do_set_up(MEDIAN_SIZE)
        process_list.execute(self.pl.next(), self.init_data)
        npt.assert_equal(self.init_data, self.expected_data)

    def test_execute_back(self):
        # this intentionally does NOT store the MEDIAN_MODE in the process
        # list, so that we can test the functionality
        self.do_set_up(MEDIAN_SIZE, MEDIAN_MODE)
        process_list.execute_back(self.pl.next(), self.init_data, MEDIAN_MODE)
        npt.assert_equal(self.init_data, self.expected_data)

    def test_execute_new(self):
        self.do_set_up(MEDIAN_SIZE, MEDIAN_MODE)
        process_list.execute(self.pl.next(), self.init_data,
                             MEDIAN_SIZE, MEDIAN_MODE)
        npt.assert_equal(self.init_data, self.expected_data)
