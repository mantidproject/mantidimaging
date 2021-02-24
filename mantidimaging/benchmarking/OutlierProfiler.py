import numpy as np
import cupy as cp

from mantidimaging.core.gpu import utility


class DummyProgress:
    def update(self):
        pass

    def mark_complete(self):
        pass


class OutlierProfiler:
    def __init__(self):
        """

        """
        self.dtype = "float32"
        self.cuda = utility.CudaExecuter(self.dtype)
        self.mode = "bright"
        self.progress = DummyProgress()
        self.diff = 0.5

    def run_outliers(self, filter_size: int, data: np.ndarray):
        """

        """
        with cp.cuda.profile():
            self.cuda.remove_outlier(data, self.diff, filter_size, self.mode, self.progress)
