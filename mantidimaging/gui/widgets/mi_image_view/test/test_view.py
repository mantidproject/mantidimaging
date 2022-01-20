# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import numpy as np
import unittest

from mantidimaging.gui.widgets.mi_image_view.view import MIImageView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MIImageViewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = MIImageView()

    def test_set_image_creates_tVals_for_small_image_size(self):
        image = np.zeros((1, 1, 1))

        self.view.setImage(image)
        self.assertTrue(hasattr(self.view, 'tVals'), 'tVals attribute missing for small image size')
