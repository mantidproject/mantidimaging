# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# import io
# from pathlib import Path
# from unittest import mock

import unittest

# import numpy as np

from mantidimaging.core.data.geometry import Geometry


class GeometryTest(unittest.TestCase):

    def test_default_geometry(self):
        geo = Geometry()
        self.assertTrue(geo.IsParallel)
        self.assertEqual(geo.centre_of_rotation, 64)
