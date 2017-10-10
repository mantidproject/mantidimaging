#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import sys
import warnings

from mantidimaging import helper as h
from mantidimaging.core.configs import recon_config

formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: \
    formatwarning_orig(message, category, filename, lineno, line='')


def check_version_info():
    python_version = sys.version_info
    if python_version < (2, 7, 0):
        raise RuntimeError(
            "Not running this script as it requires Python >= 2.7. "
            "Version found: {0}".format(python_version))


def main(default_args):
    h.initialise_logging()
    check_version_info()

    config = recon_config.grab_full_config(default_args)

    h.set_logging_from_config(config)

    if config.func.debug and config.func.debug_port:
        import pydevd
        pydevd.settrace(
            'localhost',
            port=config.func.debug_port,
            stdoutToServer=True,
            stderrToServer=True)

    cmd_line = " ".join(sys.argv)
    # dynamically attach the parameter used in recon
    config.cmd_line = cmd_line
    if config.func.gui:
        # this has the highest priority
        from mantidimaging import gui
        thingy_to_execute = gui.execute
    elif config.func.imopr:
        from mantidimaging.core.imopr import imopr
        thingy_to_execute = imopr.execute
    elif config.func.aggregate:
        from mantidimaging.core.aggregate import aggregate
        thingy_to_execute = aggregate.execute
    elif config.func.convert:
        from mantidimaging.core.convert import convert
        thingy_to_execute = convert.execute
    elif config.func.process_list:
        from mantidimaging.core.configurations import process_list_run
        thingy_to_execute = process_list_run.execute
    else:
        from mantidimaging.core.configurations import default_run
        thingy_to_execute = default_run.execute

    h.total_execution_timer()
    if not config.func.split:
        res = thingy_to_execute(config)
    else:
        from mantidimaging.core.utility import execution_splitter
        res = execution_splitter.execute(config, thingy_to_execute)
    h.total_execution_timer()

    return res


def cli_main():
    main(None)


def gui_main():
    main(['-i', '.', '--gui'])


if __name__ == '__main__':
    main()
