# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger

import numpy as np


class MIImagePresenter:

    @staticmethod
    def get_roi(image, roi_pos, roi_size):
        """
        Get a ROI based on the current real ROI selected. Clips it to be in-bounds of the
        shape of the image, to prevent issues when passed to filters
        :param image: The current image that is displayed
        :param roi_pos: The top-left position of the ROI
        :param roi_size: The size of the ROI in [right, bottom] direction
        :return: The corrected position and size to have an in-bounds ROI
        """
        # Don't allow negative point coordinates, as they do not
        # respond to any real image-data and cause issues in filters
        if roi_pos.x < 0 or roi_pos.y < 0:
            getLogger(__name__).info("Region of Interest starts outside the picture! Clipping to image bounds")
            roi_pos.x = max(roi_pos.x, 0)
            roi_pos.y = max(roi_pos.y, 0)

        if image.ndim == 2:
            image_height = image.shape[0]
            image_width = image.shape[1]
        else:
            image_height = image.shape[1]
            image_width = image.shape[2]

        roi_right = roi_pos.x + roi_size.x
        roi_bottom = roi_pos.y + roi_size.y

        # Ensures that we always get a valid ROI that isn't hanging outside
        # of the image, by accounting for the rectangle sticking out the right
        # or the bottom side of the image. The ROI is translated to be
        # inside the image
        if roi_right > image_width:
            roi_size.x -= roi_right - image_width
        if roi_bottom > image_height:
            roi_size.y -= roi_bottom - image_height
        return roi_pos, roi_size

    @staticmethod
    def get_nearest_timeline_tick(x_pos_clicked: float, x_axis, view_range: list[int]):
        """
        Calculate the closes point to the clicked position on the histogram's timeline.

        :param x_pos_clicked: The X position where the mouse clicked on the histogram widget
        :param x_axis: The X-axis object that knows pixel sizes of the widget
        :param view_range: The view range represented on the histogram
        """
        frac_pos = (x_pos_clicked - x_axis.x()) / x_axis.width()
        domain_pos = (view_range[1] - view_range[0]) * frac_pos
        return np.round(view_range[0] + domain_pos)
