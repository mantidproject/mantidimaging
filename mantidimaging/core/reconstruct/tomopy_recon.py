from logging import getLogger
from typing import List

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.data_containers import ProjectionAngles, ReconstructionParameters, ScalarCoR
from mantidimaging.core.utility.optional_imports import safe_import
from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)
tomopy = safe_import('tomopy')


class TomopyRecon(BaseRecon):
    @staticmethod
    def find_cor(images: Images, slice_idx: int, start_cor: float, proj_angles: ProjectionAngles,
                 recon_params: ReconstructionParameters) -> float:
        return tomopy.find_center(images.sinograms, None)

    @staticmethod
    def single(sino: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles, recon_params: ReconstructionParameters):
        # make sinogram manually, tomopy likes to copy a lot of data otherwise
        volume = tomopy.recon(tomo=[sino],
                              sinogram_order=True,
                              theta=proj_angles.value,
                              center=cor.value,
                              algorithm=recon_params.algorithm,
                              filter_name=recon_params.filter_name)

        return volume[0]

    @staticmethod
    def single_sino(sample: np.ndarray, cor: ScalarCoR, proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters):
        volume = tomopy.recon(tomo=[sample],
                              sinogram_order=True,
                              theta=proj_angles.value,
                              center=cor.value,
                              algorithm=recon_params.algorithm,
                              filter_name=recon_params.filter_name)

        return volume[0]

    @staticmethod
    def full(images: Images,
             cors: List[ScalarCoR],
             proj_angles: ProjectionAngles,
             recon_params: ReconstructionParameters,
             progress=None):
        """
        Performs a volume reconstruction using sample data provided as sinograms.

        :param images: Array of sinogram images
        :param cors: Array of centre of rotation values
        :param proj_angles: Array of projection angles
        :param recon_params: Reconstruction Parameters
        :param progress: Optional progress reporter
        :return: 3D image data for reconstructed volume
        """
        progress = Progress.ensure_instance(progress, task_name='TomoPy reconstruction')

        import multiprocessing
        ncores = multiprocessing.cpu_count()

        kwargs = {
            'ncore': ncores,
            'tomo': images.data,
            'sinogram_order': images._is_sinograms,
            'theta': proj_angles.value,
            'center': [cor.value for cor in cors],
            'algorithm': recon_params.algorithm,
            'filter_name': recon_params.filter_name
        }

        with progress:
            volume = tomopy.recon(**kwargs)
            LOG.info('Reconstructed 3D volume with shape: {0}'.format(volume.shape))

        return Images(volume)

    @staticmethod
    def allowed_filters() -> List[str]:
        return ["ramlak", 'shepp', 'cosine', 'hann', 'hamming', 'parzen', 'butterworth']


def allowed_recon_kwargs() -> dict:
    # only gridrec is used from tomopy
    return {'gridrec': ['num_gridx', 'num_gridy', 'filter_name', 'filter_par']}
