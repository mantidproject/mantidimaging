# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
import weakref
from dataclasses import dataclass
from typing import Optional

from mantidimaging.core.data import Images


@dataclass
class Dataset:

    def __init__(self, sample: Images, flat_before: Optional[Images] = None, flat_after: Optional[Images] = None,
                 dark_before: Optional[Images] = None, dark_after: Optional[Images] = None):
        self._sample = weakref.ref(sample)
        self._flat_before = lambda : None
        self._flat_after = lambda : None
        self._dark_before = lambda : None
        self._dark_after = lambda : None

        if isinstance(flat_before, Images):
            self._flat_before = weakref.ref(flat_before)
        if isinstance(flat_after, Images):
            self._flat_after = weakref.ref(flat_after)
        if isinstance(dark_before, Images):
            self._dark_before = weakref.ref(dark_before)
        if isinstance(dark_after, Images):
            self._dark_after = weakref.ref(dark_after)

        self._id: uuid.UUID = uuid.uuid1()

    @property
    def sample(self) -> Optional[Images]:
        return self._sample()

    @property
    def flat_before(self) -> Optional[Images]:
        return self._flat_before()

    @flat_before.setter
    def flat_before(self, flat_before: Images):
        self._flat_before = weakref.ref(flat_before)

    @property
    def flat_after(self) -> Optional[Images]:
        return self._flat_after()

    @flat_after.setter
    def flat_after(self, flat_after: Images):
        self._flat_after = weakref.ref(flat_after)

    @property
    def dark_before(self) -> Optional[Images]:
        return self._dark_before()

    @dark_before.setter
    def dark_before(self, dark_before: Images):
        self._dark_before = weakref.ref(dark_before)

    @property
    def dark_after(self) -> Optional[Images]:
        return self._dark_after()

    @dark_after.setter
    def dark_after(self, dark_after: Images):
        self._dark_after = weakref.ref(dark_after)

    @property
    def id(self) -> uuid.UUID:
        return self._id
