import logging
import unittest
from unittest import mock

from mantidimaging.core.utility.command_line_path import CommandLinePath


class CommandLinePathTest(unittest.TestCase):
    def setUp(self) -> None:
        CommandLinePath._instance = None

    def test_bad_path_calls_exit(self):
        bad_path = "does/not/exist"
        with self.assertRaises(SystemExit):
            with self.assertLogs(logging.getLogger(), level="ERROR") as mock_log:
                CommandLinePath(bad_path)
        self.assertIn(f"Path {bad_path} doesn't exist. Exiting.", mock_log.output[0])

    def test_valid_path_check_made_once(self):
        first_path = "first/path"
        with mock.patch("mantidimaging.core.utility.command_line_path.os.path.exists") as exists_mock:
            CommandLinePath(first_path)
            CommandLinePath("second/path")
        exists_mock.assert_called_once_with(first_path)
        self.assertEqual(CommandLinePath().path(), first_path)

    def test_no_check_if_no_path_is_given(self):
        with mock.patch("mantidimaging.core.utility.command_line_path.os.path.exists") as exists_mock:
            CommandLinePath()
        exists_mock.assert_not_called()
