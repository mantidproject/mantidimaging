# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import List, Optional

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.core.utility.progress_reporting import Progress

# Prevents undefined and infinite values due to negative or zero pixels in
# projection being passed into the negative log
MIN_PIXEL_VALUE: float = 1e-6


class BaseRecon:
    @staticmethod
    def find_cor(images: Images, slice_idx: int, start_cor: float, recon_params: ReconstructionParameters) -> float:
        raise NotImplementedError("Base class call")

    @staticmethod
    def sino_recon_prep(sino: np.ndarray):
        return -np.log(np.maximum(sino, MIN_PIXEL_VALUE))

    @staticmethod
    def single_sino(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters) -> np.ndarray:
        """
        Reconstruct a single sinogram

        :param sino: The 2D sinogram as a numpy array
        :param cor: Center of rotation for parallel geometry.
                    It will be converted to vector geometry before reconstructing
        :param proj_angles: Projection angles
        :param recon_params: Reconstruction parameters to configure which algorithm/filter/etc is used
        :return: 2D image data for reconstructed slice
        """
        raise NotImplementedError("Base class call")

    @staticmethod
    def full(images: Images,
             cors: List[ScalarCoR],
             recon_params: ReconstructionParameters,
             progress: Optional[Progress] = None) -> Images:
        """
        Performs a volume reconstruction using sample data provided as sinograms.

        :param images: Array of sinogram images
        :param cors: Array of centre of rotation values
        :param proj_angles: Array of projection angles
        :param recon_params: Reconstruction Parameters
        :param progress: Optional progress reporter
        :return: 3D image data for reconstructed volume
        """
        raise NotImplementedError("Base class call")

    @staticmethod
    def allowed_filters() -> List[str]:
        return []
