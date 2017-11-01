from __future__ import (absolute_import, division, print_function)

import numpy as np
from mantidimaging import helper as h


class Images(object):
    def __init__(self, sample=None, flat=None, dark=None, filenames=None):
        self.sample = sample
        self.flat = flat
        self.dark = dark
        self.filenames = filenames

    def __str__(self):
        return 'Image Stack: sample={}, flat={}, dark={}'.format(
                self.sample.shape if self.sample is not None else None,
                self.flat.shape if self.flat is not None else None,
                self.dark.shape if self.dark is not None else None)

    def get_sample(self):
        return self.sample

    def get_flat(self):
        return self.flat

    def get_dark(self):
        return self.dark

    def get_filenames(self):
        return self.filenames

    @staticmethod
    def check_data_stack(data, expected_dims=3, expected_class=np.ndarray):
        h.check_data_stack(data, expected_dims, expected_class)
