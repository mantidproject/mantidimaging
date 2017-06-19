from __future__ import absolute_import, division, print_function

import numpy as np

from isis_imaging import helper as h
from isis_imaging.core.algorithms import cor_interpolate
from isis_imaging.core.io import loader, saver
from isis_imaging.core.tools import importer
from isis_imaging.readme_creator import Readme

from isis_imaging.core.configurations import default_preprocessing, default_postprocessing


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

    result = loader.load_from_config(config)
    if isinstance(result, np.ndarray):
        sample = result
        flat = None
        dark = None
    else:
        sample, flat, dark = result

    sample, flat, dark = default_preprocessing.execute(config, sample, flat,
                                                       dark)

    # Save pre-proc images, print inside
    saver_class.save_preproc_images(sample)
    if config.func.only_preproc:
        h.tomo_print_note("Only pre-processing run, exiting.")
        readme.end()
        return sample

    if not config.func.only_postproc:
        cors = config.func.cors
        # if they're the same length then we have a COR for each slice!
        if len(cors) != sample.shape[0]:
            # interpolate the CORs
            cor_slices = config.func.cor_slices
            config.func.cors = cor_interpolate.execute(sample.shape[0],
                                                       cor_slices, cors)

        sample = tool.run_reconstruct(sample, config)
    else:
        h.tomo_print_note("Only post-processing run, skipping reconstruction.")

    sample = default_postprocessing.execute(config, sample)

    saver_class.save_recon_output(sample)
    readme.end()
    return sample
