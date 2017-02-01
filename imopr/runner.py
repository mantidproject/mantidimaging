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

    from recon.data import loader
    sample, flat, dark = loader.load_data(config, h)

    from recon.runner import pre_processing
    sample = pre_processing(config, sample, flat, dark)
    return action(sample, flat, dark, config, indices)


def get_function(str):
    if str == "recon":
        from imopr import recon
        return recon.execute
    if str == "sino":
        from imopr import sinogram
        return sinogram.execute
    if str == "show":
        from imopr import visualiser
        return visualiser.execute
