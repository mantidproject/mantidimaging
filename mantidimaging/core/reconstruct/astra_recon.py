# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from contextlib import contextmanager
from logging import getLogger
from typing import Union, List, Optional, Tuple, Generator

import astra
import numpy as np
from scipy.optimize import minimize

from mantidimaging.core.data import Images
from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)


# Full credit for following code to Daniil Kazantzev
# Source:
# https://github.com/dkazanc/ToMoBAR/blob/5990aaa264e2f08bd9b0069c8847e5021fbf2ee2/src/Python/tomobar/supp/astraOP.py#L20-L70
def rotation_matrix2d(theta):
    return np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])


def vec_geom_init2d(angles_rad: ProjectionAngles, detector_spacing_x: float, center_rot_offset: Union[float]):
    angles_value = angles_rad.value
    s0 = [0.0, -1.0]  # source
    u0 = [detector_spacing_x, 0.0]  # detector coordinates
    vectors = np.zeros([angles_value.size, 6])
    for i, theta in enumerate(angles_value):
        d0 = [center_rot_offset, 0.0]  # detector
        vectors[i, 0:2] = np.dot(rotation_matrix2d(theta), s0)[:]  # ray position
        vectors[i, 2:4] = np.dot(rotation_matrix2d(theta), d0)[:]  # center of detector position
        vectors[i, 4:6] = np.dot(rotation_matrix2d(theta), u0)[:]  # detector pixel (0,0) to (0,1).
    return vectors


@contextmanager
def _managed_recon(sino, cfg, proj_geom, vol_geom) -> Generator[Tuple[int, int], None, None]:
    proj_id = None
    sino_id = None
    rec_id = None
    alg_id = None
    try:
        proj_id = astra.create_projector('cuda', proj_geom, vol_geom)
        sino_id = astra.data2d.create('-sino', proj_geom, sino)
        rec_id = astra.data2d.create('-vol', vol_geom)

        cfg['ReconstructionDataId'] = rec_id
        cfg['ProjectionDataId'] = sino_id
        cfg['ProjectorId'] = proj_id

        alg_id = astra.algorithm.create(cfg)
        yield alg_id, rec_id
    finally:
        if alg_id:
            astra.algorithm.delete(alg_id)
        if proj_id:
            astra.projector.delete(proj_id)
        if sino_id:
            astra.data2d.delete(sino_id)
        if rec_id:
            astra.data2d.delete(rec_id)


class AstraRecon(BaseRecon):
    @staticmethod
    def _count_gpus() -> int:
        num_gpus = 0
        msg = ''
        while "Invalid device" not in msg:
            num_gpus += 1
            msg = astra.get_gpu_info(num_gpus)
        return num_gpus

    @staticmethod
    def find_cor(images: Images, slice_idx: int, start_cor: float, recon_params: ReconstructionParameters) -> float:
        """
        Find the best CoR for this slice by maximising the squared sum of the reconstructed slice.

        Larger squared sum -> bigger deviance from the mean, i.e. larger distance between noise and data
        """

        proj_angles = images.projection_angles(recon_params.max_projection_angle)

        def get_sumsq(image: np.ndarray) -> float:
            return np.sum(image**2)

        def minimizer_function(cor):
            return -get_sumsq(AstraRecon.single_sino(images.sino(slice_idx), ScalarCoR(cor), proj_angles, recon_params))

        return minimize(minimizer_function, start_cor, method='nelder-mead', tol=0.1).x[0]

    @staticmethod
    def single_sino(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters) -> np.ndarray:
        assert sino.ndim == 2, "Sinogram must be a 2D image"

        sino = BaseRecon.sino_recon_prep(sino)
        image_width = sino.shape[1]
        vectors = vec_geom_init2d(proj_angles, 1.0, cor.to_vec(image_width).value)
        vol_geom = astra.create_vol_geom((image_width, image_width))
        proj_geom = astra.create_proj_geom('parallel_vec', image_width, vectors)
        cfg = astra.astra_dict(recon_params.algorithm)
        cfg['FilterType'] = recon_params.filter_name
        with _managed_recon(sino, cfg, proj_geom, vol_geom) as (alg_id, rec_id):
            astra.algorithm.run(alg_id, iterations=recon_params.num_iter)
            return astra.data2d.get(rec_id)

    @staticmethod
    def full(images: Images,
             cors: List[ScalarCoR],
             recon_params: ReconstructionParameters,
             progress: Optional[Progress] = None) -> Images:
        progress = Progress.ensure_instance(progress, num_steps=images.height)
        output_shape = (images.num_sinograms, images.width, images.width)
        output_images: Images = Images.create_empty_images(output_shape, images.dtype, images.metadata)
        output_images.record_operation('AstraRecon.full', 'Volume Reconstruction', **recon_params.to_dict())

        proj_angles = images.projection_angles(recon_params.max_projection_angle)
        for i in range(images.height):
            output_images.data[i] = AstraRecon.single_sino(images.sino(i), cors[i], proj_angles, recon_params)
            progress.update(1, "Reconstructed slice")

        return output_images

    @staticmethod
    def allowed_filters():
        # removed from list: 'kaiser' as it hard crashes ASTRA
        #                    'projection', 'sinogram', 'rprojection', 'rsinogram' as they error
        return [
            'ram-lak', 'shepp-logan', 'cosine', 'hamming', 'hann', 'none', 'tukey', 'lanczos', 'triangular', 'gaussian',
            'barlett-hann', 'blackman', 'nuttall', 'blackman-harris', 'blackman-nuttall', 'flat-top', 'parzen'
        ]


def allowed_recon_kwargs() -> dict:
    return {
        'FBP_CUDA': ['filter_name', 'filter_par'],
        'SIRT_CUDA': ['num_iter', 'min_constraint', 'max_constraint', 'DetectorSuperSampling', 'PixelSuperSampling'],
        'SIRT3D_CUDA': ['num_iter', 'min_constraint', 'max_constraint', 'DetectorSuperSampling', 'PixelSuperSampling']
    }
