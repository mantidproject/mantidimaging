# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import uuid
from collections import UserList
from typing import List

from mantidimaging.core.data import Images


class ReconList(UserList):
    def __init__(self, data: List[Images] = []):
        super().__init__(data)
        self._id: uuid.UUID = uuid.UUID

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def ids(self) -> List[uuid.UUID]:
        return [recon.id for recon in self.data]
