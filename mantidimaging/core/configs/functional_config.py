import logging
import os

import numpy as np

from mantidimaging.core.io.utility import DEFAULT_IO_FILE_FORMAT
from mantidimaging.helper import set_logging_from_func_config


class FunctionalConfig(object):
    """
    All pre-processing options required to run a tomographic reconstruction
    """
    def __init__(self):
        """
        Builds a default post-processing configuration with a sensible choice
        of parameters

        crash_on_failed_import: Default True, this option tells if the program
                                should stop execution if an import fails and a
                                step cannot be executed:
            True - Raise an exception and stop execution immediately
            False - Note the failure to import but continue execution without
                    applying the filter
        """

        # Functionality options
        self.input_path = None
        self.input_path_flat = None
        self.input_path_dark = None
        self.in_prefix = ''
        self.in_format = DEFAULT_IO_FILE_FORMAT
        self.construct_sinograms = False

        self.output_path = None
        self.out_format = DEFAULT_IO_FILE_FORMAT
        self.out_slices_prefix = 'recon_slice'
        self.out_horiz_slices_prefix = 'recon_horiz'
        self.out_horiz_slices_subdir = 'horiz_slices'
        self.save_horiz_slices = False

        # Processing options
        self.save_preproc = True
        self.reconstruction = False
        self.skip_preproc = False
        self.preproc_subdir = 'pre_processed'
        self.swap_axes = False

        self.data_dtype = np.float32

        self.cors = None
        # single member list so that interpolation doesn't fail in
        # cor_interpolate
        self.cor_slices = [0]

        self.log_level = logging.INFO

        self.overwrite_all = False

        self.debug = True
        self.debug_port = None

        # Reconstruction options
        self.tool = 'tomopy'
        self.algorithm = 'gridrec'
        self.num_iter = 5
        self.max_angle = 360.0

        import multiprocessing
        # get max cores on the system as default
        self.cores = multiprocessing.cpu_count()

        # how to spread the image load per worker
        self.chunksize = None
        self.parallel_load = False

        # imopr
        self.imopr = None

        # aggregate
        self.aggregate = None
        self.aggregate_angles = None
        self.aggregate_single_folder_output = None

        # convert
        self.convert = False
        self.convert_prefix = 'converted_images'

        # which indices of images to load
        self.split = False
        self.indices = None
        self.max_memory = None
        self.max_ratio = 1.

        # process list execution
        self.process_list = None
        # start the GUI
        self.gui = False

    def __str__(self):
        s = ("Input directory: {in_dir}\n"
             "Flat directory: {flat_dir}\n"
             "Dark directory: {dark_dir}\n"
             "Input image prefix: {c.in_prefix}\n"
             "Input image format: {c.in_format}\n"
             "Output directory: {out_dir}\n"
             "Output image format: {c.out_format}\n"
             "Output slices filename prefix: {c.out_slices_prefix}\n"
             "Output horizontal slices file name prefix: "
             "{c.out_horiz_slices_prefix}\n"
             "Output horizontal slices subdir: {c.out_horiz_slices_subdir}\n"
             "Save horizontal slices: {c.save_horiz_slices}\n"
             "Save preprocessed images: {c.save_preproc}\n"
             "Do only pre processing and exit: {c.reconstruction}\n"
             "Skip preprocessing step: {c.skip_preproc}\n"
             "Pre processing images subdir: {preproc_dir}\n"
             "Radiograms: {c.swap_axes}\n"
             "Data type: {c.data_dtype}\n"
             "Provided center of rotation: {c.cors}\n"
             "Slice IDs for CORs: {c.cor_slices}\n"
             "Log level: {c.log_level}\n"
             "Overwrite files in output directory: {c.overwrite_all}\n"
             "Debug: {c.debug}\n"
             "Debug port: {c.debug_port}\n"
             "Tool: {c.tool}\n"
             "Algorithm: {c.algorithm}\n"
             "Number of iterations: {c.num_iter}\n"
             "Maximum angle: {c.max_angle}\n"
             "Cores: {c.cores}\n"
             "Chunk per worker: {c.chunksize}\n"
             "Load data in parallel: {c.parallel_load}\n"
             "Image operator mode: {c.imopr}\n"
             "Aggregate mode: {c.aggregate}\n"
             "Aggregate angles: {c.aggregate_angles}\n"
             "Aggregate single folder output: "
             "{c.aggregate_single_folder_output}\n"
             "Convert images mode: {c.convert}\n"
             "Prefix for the output converted images: {c.convert_prefix}\n"
             "Which images will be loaded: {c.indices}\n"
             "Split the execution into separate runs: {c.split}\n"
             "Max memory for split execution: {c.max_memory}\n"
             "Max ratio to memory for split execution: {c.max_ratio}\n"
             "Use a process list for execution: {c.process_list}\n"
             "Running the GUI: {c.gui}\n").format(c=self,
                                                  in_dir=os.path.abspath(str(self.input_path)),
                                                  flat_dir=os.path.abspath(str(self.input_path_flat)),
                                                  dark_dir=os.path.abspath(str(self.input_path_dark)),
                                                  out_dir=os.path.abspath(str(self.output_path)),
                                                  preproc_dir=os.path.abspath(str(self.preproc_subdir)))

        return s

    def _setup_parser(self, parser):
        """
        Setup the functional arguments for the script
        :param parser: The parser which is set up
        """
        grp_func = parser.add_argument_group('Functionality options')

        grp_func.add_argument("-i",
                              "--input-path",
                              required=True,
                              type=str,
                              help="Input directory",
                              default=self.input_path)

        grp_func.add_argument("-F",
                              "--input-path-flat",
                              required=False,
                              default=self.input_path_flat,
                              type=str,
                              help="Input directory for flat images")

        grp_func.add_argument("-D",
                              "--input-path-dark",
                              required=False,
                              default=self.input_path_dark,
                              type=str,
                              help="Input directory for flat images")

        grp_func.add_argument("--in-prefix",
                              required=False,
                              default=self.in_prefix,
                              type=str,
                              help="Filename prefix to use when searching for input image files "
                              "to load.")

        from mantidimaging.core.io import loader
        grp_func.add_argument("--in-format",
                              required=False,
                              default=self.out_format,
                              type=str,
                              choices=loader.supported_formats(),
                              help="Format/file extension expected for the input images.")

        grp_func.add_argument("--construct-sinograms",
                              required=False,
                              default=self.construct_sinograms,
                              action='store_true',
                              help="Construct the sinograms on load.")

        grp_func.add_argument("-o",
                              "--output-path",
                              required=False,
                              default=self.output_path,
                              type=str,
                              help="Where to write the output slice images (reconstructed "
                              "volume)")

        from mantidimaging.core.io.saver import Saver
        grp_func.add_argument("--out-format",
                              required=False,
                              default=self.out_format,
                              type=str,
                              choices=Saver.supported_formats(),
                              help="Format/file extension expected for the input images.")

        grp_func.add_argument("--out-slices-prefix",
                              required=False,
                              default=self.out_slices_prefix,
                              type=str,
                              help="The prefix for the reconstructed slices files.")

        grp_func.add_argument("--out-horiz-slices-subdir",
                              required=False,
                              default=self.out_horiz_slices_subdir,
                              type=str,
                              help="The subdirectory for the reconstructed horizontal slices.")

        grp_func.add_argument("--out-horiz-slices-prefix",
                              required=False,
                              default=self.out_horiz_slices_prefix,
                              type=str,
                              help="The prefix for the reconstructed horizontal slices files.")

        grp_func.add_argument("-s",
                              "--save-preproc",
                              required=False,
                              action='store_true',
                              help="Save out the pre-processed images.")

        grp_func.add_argument("--reconstruction",
                              required=False,
                              action='store_true',
                              help="Complete pre-processing of images and exit.")

        grp_func.add_argument("--skip-preproc",
                              required=False,
                              action='store_true',
                              help="The images loaded have already been pre-processed. "
                              "All pre-processing steps will be skipped.")

        grp_func.add_argument("--save-horiz-slices",
                              required=False,
                              action='store_true',
                              help="Save out the horizontal reconstructed files.")

        grp_func.add_argument("-p",
                              "--preproc-subdir",
                              required=False,
                              type=str,
                              default=self.preproc_subdir,
                              help="The subdirectory for the pre-processed images.\n"
                              "Default output-path/pre_processed/.")

        grp_func.add_argument("--swap-axes",
                              required=False,
                              action='store_true',
                              default=self.swap_axes,
                              help="NOT RECOMMENDED: This means an additional conversion will "
                              "be done inside Tomopy, which will double the memory usage."
                              "\nThe axis will be flipped on the pre-processing images before "
                              "saving. This means if sinograms are passed, they will be turned "
                              "into radiograms, and vice versa.")

        grp_func.add_argument("--data-dtype",
                              required=False,
                              default='float32',
                              type=str,
                              help="Default (and recommended): float32\nThe data type in which "
                              "the data converted to after loading and processed. "
                              "Supported: float32, float64")

        grp_func.add_argument("--log-level",
                              type=str,
                              default='INFO',
                              help="Log verbosity level.\n"
                              "Available options are: TRACE, DEBUG, INFO, WARN, CRITICAL")

        grp_func.add_argument("-w",
                              "--overwrite-all",
                              required=False,
                              action='store_true',
                              default=self.overwrite_all,
                              help="NO WARNINGS WILL BE GIVEN BEFORE OVERWRITING FILES. "
                              "USE WITH CAUTION!\nOverwrite all conflicting files "
                              "found in the output directory.")

        grp_func.add_argument("--cores",
                              required=False,
                              type=int,
                              default=self.cores,
                              help="Default: %(default)s (maximum available on the system). "
                              "Number of CPU cores that will be used for reconstruction.")

        grp_func.add_argument("--chunksize",
                              required=False,
                              type=int,
                              default=self.chunksize,
                              help="How to spread the load on each worker.")

        grp_func.add_argument("--parallel-load",
                              required=False,
                              action='store_true',
                              default=self.parallel_load,
                              help="Load the data with multiple reader processes. "
                              "This CAN MAKE THE LOADING slower on a local Hard Disk Drive.")

        grp_func.add_argument("--process-list",
                              required=False,
                              nargs="*",
                              default=self.process_list,
                              help="Use the process list parser. Intended use is for cluster "
                              "submission. It can parse a string from command line, file "
                              "containing the commands, or a saved process list.")

        grp_run_modes = parser.add_argument_group('Run Modes')

        grp_run_modes.add_argument("--convert",
                                   required=False,
                                   action='store_true',
                                   default=self.convert,
                                   help="Convert images to a different format. "
                                   "The output format will be the one specified with --out-format")

        grp_run_modes.add_argument("--convert-prefix",
                                   required=False,
                                   type=str,
                                   default=self.convert_prefix,
                                   help="Prefix for saved out files from conversion.")

        from mantidimaging.core.imopr import imopr
        grp_run_modes.add_argument("--imopr",
                                   nargs="*",
                                   required=False,
                                   type=str,
                                   default=self.imopr,
                                   help="Image operator currently supports the following operators: "
                                   "{}".format(imopr.get_available_operators()))

        grp_run_modes.add_argument("--aggregate",
                                   nargs="*",
                                   required=False,
                                   type=str,
                                   default=self.aggregate,
                                   help="Aggregate the selected image energy levels. The expected "
                                   "input is --aggregate <start> <end> <method:{sum, avg}>..."
                                   " to select indices.\nThere must always be an even length of "
                                   "indices: --aggregate 0 100 101 201 300 400 sum")

        grp_run_modes.add_argument("--aggregate-angles",
                                   nargs='*',
                                   required=False,
                                   type=str,
                                   default=self.aggregate_angles,
                                   help="Select which angles to be aggregated with --aggregate.\n"
                                   "This can be used to spread out the load on multiple nodes.\n"
                                   "Sample command: --aggregate-angles 0 10, "
                                   "will select only angles 0 - 10 inclusive.")

        grp_run_modes.add_argument("--aggregate-single-folder-output",
                                   action="store_true",
                                   required=False,
                                   default=self.aggregate_single_folder_output,
                                   help="The output will be images with increasing "
                                   "number in a single folder.")

        grp_run_modes.add_argument("--debug",
                                   required=False,
                                   action="store_true",
                                   help="Run debug to specified port, if no port is specified, "
                                   "it will default to 59003")

        grp_run_modes.add_argument("--debug-port",
                                   required=False,
                                   type=int,
                                   default=self.debug_port,
                                   help='Port on which a debugger is listening.')

        grp_run_modes.add_argument("--gui",
                                   required=False,
                                   action='store_true',
                                   default=self.gui,
                                   help='Start the GUI.')

        grp_recon = parser.add_argument_group('Reconstruction options')

        supported_tools = ['tomopy', 'astra']
        grp_recon.add_argument("-t",
                               "--tool",
                               required=False,
                               type=str,
                               default=self.tool,
                               choices=supported_tools,
                               help="Default: %(default)s\n"
                               "Tomographic reconstruction tool to use.\n"
                               "TODO: Describe pros and cons of each tool (Astra GPU). "
                               "Available: {0}".format(", ".join(supported_tools)))

        from mantidimaging.core.tools.tomopy_tool import TomoPyTool
        from mantidimaging.core.tools.astra_tool import AstraTool
        tomo_algs = TomoPyTool.tool_supported_methods()
        astra_algs = AstraTool.tool_supported_methods()
        grp_recon.add_argument("-a",
                               "--algorithm",
                               required=False,
                               type=str,
                               default=self.algorithm,
                               help="Default: %(default)s\nReconstruction algorithm "
                               "(tool dependent).\nAvailable:\nTomoPy: {0}\nAstra: {1}".format(
                                   ", ".join(tomo_algs), ", ".join(astra_algs)))

        grp_recon.add_argument("-n",
                               "--num-iter",
                               required=False,
                               type=int,
                               default=self.num_iter,
                               help="Number of iterations (only valid for iterative methods: "
                               "art, bart, mlem, osem, ospml_hybrid, ospml_quad, "
                               "pml_hybrid, pml_quad, sirt).")

        grp_recon.add_argument("--max-angle",
                               required=False,
                               type=float,
                               default=self.max_angle,
                               help="Maximum angle of the last projection.\n"
                               "Assuming first angle=0, and uniform angle increment "
                               "for every projection.")

        grp_recon.add_argument(
            "-c",
            "--cors",
            required=False,
            nargs='*',
            type=str,  # will be converted to floats in self.update()
            default=self.cors,
            help="Either a list of CORs or a file containing CORs.\n"
            "If a file is used it must be a text file with a pair of slice"
            "index and COR on each line.\n"
            "Provide the CORs for the selected slices with --cor-slices.\n"
            "If no slices are provided a SINGLE COR is expected, "
            "that will be used for the whole stack.\n"
            "If slices are provided, the number of CORs provided "
            "with this option MUST BE THE SAME as the slices.")

        grp_recon.add_argument(
            "--cor-slices",
            required=False,
            nargs='*',
            type=str,  # will be converted to ints in self.update()
            default=self.cor_slices,
            help="Specify the Slice IDs to which the centers of rotation from "
            "--cors correspond.\nThe number of slices passed here MUST be the "
            "same as the number of CORs provided.\nThe slice IDs MUST be "
            "ints. If no slice IDs are provided, then only 1 COR is "
            "expected and will be used for the whole stack.")

        grp_recon.add_argument("--split",
                               required=False,
                               action='store_true',
                               default=self.split,
                               help="Split execution based on --max-memory and ratio of data "
                               "size to max memory.")

        grp_recon.add_argument("--max-memory",
                               required=False,
                               type=int,
                               default=self.max_memory,
                               help="Default: All memory avialable on the system. "
                               "Works in MEGABYTES! Specify the maximum memory allowed "
                               "to the reconstruction.")

        grp_recon.add_argument("--max-ratio",
                               required=False,
                               type=float,
                               default=self.max_ratio,
                               help="Default: %(default)s. Specify the maximum allowed ratio of "
                               "predicted memory / allowed memory. "
                               "This needs to be in range of 0 < ratio < 1")

        grp_recon.add_argument(
            "--indices",
            required=False,
            nargs='*',
            type=str,  # will be converted to ints in self.update()
            default=self.indices,
            help="Specify indices you want to be loaded.\n"
            "If not provided the whole stack will be loaded.\n"
            "If a single indice is provided: --indices 15, it will load "
            "indices in range [0, 15).")

        return parser

    def _update(self, args):
        """
        Should be called after the parser has had a chance to
        parse the real arguments from the user.

        SPECIAL CASES ARE HANDLED IN:
        recon_config.ReconstructionConfig.handle_special_arguments
        """
        # remove all the built-in parameters that start with __
        all_args = filter(lambda param: not param.startswith("_"), dir(self))

        # update all the arguments
        for arg in all_args:
            setattr(self, arg, getattr(args, arg))

        set_logging_from_func_config(self)
