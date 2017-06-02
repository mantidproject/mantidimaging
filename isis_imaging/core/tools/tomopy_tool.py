from __future__ import absolute_import, division, print_function

import numpy as np

from isis_imaging import helper as h
from isis_imaging.core.algorithms import projection_angles
from isis_imaging.core.tools.abstract_tool import AbstractTool


class TomoPyTool(AbstractTool):
    @staticmethod
    def tool_supported_methods():
        return [
            'art', 'bart', 'fbp', 'gridrec', 'mlem', 'osem', 'ospml_hybrid',
            'ospml_quad', 'pml_hybrid', 'pml_quad', 'sirt'
        ]

    @staticmethod
    def check_algorithm_compatibility(algorithm):
        if algorithm not in TomoPyTool.tool_supported_methods():
            raise ValueError(
                "The selected algorithm {0} is not supported by TomoPy.".
                format(algorithm))

    def __init__(self):
        AbstractTool.__init__(self)
        self._tomopy = self.import_self()
        import tomopy.prep
        import tomopy.recon
        import tomopy.misc
        import tomopy.io
        import tomopy.sim

        # pretend we have the functions
        self.find_center = self._tomopy.find_center
        self.find_center_vo = self._tomopy.find_center_vo
        self.circ_mask = self._tomopy.circ_mask

        # make all tomopy methods available
        self.misc = tomopy.misc
        self.prep = tomopy.prep
        self.recon = tomopy.recon
        self.sim = tomopy.sim
        self.io = tomopy.io

    def import_self(self):
        try:
            import tomopy
            import tomopy.prep
            import tomopy.recon
            import tomopy.misc
            import tomopy.io

        except ImportError as exc:
            raise ImportError(
                "Could not import the tomopy package and its subpackages. "
                "Details: {0}".format(exc))

        return tomopy

    def run_reconstruct(self, sample, config, proj_angles=None, **kwargs):
        """
        Run a reconstruction with TomoPy, using the CPU algorithms they provide.

        Information for each reconstruction method is available at
            http://tomopy.readthedocs.io/en/latest/api/tomopy.recon.algorithm.html

        :param sample: The sample image data as a 3D numpy.ndarray
        :param config: A ReconstructionConfig with all the necessary parameters
                       to run a reconstruction. The Centers of Rotation
                        must be interpolated independently!
        :param proj_angles: The projection angle for each slice.
                            If not provided equidistant angles will be generated
        :param kwargs: Any keyword arguments will be forwarded to the TomoPy
                       reconstruction function
        :return: The reconstructed volume
        """
        h.check_config_integrity(config)
        h.check_data_stack(sample)

        if proj_angles is None:
            num_radiograms = sample.shape[1]
            proj_angles = projection_angles.generate(config.func.max_angle,
                                                     num_radiograms)

        alg = config.func.algorithm
        num_iter = config.func.num_iter
        cores = config.func.cores
        cors = config.func.cors

        assert len(cors) == sample.shape[0],\
            "The provided number of CORs does not match the slice number! \
            A Center of rotation must be provided for each slice. Usually \
            that is done via core.algorithms.cor_interpolate"

        iterative_algorithm = False if alg in ['gridrec', 'fbp'] else True

        if iterative_algorithm:  # run the iterative algorithms
            h.pstart(
                "Starting iterative method with TomoPy. Avg Center of Rotation:"
                " {0}, Algorithm: {1}, number of iterations: {2}...".format(
                    np.mean(cors), alg, num_iter))

            kwargs = dict(kwargs, num_iter=num_iter)
        else:  # run the non-iterative algorithms
            h.pstart(
                "Starting non-iterative reconstruction algorithm with TomoPy. "
                "Mean COR: {0}, Number of CORs provided {1}, Algorithm: {2}...".
                format(np.mean(cors), len(cors), alg))

            # TODO need to expose the filters to CLI
            # filter_name='parzen',
            # filter_par=[5.],
        recon = self._tomopy.recon(
            tomo=sample,
            theta=proj_angles,
            center=cors,
            ncore=cores,
            algorithm=alg,
            sinogram_order=True,
            **kwargs)

        h.pstop(
            "Reconstructed 3D volume. Shape: {0}, and pixel data type: {1}.".
            format(recon.shape, recon.dtype))

        return recon
