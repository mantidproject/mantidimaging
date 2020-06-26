from enum import Enum
from typing import Union

import astra
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import ScalarCoR


def rotation_matrix2d(theta):
    return np.array([[np.cos(theta), -np.sin(theta)],
                     [np.sin(theta), np.cos(theta)]])


# astra = safe_import('astra')
def vec_geom_init2d(angles_rad: np.ndarray, detector_spacing_x: float, center_rot_offset: Union[float, np.ndarray]):
    s0 = [0.0, -1.0]  # source
    u0 = [detector_spacing_x, 0.0]  # detector coordinates
    vectors = np.zeros([angles_rad.size, 6])
    for i, theta in enumerate(angles_rad):
        if np.ndim(center_rot_offset) == 0:
            d0 = [center_rot_offset, 0.0]  # detector
        else:
            d0 = [center_rot_offset[i], 0.0]  # detector
        vectors[i, 0:2] = np.dot(rotation_matrix2d(theta), s0)[:]  # ray position
        vectors[i, 2:4] = np.dot(rotation_matrix2d(theta), d0)[:]  # center of detector position
        vectors[i, 4:6] = np.dot(rotation_matrix2d(theta), u0)[:]  # detector pixel (0,0) to (0,1).
    return vectors


def reconstruct_single_preview(images: Images, slice_idx, cor: ScalarCoR, proj_angles, algorithm, recon_filter,
                               progress=None):
    sample = images.sample
    sino = np.swapaxes(sample, 0, 1)[slice_idx]
    vectors = vec_geom_init2d(proj_angles, 1.0, cor.to_vec(images.width).value)
    vol_geom = astra.create_vol_geom(
        sample.shape[1:])  # doesn't change unless stack is cropped - gonna have to re-open gui
    proj_geom = astra.create_proj_geom('parallel_vec', sino.shape[1], vectors)
    proj_id = astra.create_projector('cuda', proj_geom, vol_geom)  # no change
    sino_id = astra.data2d.create('-sino', proj_geom, sino)
    rec_id = astra.data2d.create('-vol', vol_geom)  # no change
    cfg = astra.astra_dict('FBP_CUDA')
    cfg['ReconstructionDataId'] = rec_id
    cfg['ProjectionDataId'] = sino_id
    cfg['FilterType'] = 'ram-lak'
    cfg['ProjectorId'] = proj_id
    alg_id = astra.algorithm.create(cfg)
    astra.algorithm.run(alg_id)
    recon = astra.data2d.get(rec_id)
    astra.data2d.delete(sino_id)
    astra.data2d.delete(rec_id)
    astra.projector.delete(proj_id)
    return recon


def dim3():
    vectors = vec_geom_init3D(proj_angles, 1.0, 1.0, -0.012)
    proj_geom = astra.create_proj_geom('parallel3d_vec', sinos.shape[0], sinos.shape[2], vectors)
    vol_geom = astra.create_vol_geom(sinos.shape)

    proj_id = astra.create_projector('cuda3d', proj_geom, vol_geom)
    sinos_id = astra.data3d.create('-sino', proj_geom, sinos)
    rec_id = astra.data3d.create('-vol', vol_geom)


class AstraConfig:
    class AstraPostProcessFilters(Enum):
        RAM_LAK = 'ram-lak'
        SHEPP_LOGAN = 'shepp-logan'
        COSINE = 'cosine'
        HAMMING = 'hamming'
        HANN = 'hann'
        NONE = 'none'
        TUKEY = 'tukey'
        LANCZOS = 'lanczos'
        TRIANGULAR = 'triangular'
        GAUSSIAN = 'gaussian'
        BARLETT_HANN = 'barlett-hann'
        BLACKMAN = 'blackman'
        NUTTALL = 'nuttall'
        BLACKMAN_HARRIS = 'blackman-harris'
        BLACKMAN_NUTTALL = 'blackman-nuttall'
        FLAT_TOP = 'flat-top'
        KAISER = 'kaiser'
        PARZEN = 'parzen'
        PROJECTION = 'projection'
        SINOGRAM = 'sinogram'
        RPROJECTION = 'rprojection'
        RSINOGRAM = 'rsinogram'

    projector_id: int
    projection_data_id: int
    reconstruction_data_id: int
    filter_type: AstraPostProcessFilters
