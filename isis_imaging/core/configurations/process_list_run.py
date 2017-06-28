from __future__ import absolute_import, division, print_function

from isis_imaging.core.configurations.default_run import initialise_run, end_run, load_data
from isis_imaging.core import process_list


def execute(config):
    saver_class, readme, tool = initialise_run(config)
    sample, flat, dark = load_data(config)
    pl = process_list.from_string(config.func.process_list)
    while pl:
        # TODO fix the loader confusing behaviour
        # TODO add nice documentation with return types
        # TODO do the things from ONENOTE!
        process_list.execute()
    end_run(readme)
