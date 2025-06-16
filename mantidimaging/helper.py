# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Module for commonly used functions across the modules.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QSettings

from mantidimaging.core.data import ImageStack


def initialise_logging(arg_level: str | None = None) -> None:
    log_formatter = logging.Formatter("%(asctime)s [%(name)s:L%(lineno)d] %(levelname)s: %(message)s")

    settings = QSettings()
    setting_level = settings.value("logging/log_level", defaultValue="INFO")
    retention_days = settings.value("logging/retention", defaultValue=30, type=int)

    log_level = logging.getLevelName(arg_level) if arg_level else logging.getLevelName(setting_level)

    # Capture all warnings
    logging.captureWarnings(True)
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Console Logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # File Logging
    log_directory = Path(settings.value("logging/log_dir", defaultValue=""))
    file_log = None
    if log_directory and log_directory != Path(""):
        log_directory.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        for log_file in log_directory.glob("mantid_imaging_*.log"):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if (now - file_time).days > retention_days:
                log_file.unlink()

        filename = f"mantid_imaging_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
        file_log = logging.FileHandler(log_directory / filename)
        file_log.setFormatter(log_formatter)
        root_logger.addHandler(file_log)
    logging.getLogger('mantidimaging').setLevel(log_level)

    # Performance Logging
    perf_logger = logging.getLogger('perf')
    perf_logger.setLevel(100)
    perf_logger.propagate = False
    if settings.value("logging/performance_log", defaultValue=False, type=bool):
        perf_logger.setLevel(1)
        perf_logger.addHandler(console_handler)
        if file_log is not None:
            perf_logger.addHandler(file_log)


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
