# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import uuid
from collections import UserList
from typing import List

from mantidimaging.core.data import ImageStack


class ReconList(UserList):
    def __init__(self, data: List[ImageStack] = []):
        super().__init__(data)
        self._id: uuid.UUID = uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def ids(self) -> List[uuid.UUID]:
        return [recon.id for recon in self.data]

    @property
    def stacks(self) -> List[ImageStack]:
        return self.data
