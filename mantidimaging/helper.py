# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Module for commonly used functions across the modules.
"""
from __future__ import annotations

import logging
import sys

from mantidimaging.core.data import ImageStack

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

    # Default log level for mantidimaging only
    logging.getLogger('mantidimaging').setLevel(default_level)


def check_data_stack(data, expected_dims=3, expected_class=ImageStack):
    """
    Make sure the data has expected dimensions and class.
    """
    if data is None:
        raise ValueError("Data is a None type.")

    if not isinstance(data, expected_class):
        raise ValueError(
            f"Invalid data type. It must be an {expected_class.__name__} object. Instead found: {type(data).__name__}")

    if expected_dims != data.data.ndim:
        raise ValueError(f"Invalid data format. It does not have 3 dimensions. Shape: {data.data.shape}")
