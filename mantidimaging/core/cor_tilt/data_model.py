from collections import namedtuple
from logging import getLogger
from typing import Optional, List

import numpy as np
import scipy as sp

from mantidimaging.core.data import const
from .angles import cors_to_tilt_angle

LOG = getLogger(__name__)
Point = namedtuple('Point', ['slice_index', 'cor'])


class CorTiltDataModel:
    """
    Model for finding COR/Tilt from (slice index, centre of rotation) data points
    """
    _cached_gradient: Optional[float]
    _cached_cor: Optional[float]
    _points: List[Point]

    def __init__(self):
        self._points = []
        self._cached_gradient = None
        self._cached_cor = None

    def populate_slice_indices(self, begin, end, count, cor=0.0):
        self.clear_results()

        self._points = [Point(int(idx), cor) for idx in np.linspace(begin, end, count, dtype=int)]
        LOG.debug('Populated slice indices: {}'.format(self.slices))

    def linear_regression(self):
        LOG.debug('Running linear regression with {} points'.format(self.num_points))
        self._cached_gradient, self._cached_cor, *_ = sp.stats.linregress(self.slices, self.cors)

    def add_point(self, idx=None, slice_idx=0, cor=0.0):
        self.clear_results()

        if idx is None:
            self._points.append(Point(slice_idx, cor))
        else:
            self._points.insert(idx, Point(slice_idx, cor))

    def set_point(self, idx, slice_idx=None, cor=None):
        self.clear_results()

        if slice_idx is not None:
            self._points[idx] = Point(int(slice_idx), self._points[idx].cor)

        if cor is not None:
            self._points[idx] = Point(self._points[idx].slice_index, float(cor))

    def _get_data_idx_from_slice_idx(self, slice_idx):
        for i, p in enumerate(self._points):
            if p.slice_index == slice_idx:
                return i
        return None

    def set_cor_at_slice(self, slice_idx, cor):
        data_idx = self._get_data_idx_from_slice_idx(slice_idx)
        self.set_point(data_idx, cor=cor)

    def remove_point(self, idx):
        self.clear_results()
        del self._points[idx]

    def clear_points(self):
        self._points = []
        self.clear_results()

    def clear_results(self):
        self._cached_gradient = None
        self._cached_cor = None

    def point(self, idx):
        return self._points[idx] if idx < self.num_points else None

    def sort_points(self):
        self._points.sort(key=lambda p: p.slice_index)

    def get_cor_for_slice(self, slice_idx):
        a = [p.cor for p in self._points if p.slice_index == slice_idx]
        return a[0] if a else None

    def get_cor_for_slice_from_regression(self, slice_idx):
        if not self.has_results:
            return None

        cor = (self.gradient * slice_idx) + self.cor
        return cor

    @property
    def slices(self):
        return [p.slice_index for p in self._points]

    @property
    def cors(self):
        return [float(p.cor) for p in self._points]

    @property
    def gradient(self):
        return self._cached_gradient

    @property
    def cor(self):
        return self._cached_cor

    @property
    def angle_rad(self):
        return cors_to_tilt_angle(self.slices[-1], self.gradient)

    @property
    def has_results(self):
        return self._cached_gradient is not None and self._cached_cor is not None

    @property
    def empty(self):
        return not self._points

    @property
    def num_points(self):
        return len(self._points)

    @property
    def stack_properties(self):
        return {
            const.COR_TILT_ROTATION_CENTRE: float(self.cor),
            const.COR_TILT_FITTED_GRADIENT: float(self.gradient),
            const.COR_TILT_TILT_ANGLE_RAD: float(self.angle_rad),
            const.COR_TILT_SLICE_INDICES: self.slices,
            const.COR_TILT_ROTATION_CENTRES: self.cors
        }
