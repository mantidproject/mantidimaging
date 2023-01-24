# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.core.utility.sensible_roi import SensibleROI


def mark_cropped(images: ImageStack, roi: SensibleROI):
    # avoids circular import error
    from mantidimaging.core.operations.crop_coords import CropCoordinatesFilter
    # not ideal.. but it will allow to replicate the result accurately
    images.record_operation(CropCoordinatesFilter.__name__, CropCoordinatesFilter.filter_name, region_of_interest=roi)
