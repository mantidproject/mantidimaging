from __future__ import absolute_import, division, print_function

from logging import getLogger

from mantidimaging.core.imopr import helper
from mantidimaging.core.tools import importer


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    log = getLogger(__name__)

    log.info("Running IMOPR with action COR using tomopy find_center_pc")

    tool = importer.timed_import(config)

    i1, i2, step = config.func.indices
    cor = tool._tomopy.find_center_pc(sample[0], sample[1])
    log.info(cor)

    return sample
