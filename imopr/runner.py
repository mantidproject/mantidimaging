from __future__ import (absolute_import, division, print_function)
import numpy as np


def execute(config):
    commands = config.func.imopr

    action = get_function(commands.pop())

    # the rest is a list of indices
    indices = [int(c) for c in commands]

    from recon.helper import Helper
    h = Helper(config)
    config.helper = h
    h.check_config_integrity(config)

    # from recon.data import loader
    # sample, flat, dark = loader.load_data(config, h)

    sample, flat, dark = loader.nxsread(
        'smb://files.scarf.rl.ac.uk/work/imat/RB1640003_nxs/out_preproc_image_stack.nxs')
    # from recon.runner import pre_processing
    # sample, flat, dark = pre_processing(config, sample, flat, dark)
    return action(sample, flat, dark, config, indices)


def get_function(string):
    if string == "recon":
        from imopr import recon
        return recon.execute
    if string == "sino":
        from imopr import sinogram
        return sinogram.execute
    if string == "show" or string == "vis":
        from imopr import visualiser
        return visualiser.execute
    if string == "cor":
        from imopr import cor
        return cor.execute
