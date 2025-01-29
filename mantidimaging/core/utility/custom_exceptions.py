# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path


class ImageLoadFailError(Exception):
    """
    Exception raised when an image is not loaded correctly
    """

    def __init__(self, image_path: Path, source_error, message: str = '') -> None:
        error_name = type(source_error).__name__
        if message == '':
            self.message = f"{error_name} :Could not load image f{image_path}, Exception: {source_error} "
        else:
            self.message = message
        super().__init__(message)
