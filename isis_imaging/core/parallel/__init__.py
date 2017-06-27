from __future__ import (absolute_import, division, print_function)
__doc__ = """
parallel.shared_mem: Runs a function in parallel.
                     Expects and uses a single 3D shared memory array between the processes.
parallel.two_shared_mem: Runs a function in parallel.
                         Expects and uses two 3D shared memory arrays between the processes.
parallel.exclusive_mem: Runs a function in parallel.
                         Uses a 3D memory array, but each process will copy the piece of data
                         it's processing, before processing it, if the data is in any way read
                         or modified, triggering the copy-on-write.
"""

from . import *  # noqa: F401, F403
