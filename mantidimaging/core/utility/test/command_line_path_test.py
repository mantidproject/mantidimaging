import unittest

from mantidimaging.core.utility.command_line_path import CommandLinePath


class CommandLinePathTest(unittest.TestCase):
    def test_bad_path_calls_exit(self):
        with self.assertRaises(SystemExit):
            CommandLinePath("does/not/exist")
