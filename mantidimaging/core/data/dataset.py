# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dataset:
    sample: uuid.UUID
    flat_before: Optional[uuid.UUID] = None
    flat_after: Optional[uuid.UUID] = None
    dark_before: Optional[uuid.UUID] = None
    dark_after: Optional[uuid.UUID] = None
