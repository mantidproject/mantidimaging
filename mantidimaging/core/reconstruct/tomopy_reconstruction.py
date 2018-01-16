from __future__ import absolute_import, division, print_function

from logging import getLogger
import concurrent.futures as cf

import numpy as np

from mantidimaging.core.utility.progress_reporting import Progress

# This import is used to provide the available() function which is used to
# check if the functionality of a module is available based on the presence of
# optional libraries
from mantidimaging.core.utility.optional_imports import (  # noqa: F401
    safe_import,
    tomopy_available as available)

LOG = getLogger(__name__)
tomopy = safe_import('tomopy')


def reconstruct_single_preview(sample,
                               slice_idx,
                               cor,
                               proj_angles,
                               progress=None):
    """
    Performs a preview of a single slice/sinogram from a 3D volume provided as
    a stack of projections.

    :param sample: 3D projection data
    :param slice_idx: Index of slice/sinogram to reconstruct
    :param cor: Centre of rotation value
    :param proj_angles: Array of projection angles
    :param progress: Optional progress reporter
    :return: 2D image data for reconstructed slice
    """
    progress = Progress.ensure_instance(progress,
                                        task_name='Tomopy reconstruction')

    volume = [None]
    with progress:
        s = np.swapaxes(sample[:, [slice_idx], :], 0, 1)

        volume = tomopy.recon(
                tomo=s,
                sinogram_order=True,
                theta=proj_angles,
                center=cor,
                algorithm='gridrec')

    return volume[0]


def reconstruct(sample,
                cor=None,
                proj_angles=None,
                ncores=None,
                progress=None):
    """
    Performs a volume reconstruction using sample data provided as sinograms.

    :param sample: Array of sinogram images
    :param cor: Array of centre of rotation values
    :param proj_angles: Array of projection angles
    :param ncores: Number of CPU cores to execute on, defaults to all
    :param progress: Optional progress reporter
    :return: 3D image data for reconstructed volume
    """
    progress = Progress.ensure_instance(progress,
                                        task_name='Tomopy reconstruction')

    if ncores is None:
        import multiprocessing
        ncores = multiprocessing.cpu_count()

    # Use a custom version of this function and monkey patch it to Tomopy to
    # facilitate fine grained progress reporting
    def monkey_patched_dist_recon(tomo, center, recon, algorithm, args, kwargs,
                                  ncore, nchunk):
        axis_size = recon.shape[0]

        # Use a chunk size of 1 to process one sinogram per thread execution
        ncore, slcs = tomopy.util.mproc.get_ncore_slices(
                axis_size, ncore, 1)

        progress.add_estimated_steps(len(slcs))

        if ncore == 1:
            for slc in slcs:
                algorithm(tomo[slc], center[slc], recon[slc], *args, **kwargs)
                progress.update()
        else:
            with cf.ThreadPoolExecutor(ncore) as e:
                for slc in slcs:
                    f = e.submit(algorithm, tomo[slc], center[slc], recon[slc],
                                 *args, **kwargs)
                    f.add_done_callback(lambda _: progress.update())

        return recon

    from tomopy.recon import algorithm
    algorithm._dist_recon = monkey_patched_dist_recon

    volume = None
    with progress:
        volume = tomopy.recon(
                ncore=ncores,
                tomo=sample,
                sinogram_order=True,
                theta=proj_angles,
                center=cor,
                algorithm='gridrec')

        LOG.info('Reconstructed 3D volume with shape: {0}'.format(
            volume.shape))

    return volume
