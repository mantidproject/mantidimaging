from logging import getLogger

from mantidimaging.core.data import Images
from mantidimaging.core.reconstruct import get_reconstructor_for
from mantidimaging.core.utility.data_containers import ScalarCoR, ReconstructionParameters
from .types import ImageType

LOG = getLogger(__name__)


class CORInspectionDialogModel(object):
    def __init__(self, images: Images, slice_idx: int, initial_cor: ScalarCoR, recon_params: ReconstructionParameters):
        self.image_width = images.width
        self.sino = images.sino(slice_idx)

        # Initial parameters
        self.centre_cor = initial_cor.value
        self.cor_step = images.width

        # Cache projection angles
        self.proj_angles = images.projection_angles()
        self.recon_params = recon_params
        self.reconstructor = get_reconstructor_for(recon_params.algorithm)

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
        return self.reconstructor.single_sino(self.sino, cor, self.proj_angles, self.recon_params)

    @property
    def cor_extents(self):
        return 0, self.sino.shape[1] - 1
