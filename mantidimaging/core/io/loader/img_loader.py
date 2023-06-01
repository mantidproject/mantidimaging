# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
"""
This module handles the loading of FIT, FITS, TIF, TIFF
"""
from typing import Tuple, Optional, List, Callable, Union, TYPE_CHECKING

from mantidimaging.core.data import ImageStack
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt
    from ...utility.data_containers import Indices


def execute(load_func: Callable[[str], np.ndarray],
            sample_path: List[str],
            img_format: str,
            dtype: 'npt.DTypeLike',
            indices: Union[List[int], Indices, None],
            progress: Optional[Progress] = None) -> ImageStack:
    """
    Reads a stack of images into memory, assuming dark and flat images
    are in separate directories.

    Usual type in fits is 16-bit pixel depth, data type is denoted with:
        '>i2' - uint16
        '>f2' - float16
        '>f4' - float32

    :returns: ImageStack object
    """
    if not sample_path:
        raise RuntimeError("No filenames were provided.")

    # The following codes assume that all images have the same size and properties as the first.
    # This is always true in the case of raw data
    first_sample_img = load_func(sample_path[0])

    # select the files loaded based on the indices, if any are provided
    chosen_input_filenames = sample_path[indices[0]:indices[1]:indices[2]] if indices else sample_path

    # get the shape of all images
    img_shape = first_sample_img.shape

    # forward all arguments to internal class for easy re-usage
    il = ImageLoader(load_func, img_format, img_shape, dtype, indices, progress)

    sample_data = il.load_sample_data(chosen_input_filenames)

    return ImageStack(sample_data, chosen_input_filenames, indices)


class ImageLoader(object):

    def __init__(self,
                 load_func: Callable[[str], np.ndarray],
                 img_format: str,
                 img_shape: Tuple[int, ...],
                 data_dtype: 'npt.DTypeLike',
                 indices: Union[List[int], Indices, None],
                 progress: Optional[Progress] = None):
        self.load_func = load_func
        self.img_format = img_format
        self.img_shape = img_shape
        self.data_dtype = data_dtype
        self.indices = indices
        self.progress = progress

    def load_sample_data(self, input_file_names: List[str]) -> pu.SharedArray:
        # determine what the loaded data was
        if len(self.img_shape) == 2:
            # the loaded file was a single image
            return self.load_files(input_file_names)
        else:
            raise ValueError("Data loaded has invalid shape: {0}", self.img_shape)

    def _do_files_load_seq(self, data: pu.SharedArray, files: List[str]) -> pu.SharedArray:
        progress = Progress.ensure_instance(self.progress, num_steps=len(files), task_name='Loading')

        with progress:
            for idx, in_file in enumerate(files):
                try:
                    data.array[idx, :] = self.load_func(in_file)
                    progress.update(msg='Image')
                except ValueError as exc:
                    raise ValueError("An image has different width and/or height "
                                     "dimensions! All images must have the same "
                                     "dimensions. Expected dimensions: {0} Error "
                                     "message: {1}".format(self.img_shape, exc))
                except IOError as exc:
                    raise RuntimeError("Could not load file {0}. Error details: "
                                       "{1}".format(in_file, exc))

        return data

    def load_files(self, files: List[str]) -> pu.SharedArray:
        # Zeroing here to make sure that we can allocate the memory.
        # If it's not possible better crash here than later.
        num_images = len(files)
        shape = (num_images, self.img_shape[0], self.img_shape[1])
        data = pu.create_array(shape, self.data_dtype)
        return self._do_files_load_seq(data, files)
