from typing import List, Optional

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.core.utility.progress_reporting import Progress


class BaseRecon:
    @staticmethod
    def single(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
               recon_params: ReconstructionParameters) -> np.ndarray:
        """
        Performs a preview of a single slice/sinogram from a 3D volume provided as
        a stack of projections.

        :param sino: Sinogram to reconstruct
        :param cor: Centre of rotation value
        :param proj_angles: Array of projection angles
        :param recon_params: Parameters for the reconstruction
        :return: 2D image data for reconstructed slice
        """
        raise NotImplemented("Base class call")

    @staticmethod
    def single_sino(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters) -> np.ndarray:
        """
        Reconstruct a single sinogram

        :param sino: The 2D sinogram as a numpy array
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
