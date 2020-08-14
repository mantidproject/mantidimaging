from logging import getLogger
from typing import Optional

import numpy as np
from scipy import ndimage

from ..data.images import Images

try:
    from skimage.registration import phase_cross_correlation

    def find_center_pc(images: Images, initial_guess: Optional[float] = None, tol: float = 0.5) -> float:
        """
        Find rotation axis location by finding the offset between the first
        projection and a mirrored projection 180 degrees apart using
        phase correlation in Fourier space.

        Implements an updated version of Tomopy's `find_center_pc`, source:
        https://github.com/tomopy/tomopy/blob/1ae454caf4da496499be6e6c6d6299e74550cf50/source/tomopy/recon/rotation.py#L374-L418
        The changes make use of the newer scikit-image version and it's registration module, for a faster
        registration by using the `phase_cross_correlation` function. The rest of the changes are to be compatible
        with the data structure used within this package (Images class)
        """
        # if the user provides an initial guess of the COR, take that into account to move the image to it
        initial_guess = 0 if initial_guess is None else initial_guess - images.h_middle
        p1 = ndimage.shift(images.projection(0), [0, -initial_guess], mode='constant', cval=0)
        p2 = np.fliplr(ndimage.shift(images.proj180deg.data, [0, -initial_guess], mode='constant', cval=0))
        shift = phase_cross_correlation(p1, p2, upsample_factor=1.0 / tol)
        getLogger(__name__).info(f"Found COR shift {shift}")
        # Compute center of rotation as the center of first image and the
        # registered translation with the second image
        center = (p1.shape[1] + shift[0][1]) / 2
        return center + initial_guess
except ImportError:

    def find_center_pc(images: Images, initial_guess: Optional[float] = None, tol: float = 0.5) -> float:
        return images.width / 2
