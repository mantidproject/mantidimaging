from __future__ import (absolute_import, division, print_function)

import numpy as np

from mantidimaging.core.reconstruct import calculate_cor_and_tilt


class CORTiltDialogModel(object):

    def __init__(self):
        self.stack = None
        self.preview_idx = 0
        self.roi = None
        self.slice_indices = None

        self.slices = None
        self.cors = None
        self.cor = None
        self.tilt = None

    def reset_results(self):
        self.slices = None
        self.cors = None
        self.cor = None
        self.tilt = None

    @property
    def sample(self):
        return self.stack.presenter.images.sample if self.stack else None

    @property
    def num_projections(self):
        s = self.sample
        return s.shape[0] if s is not None else 0

    def initial_select_data(self, stack):
        self.reset_results()

        self.stack = stack
        self.preview_idx = 0

        if stack is not None:
            image_shape = self.sample[0].shape
            self.roi = (0, 0, image_shape[1], image_shape[0])

    def update_roi_from_stack(self):
        self.reset_results()
        self.roi = self.stack.current_roi if self.stack else None

    def calculate_slices(self, count):
        self.reset_results()
        if self.roi is not None:
            lower = self.roi[1]
            upper = self.roi[3]

            step = int((upper - lower) / count) if count != 0 else 1

            self.slice_indices = np.arange(upper - 1, lower, -step)

    def run_finding(self):
        self.tilt, self.cor, self.slices, self.cors, self.m = \
                calculate_cor_and_tilt(
                        self.sample, self.roi, self.slice_indices)

    @property
    def preview_tilt_line_data(self):
        return ([self.cor, self.cors[-1]],
                [self.slice_indices[0], self.slice_indices[-1]]) if self.cor \
                        else None

    @property
    def preview_fit_y_data(self):
        return [self.m * s + self.cor for s in self.slices] \
                if self.cor else None
