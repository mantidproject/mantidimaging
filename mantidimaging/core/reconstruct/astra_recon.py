from contextlib import contextmanager
from typing import Union, List, Optional

import astra
import numpy as np
from scipy.optimize import minimize

from mantidimaging.core.data import Images
from mantidimaging.core.parallel import two_shared_mem as ptsm
from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.core.utility.progress_reporting import Progress


# Full credit for following code to Daniil Kazantzev
# Source: https://github.com/dkazanc/ToMoBAR/blob/master/src/Python/tomobar/supp/astraOP.py#L20-L70
def rotation_matrix2d(theta):
    return np.array([[np.cos(theta), -np.sin(theta)],
                     [np.sin(theta), np.cos(theta)]])


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


class AstraRecon(BaseRecon):
    @staticmethod
    def _count_gpus() -> int:
        num_gpus = 0
        try:
            msg = ''
            while "Invalid device" not in msg:
                num_gpus += 1
                msg = astra.set_gpu_index(num_gpus)
        except Exception:
            pass
        astra.set_gpu_index(0)
        return num_gpus

    @staticmethod
    def find_cor(images: Images, slice_idx: int, start_cor: float,
                 proj_angles: ProjectionAngles, recon_params: ReconstructionParameters) -> float:
        """
        Find the best CoR for this slice by maximising the squared sum of the reconstructed slice.

        Larger squared sum -> bigger deviance from the mean, i.e. larger distance between noise and data
        """

        def get_sumsq(image: np.ndarray) -> float:
            return np.sum(image ** 2)

        def minimizer_function(cor):
            return -get_sumsq(AstraRecon.single(images.sino(slice_idx), ScalarCoR(cor), proj_angles, recon_params))

        return minimize(minimizer_function, start_cor, method='nelder-mead', tol=0.1).x[0]

    @staticmethod
    @contextmanager
    def _managed_recon(sino, cfg, proj_geom, vol_geom) -> int:
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

    @staticmethod
    def single(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
               recon_params: ReconstructionParameters) -> np.ndarray:
        return AstraRecon.single_sino(sino, cor, proj_angles, recon_params)

    @staticmethod
    def single_sino(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters) -> np.ndarray:
        assert sino.ndim == 2, "Sinogram must be a 2D image"

        image_width = sino.shape[1]
        vectors = vec_geom_init2d(proj_angles, 1.0, cor.to_vec(image_width).value)
        vol_geom = astra.create_vol_geom(sino.shape)
        proj_geom = astra.create_proj_geom('parallel_vec', image_width, vectors)
        cfg = astra.astra_dict(recon_params.algorithm)
        cfg['FilterType'] = recon_params.filter_name
        with AstraRecon._managed_recon(sino, cfg, proj_geom, vol_geom) as (alg_id, rec_id):
            astra.algorithm.run(alg_id, iterations=recon_params.num_iter)
            return astra.data2d.get(rec_id)

    @staticmethod
    def full(images: Images, cors: List[ScalarCoR], proj_angles: ProjectionAngles,
             recon_params: ReconstructionParameters, progress: Optional[Progress] = None) -> Images:
        progress = Progress.ensure_instance(progress, num_steps=images.height)
        output_shape = (images.num_sinograms,) + images.sino(0).shape
        output_images: Images = Images.create_shared_images(output_shape, images.dtype)

        num_gpus = AstraRecon._count_gpus()
        partial = ptsm.create_partial(AstraRecon.single, ptsm.fwd_gpu_recon,
                                      num_gpus=num_gpus, cors=cors, proj_angles=proj_angles, recon_params=recon_params)
        ptsm.execute(images.sinograms, output_images.data, partial, num_gpus, progress=progress)
        # for i in range(images.height):
        #     output_images.data[i] = AstraRecon.single(images.sino(i), cors[i], proj_angles, recon_params)
        #     progress.update(1, f"Reconstructed slice {i}")

        return output_images

    @staticmethod
    def allowed_filters():
        return ['ram-lak', 'shepp-logan', 'cosine', 'hamming', 'hann', 'none', 'tukey', 'lanczos', 'triangular',
                'gaussian', 'barlett-hann', 'blackman', 'nuttall', 'blackman-harris', 'blackman-nuttall',
                'flat-top', 'kaiser', 'parzen', 'projection', 'sinogram', 'rprojection', 'rsinogram']


def allowed_recon_kwargs() -> dict:
    return {'FBP_CUDA': ['filter_name', 'filter_par'],
            'SIRT_CUDA': ['num_iter', 'min_constraint', 'max_constraint', 'DetectorSuperSampling',
                          'PixelSuperSampling'],
            'SIRT3D_CUDA': ['num_iter', 'min_constraint', 'max_constraint', 'DetectorSuperSampling',
                            'PixelSuperSampling']}
