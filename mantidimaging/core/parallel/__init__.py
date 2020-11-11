# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

"""
parallel.shared_mem: Runs a function in parallel.
                     Expects and uses a single 3D shared memory array between
                     the processes.
parallel.two_shared_mem: Runs a function in parallel.
                         Expects and uses two 3D shared memory arrays between
                         the processes.
parallel.exclusive_mem: Runs a function in parallel.
                         Uses a 3D memory array, but each process will copy the
                         piece of data it's processing, before processing it,
                         if the data is in any way read or modified, triggering
                         the copy-on-write.
"""

import os

from mantidimaging.core.parallel import shared_mem, two_shared_mem, utility  # noqa: F401

# if debugging using PTVSD (used in VSCode), it is needed
# to change the multiprocess start method.
# See https://github.com/Microsoft/ptvsd/issues/1283
if os.environ.get("PTVSD_DEBUG", False):
    import multiprocessing

    multiprocessing.set_start_method('spawn', True)
