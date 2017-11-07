from __future__ import (absolute_import, division, print_function)

import numpy as np

from mantidimaging import helper as h


class Images(object):
    def __init__(self, sample=None, flat=None, dark=None, filenames=None):

        self._sample = sample
        self._flat = flat
        self._dark = dark

        self._filenames = filenames

    def __str__(self):
        return 'Image Stack: sample={}, flat={}, dark={}'.format(
                self.sample.shape if self.sample is not None else None,
                self.flat.shape if self.flat is not None else None,
                self.dark.shape if self.dark is not None else None)

    @property
    def sample(self):
        return self._sample

    @sample.setter
    def sample(self, imgs):
        self._sample = imgs

    @property
    def flat(self):
        return self._flat

    @flat.setter
    def flat(self, imgs):
        self._flat = imgs

    @property
    def dark(self):
        return self._dark

    @dark.setter
    def dark(self, imgs):
        self._dark = imgs

    @property
    def filenames(self):
        return self._filenames

    @staticmethod
    def check_data_stack(data, expected_dims=3, expected_class=np.ndarray):
        h.check_data_stack(data, expected_dims, expected_class)
