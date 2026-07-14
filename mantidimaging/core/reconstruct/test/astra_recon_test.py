# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from contextlib import contextmanager
from unittest import mock

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.reconstruct.astra_recon import AstraRecon, allowed_recon_kwargs
from mantidimaging.core.utility.data_containers import ProjectionAngles, ReconstructionParameters, ScalarCoR


def test_allowed_recon_kwargs_include_non_negative_for_sirt():
    assert "non_negative" in allowed_recon_kwargs()["SIRT_CUDA"]
    assert "non_negative" in allowed_recon_kwargs()["SIRT3D_CUDA"]


@mock.patch("mantidimaging.core.reconstruct.astra_recon.CudaChecker.cuda_is_present", return_value=False)
@mock.patch("mantidimaging.core.reconstruct.astra_recon.astra.data2d.get", return_value=np.ones((2, 2)))
@mock.patch("mantidimaging.core.reconstruct.astra_recon.astra.algorithm.run")
@mock.patch("mantidimaging.core.reconstruct.astra_recon.astra.astra_dict",
            side_effect=lambda algorithm: {"algorithm": algorithm})
@mock.patch("mantidimaging.core.reconstruct.astra_recon.astra.create_proj_geom")
@mock.patch("mantidimaging.core.reconstruct.astra_recon.astra.create_vol_geom")
def test_single_sino_sets_min_constraint_for_non_negative_sirt(
    create_vol_geom_mock,
    create_proj_geom_mock,
    astra_dict_mock,
    algorithm_run_mock,
    _astra_get_mock,
    _cuda_mock,
):
    image_stack = ImageStack(data=np.ones((1, 2, 2), dtype=np.float32))
    image_stack.set_projection_angles(ProjectionAngles(np.array([0.0])))
    assert image_stack.geometry is not None
    image_stack.geometry.cor = ScalarCoR(1.0)

    recon_params = ReconstructionParameters("SIRT_CUDA", "none", num_iter=3, non_negative=True)

    captured_cfg = {}

    @contextmanager
    def fake_managed_recon(_sino, cfg, _proj_geom, _vol_geom):
        captured_cfg.update(cfg)
        yield 1, 2

    with mock.patch("mantidimaging.core.reconstruct.astra_recon._managed_recon", side_effect=fake_managed_recon):
        AstraRecon.single_sino(image_stack, 0, recon_params)

    assert captured_cfg["option"] == {"MinConstraint": 0.0}
    astra_dict_mock.assert_called_once_with("SIRT_CUDA")
    algorithm_run_mock.assert_called_once_with(1, iterations=3)
    create_vol_geom_mock.assert_called_once_with((2, 2))
    create_proj_geom_mock.assert_called_once()
