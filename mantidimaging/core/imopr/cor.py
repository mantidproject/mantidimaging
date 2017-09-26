from __future__ import absolute_import, division, print_function

import os
from logging import getLogger

from mantidimaging.core.algorithms import projection_angles
from mantidimaging.core.imopr import helper
from mantidimaging.core.io.saver import Saver
from mantidimaging.core.tools import importer


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    log = getLogger(__name__)

    log.info("Running IMOPR with action COR. This works ONLY with sinograms")

    tool = importer.timed_import(config)

    log.info("Calculating projection angles..")

    # developer note: we are processing sinograms,
    # but we need the number of radiograms
    num_radiograms = sample.shape[1]
    proj_angles = projection_angles.generate(config.func.max_angle,
                                             num_radiograms)

    initial_guess = config.func.cors if config.func.cors is not None else None

    num_slices = sample.shape[0]
    cors = helper.new_cor_array(num_slices)
    i1, i2, step = config.func.indices
    for i, actual_slice_index in zip(
            range(num_slices), range(i1, i2, step)):
        log.info("Running COR for index {}".format(actual_slice_index))
        cor = tool.find_center(
            tomo=sample,
            theta=proj_angles,
            sinogram_order=True,
            ind=i,
            init=initial_guess)
        log.info(cor)
        cors[i] = (actual_slice_index, cor[0])

    # Save COR data if output directory is provided
    saver = Saver(config)
    if saver.should_save_output():
        saver.make_dirs_if_needed(
                saver.get_output_path(), saver._overwrite_all)
        out_filename = os.path.join(saver.get_output_path(), 'cors.txt')
        helper.save_cors_to_file(out_filename, cors)

    return sample
