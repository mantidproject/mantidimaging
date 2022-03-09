# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import List, Optional

import numpy as np
from numpy.polynomial import Polynomial

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.core.utility.progress_reporting import Progress


class BaseRecon:
    @staticmethod
    def find_cor(images: ImageStack, slice_idx: int, start_cor: float, recon_params: ReconstructionParameters) -> float:
        raise NotImplementedError("Base class call")

    @staticmethod
    def prepare_sinogram(data: np.ndarray, recon_params: ReconstructionParameters):
        if recon_params.beam_hardening_coefs is not None:
            a0, a1, a2, a3 = recon_params.beam_hardening_coefs
            bhc_poly = Polynomial([0, 1, a0, a1, a2, a3])
            logged_data = BaseRecon.negative_log(data)
            corrected_data = bhc_poly(logged_data)
            return corrected_data
        else:
            return BaseRecon.negative_log(data)

    @staticmethod
    def negative_log(data: np.ndarray) -> np.ndarray:
        return -np.log(data)

    @staticmethod
    def single_sino(sino: np.ndarray,
                    cor: ScalarCoR,
                    proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters,
                    progress: Optional[Progress] = None) -> np.ndarray:
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
    def full(images: ImageStack,
             cors: List[ScalarCoR],
             recon_params: ReconstructionParameters,
             progress: Optional[Progress] = None) -> ImageStack:
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
