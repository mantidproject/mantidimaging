#!/usr/bin/env python
# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import argparse
import logging
import sys
import warnings
import mantidimaging.core.parallel.manager as pm

from mantidimaging import helper as h
from mantidimaging.core.utility.command_line_arguments import CommandLineArguments

formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: formatwarning_orig(
    message, category, filename, lineno, line="")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mantid Imaging GUI")

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Log verbosity level. "
        "Available options are: TRACE, DEBUG, INFO, WARN, CRITICAL",
    )

    parser.add_argument("--version", action="store_true", help="Print version number and exit.")

    parser.add_argument("--path", type=str, help="Comma separated Paths with no spaces for the data you wish to load.")
    parser.add_argument("--operation", type=str, help="The initial operation to run on the dataset.")
    parser.add_argument("--recon",
                        default=False,
                        action='store_true',
                        help="Opens the reconstruction window at start up.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Print version number and exit
    if args.version:
        from mantidimaging import __version__ as version_no

        print(version_no)
        return

    path = args.path if args.path else ""
    operation = args.operation if args.operation else ""

    CommandLineArguments(path=path, operation=operation, show_recon=args.recon)

    h.initialise_logging(logging.getLevelName(args.log_level))

    from mantidimaging import gui
    try:
        pm.create_and_start_pool()
        gui.execute()
    except BaseException as e:
        if sys.platform == 'linux':
            pm.clear_memory_from_current_process_linux()
        raise e
    finally:
        pm.end_pool()


if __name__ == "__main__":
    main()
