from unittest import TestCase

import math

from mantidimaging.core.cor_tilt import angles


class AnglesTest(TestCase):

    def test_cors_to_tilt_angle(self):
        theta = angles.cors_to_tilt_angle(10, 1)
        self.assertAlmostEqual(theta, math.pi / 4)
