from logging import getLogger

import numpy as np

from mantidimaging.core.reconstruct import tomopy_reconstruct
from mantidimaging.core.utility.projection_angles import \
    generate as generate_projection_angles

LOG = getLogger(__name__)


class TomopyReconWindowModel(object):

    def __init__(self):
        self.stack = None
        self.projection = None
        self.preview_slice_idx = 0
        self.current_algorithm = "gridrec"
        self.current_filter = "none"

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

    def generate_cors(self, cor, gradient):
        if self.stack is not None:
            num_slices = self.sample.shape[0]
            self.cors = (np.arange(0, num_slices, 1) * gradient) + cor
            LOG.debug('Generated CORs: {}'.format(self.cors))

    def generate_projection_angles(self, max_angle):
        if self.stack is not None:
            num_radiograms = self.sample.shape[1]
            self.projection_angles = \
                generate_projection_angles(max_angle, num_radiograms)

    def reconstruct_slice(self, progress):
        data = np.asarray([self.sample[self.preview_slice_idx]])
        return self._recon(data, self.cors[self.preview_slice_idx], progress)

    def reconstruct_volume(self, progress):
        return self._recon(self.sample, self.cors, progress)

    def _recon(self, data, cors, progress):
        return tomopy_reconstruct(
            sample=data,
            cor=cors,
            algorithm_name=self.current_algorithm,
            filter_name=self.current_filter,
            proj_angles=self.projection_angles,
            progress=progress)
