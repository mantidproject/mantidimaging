# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
from logging import getLogger, DEBUG
from math import sqrt, ceil
from threading import Lock
from typing import TYPE_CHECKING

import numpy as np

from cil.framework import (AcquisitionData, AcquisitionGeometry, DataOrder, ImageGeometry, BlockGeometry,
                           BlockDataContainer)
from cil.optimisation.algorithms import PDHG, SPDHG, Algorithm
from cil.optimisation.operators import GradientOperator, BlockOperator
from cil.optimisation.operators import SymmetrisedGradientOperator, ZeroOperator, IdentityOperator

from cil.optimisation.functions import MixedL21Norm, L2NormSquared, BlockFunction, ZeroFunction, IndicatorBox, Function
from cil.optimisation.utilities.callbacks import Callback
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


class MIProgressCallback(Callback):

    def __init__(self, verbose=1, progress: Progress | None = None) -> None:
        super().__init__(verbose)
        self.progress = progress

    def __call__(self, algo: Algorithm) -> None:
        if self.progress:
            extra_info = {}
            if algo.iterations and algo.iterations[-1] == algo.iteration:
                extra_info = {'iterations': algo.iterations[1:], 'losses': algo.loss[1:]}
            if hasattr(algo, "last_residual") and algo.last_residual[0] == algo.iteration:
                extra_info["residual"] = algo.last_residual[1]
            self.progress.update(
                steps=1,
                msg=f'CIL: Iteration {algo.iteration} of {algo.max_iteration}'
                f': Objective {algo.get_last_objective():.2f}',
                force_continue=False,
                extra_info=extra_info,
            )


class RecordResidualsCallback(Callback):

    def __init__(self, verbose=1, residual_interval: int = 1) -> None:
        super().__init__(verbose)
        self.residual_interval = residual_interval

    def __call__(self, algo: Algorithm) -> None:
        if algo.iteration % self.residual_interval == 0:
            if isinstance(algo, PDHG):
                forward_projection = algo.operator.direct(algo.solution)[1].as_array()
                data = algo.f[1].b.as_array()
                if forward_projection.ndim == 3:
                    # For a full 3D recon, just select the middle slice
                    slice = forward_projection.shape[0] // 2
                    forward_projection = forward_projection[slice]
                    data = data[slice]
                residual: np.ndarray = (data - forward_projection)**2
                algo.last_residual = (algo.iteration, residual**2)


