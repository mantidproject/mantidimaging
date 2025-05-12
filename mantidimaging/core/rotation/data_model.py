# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from typing import NamedTuple
from collections.abc import Iterator

import numpy as np
import scipy as sp

from mantidimaging.core.operation_history import const
from ..utility.data_containers import ScalarCoR, Degrees, Slope

LOG = getLogger(__name__)
Point = NamedTuple("Point", [("slice_index", int), ("cor", float)])


class CorTiltDataModel:
    """
    Model for finding COR/Tilt from (slice index, centre of rotation) data points
    """
    _cached_gradient: float | None
    _cached_cor: float | None
    _points: list[Point]

    def __init__(self) -> None:
        self._points = []
        self._cached_gradient = None
        self._cached_cor = None

    def populate_slice_indices(self, begin, end, count, cor=0.0) -> None:
        self.clear_results()

        self._points = [Point(int(idx), cor) for idx in np.linspace(begin, end, count, dtype=int)]
        LOG.debug(f'Populated slice indices: {self.slices}')

    def linear_regression(self) -> None:
        LOG.debug(f'Running linear regression with {self.num_points} points')
        self._cached_gradient, self._cached_cor, *_ = sp.stats.linregress(self.slices, self.cors)

    def add_point(self, idx: int | None = None, slice_idx: int = 0, cor: float = 0.0) -> None:
        self.clear_results()

        if idx is None:
            self._points.append(Point(slice_idx, cor))
        else:
            self._points.insert(idx, Point(slice_idx, cor))

    def set_point(self,
                  idx: int,
                  slice_idx: int | None = None,
                  cor: float | None = None,
                  reset_results: bool = True) -> None:

        if reset_results:
            self.clear_results()

        if len(self._points) > idx:
            if slice_idx is not None:
                self._points[idx] = Point(int(slice_idx), self._points[idx].cor)

            if cor is not None:
                self._points[idx] = Point(self._points[idx].slice_index, float(cor))

    def _get_data_idx_from_slice_idx(self, slice_idx: int) -> int:
        for i, p in enumerate(self._points):
            if p.slice_index == slice_idx:
                return i
        raise ValueError(f"Slice {slice_idx} that is not in COR table")

    def set_cor_at_slice(self, slice_idx: int, cor: float) -> None:
        data_idx = self._get_data_idx_from_slice_idx(slice_idx)
        self.set_point(data_idx, cor=cor)

    def remove_point(self, idx: int) -> None:
        self.clear_results()
        del self._points[idx]

    def clear_points(self) -> None:
        self._points = []
        self.clear_results()

    def clear_results(self) -> None:
        self._cached_gradient = None
        self._cached_cor = None

    def point(self, idx: int) -> Point | None:
        return self._points[idx] if idx < self.num_points else None

    def sort_points(self) -> None:
        self._points.sort(key=lambda p: p.slice_index)

    def get_cor_from_regression(self, slice_idx: int) -> float:
        cor = (self.gradient.value * slice_idx) + self.cor.value
        return cor

    def get_all_cors_from_regression(self, image_height: int) -> list[ScalarCoR]:
        """

        :param image_height: How many cors will be generated,
                             this should be equal to the image height
                             (i.e. number of sinograms that will be reconstructed)
        :return: List of cors for every slice of the image height
        """
        cors = []
        for i in range(image_height):
            cors.append(ScalarCoR(self.get_cor_from_regression(i)))
        return cors

    @property
    def slices(self) -> list[int]:
        return [p.slice_index for p in self._points]

    @property
    def cors(self) -> list[float]:
        return [float(p.cor) for p in self._points]

    @property
    def gradient(self) -> Slope:
        if self._cached_gradient is not None:
            return Slope(self._cached_gradient)
        else:
            return Slope(0.0)

    @property
    def cor(self) -> ScalarCoR:
        if self._cached_cor is not None:
            return ScalarCoR(self._cached_cor)
        else:
            return ScalarCoR(0.0)

    @property
    def angle_in_degrees(self) -> Degrees:
        return Degrees(-np.rad2deg(np.arctan(self.gradient.value)))

    @property
    def has_results(self) -> bool:
        return self._cached_gradient is not None and self._cached_cor is not None

    @property
    def empty(self) -> bool:
        return not self._points

    @property
    def num_points(self) -> int:
        return len(self._points)

    @property
    def stack_properties(self) -> dict:
        return {
            # TODO remove float casts
            const.COR_TILT_ROTATION_CENTRE: float(self.cor.value),
            const.COR_TILT_FITTED_GRADIENT: float(self.gradient.value),
            const.COR_TILT_TILT_ANGLE_DEG: float(self.angle_in_degrees.value),
            const.COR_TILT_SLICE_INDICES: self.slices,
            const.COR_TILT_ROTATION_CENTRES: self.cors
        }

    def set_precalculated(self, cor: ScalarCoR, tilt: Degrees) -> None:
        self._cached_cor = cor.value
        # reverse the tilt calculation to get the slope of the regression back
        self._cached_gradient = -np.tan(np.deg2rad(tilt.value))

        for idx in range(len(self._points)):
            current = self._points[idx]
            self._points[idx] = Point(current.slice_index, self.get_cor_from_regression(current.slice_index))

    def iter_points(self) -> Iterator[Point]:
        return iter(self._points)
