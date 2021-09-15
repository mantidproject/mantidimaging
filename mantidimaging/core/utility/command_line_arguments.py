# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import logging
import os

def _valid_operation(str: operation):
    pass


def _log_and_exit(msg: str):
    logging.error(msg)
    exit()


class CommandLineArguments:
    _instance = None
    images_path = ""
    init_operation = ""

    def __new__(cls, path: str = "", operation: str = "", recon: bool = False):
        """
        Creates a singleton for storing the path from the command line argument.
        """
        if cls._instance is None:
            cls._instance = super(CommandLineArguments, cls).__new__(cls)
            if path:
                if not os.path.exists(path):
                    _log_and_exit(f"Path {path} doesn't exist. Exiting.")
                else:
                    cls.images_path = path
            if operation:
                if not cls.images_path:
                    _log_and_exit("No path given for initial operation. Exiting.")
                elif not _valid_operation(operation):
                    _log_and_exit(f"{operation} is not a known operation. Exiting.")
                else:
                    cls.init_operation = operation
            if recon and not path:
                _log_and_exit("No path given for reconstruction. Exiting.")

        return cls._instance

    @classmethod
    def path(cls) -> str:
        """
        Returns the command line images path.
        """
        return cls.images_path
