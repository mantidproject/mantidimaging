# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import logging
import os
import time
from pathlib import Path
from PyQt5.QtCore import QSettings

logger = logging.getLogger("mantidimaging")


def configure_logging():
    """Configures logging globally based on user settings."""
    settings = QSettings('mantidproject', 'Mantid Imaging')

    logging_enabled = settings.value('logging/enabled', True, type=bool)
    log_directory = settings.value('logging/directory', "./logs")
    log_level = settings.value('logging/level', "INFO")
    log_retention = settings.value('logging/retention', 7, type=int)
    overwrite_log = settings.value('logging/overwrite', True, type=bool)

    if not logging_enabled:
        logging.disable(logging.CRITICAL)  # Disable
        return

    os.makedirs(log_directory, exist_ok=True)
    log_file = Path(log_directory) / "mantid_imaging.log"

    if overwrite_log and log_file.exists():
        log_file.unlink()

    logging.basicConfig(
        filename=str(log_file),
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

    # Cleanup old logs
    cleanup_old_logs(log_directory, log_retention)

    logger.info("Global logging has been configured.")


def cleanup_old_logs(log_directory, log_retention):
    """Deletes old logs based on retention settings."""
    now = time.time()
    for file in Path(log_directory).glob("mantid_imaging*.log"):
        if now - file.stat().st_mtime > log_retention * 86400:
            file.unlink()
