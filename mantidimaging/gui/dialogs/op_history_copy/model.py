# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Iterable

from mantidimaging.core.data import ImageStack
from mantidimaging.core.operation_history.operations import ops_to_partials, ImageOperation


class OpHistoryCopyDialogModel:
    def __init__(self, images):
        self.images: ImageStack = images

    def apply_ops(self, ops: Iterable[ImageOperation], copy: bool):
        if copy:
            self.images = self.images.copy()

        to_apply = ops_to_partials(ops)
        for op in to_apply:
            op(self.images)
        return self.images
