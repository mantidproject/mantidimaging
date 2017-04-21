from __future__ import (absolute_import, division, print_function)
from core.algorithms import projection_angles


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


def execute(data, flat, dark, config, indices):
    """
    :param data: the data must be in SINOGRAMS! 
    :param flat: unused, only added to conform to interface.
    :param dark: unused, only added to conform to interface.
    :param config: the full reconstruction config
    :param indices: indices that will be processed in the function.
    """
    from core.imopr import helper
    helper.print_start(
        "Running IMOPR with action COR using tomopy write_center. "
        "This works ONLY with sinograms!")

    from core.tools import importer
    tool = importer.timed_import(config)

    print("Calculating projection angles..")
    # developer note: we are processing sinograms,
    # but we need the number of radiograms
    num_radiograms = data.shape[1]
    proj_angles = projection_angles.generate(config.func.max_angle,
                                             num_radiograms)

    print("Processing indices..")
    i1, i2, step = helper.handle_indices(indices, retstep=True)
    import os
    for i in range(i1, i2, step):
        angle_output_path = os.path.join(config.func.output_path, str(i))
        print("Starting writing CORs for slice {0} in {1}".format(
            i, angle_output_path))
        tool._tomopy.write_center(
            tomo=data,
            theta=proj_angles,
            dpath=angle_output_path,
            ind=i,
            sinogram_order=True,
            cen_range=indices[-3:])

    print("Finished writing CORs in", config.func.output_path)
    return data
