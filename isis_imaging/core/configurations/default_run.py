from __future__ import absolute_import, division, print_function

from isis_imaging import helper as h
from isis_imaging.core.algorithms import cor_interpolate
from isis_imaging.core.io import loader, saver
from isis_imaging.core.tools import importer
from isis_imaging.readme_creator import Readme

from isis_imaging.core.configurations import default_filtering
from isis_imaging.core.algorithms import size_calculator

from psutil import virtual_memory


def _print_expected_memory_usage(data_shape, dtype):
    h.tomo_print_note("Predicted memory usage for data: " +
                      str(size_calculator.full_size(data_shape, 0, dtype)) +
                      " MB, Total available on system: " + str(virtual_memory().total / 1024 / 1024) + " MB")


def initialise_run(config):
    saver_class = saver.Saver(config)

    h.initialise(config, saver_class)
    h.run_import_checks(config)
    h.check_config_integrity(config)

    # import early to check if tool is available
    tool = importer.timed_import(config)

    # create directory, or throw if not empty and no --overwrite-all
    # we get the output path from the saver, because
    # that expands variables and gets the absolute path
    saver.make_dirs_if_needed(saver_class.get_output_path(),
                              saver_class._overwrite_all)

    readme = Readme(config, saver_class)
    readme.begin(config.cmd_line, config)
    h.set_readme(readme)

    data_shape = loader.read_in_shape(config)

    _print_expected_memory_usage(data_shape, config.func.data_dtype)
    return saver_class, readme, tool


def end_run(readme):
    readme.end()


def execute(config):
    """
    Run the whole reconstruction. The steps in the process are:
        - load the data
        - do pre_processing on the data
        - (optional) save out pre_processing images
        - do the reconstruction with the appropriate tool
        - save out reconstruction images

    The configuration for pre_processing and reconstruction are read from
    the config parameter.

    :param config: A ReconstructionConfig with all the necessary parameters to
                   run a reconstruction.
    :param cmd_line: The full command line text if running from the CLI.
    """

    saver_class, readme, tool = initialise_run(config)

    sample, flat, dark = loader.load_from_config(config)

    sample, flat, dark = default_filtering.execute(config, sample, flat,
                                                   dark)

    saver_class.save_preproc_images(sample)
    if not config.func.reconstruction:
        h.tomo_print_note(
            "Skipping reconstruction because no --reconstruction flag was passed.")
        readme.end()
        return sample

    cors = config.func.cors
    # if they're the same length then we have a COR for each slice, so we don't have to generate anything
    if len(cors) != sample.shape[0]:
        # interpolate the CORs
        cor_slices = config.func.cor_slices
        config.func.cors = cor_interpolate.execute(sample.shape[0],
                                                   cor_slices, cors)

    sample = tool.run_reconstruct(sample, config)

    saver_class.save_recon_output(sample)
    end_run(readme)
    return sample
