# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import uuid
from collections import UserList
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class ReconList(UserList):

    def __init__(self, data: list[ImageStack] | None = None):
        data = [] if data is None else data
        super().__init__(data)
        self._id: uuid.UUID = uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def ids(self) -> list[uuid.UUID]:
        return [recon.id for recon in self.data]

    @property
    def stacks(self) -> list[ImageStack]:
        return self.data
