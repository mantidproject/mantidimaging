from __future__ import (absolute_import, division, print_function)

from core.imgdata import saver
from core.imgdata import loader


def execute(config):
    """
    Converts images from one input format to another output format.

    :param config: The full ReconstructionConfig
    """

    output_dir = config.func.output_path
    image_out_format = config.func.out_format
    # fail early if invalid directory
    saver.make_dirs_if_needed(output_dir, config.func.overwrite_all)

    sample, flat, dark = loader.load_data(config)

    # save out in the main output directory
    saver.save(
        sample,
        output_dir,
        config.func.convert_prefix,
        config.func.swap_axes,
        image_out_format,
        zfill_len=0,
        indices=config.func.indices)