class CILRecon(BaseRecon):

    @staticmethod
    def set_up_TV_regularisation(
            image_geometry: ImageGeometry, acquisition_data: AcquisitionData,
            recon_params: ReconstructionParameters) -> tuple[BlockOperator, BlockFunction, Function]:

        # Forward operator
        A2d = ProjectionOperator(image_geometry, acquisition_data.geometry, 'gpu')

        if recon_params.stochastic:
            for partition_geometry, partition_operator in zip(acquisition_data.geometry, A2d, strict=True):
                CILRecon.set_approx_norm(partition_operator, partition_geometry, image_geometry)
        else:
            CILRecon.set_approx_norm(A2d, acquisition_data.geometry, image_geometry)

        # Define Gradient Operator and BlockOperator
        alpha = recon_params.alpha
        Grad = GradientOperator(image_geometry)

        if recon_params.stochastic:
            # now, A2d is a BlockOperator as acquisition_data is a BlockDataContainer
            fs = []
            for i, _ in enumerate(acquisition_data.geometry):
                fs.append(L2NormSquared(b=acquisition_data.get_item(i)))
            fs.append(MixedL21Norm())

            F = BlockFunction(*fs)

            # needs to unrol the A2d BlockOperator and put it in another, followed by
            # the gradient operator, as in the deterministic case
            K = BlockOperator(*A2d.get_as_list(), alpha * Grad)

        else:
            # Define BlockFunction F using the MixedL21Norm() and the L2NormSquared()
            f1 = MixedL21Norm()
            f2 = L2NormSquared(b=acquisition_data)

            F = BlockFunction(f1, f2)

            # define the BlockOperator
            K = BlockOperator(alpha * Grad, A2d)

        if recon_params.non_negative:
            G = IndicatorBox(lower=0)
        else:
            # Define Function G simply as zero
            G = ZeroFunction()

        return (K, F, G)

    @staticmethod
    def set_up_TGV_regularisation(
            image_geometry: ImageGeometry, acquisition_data: AcquisitionData,
            recon_params: ReconstructionParameters) -> tuple[BlockOperator, BlockFunction, Function]:

        # Forward operator
        A2d = ProjectionOperator(image_geometry, acquisition_data.geometry, 'gpu')

        if recon_params.stochastic:
            for partition_geometry, partition_operator in zip(acquisition_data.geometry, A2d, strict=True):
                CILRecon.set_approx_norm(partition_operator, partition_geometry, image_geometry)
        else:
            CILRecon.set_approx_norm(A2d, acquisition_data.geometry, image_geometry)

        # Define Gradient Operator and BlockOperator
        alpha = recon_params.alpha
        gamma = recon_params.gamma
        beta = alpha * gamma

        f2 = MixedL21Norm()
        f3 = MixedL21Norm()

        if recon_params.stochastic:
            raise ValueError("TGV reconstruction does not yet support stochastic mode")
            # now, A2d is a BlockOperator as acquisition_data is a BlockDataContainer
            fs = []
            for i, _ in enumerate(acquisition_data.geometry):
                fs.append(L2NormSquared(b=acquisition_data.get_item(i)))

            F = BlockFunction(*fs, f2, f3)

        else:
            # Define BlockFunction F using the MixedL21Norm() and the L2NormSquared()
            # mathematicians like to multiply 1/2 in front of L2NormSquared. This is not necessary
            # it will mean that the regularisation parameter alpha is doubled
            f1 = L2NormSquared(b=acquisition_data)

            F = BlockFunction(f1, f2, f3)

        # Define BlockOperator K

        # Set up the 3 operator A, Grad and Symmetrised Gradient
        K11 = A2d
        K21 = alpha * GradientOperator(K11.domain)
        K32 = beta * SymmetrisedGradientOperator(K21.range)
        # these define the domain and range of the other operators
        K12 = ZeroOperator(K32.domain, K11.range)
        K22 = -alpha * IdentityOperator(domain_geometry=K21.range, range_geometry=K32.range)
        K31 = ZeroOperator(K11.domain, K32.range)

        K = BlockOperator(K11, K12, K21, K22, K31, K32, shape=(3, 2))

        if recon_params.non_negative:
            G = BlockFunction(IndicatorBox(lower=0, upper=None), ZeroFunction())

        else:
            # Define Function G simply as zero
            G = ZeroFunction()

        return (K, F, G)

    @staticmethod
    def set_approx_norm(A2d: BlockOperator, acquisition_data: AcquisitionGeometry,
                        image_geometry: ImageGeometry) -> None:
        """
        Use an analytic approximation of the norm of the operator
        Otherwise this is slow to calculate, this approximation is good to with in 5%
        When running in debug mode, check the approximation and raise an error if it is bad
        """
        assert all(s == 1.0 for s in image_geometry.spacing), "Norm approximations assume voxel size == 1"
        approx_a2d_norm = sqrt(image_geometry.voxel_num_x * acquisition_data.num_projections)
        if LOG.isEnabledFor(DEBUG):
            num_a2d_norm = A2d.PowerMethod(A2d, max_iteration=100)
            diff = abs(approx_a2d_norm - num_a2d_norm) / max(approx_a2d_norm, num_a2d_norm)
            LOG.debug(f"ProjectionOperator approx norm: {diff=} {approx_a2d_norm=} {num_a2d_norm=}")
            if diff > 0.05:
                raise RuntimeError(f"Bad ProjectionOperator norm: {diff=} {approx_a2d_norm=} {num_a2d_norm=}\n")
        A2d.set_norm(approx_a2d_norm)

    @staticmethod
    def get_data(sino: np.ndarray, ag: AcquisitionGeometry, recon_params: ReconstructionParameters,
                 num_subsets: int) -> BlockDataContainer | AcquisitionData:
        data = AcquisitionData(sino, deep_copy=False, geometry=ag, suppress_warning=True)

        if recon_params.stochastic:
            # split the data and put it in a BlockDataContainer
            # unfortunately now the data will be duplicated in memory
            data = data.partition(num_subsets, 'staggered')
            geo = []
            for i in range(len(data)):
                data.get_item(i).reorder('astra')
                geo.append(data.get_item(i).geometry)
            # COMPAT - workaround for https://github.com/TomographicImaging/CIL/issues/1445
            data.geometry = BlockGeometry(*geo)
        else:
            data.reorder('astra')

        return data

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
                    progress: Progress | None = None) -> np.ndarray:
        """
        Reconstruct a single slice from a single sinogram. Used for the preview and the single slice button.
        Should return a numpy array,
        """

        num_iter = recon_params.num_iter
        num_subsets = ceil(sino.shape[0] / recon_params.projections_per_subset)
        if recon_params.stochastic:
            # The UI will pass the number of epochs in this case
            num_iter *= num_subsets

        if progress:
            progress.add_estimated_steps(num_iter + 1)
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

            # let's create a CIL AcquisitionData or BlockDataContainer
            data = CILRecon.get_data(sino, ag, recon_params, num_subsets)

            ig = ag.get_ImageGeometry()

            if recon_params.regulariser == 'TV':
                K, F, G = CILRecon.set_up_TV_regularisation(ig, data, recon_params)
            elif recon_params.regulariser == 'TGV':
                K, F, G = CILRecon.set_up_TGV_regularisation(ig, data, recon_params)
            else:
                raise ValueError(f"Regulariser must be one of 'TV', 'TGV'. Received '{recon_params.regulariser}'")

            # this should set to a sensible number as evaluating the objective is costly
            update_objective_interval = 10
            if recon_params.stochastic:
                reg_percent = recon_params.regularisation_percent
                probs = [(1 - reg_percent / 100) / num_subsets] * num_subsets + [reg_percent / 100]
                algo = SPDHG(f=F, g=G, operator=K, prob=probs, update_objective_interval=update_objective_interval)
            else:
                normK = K.norm()
                sigma = 1
                tau = 1 / (sigma * normK**2)
                algo = PDHG(f=F,
                            g=G,
                            operator=K,
                            tau=tau,
                            sigma=sigma,
                            update_objective_interval=update_objective_interval)

            try:
                # this may be confusing for the user in case of SPDHG, because they will
                # input num_iter and they will run num_iter * num_subsets
                algo.max_iteration = num_iter
                algo.run(num_iter,
                         callbacks=[
                             RecordResidualsCallback(residual_interval=update_objective_interval),
                             MIProgressCallback(progress=progress)
                         ])

            finally:
                if progress:
                    progress.mark_complete()
            t1 = time.perf_counter()
            LOG.info(f"single_sino time: {t1-t0}s for shape {sino.shape}")

            if isinstance(algo.solution, BlockDataContainer):
                # TGV case
                return algo.solution[0].as_array()

            return algo.solution.as_array()

    @staticmethod
    def full(images: ImageStack,
             cors: list[ScalarCoR],
             recon_params: ReconstructionParameters,
             progress: Progress | None = None) -> ImageStack:
        """
        Performs a volume reconstruction using sample data provided as sinograms.

        :param images: Array of sinogram images
        :param cors: Array of centre of rotation values
        :param recon_params: Reconstruction Parameters
        :param progress: Optional progress reporter
        :return: 3D image data for reconstructed volume
        """

        num_iter = recon_params.num_iter
        num_subsets = ceil(images.num_projections / recon_params.projections_per_subset)
        if recon_params.stochastic:
            # The UI will pass the number of epochs in this case
            num_iter *= num_subsets

        progress = Progress.ensure_instance(progress, task_name='CIL reconstruction', num_steps=num_iter + 1)

        pixel_num_h = images.width
        pixel_num_v = images.height

        projection_size = full_size_KB(images.data.shape, images.dtype)
        recon_volume_shape = pixel_num_h, pixel_num_h, pixel_num_v
        recon_volume_size = full_size_KB(recon_volume_shape, images.dtype)
        if recon_params.stochastic:
            estimated_mem_required = 3 * projection_size + 14 * recon_volume_size
        else:
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
                     f"Non-negative {recon_params.non_negative},"
                     f"Stochastic {recon_params.stochastic}, subsets {num_subsets}")
            progress.update(steps=1, msg='CIL: Setting up reconstruction', force_continue=False)

            if recon_params.tilt is None:
                raise ValueError("recon_params.tilt is not set")
            tilt = recon_params.tilt.value

            if images.is_sinograms:
                data_order = DataOrder.ASTRA_AG_LABELS
            else:
                data_order = DataOrder.TIGRE_AG_LABELS

            if images.geometry is None:
                raise ValueError("images.geometry is not set")

            images.geometry.set_geometry_from_cor_tilt(cors[0], tilt)
            images.geometry.set_labels(data_order)
            ig = images.geometry.get_ImageGeometry()

            data = CILRecon.get_data(BaseRecon.prepare_sinogram(images.data, recon_params), images.geometry,
                                     recon_params, num_subsets)

            if recon_params.regulariser == 'TV':
                K, F, G = CILRecon.set_up_TV_regularisation(ig, data, recon_params)
            elif recon_params.regulariser == 'TGV':
                K, F, G = CILRecon.set_up_TGV_regularisation(ig, data, recon_params)
            else:
                raise ValueError(f"Regulariser must be one of 'TV', 'TGV'. Received '{recon_params.regulariser}'")

            # this should set to a sensible number as evaluating the objective is costly
            update_objective_interval = 10
            if recon_params.stochastic:
                reg_percent = recon_params.regularisation_percent
                probs = [(1 - reg_percent / 100) / num_subsets] * num_subsets + [reg_percent / 100]
                algo = SPDHG(f=F, g=G, operator=K, prob=probs, update_objective_interval=update_objective_interval)
            else:
                normK = K.norm()
                sigma = 1
                tau = 1 / (sigma * normK**2)
                algo = PDHG(f=F,
                            g=G,
                            operator=K,
                            tau=tau,
                            sigma=sigma,
                            update_objective_interval=update_objective_interval)

            with progress:
                # this may be confusing for the user in case of SPDHG, because they will
                # input num_iter and they will run num_iter * num_subsets
                algo.max_iteration = num_iter
                algo.run(num_iter,
                         callbacks=[
                             RecordResidualsCallback(residual_interval=update_objective_interval),
                             MIProgressCallback(progress=progress)
                         ])

                if isinstance(algo.solution, BlockDataContainer):
                    # TGV case
                    volume = algo.solution[0].as_array()
                else:
                    volume = algo.solution.as_array()
                LOG.info(f'Reconstructed 3D volume with shape: {volume.shape}')
            t1 = time.perf_counter()
            LOG.info(f"full reconstruction time: {t1-t0}s for shape {images.data.shape}")
            ImageStack(volume).metadata['convergence'] = {'iterations': algo.iterations, 'losses': algo.loss}
            return ImageStack(volume)


def allowed_recon_kwargs() -> dict[str, list[str]]:
    return {
        'CIL_PDHG-TV':
        ['alpha', 'num_iter', 'non_negative', 'stochastic', 'projections_per_subset', 'regularisation_percent']
    }
