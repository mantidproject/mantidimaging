# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Module for commonly used functions across the modules.
"""

import logging
import sys

from mantidimaging.core.data import Images

_log_file_handler = None
_log_formatter = None

_time_start = None


def initialise_logging(default_level=logging.DEBUG):
    global _log_formatter
    _log_formatter = logging.Formatter("%(asctime)s [%(name)s:L%(lineno)d] %(levelname)s: %(message)s")

    # Add a very verbose logging level
    logging.addLevelName(5, 'TRACE')

    # Capture all warnings
    logging.captureWarnings(True)

    # Remove default handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_log_formatter)
    root_logger.addHandler(console_handler)

    # Default log level
    root_logger.setLevel(default_level)

    # Don't ever print all the debug logging from Qt
    logging.getLogger('PyQt5').setLevel(logging.INFO)


def check_data_stack(data, expected_dims=3, expected_class=Images):
    """
    Make sure the data has expected dimensions and class.
    """
    if data is None:
        raise ValueError("Data is a None type.")

    if not isinstance(data, expected_class):
        raise ValueError("Invalid data type. It must be an Images object. Instead found: {0}".format(type(data)))

    if expected_dims != data.data.ndim:
        raise ValueError("Invalid data format. It does not have 3 dimensions. " "Shape: {0}".format(data.data.shape))
