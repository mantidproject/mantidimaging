from unittest import TestCase

from isis_imaging.core import process_list
from isis_imaging.core.filters import median_filter
from isis_imaging.tests import test_helper as th

# global var that will be incremented when the executor successfully executes the function
global_variable = 0

MEDIAN_SIZE = 5


class ExecutorTest(TestCase):
    @staticmethod
    def fake_function(increment: int) -> None:
        global global_variable
        global_variable += increment

    def setUp(self):
        shape = (1, 10, 10)

        random = th.gen_img_numpy_rand(shape[1:])

        # set one of the rows to a high value to make sure the median will have a large effect
        random[3] = 411.0

        self.expected_data = th.gen_empty_shared_array(shape)

        # deep copy
        self.expected_data[:] = random

        self.init_data = th.gen_empty_shared_array(shape)

        # copy the expected data values
        self.init_data[:] = self.expected_data

        self.expected_data = median_filter.execute(self.expected_data, MEDIAN_SIZE)

        # sanity check
        th.assert_not_equals(self.init_data, self.expected_data)

        self.pl = process_list.ProcessList()
        self.pl.store(median_filter.execute, MEDIAN_SIZE)

    def test_execute(self):
        process_list.execute(self.pl.next(), self.init_data)
        th.assert_equals(self.init_data, self.expected_data)
