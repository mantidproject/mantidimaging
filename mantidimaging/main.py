#!/usr/bin/env python
# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import argparse
import sys
import warnings
import os

import darkdetect
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from PyQt5.QtGui import QGuiApplication, QFont, QFontInfo

import mantidimaging.core.parallel.manager as pm

from mantidimaging import helper as h
from mantidimaging.core.utility.command_line_arguments import CommandLineArguments

formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: formatwarning_orig(
    message, category, filename, lineno, line="")

settings = QtCore.QSettings('mantidproject', 'Mantid Imaging')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mantid Imaging GUI")

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Log verbosity level. "
        "Available options are: DEBUG, INFO, WARN, CRITICAL",
    )

    parser.add_argument("--version", action="store_true", help="Print version number and exit.")

    parser.add_argument("--path", type=str, help="Comma separated Paths with no spaces for the data you wish to load.")
    parser.add_argument("--operation", type=str, help="The initial operation to run on the dataset.")
    parser.add_argument("--recon",
                        default=False,
                        action='store_true',
                        help="Opens the reconstruction window at start up.")
    parser.add_argument("-sv",
                        "--spectrum_viewer",
                        default=False,
                        action='store_true',
                        help="Opens the spectrum viewer window at start up.")
    parser.add_argument("-lv",
                        "--live_viewer",
                        type=str,
                        help="Path of directory to watch for new files in live viewer.")

    return parser.parse_args()


def setup_application() -> QApplication:
    QGuiApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    q_application = QApplication(sys.argv)

    default_font = QFont()
    default_font_info = QFontInfo(default_font)

    extra_style_default = {

        # Density Scale
        'density_scale': '-5',

        # font
        'font_size': str(default_font.pointSize()) + 'px',
    }
    settings.setValue('extra_style_default', extra_style_default)
    if settings.value('extra_style') is None:
        settings.setValue('extra_style', extra_style_default)

    settings.setValue('os_theme', darkdetect.theme())
    settings.setValue('default_font_size', str(default_font.pointSize()))
    settings.setValue('default_font_family', str(default_font_info.family()))

    q_application.setApplicationName("Mantid Imaging")
    q_application.setOrganizationName("mantidproject")
    q_application.setOrganizationDomain("mantidproject.org")
    if sys.platform == 'win32':
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"
    return q_application


def main() -> None:
    args = parse_args()
    # Print version number and exit
    if args.version:
        from mantidimaging import __version__ as version_no

        print(version_no)
        return

    q_application = setup_application()

    path = args.path if args.path else ""
    operation = args.operation if args.operation else ""

    CommandLineArguments(path=path,
                         operation=operation,
                         show_recon=args.recon,
                         show_live_viewer=args.live_viewer,
                         show_spectrum_viewer=args.spectrum_viewer)

    h.initialise_logging(args.log_level)

    settings = QSettings()
    process_count = settings.value("multiprocessing/process_count", 8, type=int)

    from mantidimaging import gui
    try:
        pm.create_and_start_pool(process_count)
        gui.execute()
        result = q_application.exec_()
    except BaseException as e:
        if sys.platform == 'linux':
            pm.clear_memory_from_current_process_linux()
        raise e
    finally:
        pm.end_pool()

    return result


if __name__ == "__main__":
    main()
