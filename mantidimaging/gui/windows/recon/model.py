from logging import getLogger
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import numpy as np

from mantidimaging.core.operation_history import const
from mantidimaging.core.reconstruct import get_reconstructor_for
from mantidimaging.core.reconstruct.astra_recon import AstraRecon
from mantidimaging.core.reconstruct.astra_recon import allowed_recon_kwargs as astra_allowed_kwargs
from mantidimaging.core.reconstruct.tomopy_recon import allowed_recon_kwargs as tomopy_allowed_kwargs
from mantidimaging.core.rotation.phase_cross_correlation import find_center_pc
from mantidimaging.core.rotation.polyfit_correlation import find_center
from mantidimaging.core.utility.data_containers import (Degrees, ProjectionAngles, ReconstructionParameters, ScalarCoR,
                                                        Slope)
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.projection_angles import generate as generate_projection_angles
from mantidimaging.gui.windows.recon.point_table_model import CorTiltPointQtModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

LOG = getLogger(__name__)


class ReconstructWindowModel(object):
    proj_angles: Optional[ProjectionAngles]

    def __init__(self, data_model: CorTiltPointQtModel):
        self.stack: Optional['StackVisualiserView'] = None
        self.preview_projection_idx = 0
        self.preview_slice_idx = 0
        self.selected_row = 0
        self.projection_indices = None
        self.data_model = data_model
        self.last_result = None
        self._last_cor = ScalarCoR(0.0)

    @property
    def last_cor(self):
        return self._last_cor

    @last_cor.setter
    def last_cor(self, value):
        self._last_cor = value

    @property
    def has_results(self):
        return self.data_model.has_results

    def get_results(self) -> Tuple[ScalarCoR, Degrees, Slope]:
        return self.data_model.cor, self.data_model.angle_in_degrees, self.data_model.gradient

    @property
    def images(self):
        return self.stack.presenter.images if self.stack else None

    @property
    def num_points(self):
        return self.data_model.num_points

    def initial_select_data(self, stack):
        self.data_model.clear_results()

        self.stack = stack
        slice_idx, cor = self.find_initial_cor()
        self.last_cor = cor
        self.preview_projection_idx = 0
        self.preview_slice_idx = slice_idx

        if stack is not None:
            self.proj_angles = generate_projection_angles(360, self.images.num_projections)

    def find_initial_cor(self) -> Tuple[int, ScalarCoR]:
        if self.images is None:
            return 0, ScalarCoR(0)

        first_slice_to_recon = 0
        cor = ScalarCoR(find_center_pc(self.images))
        return first_slice_to_recon, cor

    def do_fit(self):
        # Ensure we have some sample data
        if self.stack is None:
            raise ValueError('No image stack is provided')

        self.data_model.linear_regression()
        self.images.record_operation(const.OPERATION_NAME_COR_TILT_FINDING,
                                     display_name="Calculated COR/Tilt",
                                     **self.data_model.stack_properties)

        # Cache last result
        self.last_result = self.data_model.stack_properties

        # Async task needs a non-None result of some sort
        return True

    def run_preview_recon(self, slice_idx, cor: ScalarCoR, recon_params: ReconstructionParameters):
        # Ensure we have some sample data
        if self.images is None or self.proj_angles is None:
            return None

        # Perform single slice reconstruction
        reconstructor = get_reconstructor_for(recon_params.algorithm)
        return reconstructor.single(self.images.sino(slice_idx), cor, self.proj_angles, recon_params)

    def run_full_recon(self, recon_params: ReconstructionParameters, progress: Progress):
        # Ensure we have some sample data
        if self.images is None or self.proj_angles is None:
            return None
        reconstructor = get_reconstructor_for(recon_params.algorithm)
        # get the image height based on the current ROI
        return reconstructor.full(self.images, self.data_model.get_all_cors_from_regression(self.images.height),
                                  self.proj_angles, recon_params, progress)

    @property
    def tilt_angle(self) -> Optional[Degrees]:
        if self.data_model.has_results:
            return self.data_model.angle_in_degrees
        else:
            return None

    @property
    def cors(self):
        return self.data_model.cors

    @property
    def slices(self):
        return self.data_model.slices

    @staticmethod
    def load_allowed_recon_kwargs():
        d = tomopy_allowed_kwargs()
        d.update(astra_allowed_kwargs())
        return d

    @staticmethod
    def get_allowed_filters(alg_name: str):
        reconstructor = get_reconstructor_for(alg_name)
        return reconstructor.allowed_filters()

    def get_me_a_cor(self, cor=None):
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

    def reset_selected_row(self):
        self.selected_row = 0

    def set_precalculated(self, cor: ScalarCoR, tilt: Degrees):
        self.data_model.set_precalculated(cor, tilt)
        self.last_result = self.data_model.stack_properties

    def is_current_stack(self, stack):
        return self.stack == stack

    def get_slice_indices(self, num_cors: int) -> Tuple[int, List[int]]:
        # used to crop off 20% off the top and bottom, which is usually noise/empty
        remove_a_bit = self.images.height * 0.2
        slices: List[int] = np.linspace(remove_a_bit, self.images.height - remove_a_bit, num=num_cors, dtype=np.int32)
        return self.selected_row, slices

    def auto_find_minimisation_sqsum(self, slices: List[int], recon_params: ReconstructionParameters,
                                     initial_cor: Union[float, List[float]], progress: Progress) -> List[float]:
        """

        :param slices: Slice indices to be reconstructed
        :param recon_params: Reconstruction parameters
        :param initial_cor: Initial COR for the slices. Will be used as the start for the minimisation.
                            If a float is passed it will be used for all slices.
                            If a list is passed, the COR will be retrieved for each slice.
        :param progress: Progress reporter
        """

        # Ensure we have some sample data
        if self.images is None or self.proj_angles is None:
            return [0.0]

        if isinstance(initial_cor, list):
            assert len(slices) == len(initial_cor), "A COR for each slice index being reconstructed must be provided"
        else:
            # why be efficient when you can be lazy?
            initial_cor = [initial_cor] * len(slices)

        progress = Progress.ensure_instance(progress, num_steps=len(slices))
        progress.update(0, msg=f"Calculating COR for slice {slices[0]}")
        cors = []
        for idx, slice in enumerate(slices):
            cor = AstraRecon.find_cor(self.images, slice, initial_cor[idx], self.proj_angles, recon_params)
            cors.append(cor)
            progress.update(msg=f"Calculating COR for slice {slice}")
        return cors

    def auto_find_correlation(self) -> Tuple[ScalarCoR, Degrees]:
        return find_center(self.images)
