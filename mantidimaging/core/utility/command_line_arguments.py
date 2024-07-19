# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
import os
from typing import NoReturn

from mantidimaging.core.operations.loader import load_filter_packages

logger = getLogger(__name__)


def _get_filter_names() -> dict[str, str]:
    return {package.filter_name.replace(" ", "-").lower(): package.filter_name for package in load_filter_packages()}


def _log_and_exit(msg: str) -> NoReturn:
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
    _show_live_viewer = ""
    _show_spectrum_viewer = False

    def __new__(cls,
                path: str = "",
                operation: str = "",
                show_recon: bool = False,
                show_live_viewer: str = "",
                show_spectrum_viewer: bool = False):
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
                command_line_names = _get_filter_names()
                if not cls._images_path:
                    _log_and_exit("No path given for initial operation. Exiting.")
                elif operation.lower() not in command_line_names:
                    valid_filters = ", ".join(command_line_names.keys())
                    _log_and_exit(
                        f"{operation} is not a known operation. Available filters arguments are {valid_filters}."
                        " Exiting.")
                else:
                    cls._init_operation = command_line_names[operation.lower()]
            if show_recon and not path:
                _log_and_exit("No path given for reconstruction. Exiting.")
            else:
                cls._show_recon = show_recon
            if show_spectrum_viewer and not path:
                _log_and_exit("No path given for reconstruction. Exiting.")
            else:
                cls._show_spectrum_viewer = show_spectrum_viewer
            if show_live_viewer and show_live_viewer != cls._show_live_viewer:
                if not os.path.exists(show_live_viewer):
                    _log_and_exit("Path given for live view does not exist. Exiting.")
                else:
                    cls._show_live_viewer = show_live_viewer

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

    @classmethod
    def spectrum_viewer(cls) -> bool:
        """
        Returns whether or not the recon window should be started.
        """
        return cls._show_spectrum_viewer

    @classmethod
    def live_viewer(cls) -> str:
        """
        Returns live view path.
        """
        return cls._show_live_viewer

    @classmethod
    def clear_window_args(cls) -> None:
        """
        Clears the command line arguments.
        """
        cls._init_operation = ""
        cls._show_recon = False
        cls._show_spectrum_viewer = False
        cls._show_live_viewer = ""
