from unittest import TestCase

import numpy as np

from mantidimaging.core.reconstruct import tomopy_reconstruct


class TomopyReconstructionTest(TestCase):

    def test_basic(self):
        num_sinograms = 50
        num_projections = 10
        dim_x = 128

        sinograms = np.ones((num_sinograms, num_projections, dim_x))
        cors = np.linspace(50, 52, num_sinograms)
        proj_angles = np.linspace(0, 360, num_projections)

        recon = tomopy_reconstruct(sinograms, cors, proj_angles)

        self.assertEquals(recon.shape, (num_sinograms, dim_x, dim_x))
