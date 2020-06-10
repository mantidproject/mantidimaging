"""
This module handles the loading of FIT, FITS, TIF, TIFF
"""
from typing import List, Tuple, Union

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.io.utility import get_file_names
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from . import stack_loader


def execute(load_func, sample_path, flat_path, dark_path, img_format, dtype, indices, progress=None):
    """
    Reads a stack of images into memory, assuming dark and flat images
    are in separate directories.

    If several files are found in the same directory (for example you
    give image0001.fits and there's also image0002.fits,
    image0003.fits) these will also be loaded as the usual convention
    in ImageJ and related imaging tools, using the last digits to sort
    the images in the stack.

    Usual type in fits is 16-bit pixel depth, data type is denoted with:
        '>i2' - uint16
        '>f2' - float16
        '>f4' - float32

    :returns: Images object
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

    # we load the flat and dark first, because if they fail we don't want to
    # fail after we've loaded a big stack into memory
    flat_avg, flat_filenames, flat_mfname = il.load_data(flat_path)
    dark_avg, dark_filenames, dark_mfname = il.load_data(dark_path)
    sample_data, sample_mfname = il.load_sample_data(chosen_input_filenames)

    return Images(sample_data, flat_avg, dark_avg, chosen_input_filenames, indices, flat_filenames, dark_filenames,
                  sample_memory_file_name=sample_mfname,
                  flat_memory_file_name=flat_mfname,
                  dark_memory_file_name=dark_mfname)


class ImageLoader(object):
    def __init__(self, load_func, img_format, img_shape, data_dtype, indices, progress=None):
        self.load_func = load_func
        self.img_format = img_format
        self.img_shape = img_shape
        self.data_dtype = data_dtype
        self.indices = indices
        self.progress = progress

    def load_sample_data(self, input_file_names):
        # determine what the loaded data was
        if len(self.img_shape) == 2:
            memory_file_name = pu.create_shared_name(input_file_names[0])
            # the loaded file was a single image
            sample_data = self.load_files(input_file_names, memory_file_name), memory_file_name
        elif len(self.img_shape) == 3:
            # the loaded file was a file containing a stack of images
            sample_data = stack_loader.execute(self.load_func,
                                               input_file_names[0],
                                               self.data_dtype,
                                               "Sample",
                                               self.indices,
                                               progress=self.progress)
        else:
            raise ValueError("Data loaded has invalid shape: {0}", self.img_shape)

        return sample_data

    def load_data(self, file_path) -> Union[Tuple[np.ndarray, List[str], str], Tuple[None, None, None]]:
        if file_path:
            file_names = get_file_names(file_path, self.img_format)
            memory_file_name = pu.create_shared_name(file_names[0])
            return self.load_files(file_names, memory_file_name), file_names, memory_file_name
        return None, None, None

    def _do_files_load_seq(self, data, files, name):
        num_images = len(files)
        progress = Progress.ensure_instance(self.progress, num_steps=len(files), task_name=f'Load {name}')

        with progress:
            for idx, in_file in enumerate(files):
                try:
                    data[idx, :] = self.load_func(in_file)
                    progress.update(msg='Image {} of {}'.format(idx, num_images))
                except ValueError as exc:
                    raise ValueError("An image has different width and/or height "
                                     "dimensions! All images must have the same "
                                     "dimensions. Expected dimensions: {0} Error "
                                     "message: {1}".format(self.img_shape, exc))
                except IOError as exc:
                    raise RuntimeError("Could not load file {0}. Error details: " "{1}".format(in_file, exc))

        return data

    def load_files(self, files, memory_name=None) -> np.ndarray:
        # Zeroing here to make sure that we can allocate the memory.
        # If it's not possible better crash here than later.
        num_images = len(files)
        shape = (num_images, self.img_shape[0], self.img_shape[1])
        data = pu.create_shared_array(memory_name, shape, self.data_dtype)
        return self._do_files_load_seq(data, files, memory_name)


def _get_data_average(data):
    return np.mean(data, axis=0)
