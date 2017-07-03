from __future__ import absolute_import, division, print_function

from isis_imaging.core.configurations.default_run import initialise_run, end_run
from isis_imaging.core import process_list
from isis_imaging.core.io import loader


def execute(config):
    saver_class, readme, tool = initialise_run(config)
    sample, flat, dark = loader.load_from_config(config)

    pl = process_list.from_string(config.func.process_list)
    while not pl.is_over():
        process_list.execute(next(pl), sample)
    end_run(readme)
