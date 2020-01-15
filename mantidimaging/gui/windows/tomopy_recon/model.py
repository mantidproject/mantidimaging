from logging import getLogger
from typing import Optional, Dict, Any

import numpy as np

from mantidimaging.core.reconstruct import tomopy_reconstruct, allowed_recon_kwargs
from mantidimaging.core.utility.projection_angles import \
    generate as generate_projection_angles
from mantidimaging.core.data.images import Images

LOG = getLogger(__name__)


class TomopyReconWindowModel(object):

    def __init__(self):
        self.stack = None
        self.projection = None
        self.preview_slice_idx = 0
        self.current_algorithm = "gridrec"
        self.current_filter = "none"
        self.images_are_sinograms = True
        self.num_iter = None

        self.cors = None
        self.projection_angles = None

        self.recon_params: Dict[str, Any] = {}

    @property
    def sample(self):
        return self.stack.presenter.images.sample if self.stack is not None \
            else None

    @property
    def images(self) -> Optional[Images]:
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
            self.projection_angles = generate_projection_angles(max_angle, num_radiograms)

    def reconstruct_slice(self, progress):
        data = np.asarray([self.sample[self.preview_slice_idx]])
        return self._recon(data, self.cors[self.preview_slice_idx], progress)

    def reconstruct_volume(self, progress):
        return self._recon(self.sample, self.cors, progress)

    def _recon(self, data, cors, progress):
        # Copy of kwargs kept for recording the operation (in the presenter)
        # If args are added, they will need to be kept and used in the same way.
        kwargs = {"sample": data,
                  "cor": cors,
                  "algorithm_name": self.current_algorithm,
                  "filter_name": self.current_filter,
                  "proj_angles": self.projection_angles,
                  "num_iter": self.num_iter,
                  "progress": progress,
                  "images_are_sinograms": self.images_are_sinograms}
        self.recon_params = kwargs
        return tomopy_reconstruct(**kwargs)

    @staticmethod
    def load_allowed_recon_kwargs():
        return allowed_recon_kwargs()
