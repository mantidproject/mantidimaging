# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import logging
import unittest
from pathlib import Path
from unittest import mock

from mantidimaging.core.utility.command_line_arguments import CommandLineArguments


class CommandLineArgumentsTest(unittest.TestCase):

    def setUp(self) -> None:
        self.reset_singleton()
        self.logger = logging.getLogger("mantidimaging.core.utility.command_line_arguments")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.reset_singleton()

    @staticmethod
    def reset_singleton():
        CommandLineArguments._instance = None
        CommandLineArguments._images_path = []
        CommandLineArguments._init_operation = ""
        CommandLineArguments._show_recon = False
        CommandLineArguments._show_live_viewer = ""
        CommandLineArguments._show_spectrum_viewer = False

    def test_bad_path_calls_exit(self):
        bad_path = "does/not/exist"
        with self.assertRaises(SystemExit):
            with self.assertLogs(self.logger, level="ERROR") as mock_log:
                CommandLineArguments(bad_path)
        self.assertIn(f"Path {bad_path} doesn't exist. Exiting.", mock_log.output[0])

    def test_valid_path_check_made_once(self):
        first_path = Path("first/path").as_posix()
        with mock.patch("mantidimaging.core.utility.command_line_arguments.Path.exists") as exists_mock:
            exists_mock.return_value = True
            CommandLineArguments(first_path)
            CommandLineArguments("second/path")
        exists_mock.assert_called_once()
        self.assertEqual(CommandLineArguments().path(), [first_path])

    def test_no_check_if_no_path_is_given(self):
        with mock.patch.object(Path, "exists") as exists_mock:
            CommandLineArguments()
        exists_mock.assert_not_called()

    def test_set_valid_operation_with_path(self):
        operation = "median"
        command_line_arguments = CommandLineArguments(path="./", operation=operation)
        assert command_line_arguments.operation() == "Median"

    def test_set_valid_operation_without_path(self):
        with self.assertRaises(SystemExit):
            with self.assertLogs(self.logger, level="ERROR") as mock_log:
                CommandLineArguments(operation="median")
        self.assertIn("No path given for initial operation. Exiting.", mock_log.output[0])

    def test_set_invalid_operation(self):
        with self.assertRaises(SystemExit):
            with self.assertLogs(self.logger, level="ERROR") as mock_log:
                bad_operation = "aaaaaa"
                CommandLineArguments(path="./", operation=bad_operation)
        self.assertIn(f"{bad_operation} is not a known operation. Available filters arguments are ", mock_log.output[0])

    def test_set_show_recon(self):
        command_line_arguments = CommandLineArguments(path="./", show_recon=True)
        assert command_line_arguments.recon()

    def test_set_show_recon_without_path(self):
        with self.assertRaises(SystemExit):
            with self.assertLogs(self.logger, level="ERROR") as mock_log:
                CommandLineArguments(show_recon=True)
        self.assertIn("No path given for reconstruction. Exiting.", mock_log.output[0])
