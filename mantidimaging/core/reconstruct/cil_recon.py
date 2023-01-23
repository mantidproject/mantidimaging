# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
from logging import getLogger, DEBUG
from math import sqrt
from threading import Lock
from typing import List, Optional, TYPE_CHECKING

import numpy as np

from cil.framework import AcquisitionData, AcquisitionGeometry, DataOrder, ImageGeometry
from cil.optimisation.algorithms import PDHG
from cil.optimisation.operators import GradientOperator, BlockOperator
from cil.optimisation.functions import MixedL21Norm, L2NormSquared, BlockFunction, ZeroFunction, IndicatorBox
from cil.plugins.astra.operators import ProjectionOperator

from mantidimaging.core.data import ImageStack
from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.optional_imports import safe_import
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.size_calculator import full_size_KB
from mantidimaging.core.utility.memory_usage import system_free_memory

if TYPE_CHECKING:
    from mantidimaging.core.utility.data_containers import ProjectionAngles, ReconstructionParameters, ScalarCoR

LOG = getLogger(__name__)
tomopy = safe_import('tomopy')
cil_mutex = Lock()


class CILRecon(BaseRecon):
    @staticmethod
    def set_up_TV_regularisation(image_geometry: ImageGeometry, acquisition_data: AcquisitionData,
                                 recon_params: ReconstructionParameters):
        # Forward operator
        A2d = ProjectionOperator(image_geometry, acquisition_data.geometry, 'gpu')

        assert all(s == 1.0 for s in image_geometry.spacing), "Norm approximations assume voxel size == 1"

        # This is slow to calculate, this approximation is good to with in 5%
        # When running in debug mode, check the approximation and raise an error if it is bad
        approx_a2d_norm = sqrt(image_geometry.voxel_num_x * acquisition_data.geometry.num_projections)
        if LOG.isEnabledFor(DEBUG):
            num_a2d_norm = A2d.PowerMethod(A2d, max_iteration=100)
            diff = abs(approx_a2d_norm - num_a2d_norm) / max(approx_a2d_norm, num_a2d_norm)
            LOG.debug(f"ProjectionOperator approx norm: {diff=} {approx_a2d_norm=} {num_a2d_norm=}")
            if diff > 0.05:
                raise RuntimeError(f"Bad ProjectionOperator norm: {diff=} {approx_a2d_norm=} {num_a2d_norm=}\n")
        A2d.set_norm(approx_a2d_norm)

        # Define Gradient Operator and BlockOperator
        alpha = recon_params.alpha
        Grad = GradientOperator(image_geometry)

        if image_geometry.voxel_num_z == 0:
            Grad.set_norm(sqrt(8))
        else:
            Grad.set_norm(sqrt(12))

        K = BlockOperator(alpha * Grad, A2d)

        # Define BlockFunction F using the MixedL21Norm() and the L2NormSquared()
        f1 = MixedL21Norm()
        f2 = L2NormSquared(b=acquisition_data)

        if recon_params.non_negative:
            G = IndicatorBox(lower=0)
        else:
            # Define Function G simply as zero
            G = ZeroFunction()

        return (K, f1, f2, G)

    @staticmethod
    def find_cor(images: ImageStack, slice_idx: int, start_cor: float, recon_params: ReconstructionParameters) -> float:
        return tomopy.find_center(images.sinograms,
                                  images.projection_angles(recon_params.max_projection_angle).value,
                                  ind=slice_idx,
                                  init=start_cor,
                                  sinogram_order=True)

    @staticmethod
    def single_sino(sino: np.ndarray,
                    cor: ScalarCoR,
                    proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters,
                    progress: Optional[Progress] = None):
        """
        Reconstruct a single slice from a single sinogram. Used for the preview and the single slice button.
        Should return a numpy array,
        """

        print(f"SPDHG params: {recon_params.stochastic=} {recon_params.subsets=}")

        if progress:
            progress.add_estimated_steps(recon_params.num_iter + 1)
            progress.update(steps=1, msg='CIL: Setting up reconstruction', force_continue=False)

        if cil_mutex.locked():
            LOG.warning("CIL recon already in progress")

        with cil_mutex:
            t0 = time.perf_counter()
            sino = BaseRecon.prepare_sinogram(sino, recon_params)
            pixel_num_h = sino.shape[1]
            pixel_size = 1.
            rot_pos_x = (cor.value - pixel_num_h / 2) * pixel_size
            ag = AcquisitionGeometry.create_Parallel2D(rotation_axis_position=[rot_pos_x, 0])

            ag.set_panel(pixel_num_h, pixel_size=pixel_size)
            ag.set_labels(DataOrder.ASTRA_AG_LABELS)
            ag.set_angles(angles=proj_angles.value, angle_unit='radian')

            data = ag.allocate(None)
            data.fill(sino)

            ig = ag.get_ImageGeometry()
            K, f1, f2, G = CILRecon.set_up_TV_regularisation(ig, data, recon_params)

            F = BlockFunction(f1, f2)
            normK = K.norm()
            sigma = 1
            tau = 1 / (sigma * normK**2)

            pdhg = PDHG(f=F, g=G, operator=K, tau=tau, sigma=sigma, max_iteration=100000, update_objective_interval=10)

            try:
                for iter in range(recon_params.num_iter):
                    if progress:
                        progress.update(steps=1,
                                        msg=f'CIL: Iteration {iter + 1} of {recon_params.num_iter}'
                                        f': Objective {pdhg.get_last_objective():.2f}',
                                        force_continue=False)
                    pdhg.next()
            finally:
                if progress:
                    progress.mark_complete()
            t1 = time.perf_counter()
            LOG.info(f"single_sino time: {t1-t0}s for shape {sino.shape}")
            return pdhg.solution.as_array()

    @staticmethod
    def full(images: ImageStack,
             cors: List[ScalarCoR],
             recon_params: ReconstructionParameters,
             progress: Optional[Progress] = None):
        """
        Performs a volume reconstruction using sample data provided as sinograms.

        :param images: Array of sinogram images
        :param cors: Array of centre of rotation values
        :param proj_angles: Array of projection angles in radians
        :param recon_params: Reconstruction Parameters
        :param progress: Optional progress reporter
        :return: 3D image data for reconstructed volume
        """

        progress = Progress.ensure_instance(progress,
                                            task_name='CIL reconstruction',
                                            num_steps=recon_params.num_iter + 1)
        shape = images.data.shape
        if images.is_sinograms:
            data_order = DataOrder.ASTRA_AG_LABELS
            pixel_num_h, pixel_num_v = shape[2], shape[0]
        else:
            data_order = DataOrder.TIGRE_AG_LABELS
            pixel_num_h, pixel_num_v = shape[2], shape[1]

        projection_size = full_size_KB(images.data.shape, images.dtype)
        recon_volume_shape = pixel_num_h, pixel_num_h, pixel_num_v
        recon_volume_size = full_size_KB(recon_volume_shape, images.dtype)
        estimated_mem_required = 5 * projection_size + 13 * recon_volume_size
        free_mem = system_free_memory().kb()

        if (estimated_mem_required > free_mem):
            estimate_gb = estimated_mem_required / 1024 / 1024
            raise RuntimeError(
                "The machine does not have enough physical memory available to allocate space for this data."
                f" Estimated RAM needed is {estimate_gb:.2f} GB")

        if cil_mutex.locked():
            LOG.warning("CIL recon already in progress")

        with cil_mutex:
            t0 = time.perf_counter()
            LOG.info(f"Starting 3D PDHG-TV reconstruction: input shape {images.data.shape}"
                     f"output shape {recon_volume_shape}\n"
                     f"Num iter {recon_params.num_iter}, alpha {recon_params.alpha}, "
                     f"Non-negative {recon_params.non_negative}")
            progress.update(steps=1, msg='CIL: Setting up reconstruction', force_continue=False)
            angles = images.projection_angles(recon_params.max_projection_angle).value

            pixel_size = 1.
            if recon_params.tilt is None:
                raise ValueError("recon_params.tilt is not set")
            rot_pos = [(cors[pixel_num_v // 2].value - pixel_num_h / 2) * pixel_size, 0, 0]
            slope = -np.tan(np.deg2rad(recon_params.tilt.value))
            rot_angle = [slope, 0, 1]

            ag = AcquisitionGeometry.create_Parallel3D(rotation_axis_position=rot_pos,
                                                       rotation_axis_direction=rot_angle)
            ag.set_panel([pixel_num_h, pixel_num_v], pixel_size=(pixel_size, pixel_size))
            ag.set_angles(angles=angles, angle_unit='radian')
            ag.set_labels(data_order)

            data = ag.allocate(None)
            data.fill(BaseRecon.prepare_sinogram(images.data, recon_params))
            data.reorder('astra')

            ig = ag.get_ImageGeometry()
            K, f1, f2, G = CILRecon.set_up_TV_regularisation(ig, data, recon_params)

            F = BlockFunction(f1, f2)
            normK = K.norm()
            sigma = 1
            tau = 1 / (sigma * normK**2)

            pdhg = PDHG(f=F, g=G, operator=K, tau=tau, sigma=sigma, max_iteration=100000, update_objective_interval=10)

            with progress:
                for iter in range(recon_params.num_iter):
                    progress.update(steps=1,
                                    msg=f'CIL: Iteration {iter+1} of {recon_params.num_iter}:'
                                    f'Objective {pdhg.get_last_objective():.2f}',
                                    force_continue=False)
                    pdhg.next()
                volume = pdhg.solution.as_array()
                LOG.info('Reconstructed 3D volume with shape: {0}'.format(volume.shape))
            t1 = time.perf_counter()
            LOG.info(f"full reconstruction time: {t1-t0}s for shape {images.data.shape}")
            return ImageStack(volume)


def allowed_recon_kwargs() -> dict:
    return {'CIL: PDHG-TV': ['alpha', 'num_iter', 'non_negative', 'stochastic', 'subsets']}
