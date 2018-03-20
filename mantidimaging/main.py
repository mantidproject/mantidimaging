#!/usr/bin/env python

import argparse
import warnings
import logging

from mantidimaging import helper as h
from mantidimaging.core.utility.optional_imports import safe_import

formatwarning_orig = warnings.formatwarning
warnings.formatwarning = \
    lambda message, category, filename, lineno, line=None: \
    formatwarning_orig(message, category, filename, lineno, line='')


def startup_checks():
    tomopy = safe_import('tomopy')
    if tomopy is not None:
        ver = tomopy.__version__
        if ver != '1.1.2':
            raise RuntimeError(
                    'Unexpected TomoPy version {}, '
                    'please update Conda environment'.format(ver))


def parse_args():
    parser = argparse.ArgumentParser(description="Mantid Imaging GUI")

    parser.add_argument(
        "--log-level",
        type=str,
        default='INFO',
        help="Log verbosity level. "
             "Available options are: TRACE, DEBUG, INFO, WARN, CRITICAL")

    return parser.parse_args()


def main():
    args = parse_args()
    h.initialise_logging(logging.getLevelName(args.log_level))

    startup_checks()

    from mantidimaging import gui
    gui.execute()


if __name__ == '__main__':
    main()
