from logging import getLogger
from typing import Optional, Tuple
from typing import TYPE_CHECKING

import numpy as np

from mantidimaging.core.cor_tilt import (update_image_operations)
from mantidimaging.core.reconstruct import get_reconstructor_for
from mantidimaging.core.reconstruct.astra_recon import allowed_recon_kwargs as astra_allowed_kwargs
from mantidimaging.core.reconstruct.tomopy_recon import allowed_recon_kwargs as tomopy_allowed_kwargs
from mantidimaging.core.utility.data_containers import ScalarCoR, Degrees, Slope
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.projection_angles import (generate as generate_projection_angles)
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.recon.point_table_model import CorTiltPointQtModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

LOG = getLogger(__name__)


class ReconstructWindowModel(object):
    proj_angles: Optional[np.ndarray]

    def __init__(self, data_model: CorTiltPointQtModel):
        self.stack: Optional['StackVisualiserView'] = None
        self.preview_projection_idx = 0
        self.preview_slice_idx = 0
        self.selected_row = 0
        self._roi = None
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
    def sample(self):
        return self.stack.presenter.images.sample if self.stack else None

    @property
    def images(self):
        return self.stack.presenter.images if self.stack else None

    @property
    def num_projections(self):
        return self.sample.shape[0] if self.sample is not None else 0

    @property
    def num_slices(self):
        return self.sample.shape[1] if self.sample is not None else 0

    @property
    def num_points(self):
        return self.data_model.num_points

    @property
    def cor_for_current_preview_slice(self):
        return ScalarCoR(self.data_model.get_cor_for_slice(self.preview_slice_idx))

    def set_all_cors(self, cor: ScalarCoR):
        for slice_idx in self.data_model.slices:
            self.data_model.set_cor_at_slice(slice_idx, cor.value)

    def initial_select_data(self, stack):
        self.data_model.clear_results()

        self.stack = stack
        slice_idx, _ = self.find_initial_cor()

        self.preview_projection_idx = 0
        self.preview_slice_idx = slice_idx

        if stack is not None:
            image_shape = self.sample.shape
            self.roi = SensibleROI(0, 0, image_shape[1], image_shape[2])
            self.proj_angles = generate_projection_angles(360, image_shape[0])

    def update_roi_from_stack(self):
        self.data_model.clear_results()
        self.roi = self.stack.current_roi if self.stack else None

    def calculate_slices(self, count):
        self.data_model.clear_results()
        if self.roi is not None:
            lower = self.roi.top
            upper = self.roi.bottom
            # move the bounds by 20% as the ends of the image are usually empty
            # or contain unimportant information
            lower = lower * 1.2 if lower != 0 else 0.2 * self.sample.shape[1]
            upper = upper - upper * 0.2
            self.data_model.populate_slice_indices(lower, upper, count)

    def calculate_projections(self, count):
        self.data_model.clear_results()
        if self.sample is not None:
            sample_proj_count = self.sample.shape[0]
            downsample_proj_count = min(sample_proj_count, count)
            self.projection_indices = \
                np.linspace(int(sample_proj_count * 0.1), sample_proj_count - 1, downsample_proj_count,
                            dtype=int)

    def find_initial_cor(self) -> [int, ScalarCoR]:
        if self.sample is not None:
            first_slice_to_recon = self.get_initial_slice_index()
            # Getting the middle of the image is probably closer than Tomopy's CoR from what I've seen
            # and certainly much faster. IF a better method is found it might be worth going to it instead
            cor = ScalarCoR(self.images.height // 2)
            # cor = ScalarCoR(find_cor_at_slice(self.sample, first_slice_to_recon)[0])
            self.last_cor = cor

            return first_slice_to_recon, cor
        return 0, ScalarCoR(0)

    def get_initial_slice_index(self):
        first_slice_to_recon = self.sample.shape[1] // 2
        return first_slice_to_recon

    def do_fit(self, progress):
        # Ensure we have some sample data
        if self.stack is None:
            raise ValueError('No image stack is provided')

        if self.roi is None:
            raise ValueError('No region of interest is defined')

        self.data_model.linear_regression()
        update_image_operations(self.images, self.data_model)

        # Cache last result
        self.last_result = self.data_model.stack_properties

        # Async task needs a non-None result of some sort
        return True

    def run_preview_recon(self, slice_idx, cor: ScalarCoR, algorithm: str, recon_filter: str):
        # Ensure we have some sample data
        if self.sample is None:
            return None

        # Perform single slice reconstruction
        reconstructor = get_reconstructor_for(algorithm)
        return reconstructor.single(self.images, slice_idx, cor, self.proj_angles, algorithm, recon_filter)

    def run_full_recon(self, algorithm: str, recon_filter: str, num_iter: int, progress: Progress):
        reconstructor = get_reconstructor_for(algorithm)
        # get the image height based on the current ROI
        self.images.set_roi(self.roi)
        return reconstructor.full(self.images, self.data_model.get_all_cors_from_regression(self.images.height),
                                  self.proj_angles, algorithm, recon_filter, num_iter, progress)

    @property
    def tilt_angle(self) -> Optional[Degrees]:
        if self.data_model.has_results:
            return self.data_model.angle_in_degrees

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

    def get_me_a_cor(self, cor=None):
        if cor is not None:
            # a cor has been passed in!
            return cor

        if self.has_results:
            cor = self.get_cor_for_slice_from_regression()
        elif self.last_cor is not None:
            # otherwise just use the last cached CoR
            cor = self.last_cor
        return cor

    def get_cor_for_slice_from_regression(self) -> ScalarCoR:
        return ScalarCoR(self.data_model.get_cor_from_regression(self.preview_slice_idx))

    def reset_selected_row(self):
        self.selected_row = 0

    def set_precalculated(self, cor: ScalarCoR, tilt: Degrees):
        self.data_model.set_precalculated(cor, tilt)

    @property
    def roi(self) -> SensibleROI:
        return self._roi

    @roi.setter
    def roi(self, value: SensibleROI):
        self._roi = value

    def is_current_stack(self, stack):
        return self.stack == stack
