from __future__ import (absolute_import, division, print_function)

import numpy as np

from mantidimaging.core.cor_tilt import (
        CorTiltDataModel, run_auto_finding_on_images)


class CORTiltDialogModel(object):

    def __init__(self):
        self.stack = None
        self.preview_idx = 0
        self.roi = None
        self.projection_indices = None
        self.model = CorTiltDataModel()

    @property
    def sample(self):
        return self.stack.presenter.images.sample if self.stack else None

    @property
    def images(self):
        return self.stack.presenter.images if self.stack else None

    @property
    def num_projections(self):
        s = self.sample
        return s.shape[0] if s is not None else 0

    def initial_select_data(self, stack):
        self.model.clear_results()

        self.stack = stack
        self.preview_idx = 0

        if stack is not None:
            image_shape = self.sample[0].shape
            self.roi = (0, 0, image_shape[1] - 1, image_shape[0] - 1)

    def update_roi_from_stack(self):
        self.model.clear_results()
        self.roi = self.stack.current_roi if self.stack else None

    def calculate_slices(self, count):
        self.model.clear_results()
        if self.roi is not None:
            lower = self.roi[1]
            upper = self.roi[3]
            self.model.populate_slice_indices(lower, upper, count)

    def calculate_projections(self, count):
        self.model.clear_results()
        if self.sample is not None:
            sample_proj_count = self.sample.shape[0]
            downsample_proj_count = min(sample_proj_count, count)
            self.projection_indices = \
                np.linspace(0, sample_proj_count - 1, downsample_proj_count,
                            dtype=int)

    def run_finding(self, progress):
        if self.stack is None:
            raise ValueError('No image stack is provided')

        if self.roi is None:
            raise ValueError('No region of interest is defined')

        run_auto_finding_on_images(
                self.images,
                self.model,
                self.roi,
                self.projection_indices,
                progress=progress)

        return True

    @property
    def preview_tilt_line_data(self):
        return ([self.model.c, self.model.cors[-1]],
                [self.model.slices[0], self.model.slices[-1]]) \
                        if self.model.has_results else None

    @property
    def preview_fit_y_data(self):
        return [self.model.m * s + self.model.c for s in self.model.slices] \
                if self.model.has_results else None
