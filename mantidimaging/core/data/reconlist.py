# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import uuid
from collections import UserList
from typing import List


class ReconList(UserList):
    def __init__(self):
        super().__init__()
        self._id: uuid.UUID = uuid.UUID

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def ids(self) -> List[uuid.UUID]:
        return [recon.id for recon in self.data]
