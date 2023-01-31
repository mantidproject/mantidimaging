# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
import os

from mantidimaging.core.operations.loader import load_filter_packages

logger = getLogger(__name__)

filter_names = [package.filter_name for package in load_filter_packages()]
command_line_names = {}

for filter_name in filter_names:
    command_line_names[filter_name.replace(" ", "-").lower()] = filter_name


def _valid_operation(operation: str):
    """
    Checks if a given operation exists in Mantid Imaging.
    :param operation: The name of the operation.
    :return: True if it is a valid operation, False otherwise.
    """
    return operation.lower() in command_line_names.keys()


def _log_and_exit(msg: str):
    """
    Log an error message and exit.
    :param msg: The log message.
    """
    logger.error(msg)
    exit()


class CommandLineArguments:
    _instance = None
    _images_path: list[str] = []
    _init_operation = ""
    _show_recon = False

    def __new__(cls, path: str = "", operation: str = "", show_recon: bool = False):
        """
        Creates a singleton for storing the command line arguments.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            valid_paths: list[str] = []
            if path:
                for filepath in path.split(","):
                    if not os.path.exists(filepath):
                        _log_and_exit(f"Path {filepath} doesn't exist. Exiting.")
                    else:
                        valid_paths.append(filepath)
                cls._images_path = valid_paths
            if operation:
                if not cls._images_path:
                    _log_and_exit("No path given for initial operation. Exiting.")
                elif not _valid_operation(operation):
                    valid_filters = ", ".join(command_line_names.keys())
                    _log_and_exit(
                        f"{operation} is not a known operation. Available filters arguments are {valid_filters}."
                        " Exiting.")
                else:
                    cls._init_operation = command_line_names[operation]
            if show_recon and not path:
                _log_and_exit("No path given for reconstruction. Exiting.")
            else:
                cls._show_recon = show_recon

        return cls._instance

    @classmethod
    def path(cls) -> list:
        """
        Returns the command line images path.
        """
        return cls._images_path

    @classmethod
    def operation(cls) -> str:
        """
        Returns the initial operation.
        """
        return cls._init_operation

    @classmethod
    def recon(cls) -> bool:
        """
        Returns whether or not the recon window should be started.
        """
        return cls._show_recon
