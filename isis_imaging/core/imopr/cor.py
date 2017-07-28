from __future__ import absolute_import, division, print_function

from isis_imaging.core.algorithms import projection_angles
from isis_imaging.core.imopr import helper
from isis_imaging.core.tools import importer


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    helper.print_start(
        "Running IMOPR with action COR. This works ONLY with sinograms")

    tool = importer.timed_import(config)

    print("Calculating projection angles..")

    # developer note: we are processing sinograms,
    # but we need the number of radiograms
    num_radiograms = sample.shape[1]
    proj_angles = projection_angles.generate(config.func.max_angle,
                                             num_radiograms)

    initial_guess = config.func.cors if config.func.cors is not None else None

    i1, i2, step = config.func.indices
    for i, actual_slice_index in zip(
            range(sample.shape[0]), range(i1, i2, step)):
        print("Running COR for index", actual_slice_index, end=" ")
        cor = tool.find_center(
            tomo=sample,
            theta=proj_angles,
            sinogram_order=True,
            ind=i,
            init=initial_guess)
        print(cor)

    return sample
