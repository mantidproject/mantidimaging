from logging import getLogger

import numpy as np

from mantidimaging.core.cor_tilt import run_auto_finding_on_images
from mantidimaging.core.reconstruct import tomopy_reconstruct_preview
from mantidimaging.core.utility.projection_angles import (
        generate as generate_projection_angles)

LOG = getLogger(__name__)


class CORTiltWindowModel(object):

    def __init__(self, model):
        self.stack = None
        self.preview_projection_idx = 0
        self.preview_slice_idx = 0
        self.roi = None
        self.projection_indices = None
        self.model = model
        self.last_result = None

    @property
    def has_results(self):
        return self.model.has_results

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

    @property
    def num_slices(self):
        s = self.sample
        return s.shape[1] if s is not None else 0

    @property
    def cor_for_current_preview_slice(self):
        return self.model.get_cor_for_slice(self.preview_slice_idx)

    def initial_select_data(self, stack):
        self.model.clear_results()

        self.stack = stack
        self.preview_projection_idx = 0
        self.preview_slice_idx = 0

        if stack is not None:
            image_shape = self.sample[0].shape
            self.roi = (0, 0, image_shape[1] - 1, image_shape[0] - 1)
            self.proj_angles = generate_projection_angles(
                    360, self.sample.shape[0])

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

    def run_finding_automatic(self, progress):
        # Ensure we have some sample data
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

        # Cache last result
        self.last_result = self.model.stack_properties

        # Async task needs a non-None result of some sort
        return True

    def run_finding_manual(self, progress):
        # Ensure we have some sample data
        if self.stack is None:
            raise ValueError('No image stack is provided')

        if self.roi is None:
            raise ValueError('No region of interest is defined')

        self.model.linear_regression()
        self.images.properties.update(self.model.stack_properties)

        # Cache last result
        self.last_result = self.model.stack_properties

        # Async task needs a non-None result of some sort
        return True

    def run_preview_recon(self, slice_idx, cor):
        # Ensure we have some sample data
        if self.sample is None:
            raise ValueError('No sample to use for preview reconstruction')

        # Perform single slice reconstruction
        return tomopy_reconstruct_preview(
               self.sample, slice_idx, cor, self.proj_angles)

    @property
    def preview_tilt_line_data(self):
        return ([self.model.c, self.model.cors[-1]],
                [self.model.slices[0], self.model.slices[-1]]) \
                        if self.model.has_results else None

    @property
    def preview_fit_y_data(self):
        return [self.model.m * s + self.model.c for s in self.model.slices] \
                if self.model.has_results else None
