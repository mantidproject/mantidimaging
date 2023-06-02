# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import logging
import unittest
from unittest import mock

from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.core.utility.command_line_arguments import CommandLineArguments, _valid_operation, command_line_names


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
        CommandLineArguments._images_path = ""
        CommandLineArguments._init_operation = ""
        CommandLineArguments._show_recon = False

    def test_bad_path_calls_exit(self):
        bad_path = "does/not/exist"
        with self.assertRaises(SystemExit):
            with self.assertLogs(self.logger, level="ERROR") as mock_log:
                CommandLineArguments(bad_path)
        self.assertIn(f"Path {bad_path} doesn't exist. Exiting.", mock_log.output[0])

    def test_valid_path_check_made_once(self):
        first_path = "first/path"
        with mock.patch("mantidimaging.core.utility.command_line_arguments.os.path.exists") as exists_mock:
            CommandLineArguments(first_path)
            CommandLineArguments("second/path")
        exists_mock.assert_called_once_with(first_path)
        self.assertEqual(CommandLineArguments().path(), [first_path])

    def test_no_check_if_no_path_is_given(self):
        with mock.patch("mantidimaging.core.utility.command_line_arguments.os.path.exists") as exists_mock:
            CommandLineArguments()
        exists_mock.assert_not_called()

    def test_user_input_in_filter_names(self):
        user_inputs = [filter_package.filter_name.replace(" ", "-") for filter_package in load_filter_packages()]
        print(command_line_names)
        for filter_name in user_inputs:
            with self.subTest(filter_name=filter_name):
                assert _valid_operation(filter_name)

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
        valid_filters = ", ".join(command_line_names.keys())
        self.assertIn(
            f"{bad_operation} is not a known operation. Available filters arguments are {valid_filters}. Exiting.",
            mock_log.output[0])

    def test_set_show_recon(self):
        command_line_arguments = CommandLineArguments(path="./", show_recon=True)
        assert command_line_arguments.recon()

    def test_set_show_recon_without_path(self):
        with self.assertRaises(SystemExit):
            with self.assertLogs(self.logger, level="ERROR") as mock_log:
                CommandLineArguments(show_recon=True)
        self.assertIn("No path given for reconstruction. Exiting.", mock_log.output[0])
