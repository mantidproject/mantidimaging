from __future__ import absolute_import, division, print_function

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

from . import exclusive_mem, shared_mem, two_shared_mem, utility  # noqa: F401

"""
Replace the memory allocation function for subprocesses. In Python 2.7 this would allocate the memory in RAM and then
share it between the processes. This was changed in Python 3.x to allocate a file that is used for shared memory.
The following code reverts that change back to the Python 2.7 behaviour. 

The `mmap.mmap(-1, self.size)` is taken from the Python 2.7 source.
The Python 3.x source function is this:

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

multiprocessing.set_start_method() supports multiple methods, this change will break any code 
that uses the 'spawn' or 'forkserver' start methods. Currently they are not used anywhere in the package, but it
is noted as a precaution.
"""
import mmap
import sys

if sys.platform != 'win32':
    import multiprocessing.heap


    def allocate_in_ram(self, size, fd=-1):
        self.size = size
        self.fd = fd
        self.buffer = mmap.mmap(-1, self.size)


    # monkey patch the old behaviour
    multiprocessing.heap.Arena.__init__ = allocate_in_ram

del absolute_import, division, print_function
