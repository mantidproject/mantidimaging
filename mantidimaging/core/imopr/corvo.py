from __future__ import absolute_import, division, print_function

from logging import getLogger

from mantidimaging.core.imopr import helper
from mantidimaging.core.tools import importer


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    log = getLogger(__name__)

    log.info("Running IMOPR with action COR")

    tool = importer.timed_import(config)

    i1, i2, step = config.func.indices

    for i, actual_slice_index in zip(
            range(sample.shape[0]), range(i1, i2, step)):
        log.info("Running COR for index {}".format(actual_slice_index))
        cor = tool.find_center_vo(
            tomo=sample,
            ind=i,
            ratio=1.,
            smin=0,
            smax=200,
            srad=10,
            step=2,
            drop=0)
        log.info(cor)

    return sample
