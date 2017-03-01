from __future__ import (absolute_import, division, print_function)
from recon.tools.abstract_tool import AbstractTool


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
                "Could not import the tomopy package and its subpackages. Details: {0}".
                format(exc))

        return tomopy

    def run_reconstruct(self,
                        sample,
                        config,
                        h=None,
                        proj_angles=None,
                        **kwargs):
        """
        Run a reconstruction with TomoPy, using the CPU algorithms they provide.

        Information for each reconstruction method is available at
        http://tomopy.readthedocs.io/en/latest/api/tomopy.recon.algorithm.html

        :param sample: The sample image data as a 3D numpy.ndarray
        :param config: A ReconstructionConfig with all the necessary parameters to run a reconstruction.
        :param h: Helper class, if not provided will be initialised with empty constructor
        :param proj_angles: The projection angle for each slice
        :param kwargs: Any keyword arguments will be forwarded to the TomoPy reconstruction function
        :return: The reconstructed volume
        """
        import numpy as np
        from helper import Helper
        h = Helper(config) if h is None else h
        h.check_config_integrity(config)
        h.check_data_stack(sample)

        if proj_angles is None:
            num_proj = sample.shape[0]
            inc = float(config.func.max_angle) / num_proj
            proj_angles = np.arange(0, num_proj * inc, inc)
            proj_angles = np.radians(proj_angles)

        alg = config.func.algorithm
        cor = config.func.cor
        num_iter = config.func.num_iter
        cores = config.func.cores

        # Generating a COR for each slice created a better reconstruction
        # this approach works, however it needs to be made flexible.
        # That's on the TODO list
        print("Using pre-set CORs for chadwick tomo")

        import numpy as np
        # xp in numpy's interp
        slice_id = [222., 422., 822., 1222., 1622., 1822.]
        # yp in numpy's interp
        slice_cor = [542., 542., 540., 540., 537., 536.]
        # calculate as many CORs as there are sinograms (i.e. shape of Y)
        cors = np.interp(list(range(sample.shape[1])), slice_id, slice_cor)

        iterative_algorithm = False if alg in ['gridrec', 'fbp'] else True

        if iterative_algorithm:  # run the iterative algorithms
            h.pstart(
                "Starting iterative method with TomoPy. Center of Rotation: {0}, Algorithm: {1}, "
                "number of iterations: {2}...".format(cor, alg, num_iter))
            kwargs = dict(kwargs, num_iter=num_iter)
        else:  # run the non-iterative algorithms
            h.pstart(
                "Starting non-iterative reconstruction algorithm with TomoPy. "
                "Center of Rotation: {0}, Algorithm: {1}...".format(cor, alg))

        recon = self._tomopy.recon(
            tomo=sample[:],
            theta=proj_angles,
            center=cors,
            ncore=cores,
            algorithm=alg,
            **kwargs)

        h.pstop(
            "Reconstructed 3D volume. Shape: {0}, and pixel data type: {1}.".
            format(recon.shape, recon.dtype))

        return recon
