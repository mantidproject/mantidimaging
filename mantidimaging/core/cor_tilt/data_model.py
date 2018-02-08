from __future__ import absolute_import, division, print_function

from enum import Enum
from logging import getLogger

import numpy as np
import scipy as sp

from mantidimaging.core.data import const

from .angles import cors_to_tilt_angle


LOG = getLogger(__name__)


class Field(Enum):
    SLICE_INDEX = 0
    CENTRE_OF_ROTATION = 1


FIELD_NAMES = {
    Field.SLICE_INDEX: 'Slice Index',
    Field.CENTRE_OF_ROTATION: 'COR'
}


class CorTiltDataModel(object):
    """
    Data model for COR/Tilt finding from (slice index, centre of rotation) data
    pairs.
    """

    def __init__(self):
        self._points = []
        self._cached_m = None
        self._cached_c = None

    def populate_slice_indices(self, begin, end, count, cor=0.0):
        self.clear_results()

        self._points = [[int(idx), cor] for idx in np.linspace(
            begin, end, count, dtype=int)]
        LOG.debug('Populated slice indices: {}'.format(self.slices))

    def linear_regression(self):
        LOG.debug('Running linear regression with {} points'.format(
            self.num_points))
        result = sp.stats.linregress(self.slices, self.cors)
        self._cached_m, self._cached_c = result[:2]

    def add_point(self, idx=None, slice_idx=0, cor=0.0):
        self.clear_results()

        if idx is None:
            self._points.append([slice_idx, cor])
        else:
            self._points.insert(idx, [slice_idx, cor])

    def set_point(self, idx, slice_idx=None, cor=None):
        self.clear_results()

        if slice_idx is not None:
            self._points[idx][Field.SLICE_INDEX.value] = int(slice_idx)

        if cor is not None:
            self._points[idx][Field.CENTRE_OF_ROTATION.value] = float(cor)

    def remove_point(self, idx):
        self.clear_results()
        del self._points[idx]

    def clear_points(self):
        self._points = []
        self.clear_results()

    def clear_results(self):
        self._cached_m = None
        self._cached_c = None

    def point(self, idx):
        return self._points[idx] if idx < self.num_points else None

    def sort_points(self):
        self._points.sort(key=lambda p: p[Field.SLICE_INDEX.value])

    def get_cor_for_slice(self, slice_idx):
        a = [p[Field.CENTRE_OF_ROTATION.value] for p in self._points if \
                p[Field.SLICE_INDEX.value] == slice_idx]
        return a[0] if a else None

    def get_cor_for_slice_from_regression(self, slice_idx):
        if not self.has_results:
            return None

        cor = (self.m * slice_idx) + self.c
        return cor

    @property
    def slices(self):
        return [int(p[Field.SLICE_INDEX.value]) for p in self._points]

    @property
    def cors(self):
        return [float(p[Field.CENTRE_OF_ROTATION.value]) for p in self._points]

    @property
    def m(self):
        return self._cached_m

    @property
    def c(self):
        return self._cached_c

    @property
    def angle_rad(self):
        return cors_to_tilt_angle(self.slices[-1], self.m)

    @property
    def has_results(self):
        return self._cached_m is not None and self._cached_c is not None

    @property
    def empty(self):
        return not self._points

    @property
    def num_points(self):
        return len(self._points)

    @property
    def stack_properties(self):
        return {
            const.AUTO_COR_TILT: {
                'rotation_centre': self.c,
                'fitted_gradient': self.m,
                'tilt_angle_rad': self.angle_rad,
                'slice_indices': self.slices,
                'rotation_centres': self.cors
            }
        }
