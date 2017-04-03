from __future__ import (absolute_import, division, print_function)
import numpy as np


def sanity_checks(config):
    if not config.func.output_path:
        raise ValueError(
            "The flag -o/--output-path MUST be passed for this COR mode!")

    if not len(config.func.indices) >= 4:
        raise ValueError(
            "You need to provide input in the format:\n"
            "--imopr <slice_idx> <cors_start> <cors_end> <cors_step>: "
            "--imopr 30 5 50 5 corwrite \n"
            "--imopr <idx_start> <idx_end> <cors_start> <cors_end> <cors_step>"
            ": --imopr 30 40 5 50 5 corwrite \n"
            "--imopr <idx_start> <idx_end> <idx_step> <cors_start> <cors_end>"
            "<cors_step>: --imopr 100 400 50 5 50 5 corwrite")


def execute(sample, flat, dark, config, indices):
    """
    :param sample:
    :param flat:
    :param dark:
    :param config:
    :param indices:
    """
    from core.imopr import helper
    helper.print_start(
        "Running IMOPR with action COR using tomopy write_center")

    from core.tools import importer
    tool = importer.timed_import(config)

    print("Calculating projection angles..")
    inc = float(config.func.max_angle) / sample.shape[0]
    proj_angles = np.arange(0, sample.shape[0] * inc, inc)
    proj_angles = np.radians(proj_angles)

    print("Processing indices..")
    i1, i2, step = helper.handle_indices(indices, retstep=True)
    import os
    for i in range(i1, i2, step):
        angle_output_path = os.path.join(config.func.output_path, str(i))
        print("Starting writing CORs for slice {0} in {1}".format(
            i, angle_output_path))
        tool._tomopy.write_center(
            tomo=sample,
            theta=proj_angles,
            dpath=angle_output_path,
            ind=i,
            sinogram_order=True,
            cen_range=indices[-3:])

    print("Finished writing CORs in", config.func.output_path)
    return sample
