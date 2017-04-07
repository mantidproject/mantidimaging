from __future__ import (absolute_import, division, print_function)

from core.imgdata import saver


def execute(config):
    """
    Converts images from one input format to another output format.

    :param config: The full ReconstructionConfig
    """

    output_dir = config.func.output_path
    image_out_format = config.func.out_format
    s = saver.Saver(config)
    # fail early if invalid directory
    saver.make_dirs_if_needed(s.get_output_path(), s._overwrite_all)

    from core.imgdata import loader
    sample, flat, dark = loader.load_data(config)

    # save out in the main output directory
    s.save(
        sample,
        output_dir,
        config.func.convert_prefix,
        config.func.swap_axes,
        image_out_format,
        zfill_len=0,
        indices=config.func.indices)
