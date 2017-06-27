from __future__ import absolute_import, division, print_function

import tempfile
import unittest


from isis_imaging.tests import test_helper as th
from isis_imaging.core import process_list
from isis_imaging.core.filters import median_filter
# def execute(data, size, mode=modes()[0], cores=None, chunksize=None):

PACKAGE_LOCATION_STRING = 'isis_imaging/core/filters/median_filter'
FUNC_NAME = 'execute'


class ProcessListTest(unittest.TestCase):
    def setUp(self):
        self.pl = process_list.ProcessList()
        self.pl.store(median_filter.execute, 3)
        self.pl.store(median_filter.execute, size=55)
        self.pl.store(median_filter.execute, 11, mode='test')

    def test_store(self):
        self.pl.store(median_filter.execute, 3)
        self.pl.store(median_filter.execute, 1)
        self.pl.store(median_filter.execute, 2)

        # 3 from setup and 3 from here
        self.assertEquals(len(self.pl), 6)

    def test_pop(self):
        func_tuple = self.pl.pop()
        self.assertEqual(func_tuple[0], PACKAGE_LOCATION_STRING)
        self.assertEqual(func_tuple[1], FUNC_NAME)
        self.assertEqual(func_tuple[2], (3,))
        self.assertEqual(func_tuple[3], {})

        func_tuple = self.pl.pop()
        self.assertEqual(func_tuple[0], PACKAGE_LOCATION_STRING)
        self.assertEqual(func_tuple[1], FUNC_NAME)
        self.assertEqual(func_tuple[2], ())
        self.assertEqual(func_tuple[3], {'size': 55})

        func_tuple = self.pl.pop()
        self.assertEqual(func_tuple[0], PACKAGE_LOCATION_STRING)
        self.assertEqual(func_tuple[1], FUNC_NAME)
        self.assertEqual(func_tuple[2], (11,))
        self.assertEqual(func_tuple[3], {'mode': 'test'})

    def test_save(self):
        with tempfile.NamedTemporaryFile() as f:
            self.pl.save(f.name)
            th.assert_files_exist(
                self, f.name, file_extension='', file_extension_separator='')

    def test_load(self):
        with tempfile.NamedTemporaryFile() as f:
            self.pl.save(f.name)
            process_list2 = process_list.load(f.name)
            self.assertTrue(self.pl == process_list2)

    def test_to_string(self):
        res = self.pl.to_string()
        self.assertEqual(res.count(PACKAGE_LOCATION_STRING), 3)

    def test_to_string_and_from_string(self):
        res = self.pl.to_string()
        new_pl = process_list.ProcessList()
        new_pl.from_string(res)
        self.assertEqual(self.pl, new_pl)

    def test_to_string_equals_str(self):
        self.assertTrue(self.pl.to_string() == str(self.pl))

    def test_fail_store(self):
        self.assertRaises(AssertionError, self.pl.store,
                          median_filter.execute, 3, not_existing_kwarg=3)

    def test_from_string_fail(self):
        input_string = "some arbitrary string here"
        self.assertRaises(ValueError, self.pl.from_string, input_string)

    def test_from_string(self):
        input_string = "isis_imaging/core/filters/median_filter execute (3, 'reflect') {'cores': 3}"
        # empty the pre-setup list
        self.pl._list = []
        self.pl.from_string(input_string)
        exp_package = 'isis_imaging/core/filters/median_filter'
        exp_func = 'execute'
        exp_args = (3, 'reflect')
        exp_kwargs = {'cores': 3}

        self.assertEqual(self.pl._list[0][0], exp_package)
        self.assertEqual(self.pl._list[0][1], exp_func)
        self.assertEqual(self.pl._list[0][2], exp_args)
        self.assertEqual(self.pl._list[0][3], exp_kwargs)

    def test_from_string_multiple(self):
        REPS = 3
        # duplicate the string
        input_string = "isis_imaging/core/filters/median_filter execute (3, 'reflect') {'cores': 3};" * REPS
        # empty the pre-setup list
        self.pl._list = []
        self.pl.from_string(input_string)
        exp_package = 'isis_imaging/core/filters/median_filter'
        exp_func = 'execute'
        exp_args = (3, 'reflect')
        exp_kwargs = {'cores': 3}

        # check if all are equal
        for i in range(REPS):
            self.assertEqual(self.pl._list[i][0], exp_package)
            self.assertEqual(self.pl._list[i][1], exp_func)
            self.assertEqual(self.pl._list[i][2], exp_args)
            self.assertEqual(self.pl._list[i][3], exp_kwargs)
