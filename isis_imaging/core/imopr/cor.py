from __future__ import (absolute_import, division, print_function)

from core.algorithms import projection_angles


def sanity_checks(config):
    indices = config.func.indices
    if len(indices) < 3:
        raise ValueError(
            "Indices must be provided! Please use the following format:\n "
            "--imopr cor <start> <end> <step> with numbers:\n "
            "--imopr cor 12 20 1, this will go from slice 12 to 20 with step 1")


def execute(sample, flat, dark, config, indices):
    from core.imopr import helper
    helper.print_start("Running IMOPR with action COR")

    from core.tools import importer
    tool = importer.timed_import(config)

    print("Calculating projection angles..")
    # developer note: we are processing sinograms,
    # but we need the number of radiograms
    num_radiograms = sample.shape[1]
    proj_angles = projection_angles.generate(config.func.max_angle,
                                             num_radiograms)

    print("Processing indices..")
    i1, i2, step = helper.handle_indices(indices, retstep=True)
    initial_guess = config.func.cors if config.func.cors is not None else None

    for i in range(i1, i2, step):
        print("Running COR for index", i, end=" ")
        cor = tool.find_center(
            tomo=sample[:, :, :],
            theta=proj_angles,
            sinogram_order=True,
            ind=i,
            init=initial_guess)
        print(cor)

    return sample
