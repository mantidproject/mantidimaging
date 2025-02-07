# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path


class ImageLoadFailError(Exception):
    """
    Exception raised when an image is not loaded correctly
    """
    error_paths: dict[Path, list] = {}

    def __init__(self, image_path: Path, source_error, message: str = '') -> None:
        self.error_name = type(source_error).__name__
        self.image_path = image_path
        if message == '':
            self.message = f"{self.error_name} :Could not load image f{image_path}, Exception: {source_error} "
        else:
            self.message = message
        if image_path in self.error_paths.keys():
            self.error_paths[image_path].append(self.error_name)
        else:
            self.error_paths[image_path] = [self.error_name]

        super().__init__(message)

    def is_logged(self):
        return self.error_name in self.error_paths[self.image_path]
