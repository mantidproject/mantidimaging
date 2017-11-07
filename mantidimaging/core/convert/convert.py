from __future__ import (absolute_import, division, print_function)

from mantidimaging.core.io import saver
from mantidimaging.core.io import loader


def execute(config):
    """
    Converts images from one input format to another output format.
    This module only works on the -i/--input-path input images!

    :param config: The full ReconstructionConfig
    """

    output_dir = config.func.output_path
    image_out_format = config.func.out_format

    # force no loading of dark and flat
    config.func.input_path_dark = None
    config.func.input_path_flat = None

    # fail early if invalid directory
    saver.make_dirs_if_needed(output_dir, config.func.overwrite_all)

    images = loader.load_from_config(config)

    # save out in the main output directory
    saver.save(
        images.sample,
        output_dir,
        config.func.convert_prefix,
        config.func.swap_axes,
        image_out_format,
        zfill_len=0,
        indices=config.func.indices,
        overwrite_all=config.func.overwrite_all)
