# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import uuid


class ReconList(list):
    def __init__(self):
        super().__init__()
        self._id: uuid.UUID = uuid.UUID

    @property
    def id(self) -> uuid.UUID:
        return self._id
