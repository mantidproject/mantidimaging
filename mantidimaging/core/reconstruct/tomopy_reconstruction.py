from __future__ import absolute_import, division, print_function

from logging import getLogger

from mantidimaging.core.utility.progress_reporting import Progress

# This import is used to provide the available() function which is used to
# check if the functionality of a module is available based on the presence of
# optional libraries
from mantidimaging.core.utility.optional_imports import (  # noqa: F401
        safe_import,
        tomopy_available as available)

LOG = getLogger(__name__)
tomopy = safe_import('tomopy')


def reconstruct(sample,
                cor=None,
                proj_angles=None,
                ncores=None,
                progress=None):

    progress = Progress.ensure_instance(progress)

    if ncores is None:
        import multiprocessing
        ncores = multiprocessing.cpu_count()

    volume = None
    with progress:
        # TODO
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
