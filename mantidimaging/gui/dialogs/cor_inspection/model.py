from logging import getLogger

import numpy as np

from mantidimaging.core.reconstruct import (tomopy_reconstruct_preview_from_sinogram)
from mantidimaging.core.utility.data_containers import ScalarCoR
from mantidimaging.core.utility.projection_angles import (generate as generate_projection_angles)
from .types import ImageType

LOG = getLogger(__name__)


class CORInspectionDialogModel(object):
    def __init__(self, data, slice_idx, initial_cor: ScalarCoR, initial_step=50, max_angle=360):
        # Extract the sinogram
        if slice_idx is None:
            self.sino = data
        else:
            LOG.debug('Extracting sinogram at index {}'.format(slice_idx))
            self.sino = np.swapaxes(data, 0, 1)[slice_idx]
        LOG.debug('Sinogram shape: {}'.format(self.sino.shape))

        # Initial parameters
        self.centre_cor = initial_cor.value
        self.cor_step = initial_step

        # Cache projection angles
        self.proj_angles = generate_projection_angles(max_angle, self.sino.shape[0])

    def adjust_cor(self, image):
        """
        Adjusts the rotation centre and step after an image is selected as the
        optimal of an iteration.
        """
        if image == ImageType.LESS:
            self.centre_cor -= self.cor_step
        elif image == ImageType.MORE:
            self.centre_cor += self.cor_step
        elif image == ImageType.CURRENT:
            self.cor_step /= 2

    def cor(self, image):
        """
        Gets the rotation centre for a given image in the current iteration.
        """
        if image == ImageType.LESS:
            return max(self.cor_extents[0], self.centre_cor - self.cor_step)
        elif image == ImageType.CURRENT:
            return self.centre_cor
        elif image == ImageType.MORE:
            return min(self.cor_extents[1], self.centre_cor + self.cor_step)

    def recon_preview(self, image):
        cor = self.cor(image)
        # TODO
        # Only two images should need to be reconstructed per iteration
        # (currently all three are).
        # Look for a way to cache them after the iteration step has been
        # finalised with scientists.
        return tomopy_reconstruct_preview_from_sinogram(self.sino, cor, self.proj_angles)

    @property
    def cor_extents(self):
        return 0, self.sino.shape[1] - 1
