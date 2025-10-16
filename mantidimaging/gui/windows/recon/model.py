# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
from typing import TYPE_CHECKING, Any

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.operation_history import const
from mantidimaging.core.operations.divide import DivideFilter
from mantidimaging.core.reconstruct import get_reconstructor_for
from mantidimaging.core.reconstruct.astra_recon import allowed_recon_kwargs as astra_allowed_kwargs
from mantidimaging.core.reconstruct.tomopy_recon import allowed_recon_kwargs as tomopy_allowed_kwargs
from mantidimaging.core.reconstruct.cil_recon import allowed_recon_kwargs as cil_allowed_kwargs
from mantidimaging.core.rotation.polyfit_correlation import find_center
from mantidimaging.core.utility.cuda_check import CudaChecker
from mantidimaging.core.utility.data_containers import (Degrees, ReconstructionParameters, ScalarCoR, Slope)
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.windows.recon.point_table_model import CorTiltPointQtModel

if TYPE_CHECKING:
    import uuid

LOG = getLogger(__name__)


class ReconstructWindowModel:

    def __init__(self, data_model: CorTiltPointQtModel):
        self._images: ImageStack | None = None
        self._preview_projection_idx = 0
        self._preview_slice_idx = 0
        self._selected_row = 0
        self.data_model = data_model
        self._last_cor = ScalarCoR(0.0)

    @property
    def selected_row(self) -> int:
        return self._selected_row

    @selected_row.setter
    def selected_row(self, value: int) -> None:
        self._selected_row = value

    @property
    def preview_projection_idx(self) -> int:
        return self._preview_projection_idx

    @preview_projection_idx.setter
    def preview_projection_idx(self, value: int) -> None:
        self._preview_projection_idx = value

    @property
    def preview_slice_idx(self) -> int:
        return self._preview_slice_idx

    @preview_slice_idx.setter
    def preview_slice_idx(self, value: int) -> None:
        self._preview_slice_idx = value

    @property
    def last_cor(self) -> ScalarCoR:
        return self._last_cor

    @last_cor.setter
    def last_cor(self, value: ScalarCoR) -> None:
        self._last_cor = value

    @property
    def has_results(self) -> bool:
        return self.data_model.has_results

    def get_results(self) -> tuple[ScalarCoR, Degrees, Slope]:
        return self.data_model.cor, self.data_model.angle_in_degrees, self.data_model.gradient

    @property
    def images(self):
        return self._images

    @property
    def num_points(self) -> int:
        return self.data_model.num_points

    def initial_select_data(self, images: ImageStack | None) -> None:
        self._images = images
        self.reset_cor_model()

    def reset_cor_model(self) -> None:
        self.data_model.clear_results()

        slice_idx, cor = self.find_initial_cor()
        self.last_cor = cor
        self.preview_projection_idx = 0
        self.preview_slice_idx = slice_idx

    def find_initial_cor(self) -> tuple[int, ScalarCoR]:
        if self.images is None:
            return 0, ScalarCoR(0)

        first_slice_to_recon = self.images.height // 2
        cor = ScalarCoR(self.images.h_middle)
        return first_slice_to_recon, cor

    def do_fit(self) -> bool:
        # Ensure we have some sample data
        if self.images is None:
            raise ValueError('No image stack is provided')
        self.data_model.linear_regression()
        self.images.record_operation(const.OPERATION_NAME_COR_TILT_FINDING,
                                     display_name="Calculated COR/Tilt",
                                     **self.data_model.stack_properties)

        LOG.info("COR/Tilt fitting completed: COR=%.3f, Tilt=%.3f°, Slope=%.3f", self.data_model.cor.value,
                 self.data_model.angle_in_degrees.value, self.data_model.gradient.value)
        # Async task needs a non-None result of some sort
        return True

    @staticmethod
    def _image_stack_is_recon_ready(images: ImageStack) -> bool:
        return images is not None and images.projection_angles() is not None

    def run_preview_recon(self,
                          slice_idx: int,
                          recon_params: ReconstructionParameters,
                          progress: Progress | None = None) -> ImageStack | None:
        # Ensure we have some sample data
        images = self.images
        if not self._image_stack_is_recon_ready(images):
            return None

        # Perform single slice reconstruction
        reconstructor = get_reconstructor_for(recon_params.algorithm)
        output_shape = (1, images.width, images.width)

        recon: ImageStack = ImageStack.create_empty_image_stack(output_shape, images.dtype, images.metadata)

        # Log only if the slice index is different from the previous one
        if getattr(self, "_last_preview_slice_idx", None) != slice_idx:
            LOG.info("Running preview reconstruction: slice_idx=%d, COR=%.3f, algorithm=%s", slice_idx,
                     images.geometry.cor.value, recon_params.algorithm)
            self._last_preview_slice_idx = slice_idx

        recon.data[0] = reconstructor.single_sino(images, slice_idx, recon_params, progress=progress)

        recon = self._apply_pixel_size(recon, recon_params)
        return recon

    def run_full_recon(self, recon_params: ReconstructionParameters, progress: Progress) -> ImageStack | None:
        # Ensure we have some sample data
        images = self.images
        if not self._image_stack_is_recon_ready(images):
            return None

        LOG.info("Starting full reconstruction: algorithm=%s, slices=%d", recon_params.algorithm, self.images.height)

        reconstructor = get_reconstructor_for(recon_params.algorithm)

        recon = reconstructor.full(images, recon_params, progress)
        recon = self._apply_pixel_size(recon, recon_params, progress)
        return recon

    @staticmethod
    def _apply_pixel_size(recon: ImageStack, recon_params: ReconstructionParameters, progress=None) -> ImageStack:
        if recon_params.pixel_size > 0.:
            recon = DivideFilter.filter_func(recon, value=recon_params.pixel_size, unit="micron", progress=progress)
            # update the reconstructed stack pixel size with the value actually used for division
            recon.pixel_size = recon_params.pixel_size
            recon.record_operation(DivideFilter.__name__,
                                   DivideFilter.filter_name,
                                   value=recon_params.pixel_size,
                                   unit="micron")
        return recon

    @property
    def tilt_angle(self) -> Degrees | None:
        if self.data_model.has_results:
            return self.data_model.angle_in_degrees
        else:
            return None

    @property
    def cors(self) -> np.ndarray:
        return self.data_model.cors  # type: ignore

    @property
    def slices(self) -> np.ndarray:
        return self.data_model.slices  # type: ignore

    @staticmethod
    def load_allowed_recon_kwargs() -> dict[str, Any]:
        d = tomopy_allowed_kwargs()
        if CudaChecker().cuda_is_present():
            d.update(astra_allowed_kwargs())
            d.update(cil_allowed_kwargs())
        return d

    @staticmethod
    def get_allowed_filters(alg_name: str) -> list:
        reconstructor = get_reconstructor_for(alg_name)
        return reconstructor.allowed_filters()

    def get_me_a_cor(self, cor: ScalarCoR | None = None) -> ScalarCoR:
        if cor is not None:
            # a rotation has been passed in!
            return cor

        if self.has_results:
            cor = self.get_cor_for_slice_from_regression()
        else:
            # otherwise just use the last cached CoR
            cor = self.last_cor
        return cor

    def get_cor_for_slice_from_regression(self) -> ScalarCoR:
        return ScalarCoR(self.data_model.get_cor_from_regression(self.preview_slice_idx))

    def reset_selected_row(self) -> None:
        self.selected_row = 0

    def set_precalculated(self, cor: ScalarCoR, tilt: Degrees) -> None:
        self.data_model.set_precalculated(cor, tilt)

    def is_current_stack(self, uuid: uuid.UUID | None) -> bool:
        return self.stack_id == uuid

    def get_slice_indices(self, num_cors: int) -> tuple[int, np.ndarray]:
        # used to crop off 20% off the top and bottom, which is usually noise/empty
        remove_a_bit = self.images.height * 0.2
        slices = np.linspace(remove_a_bit, self.images.height - remove_a_bit, num=num_cors, dtype=np.int32)
        return self.selected_row, slices

    def auto_find_minimisation_sqsum(self, slices: list[int], recon_params: ReconstructionParameters,
                                     progress: Progress) -> list[float]:
        """
        Automatically find the COR (Center of Rotation) by minimising the sum of squared differences.

        :param slices: Slice indices to be reconstructed
        :param recon_params: Reconstruction parameters
        :param progress: Progress reporter
        """
        if self.images is None:
            LOG.warning("No image stack loaded; returning default COR=0.0")
            return [0.0]

        initial_cor = []
        for slc in slices:
            initial_cor.append(self.images.geometry.get_cor_at_slice_index(slc).value)

        if len(initial_cor) == 1:
            initial_cor = initial_cor * len(slices)
        if len(initial_cor) != len(slices):
            raise ValueError("The number of initial COR values must match the number of slices")

        reconstructor = get_reconstructor_for(recon_params.algorithm)
        progress = Progress.ensure_instance(progress, num_steps=len(slices))
        cors = []
        for idx, slice in enumerate(slices):
            cor = reconstructor.find_cor(self.images, slice, initial_cor[idx], recon_params)
            cors.append(cor)
            progress.update(msg=f"Calculating COR for slice {slice}")
        LOG.info("COR minimisation completed: CORs=%s", cors)
        return cors

    def auto_find_correlation(
        self,
        progress: Progress,
        use_projections: tuple[int, int] | None = None,
    ) -> tuple[ScalarCoR, Degrees]:
        return find_center(self.images, progress, use_projections)

    def stack_contains_nans(self) -> bool:
        return bool(np.any(np.isnan(self.images.data)))

    def stack_contains_zeroes(self) -> bool:
        return not np.all(self.images.data)

    def stack_contains_negative_values(self) -> bool:
        return bool(np.any(self.images.data < 0))

    @property
    def stack_id(self) -> uuid.UUID | None:
        if self.images is not None:
            return self.images.id
        return None
