from contextlib import contextmanager
from typing import Union, Tuple, List, Optional

import astra
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.core.utility.progress_reporting import Progress


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


class AstraRecon:

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
    def single(images: Images, slice_idx: int, cor: ScalarCoR, proj_angles: ProjectionAngles,
               recon_params: ReconstructionParameters) -> np.ndarray:
        return AstraRecon.single_sino(images.sino(slice_idx), images.projection(0).shape, cor,
                                      proj_angles, recon_params)

    @staticmethod
    def single_sino(sino: np.ndarray, shape: Tuple[int, int],
                    cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters) -> np.ndarray:
        """

        :param sino: Single sinogram, i.e. 2D array
        :param shape: The original shape of the 3D dataset - used to make the correct reconstruction output shape
        :param cor: Center of rotation for parallel geometry. It will be converted to vector geometry before reconstructing
        :param proj_angles: Projection angles
        :param recon_params: Reconstruction parameters to configure which algorithm/filter/etc is used
        """
        assert sino.ndim == 2, "Sinogram must be a 2D image"
        assert len(shape) == 2, "Projection shape of the data must be 2D"

        image_width = shape[1]
        vectors = vec_geom_init2d(proj_angles, 1.0, cor.to_vec(image_width).value)
        vol_geom = astra.create_vol_geom(shape)
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
        output_images: Images = Images.create_shared_images((images.height, images.height, images.width), images.dtype)
        for i in range(images.height):
            output_images.data[i] = AstraRecon.single(images, i, cors[i], proj_angles, recon_params)
            progress.update(1, f"Reconstructed slice {i}")

        return output_images


def allowed_recon_kwargs() -> dict:
    return {'FBP_CUDA': ['filter_name', 'filter_par'],
            'SIRT_CUDA': ['num_iter', 'min_constraint', 'max_constraint', 'DetectorSuperSampling',
                          'PixelSuperSampling'],
            'SIRT3D_CUDA': ['num_iter', 'min_constraint', 'max_constraint', 'DetectorSuperSampling',
                            'PixelSuperSampling']}
