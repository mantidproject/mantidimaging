# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
import unittest

from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MIMiniImageViewTest(unittest.TestCase):

    def setUp(self) -> None:
        self.view = MIMiniImageView()

    def test_set_image_uses_brightness_percentile(self):
        image = generate_images(seed=2023, shape=(20, 10, 10))
        self.view.set_brightness_percentiles(1, 99)
        self.view.setImage(image.data)
        np.testing.assert_array_equal(self.view.im.getLevels().round(5),
                                      np.array(self.view.levels).round(5), 'Brightness levels not set correctly')
