from logging import getLogger

import numpy as np
from typing import Optional

from mantidimaging.core.cor_tilt import (run_auto_finding_on_images, update_image_operations)
from mantidimaging.core.reconstruct import tomopy_reconstruct_preview
from mantidimaging.core.utility.projection_angles import (generate as generate_projection_angles)

from mantidimaging.gui.windows.cor_tilt.point_table_model import CorTiltPointQtModel
from mantidimaging.core.data import Images

LOG = getLogger(__name__)


class CORTiltWindowModel(object):
    def __init__(self, data_model: CorTiltPointQtModel):
        self.stack: Optional[Images] = None
        self.preview_projection_idx = 0
        self.preview_slice_idx = 0
        self.selected_row = 0
        self.roi = None
        self.projection_indices = None
        self.data_model = data_model
        self.last_result = None

    @property
    def has_results(self):
        return self.data_model.has_results

    def get_results(self):
        return self.data_model.cor, self.data_model.angle_rad, self.data_model.gradient

    @property
    def sample(self):
        return self.stack.presenter.images.sample if self.stack else None

    @property
    def images(self):
        return self.stack.presenter.images if self.stack else None

    @property
    def num_projections(self):
        return self.sample.shape[0] if self.sample is not None else 0

    @property
    def num_slices(self):
        return self.sample.shape[1] if self.sample is not None else 0

    @property
    def num_points(self):
        return self.data_model.num_points

    @property
    def cor_for_current_preview_slice(self):
        return self.data_model.get_cor_for_slice(self.preview_slice_idx)

    def set_all_cors(self, cor: float):
        for slice_idx in self.data_model.slices:
            self.data_model.set_cor_at_slice(slice_idx, cor)

    def initial_select_data(self, stack):
        self.data_model.clear_results()

        self.stack = stack
        self.preview_projection_idx = 0
        self.preview_slice_idx = 0

        if stack is not None:
            image_shape = self.sample[0].shape
            self.roi = (0, 0, image_shape[1] - 1, image_shape[0] - 1)
            self.proj_angles = generate_projection_angles(360, self.sample.shape[0])

    def update_roi_from_stack(self):
        self.data_model.clear_results()
        self.roi = self.stack.current_roi if self.stack else None

    def calculate_slices(self, count):
        self.data_model.clear_results()
        if self.roi is not None:
            lower = self.roi[1]
            upper = self.roi[3]
            self.data_model.populate_slice_indices(lower, upper, count)

    def calculate_projections(self, count):
        self.data_model.clear_results()
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

        run_auto_finding_on_images(self.images, self.data_model, self.roi, self.projection_indices, progress=progress)

        # Cache last result
        self.last_result = self.data_model.stack_properties

        # Async task needs a non-None result of some sort
        return True

    def run_finding_manual(self, progress):
        # Ensure we have some sample data
        if self.stack is None:
            raise ValueError('No image stack is provided')

        if self.roi is None:
            raise ValueError('No region of interest is defined')

        self.data_model.linear_regression()
        update_image_operations(self.images, self.data_model)

        # Cache last result
        self.last_result = self.data_model.stack_properties

        # Async task needs a non-None result of some sort
        return True

    def run_preview_recon(self, slice_idx, cor):
        # Ensure we have some sample data
        if self.sample is None:
            raise ValueError('No sample to use for preview reconstruction')

        # Perform single slice reconstruction
        return tomopy_reconstruct_preview(self.sample, slice_idx, cor, self.proj_angles)

    @property
    def preview_tilt_line_data(self):
        return ([self.data_model.cor, self.cors[-1]],
                [self.slices[0], self.slices[-1]]) if self.data_model.has_results else None

    @property
    def preview_fit_y_data(self):
        return [self.data_model.gradient * slice_idx + self.data_model.cor
                for slice_idx in self.slices] if self.data_model.has_results else None

    @property
    def cors(self):
        return self.data_model.cors

    @property
    def slices(self):
        return self.data_model.slices

    def get_cor_for_slice_from_regression(self):
        return self.data_model.get_cor_for_slice_from_regression(self.preview_slice_idx)
