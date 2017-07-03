from __future__ import absolute_import, division, print_function

import os

from isis_imaging.core.algorithms import cor_interpolate
from isis_imaging.core.configurations.default_run import initialise_run, end_run
from isis_imaging.core import process_list
from isis_imaging.core.io import loader


def execute(config):
    saver_class, readme, tool = initialise_run(config)
    sample, flat, dark = loader.load_from_config(config)

    if os.path.isfile(config.func.process_list):
        pl = process_list.load(config.func.process_list)
    else:
        pl = process_list.from_string(config.func.process_list)

    if not config.func.reconstruction:
        while not pl.is_over():
            process_list.execute(next(pl), sample)
        saver_class.save_preproc_images(sample)
    else:  # run reconstruction
        _do_reconstruction(sample, config, pl)
        saver_class.save_recon_output(sample)

    end_run(readme)
    return sample


def _do_reconstruction(sample, config, pl):
    cors = config.func.cors
    # if they're the same length then we have a COR for each slice, so we don't have to generate anything
    if len(cors) != sample.shape[0]:
        # interpolate the CORs
        cor_slices = config.func.cor_slices
        config.func.cors = cor_interpolate.execute(sample.shape[0], cor_slices, cors)
    while not pl.is_over():
        process_list.execute(next(pl), sample, config)
    return sample