from typing import Tuple, List, Optional

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.core.utility.progress_reporting import Progress


class BaseRecon:
    @staticmethod
    def single(images: Images, slice_idx: int, cor: ScalarCoR, proj_angles: ProjectionAngles,
               recon_params: ReconstructionParameters) -> np.ndarray:
        """
        Performs a preview of a single slice/sinogram from a 3D volume provided as
        a stack of projections.

        :param images: 3D projection data
        :param slice_idx: Index of slice/sinogram to reconstruct
        :param cor: Centre of rotation value
        :param proj_angles: Array of projection angles
        :return: 2D image data for reconstructed slice
        """
        raise NotImplemented("Base class call")

    @staticmethod
    def single_sino(sino: np.ndarray, shape: Tuple[int, int],
                    cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters) -> np.ndarray:
        """
        Reconstruct a single sinogram

        :param sino: The 2D sinogram as a numpy array
        :param shape: Shape of the 2D projection
        :param cor: Center of rotation for parallel geometry. It will be converted to vector geometry before reconstructing
        :param proj_angles: Projection angles
        :param recon_params: Reconstruction parameters to configure which algorithm/filter/etc is used
        :return: 2D image data for reconstructed slice
        """
        raise NotImplemented("Base class call")

    @staticmethod
    def full(images: Images, cors: List[ScalarCoR], proj_angles: ProjectionAngles,
             recon_params: ReconstructionParameters, progress: Optional[Progress] = None) -> Images:
        """
        Performs a volume reconstruction using sample data provided as sinograms.

        :param images: Array of sinogram images
        :param cors: Array of centre of rotation values
        :param proj_angles: Array of projection angles
        :param recon_params: Reconstruction Parameters
        :param progress: Optional progress reporter
        :return: 3D image data for reconstructed volume
        """
        raise NotImplemented("Base class call")

    @staticmethod
    def allowed_filters() -> List[str]:
        raise NotImplemented("Base class call")
