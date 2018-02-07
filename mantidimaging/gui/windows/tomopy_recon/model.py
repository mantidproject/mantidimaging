from __future__ import (absolute_import, division, print_function)

from logging import getLogger

import numpy as np

from mantidimaging.core.utility.projection_angles import \
        generate as generate_projection_angles
from mantidimaging.core.cor_tilt import tilt_angle_to_cors
from mantidimaging.core.reconstruct import tomopy_reconstruct


LOG = getLogger(__name__)


class TomopyReconWindowModel(object):

    def __init__(self):
        self.stack = None
        self.projection = None
        self.preview_slice_idx = 0

        self.cors = None
        self.projection_angles = None

    @property
    def sample(self):
        return self.stack.presenter.images.sample if self.stack is not None \
                else None

    @property
    def images(self):
        return self.stack.presenter.images if self.stack is not None else None

    def initial_select_data(self, stack):
        self.stack = stack

        self.projection = self.sample.swapaxes(0, 1) \
            if stack is not None else None

    def generate_cors(self, cor, tilt):
        if self.stack is not None:
            num_slices = self.sample.shape[0]
            self.cors = tilt_angle_to_cors(
                    tilt, cor, np.arange(0, num_slices, 1))
            LOG.debug('Generated CORs: {}'.format(self.cors))

    def generate_projection_angles(self, max_angle):
        if self.stack is not None:
            num_radiograms = self.sample.shape[1]
            self.projection_angles = \
                generate_projection_angles(max_angle, num_radiograms)

    def reconstruct_slice(self, progress):
        data = np.asarray([self.sample[self.preview_slice_idx]])

        return tomopy_reconstruct(
                sample=data,
                cor=self.cors[self.preview_slice_idx],
                proj_angles=self.projection_angles,
                progress=progress)

    def reconstruct_volume(self, progress):
        return tomopy_reconstruct(
                sample=self.sample,
                cor=self.cors,
                proj_angles=self.projection_angles,
                progress=progress)
