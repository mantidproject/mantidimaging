from __future__ import absolute_import, division, print_function

from isis_imaging import helper as h
from isis_imaging.core.tools.abstract_tool import AbstractTool


class AstraTool(AbstractTool):
    """
    Uses TomoPy's integration of Astra
    """

    @staticmethod
    def tool_supported_methods():
        return [
            'FP', 'FP_CUDA', 'BP', 'BP_CUDA', 'FBP', 'FBP_CUDA', 'SIRT',
            'SIRT_CUDA', 'SART', 'SART_CUDA', 'CGLS', 'CGLS_CUDA'
        ]

    @staticmethod
    def check_algorithm_compatibility(algorithm):
        # get full caps, because all the names in ASTRA are in FULL CAPS
        ALGORITHM = algorithm.upper()

        if ALGORITHM not in AstraTool.tool_supported_methods():
            raise ValueError(
                "The selected algorithm {0} is not supported by Astra.".format(
                    ALGORITHM))

    def __init__(self):
        AbstractTool.__init__(self)

        # we import tomopy so that we can use Astra through TomoPy's
        # implementation
        self._astra = self.import_self()

    def import_self(self):
        try:
            import astra
        except ImportError as exc:
            raise ImportError(
                "Cannot find and import the astra toolbox package: {0}".format(
                    exc))

        min_astra_version = 1.8
        astra_version = float(astra.__version__)
        if isinstance(astra_version,
                      float) and astra_version >= min_astra_version:
            print("Imported astra successfully. Version: {0}".format(
                astra_version))
        else:
            raise RuntimeError(
                "Could not find the required version of astra. Found version: {0}".
                format(astra_version))

        print("Astra using CUDA: {0}".format(astra.astra.use_cuda()))
        return astra

    def run_reconstruct(self, data, config, proj_angles=None, **kwargs):
        """
        Run a reconstruction with TomoPy's ASTRA integration, using the CPU and GPU algorithms they provide.
        TODO This reconstruction function does NOT fully support the full range of options that are available for
         each algorithm in Astra.

        Information about how to use Astra through TomoPy is available at:
        http://tomopy.readthedocs.io/en/latest/ipynb/astra.html

        More information about the ASTRA Reconstruction parameters is available at:
        http://www.astra-toolbox.com/docs/proj2d.html
        http://www.astra-toolbox.com/docs/algs/index.html

        :param data: Input data as a 3D numpy.ndarray

        :param config: A ReconstructionConfig with all the necessary parameters to run a reconstruction.

        :param proj_angles: The projection angle for each slice

        :param kwargs: Any keyword arguments will be forwarded to the TomoPy reconstruction function

        :return: 3D numpy.ndarray containing the reconstructed data

        """

        # import pydevd
        # pydevd.settrace('localhost', port=59003, stdoutToServer=True, stderrToServer=True)

        # plow = (data.shape[2] - cor * 2)
        # phigh = 0

        from isis_imaging.core.algorithms import projection_angles
        if proj_angles is None:
            proj_angles = projection_angles.generate(config.func.max_angle,
                                                     data.shape[1])

        print(len(proj_angles))

        detector_spacing_x = 0.55
        detector_spacing_y = 0.55

        assert (detector_spacing_x > 0) and (
            detector_spacing_y > 0
        ), "Det spacing must be positive or Astra will crash"

        projections_geometry = self._astra.create_proj_geom(
            'parallel3d', detector_spacing_x, detector_spacing_y,
            data.shape[0], data.shape[2], proj_angles)

        print(projections_geometry)

        sinogram_id = self._astra.data3d.create('-sino', projections_geometry,
                                                data)
        d = self._astra.data3d.get(sinogram_id)
        recon_volume_geometry = self._astra.create_vol_geom(data.shape)
        recon_id = self._astra.data3d.create('-vol', recon_volume_geometry)

        # algorithm = config.func.algorithm
        algorithm = 'FBP_CUDA'
        alg_cfg = self._astra.astra_dict(algorithm)
        alg_cfg['ReconstructionDataId'] = recon_id
        alg_cfg['ProjectionDataId'] = sinogram_id

        alg_id = self._astra.algorithm.create(alg_cfg)

        number_of_iters = 1
        self._astra.algorithm.run(alg_id, number_of_iters)
        recon = self._astra.data3d.get(recon_id)

        self._astra.algorithm.delete(alg_id)
        self._astra.data3d.delete(recon_id)
        self._astra.data3d.delete(sinogram_id)

        return recon

    def algorithm_name_handling(self, alg):
        # remove xxx_CUDA from the string with the [0:find..]
        iterative_algorithm = False if alg[0:alg.find(
            '_')] in ['FBP', 'FB', 'BP'] else True

        # are we using a CUDA algorithm
        proj_type = 'cuda' if alg[alg.find('_') + 1:] == 'CUDA' else 'linear'
