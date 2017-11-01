from __future__ import absolute_import, division, print_function

import unittest

import numpy as np

from mantidimaging.core.io.loader import Images


class ImagesTest(unittest.TestCase):

    def test_to_string_empty(self):
        imgs = Images()
        self.assertEquals(
                str(imgs),
                'Image Stack: sample=None, flat=None, dark=None')

    def test_to_string_with_sample(self):
        sample = np.ndarray(shape=(2, 64, 64))
        imgs = Images(sample)
        self.assertEquals(
                str(imgs),
                'Image Stack: sample=(2, 64, 64), flat=None, dark=None')
