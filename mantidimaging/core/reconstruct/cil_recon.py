# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from logging import getLogger
from typing import List

import numpy as np

# import cil

from mantidimaging.core.data import Images
from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.data_containers import ProjectionAngles, ReconstructionParameters, ScalarCoR
from mantidimaging.core.utility.optional_imports import safe_import
from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)
tomopy = safe_import('tomopy')


def empty_array(shape):
    return (np.indices(shape).sum(axis=0) % 2).astype(np.float32)


class CILRecon(BaseRecon):
    @staticmethod
    def find_cor(images: Images, slice_idx: int, start_cor: float, recon_params: ReconstructionParameters) -> float:
        return tomopy.find_center(images.sinograms,
                                  images.projection_angles(recon_params.max_projection_angle).value,
                                  ind=slice_idx,
                                  init=start_cor,
                                  sinogram_order=True)

    @staticmethod
    def single_sino(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters):
        """
        Reconstruct a single slice from a single sinogram. Used for the preview and the single slice button.
        Should return a numpy array,
        """
        sino = BaseRecon.sino_recon_prep(sino)
        # volume = tomopy.recon(tomo=[sino],
        #                      sinogram_order=True,
        #                      theta=proj_angles.value,
        #                      center=cor.value,
        #                      algorithm=recon_params.algorithm,
        #                      filter_name=recon_params.filter_name)

        print("cor", cor)
        print("sino.shape", sino.shape)
        print("proj_angles", proj_angles.value[:10], "...")
        print("recon_params", recon_params)
        width = sino.shape[1]
        slice = empty_array([width, width])
        return slice

    @staticmethod
    def full(images: Images, cors: List[ScalarCoR], recon_params: ReconstructionParameters, progress=None):
        """
        Performs a volume reconstruction using sample data provided as sinograms.

        :param images: Array of sinogram images
        :param cors: Array of centre of rotation values
        :param proj_angles: Array of projection angles in radians
        :param recon_params: Reconstruction Parameters
        :param progress: Optional progress reporter
        :return: 3D image data for reconstructed volume
        """
        progress = Progress.ensure_instance(progress, task_name='CIL reconstruction')

        import multiprocessing
        ncores = multiprocessing.cpu_count()

        kwargs = {
            'ncore': ncores,
            'tomo': images.data,
            'sinogram_order': images._is_sinograms,
            'theta': images.projection_angles(recon_params.max_projection_angle).value,
            'center': [cor.value for cor in cors],
            'alpha': recon_params.alpha,
            'num_iter': recon_params.num_iter,
        }
        print("kwargs", kwargs)

        with progress:
            # volume = tomopy.recon(**kwargs)
            width = images.width
            slices = images.height
            volume = empty_array([slices, width, width])
            LOG.info('Reconstructed 3D volume with shape: {0}'.format(volume.shape))

        return Images(volume)


def allowed_recon_kwargs() -> dict:
    return {'CIL': ['alpha', 'num_iter']}
