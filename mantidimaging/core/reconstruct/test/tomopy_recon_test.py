# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np

from mantidimaging.core.reconstruct.tomopy_recon import TomopyRecon
from mantidimaging.core.utility.data_containers import ReconstructionParameters
from mantidimaging.test_helpers.unit_test_helper import generate_images_with_geometry


def test_single_sino_with_numpy_2():
    images = generate_images_with_geometry(360, seed=10)
    recon_params = ReconstructionParameters("gridrec", "ramlak")

    result = TomopyRecon.single_sino(images, 0, recon_params)

    assert result.shape == (images.width, images.width)
    assert np.isfinite(result).all()


def test_find_cor_with_numpy_2():
    images = generate_images_with_geometry(360, seed=10)
    recon_params = ReconstructionParameters("gridrec", "ramlak")

    result = TomopyRecon.find_cor(images, 0, images.width / 2, recon_params)

    assert np.isfinite(result)
