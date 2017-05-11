from __future__ import absolute_import, division, print_function

from core.imopr import helper
from core.tools import importer


def sanity_checks(config):
    pass


def execute(sample, flat, dark, config, indices):
    helper.print_start("Running IMOPR with action COR")

    tool = importer.timed_import(config)

    i1, i2, step = config.func.indices

    for i, actual_slice_index in zip(
            range(sample.shape[0]), range(i1, i2, step)):
        print("Running COR for index", actual_slice_index, end=" ")
        cor = tool.find_center_vo(
            tomo=sample,
            ind=i,
            ratio=1.,
            smin=0,
            smax=200,
            srad=10,
            step=2,
            drop=0)
        print(cor)

    return sample
