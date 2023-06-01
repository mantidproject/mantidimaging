# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import List

import numpy as np
import pytest

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.gui.widgets.mi_image_view.presenter import MIImagePresenter


@pytest.mark.parametrize(
    'init_pos,init_size,exp_pos,exp_size',
    [
        ([0, 0], [10, 10], [0, 0], [10, 10]),  # all in bounds
        ([-50, -50], [10, 10], [0, 0], [10, 10]),  # outside of bounds on the left/top
        ([-50, -50], [101, 101], [0, 0], [100, 100]),  # also outside of bounds on the bottom/right
    ])
def test_get_roi(init_pos: List[int], init_size: List[int], exp_pos: List[int], exp_size: List[int]):
    image = np.zeros((100, 100))
    pres = MIImagePresenter()
    roi_pos = CloseEnoughPoint(init_pos)
    roi_size = CloseEnoughPoint(init_size)

    res_pos, res_size = pres.get_roi(image, roi_pos, roi_size)
    assert res_pos.x == exp_pos[0]
    assert res_pos.y == exp_pos[1]
    assert res_size.x == exp_size[0]
    assert res_size.y == exp_size[1]


class Fake_x_axis:

    def __init__(self, x, width):
        self._x = x
        self._width = width

    def x(self):
        return self._x

    def width(self):
        return self._width


def test_get_nearest_timeline_tick():
    # the real pixel-size of the X-axis is used here
    # x is the position of the left side
    # and the other number is the right side
    x = 108
    x_axis = Fake_x_axis(x, 1080)

    start_range = 150
    # this is the actual value range that the histogram shows
    view_range = [start_range, 1200]
    pres = MIImagePresenter()

    # we click perfectly on the start - we get the start of the range
    assert pres.get_nearest_timeline_tick(x, x_axis, view_range) == start_range
    # we click somewhere away from the start - we get a point between start and end of the view range
    assert pres.get_nearest_timeline_tick(x * 2, x_axis, view_range) == 255.0
    assert pres.get_nearest_timeline_tick(x * 3, x_axis, view_range) == 360.0
