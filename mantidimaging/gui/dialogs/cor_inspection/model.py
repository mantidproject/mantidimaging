# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from dataclasses import replace
from logging import getLogger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.reconstruct import get_reconstructor_for
from mantidimaging.core.utility.data_containers import ScalarCoR, ReconstructionParameters
from .types import ImageType

LOG = getLogger(__name__)

INIT_ITERS_CENTRE_VALUE = 100
INIT_ITERS_STEP = 50


class CORInspectionDialogModel:

    def __init__(self, images: ImageStack, slice_idx: int, initial_cor: ScalarCoR,
                 recon_params: ReconstructionParameters, iters_mode: bool):
        self.images = images
        self.slice_idx = slice_idx

        # Initial parameters
        if iters_mode:
            self.centre_value: int | float = INIT_ITERS_CENTRE_VALUE
            self.step: float = INIT_ITERS_STEP
            self.initial_cor = initial_cor
            self._recon_preview = self._recon_iters_preview
            self._divide_step = self._divide_iters_step
        else:
            self.centre_value = initial_cor.value
            self.step = self.images.width * 0.05
            self._recon_preview = self._recon_cor_preview
            self._divide_step = self._divide_cor_step

        # Cache projection angles
        self.proj_angles = images.projection_angles(recon_params.max_projection_angle)
        self.recon_params = recon_params
        self.reconstructor = get_reconstructor_for(recon_params.algorithm)

    def _divide_iters_step(self) -> None:
        self.step = self.step // 2

    def _divide_cor_step(self) -> None:
        self.step /= 2

    def adjust(self, image: ImageType) -> None:
        """
        Adjusts the rotation centre/number of iterations and step after an image is selected as the
        optimal of an iteration.
        """
        if image == ImageType.LESS:
            self.centre_value -= self.step
        elif image == ImageType.MORE:
            self.centre_value += self.step
        elif image == ImageType.CURRENT:
            self._divide_step()

    def cor(self, image: ImageType) -> float:
        """
        Gets the rotation centre for a given image in the current iteration.
        """
        if image == ImageType.LESS:
            return max(self.cor_extents[0], self.centre_value - self.step)
        elif image == ImageType.CURRENT:
            return self.centre_value
        elif image == ImageType.MORE:
            return min(self.cor_extents[1], self.centre_value + self.step)

    def iterations(self, image: ImageType) -> float:
        if image == ImageType.LESS:
            return max(1, self.centre_value - self.step)
        elif image == ImageType.CURRENT:
            return self.centre_value
        elif image == ImageType.MORE:
            return self.centre_value + self.step

    def _recon_cor_preview(self, image: ImageType) -> np.ndarray:
        assert (self.images.geometry is not None)
        assert self.proj_angles is not None
        self.images.geometry.cor = ScalarCoR(self.cor(image))
        return self.reconstructor.single_sino(self.images, self.slice_idx, self.recon_params)

    def _recon_iters_preview(self, image: ImageType) -> np.ndarray:
        assert self.proj_angles is not None
        iters = self.iterations(image)
        new_params = replace(self.recon_params, num_iter=int(iters))
        return self.reconstructor.single_sino(self.images, self.slice_idx, new_params)

    def recon_preview(self, image: ImageType) -> np.ndarray:
        return self._recon_preview(image)

    @property
    def cor_extents(self) -> tuple[int, int]:
        sino = self.images.sino(self.slice_idx)
        return 0, sino.shape[1] - 1
