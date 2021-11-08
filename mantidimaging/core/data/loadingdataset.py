from dataclasses import dataclass
from typing import Optional

from mantidimaging.core.data import Images
# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later


@dataclass
class LoadingDataset:
    sample: Images
    flat_before: Optional[Images] = None
    flat_after: Optional[Images] = None
    dark_before: Optional[Images] = None
    dark_after: Optional[Images] = None
