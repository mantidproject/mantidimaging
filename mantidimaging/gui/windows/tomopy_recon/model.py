from logging import getLogger
from typing import Optional, Dict, Any

import numpy as np

from mantidimaging.core.cor_tilt.auto import generate_cors
from mantidimaging.core.data.images import Images
from mantidimaging.core.reconstruct import tomopy_reconstruct, allowed_recon_kwargs
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
        self.num_iter = None
        self.rotation_centre = None
        self.cor_gradient = None
        self.max_proj_angle = None

        self.recon_params: Dict[str, Any] = {}

    @property
    def sample(self) -> Optional[np.ndarray]:
        return self.stack.presenter.images.sample if self.stack is not None else None

    @property
    def images(self) -> Optional[Images]:
        return self.stack.presenter.images if self.stack is not None else None

    def initial_select_data(self, stack):
        self.stack = stack

    def reconstruct_slice(self, progress):
        images = self.images
        if images is not None:
            if images.sinograms is False:
                data = np.asarray([np.swapaxes(images.sample[:, self.preview_slice_idx, :], 0, 1)])
            else:
                data = np.asarray([images.sample[self.preview_slice_idx]])
            return self.do_recon(data, progress, **self._load_kwargs())

    def reconstruct_volume(self, progress):
        kwargs = self._load_kwargs()
        kwargs["images_are_sinograms"] = self.images.sinograms
        return self.do_recon(self.sample, progress, **kwargs)

    def _load_kwargs(self):
        # Copy of kwargs kept for recording the operation (in the presenter)
        # If args are added, they will need to be kept and used in the same way.
        kwargs = {
            "rotation_centre": self.rotation_centre,
            "gradient": self.cor_gradient,
            "algorithm_name": self.current_algorithm,
            "filter_name": self.current_filter,
            "max_proj_angle": self.max_proj_angle,
            "num_iter": self.num_iter,
        }
        self.recon_params = kwargs
        return kwargs

    @staticmethod
    def do_recon(data, progress=None, **kwargs):
        if data is None or not data.shape[0] > 0:
            raise RuntimeError("No data provided to reconstruct from")

        # Some kwargs required by tomopy are arrays, which are not recorded in op history as they can be large.
        # To be able to replay reconstructions from op history, we instead record the values required to calculate
        # the arrays (rotation_centre + gradient -> cor, max_proj_angle -> proj_angles) in the stack's operation
        # history, and do the array calculation here.
        just_copy = ["algorithm_name", "filter_name", "num_iter", "images_are_sinograms"]
        calculated_kwargs = {k: kwargs[k] for k in just_copy if k in kwargs}
        calculated_kwargs.update({
            "cor": generate_cors(kwargs["rotation_centre"], kwargs["gradient"], data.shape[0]),
            "proj_angles": generate_projection_angles(kwargs["max_proj_angle"], data.shape[1]),
        })
        return tomopy_reconstruct(sample=data, progress=progress, **calculated_kwargs)

    @staticmethod
    def load_allowed_recon_kwargs():
        return allowed_recon_kwargs()
