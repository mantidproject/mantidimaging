from __future__ import absolute_import, division, print_function

import os

from logging import getLogger

from mantidimaging.core.imopr import helper
from mantidimaging.core.tools import importer
from mantidimaging.core.utility import projection_angles


def sanity_checks(config):
    if not config.func.output_path:
        raise ValueError(
            "The flag -o/--output-path MUST be passed for this COR mode!")

    if not len(config.func.indices) == 3:
        raise ValueError(
            "You need to provide input in the format:\n"
            "--indices <start> <stop> <step> --imopr <cors_start> <cors_end> <cors_step> corwrite: "
            "--indices 100 200 14 --imopr 5 50 7 corwrite\n"
            "To load and reconstruct every 14 indices from 100 to 200, with COR from 5 to 50, incrementing by 7."
        )


def execute(sample, flat, dark, config, indices):
    """
    :param sample: the sample must be in SINOGRAMS!
    :param flat: unused, only added to conform to interface.
    :param dark: unused, only added to conform to interface.
    :param config: the full reconstruction config
    :param indices: indices that will be processed in the function.
    """
    log = getLogger(__name__)

    log.info(
        "Running IMOPR with action COR using tomopy write_center. "
        "This works ONLY with sinograms!")

    tool = importer.timed_import(config)

    log.info("Calculating projection angles..")
    # developer note: we are processing sinograms,
    # but we need the number of radiograms
    num_radiograms = sample.shape[1]
    proj_angles = projection_angles.generate(config.func.max_angle,
                                             num_radiograms)

    i1, i2, step = config.func.indices
    log.info(indices)
    for i, actual_slice_index in zip(
            range(sample.shape[0]), range(i1, i2, step)):

        angle_output_path = os.path.join(config.func.output_path,
                                         str(actual_slice_index))

        log.info("Starting writing CORs for slice {0} in {1}".format(
            actual_slice_index, angle_output_path))

        tool._tomopy.write_center(
            tomo=sample,
            theta=proj_angles,
            dpath=angle_output_path,
            ind=i,
            sinogram_order=True,
            cen_range=indices[0:])

    log.info("Finished writing CORs in", config.func.output_path)
    return sample
