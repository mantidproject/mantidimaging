from __future__ import (absolute_import, division, print_function)
import numpy as np


class ShapeSplitter(object):
    def __init__(self, shape, axis, dtype, max_mem, max_ratio=1):
        self.shape = shape
        self.axis = axis
        self.dtype = dtype
        self.max_mem = max_mem
        self.max_ratio = max_ratio

    def single_size(self, shape=None, axis=None):
        """
        Size of a single unit across the axis we are traversing.
        This does not take into account data type, it returns the pure size.

        To get bits from this, multiply by the data size.
        To get bytes, divide the bits by 8.
        To get the size of the whole dataset, multiply by the length axis (the one that we are traversing across).
        To get kilobytes, divide by 1024.
        To get megabytes, divide by 1024 again.
        """
        shape = self.shape if shape is None else shape
        axis = self.axis if axis is None else axis
        single = 1
        for i in range(len(shape)):
            if i == axis:
                continue
            single *= shape[i]

        return single

    def _determine_dtype_size(self, dtype=None):
        dtype = self.dtype if dtype is None else dtype
        if dtype in ['int16', 'float16', 'np.int16', 'np.float16', '16']\
                    or isinstance(dtype,np.int16) \
                    or isinstance(dtype,np.float16) \
                    or self.dtype is np.int16 \
                    or self.dtype is np.float16:

            return 16
        elif dtype in ['int32', 'float32', 'np.int32', 'np.float32','32'] \
                    or isinstance(dtype,np.int32) \
                    or isinstance(dtype,np.float32) \
                    or self.dtype is np.int32 \
                    or self.dtype is np.float32:
            return 32
        elif dtype in ['int64', 'float64', 'np.int64', 'np.float64', '64'] \
                    or isinstance(dtype,np.int64) \
                    or isinstance(dtype,np.float64) \
                    or self.dtype is np.int64 \
                    or self.dtype is np.float64:
            return 64

    def full_size(self, shape=None, axis=None, dtype=None):
        """
        Compute the full size of the data and return in Megabytes.

        If a parameter is not specified on call, the one provided at the class initialisation will be used!

        :param shape: The shape of the data for which the size will be calculated
        :param axis: The axis on which the shape is going to be traversed
        :param dtype: The data type

        """
        shape = self.shape if shape is None else shape
        axis = self.axis if axis is None else axis
        dtype = self.dtype if dtype is None else dtype

        mul = self._determine_dtype_size(dtype)

        single_size = self.single_size(shape, axis)
        # get the bits
        single_bits = single_size * mul
        # get the bytes
        single_bytes = single_bits / 8

        full_size_bytes = shape[axis] * single_bytes
        # convert to MB
        return full_size_bytes / 1024 / 1024

    def R(self, size, sinograms=True):
        # we are using sinograms, so the reconstructed shape will be exactly the same,
        # thus we double the size of the reconstruction
        ratio = size * 2 / self.max_mem
        return ratio

    def execute(self):
        assert self.axis < len(
            self.shape), "The required axis is outside the shape of the data!"

        # length will be the shape across the axis we're traversing
        length = self.shape[self.axis]

        # the size of a single object across the length axis
        single = self.single_size()

        print(
            "Single size of shape {0} on axis {1}: {2}\nTotal size: {3}\nAllowed memory: {4}"
            .format(self.shape, self.axis, single,
                    self.full_size(), self.max_mem))

        full_size = self.full_size()
        ratio = self.R(full_size)
        ratio = int(np.ceil(ratio))

        # if ratio is == 1 then numpy linspace returns just [0.] and a step of NaN
        if ratio <= 1:
            ratio += 1

        split, step = np.linspace(
            0, length, ratio, dtype=np.int32, retstep=True)
        new_shape = self.shape[:self.axis] + (int(step),
                                              ) + self.shape[self.axis + 1:]

        while self.R(self.full_size(new_shape)) > self.max_ratio:
            split, step = np.linspace(
                0, length, ratio, dtype=np.int32, retstep=True)
            new_shape = self.shape[:self.axis] + (
                int(step), ) + self.shape[self.axis + 1:]
            ratio += 1
            print("Step per reconstruction", step, "with a ratio to memory",
                  self.R(self.full_size(new_shape)), "indices", split)

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