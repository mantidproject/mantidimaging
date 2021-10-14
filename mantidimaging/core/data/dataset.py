# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from dataclasses import dataclass
from typing import Optional

from mantidimaging.core.data import Images


@dataclass
class Dataset:
    sample: Images
    flat_before: Optional[Images] = None
    flat_after: Optional[Images] = None
    dark_before: Optional[Images] = None
    dark_after: Optional[Images] = None
    uu_id: Optional[uuid.UUID] = uuid.UUID()
