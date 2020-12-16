# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os

# if debugging using PTVSD (used in VSCode), it is needed
# to change the multiprocess start method.
# See https://github.com/Microsoft/ptvsd/issues/1283
if os.environ.get("PTVSD_DEBUG", False):
    import multiprocessing

    multiprocessing.set_start_method('spawn', True)
