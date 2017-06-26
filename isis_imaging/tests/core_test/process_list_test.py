from __future__ import absolute_import, division, print_function

import os
import tempfile
import unittest


from isis_imaging.tests import test_helper as th
from isis_imaging.core.process_list import ProcessList
from isis_imaging.core.filters import median_filter
# def execute(data, size, mode=modes()[0], cores=None, chunksize=None):

PACKAGE_LOCATION_STRING = 'isis_imaging/core/filters/median_filter'
FUNC_NAME = 'execute'


class ProcessListTest(unittest.TestCase):
    def setUp(self):
        self.pl = ProcessList()
        self.pl.store(median_filter.execute, 3)
        self.pl.store(median_filter.execute, size=55)
        self.pl.store(median_filter.execute, 11, mode='test')

    def test_store(self):
        self.pl.store(median_filter.execute, 3)
        self.pl.store(median_filter.execute, 1)
        self.pl.store(median_filter.execute, 2)

        self.assertEquals(len(self.pl), 4)

    def test_pop(self):
        func_tuple = self.pl.pop()
        self.assertEqual(func_tuple[0], PACKAGE_LOCATION_STRING)
        self.assertEqual(func_tuple[1], FUNC_NAME)
        self.assertEqual(func_tuple[2], 3)
        self.assertEqual(func_tuple[3], None)

        func_tuple = self.pl.pop()
        self.assertEqual(func_tuple[0], PACKAGE_LOCATION_STRING)
        self.assertEqual(func_tuple[1], FUNC_NAME)
        self.assertEqual(func_tuple[2], None)
        self.assertEqual(func_tuple[3], 55)

        func_tuple = self.pl.pop()
        self.assertEqual(func_tuple[0], PACKAGE_LOCATION_STRING)
        self.assertEqual(func_tuple[1], FUNC_NAME)
        self.assertEqual(func_tuple[2], 11)
        self.assertEqual(func_tuple[3], 'test')

    def test_save(self):
        with tempfile.NamedTemporaryFile() as f:
            self.pl.save(f.name)
            th.assert_files_exist(
                self, f.name, file_extension='', file_extension_separator='')

    def test_load(self):
        with tempfile.NamedTemporaryFile() as f:
            self.pl.save(f.name)
            process_list2 = ProcessList()
            process_list2.load(f.name)
            self.assertTrue(self.pl == process_list2)

    def test_to_string(self):
        self.assertTrue(self.pl.to_string == str(self.pl))
        # TODO determine string format

    def test_from_string(self):
        # TODO determine string format
        pass

    def test_fail_store(self):
        self.assertRaises(AssertionError, self.pl.store,
                          median_filter.execute, 3)
