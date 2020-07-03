from logging import getLogger

from mantidimaging.core.data import Images
from mantidimaging.core.reconstruct import get_reconstructor_for
from mantidimaging.core.utility.data_containers import ScalarCoR
from mantidimaging.core.utility.projection_angles import (generate as generate_projection_angles)
from .types import ImageType

LOG = getLogger(__name__)


class CORInspectionDialogModel(object):
    def __init__(self, data: Images, slice_idx: int, initial_cor: ScalarCoR, initial_step=50, max_angle=360,
                 algorithm="FBP_CUDA", filter_name="ram-lak"):
        self.projection_shape = data.projection(0).shape
        self.sino = data.sino(slice_idx)

        # Initial parameters
        self.centre_cor = initial_cor.value
        self.cor_step = initial_step

        # Cache projection angles
        self.proj_angles = generate_projection_angles(max_angle, data.num_projections)
        self.algorithm = algorithm
        self.reconstructor = get_reconstructor_for(algorithm)
        self.filter = filter_name

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
        cor = ScalarCoR(self.cor(image))
        return self.reconstructor.single_sino(self.sino, self.projection_shape, cor, self.proj_angles,
                                              self.algorithm, self.filter)

    @property
    def cor_extents(self):
        return 0, self.sino.shape[1] - 1
