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

import sys

from . import (  # noqa: F401
        exclusive_mem,
        shared_mem,
        two_shared_mem,
        utility)

"""
Replace the memory allocation function for subprocesses. In Python 2.7 this
would allocate the memory in RAM and then share it between the processes. This
was changed in Python 3.x to allocate a file that is used for shared memory.
The following code reverts that change back to the Python 2.7 behaviour.

The `mmap.mmap(-1, self.size)` is taken from the Python 2.7 source.
The source up to Python 3.6 function is this:

def __init__(self, size, fd=-1):
    self.size = size
    self.fd = fd
    if fd == -1:
        self.fd, name = tempfile.mkstemp(
             prefix='pym-%d-'%os.getpid(), dir=util.get_temp_dir())
        os.unlink(name)
        util.Finalize(self, os.close, (self.fd,))
        with open(self.fd, 'wb', closefd=False) as f:
            bs = 1024 * 1024
            if size >= bs:
                zeros = b'\0' * bs
                for _ in range(size // bs):
                    f.write(zeros)
                del zeros
            f.write(b'\0' * (size % bs))
            assert f.tell() == size
    self.buffer = mmap.mmap(self.fd, self.size)

On the line with open(...) python allocates the shared memory as a file.

This is the code from the bug issue at http://bugs.python.org/issue30919.

The performance testing that has been done with the fix (copied the code from
Python 3.7) seems to give the same performance as the Python 2.7.

It will be officially in Python when 3.7 is released.
"""

if sys.platform != 'win32':
    import mmap
    import multiprocessing.heap
    import tempfile
    import os
    import multiprocessing.util as util

    multiprocessing.heap.Arena._dir_candidates = ['/dev/shm']

    def _choose_dir(self, size):
        # Choose a non-storage backed directory if possible,
        # to improve performance
        for d in self._dir_candidates:
            st = os.statvfs(d)
            if st.f_bavail * st.f_frsize >= size:  # enough free space?
                return d
        return util.get_temp_dir()

    multiprocessing.heap.Arena._choose_dir = _choose_dir

    def ftruncate_allocation(self, size, fd=-1):
        self.size = size
        self.fd = fd
        if fd == -1:
            self.fd, name = tempfile.mkstemp(
                prefix='pym-%d-' % os.getpid(),
                dir=self._choose_dir(size))
            os.unlink(name)
            util.Finalize(self, os.close, (self.fd,))
            os.ftruncate(self.fd, size)
        self.buffer = mmap.mmap(self.fd, self.size)

    multiprocessing.heap.Arena.__init__ = ftruncate_allocation

del absolute_import, division, print_function
