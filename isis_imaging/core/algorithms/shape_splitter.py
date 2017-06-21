from __future__ import (absolute_import, division, print_function)
import numpy as np

from isis_imaging.core.algorithms import size_calc


class ShapeSplitter(object):
    def __init__(self,
                 shape,
                 axis,
                 dtype,
                 max_mem,
                 max_ratio=1,
                 no_recon=False):
        self.shape = shape
        self.axis = axis
        self.dtype = dtype
        self.max_mem = max_mem
        self.max_ratio = max_ratio
        self.no_recon = no_recon

    def R(self, size, sinograms=True):
        # we are using sinograms, so the reconstructed shape will be exactly the same,
        # thus we double the size of the reconstruction
        if self.no_recon:
            ratio = size / self.max_mem
        else:
            ratio = size * 2 / self.max_mem
        return ratio

    def execute(self):
        assert self.axis < len(
            self.shape), "The required axis is outside the shape of the data!"

        # length will be the shape across the axis we're traversing
        length = self.shape[self.axis]

        # the size of a single object across the length axis
        single = size_calc.single_size(self.shape, self.axis)

        def func_full_size(shape): return size_calc.full_size(
            shape, self.axis, self.dtype)
        full_size = func_full_size(self.shape)

        print(
            "Single size of shape {0} on axis {1}: {2}\nTotal size: {3}\nAllowed memory: {4}"
            .format(self.shape, self.axis, single, full_size, self.max_mem))

        ratio = self.R(full_size)
        ratio = int(np.ceil(ratio))

        # if ratio is == 1 then numpy linspace returns just [0.] and a step of NaN
        if ratio <= 1:
            ratio += 1

        split, step = np.linspace(
            0, length, ratio, dtype=np.int32, retstep=True)

        # build the new shape around the axis we're traversing
        # if we're traversing along axis 0, with a shape (15,300,400)
        # this will create the new shape (step, 300, 400). If we're
        # traversing along axis 1, then it will be (15, step, 400)
        new_shape = self.shape[:self.axis] + \
            (int(step),) + self.shape[self.axis + 1:]

        while self.R(func_full_size(new_shape)) > self.max_ratio:
            split, step = np.linspace(
                0, length, ratio, dtype=np.int32, retstep=True)

            new_shape = self.shape[:self.axis] + \
                (int(step), ) + self.shape[self.axis + 1:]

            # same reason as in the if statement
            ratio += 1
            print("Step per reconstruction", step, "with a ratio to memory",
                  self.R(func_full_size(new_shape)), "indices", split)

        return split, step


if __name__ == '__main__':
    import sys
    axis_0 = int(sys.argv[1])
    axis_1 = int(sys.argv[2])
    axis_2 = int(sys.argv[3])
    max_mem = int(sys.argv[4])
    max_ratio = float(sys.argv[5])
    dtype = str(sys.argv[6])
    s = ShapeSplitter(
        (axis_0, axis_1, axis_2), 0, dtype, max_mem, max_ratio=max_ratio)
    print(s.calc())
