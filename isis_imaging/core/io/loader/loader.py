from __future__ import absolute_import, division, print_function

import numpy as np

from isis_imaging import helper as h
from isis_imaging.core.io.utility import get_file_names

from . import img_loader, stack_loader


def _fitsread(filename):
    """
    Read one image and return it as a 2d numpy array

    :param filename :: name of the image file, can be relative or absolute path
    :param img_format: format of the image ('fits')
    """
    from .imports import import_pyfits
    pyfits = import_pyfits()
    image = pyfits.open(filename)
    if len(image) < 1:
        raise RuntimeError(
            "Could not load at least one FITS image/table file from: {0}".
            format(filename))

    # get the image data
    return image[0].data


def _nxsread(filename):
    import h5py
    nexus = h5py.File(filename, 'r')
    data = nexus["tomography/sample_data"]
    return data


def _imread(filename):
    from .imports import import_skimage_io
    skio = import_skimage_io()
    return skio.imread(filename)


def supported_formats():
    # ignore errors for unused import (F401), we are only checking availability
    try:
        import h5py  # noqa: F401
        h5nxs_available = True
    except ImportError:
        h5nxs_available = False

    try:
        from skimage import io as skio  # noqa: F401
        skio_available = True
    except ImportError:
        skio_available = False

    avail_list = \
        (['nxs'] if h5nxs_available else []) + \
        (['fits', 'fit', 'tif', 'tiff', 'png', 'jpg'] if skio_available else [])

    return avail_list


def read_in_shape(config):
    """
    This function is intended for internal usage.

    Read in ONLY the first image in the specified directory, and return the total shape
    that all the images in that folder will have after loaded. This is determined by the
    number of images, and the loaded image's width and height.

    It is assumed all images are the same. If they are not the loader will fail on runtime.

    :param config: The reconstruction config from which the parameters are read.

    :returns: The full shape of the images in the specified directory in a tuple of (Length, X, Y)
    """
    input_path = config.func.input_path
    img_format = config.func.in_format
    data_dtype = config.func.data_dtype
    cores = config.func.cores
    chunksize = config.func.chunksize
    parallel_load = config.func.parallel_load

    input_file_names = get_file_names(input_path, img_format)
    sample, _, _ = load(input_path, None, None,
                        img_format, data_dtype, cores, chunksize,
                        parallel_load, indices=[0, 1, 1])

    # construct and return the new shape
    return (len(input_file_names),) + sample.shape[1:]


def load_from_config(config):
    """
    Load data by reading the provided configuration file for paths.
    This is intended to be used internally within the scripts.

    :param config: The full reconstruction config

    :return: the loaded data as a tuple (sample, flat, dark)
    """

    input_path = config.func.input_path
    input_path_flat = config.func.input_path_flat
    input_path_dark = config.func.input_path_dark
    img_format = config.func.in_format
    data_dtype = config.func.data_dtype
    cores = config.func.cores
    chunksize = config.func.chunksize
    parallel_load = config.func.parallel_load
    indices = config.func.indices

    return load(input_path, input_path_flat, input_path_dark,
                img_format, data_dtype, cores, chunksize,
                parallel_load, indices=indices)


def load(input_path,
         input_path_flat=None,
         input_path_dark=None,
         img_format=None,
         dtype=np.float32,
         cores=None,
         chunksize=None,
         parallel_load=False,
         file_names=None,
         indices=None):
    """
    Loads a stack, including sample, white and dark images.


    :param input_path: Path for the input data folder

    :param input_path_flat: Optional: Path for the input Flat images folder

    :param input_path_dark: Optional: Path for the input Dark images folder

    :param img_format: Default:'fits', format for the input images

    :param dtype: Default:np.float32, data type for the input images

    :param cores: Default:None (max available), cores to be used if
                  parallel_load is True

    :param chunksize: Default:None (auto calculated), chunk of work per worker

    :param parallel_load: Default: False, if set to true the loading of the data
                          will be done in parallel.
                          This could be faster depending on the IO system.
                          For local runs (with HDD) recommended setting is False

    :param file_names: Use provided file names for loading
    :param indices: Specify which indices are loaded from the found files. 
                    This **DOES NOT** check for the number in the image filename, 
                    but removes all indices from the filenames list that are not selected

    :return: a tuple with shape 3: (sample, flat, dark), if no flat and dark were loaded, they will be None
    """
    if img_format not in supported_formats():
        raise ValueError("Image format " + img_format + " not supported!")

    if indices and len(indices) < 3:
        raise ValueError(
            "Indices at this point MUST have 3 elements: [start, stop, step]!")

    if not file_names:
        input_file_names = get_file_names(input_path, img_format)
    else:
        input_file_names = file_names

    if img_format in ['nxs']:
        # pass only the first filename as we only expect a stack
        input_file = input_file_names[0]
        sample = stack_loader.execute(_nxsread, input_file, dtype, "NXS Load",
                                      cores, chunksize, parallel_load, indices)
        flat = dark = None
    else:
        if img_format in ['fits', 'fit']:
            load_func = _fitsread
        else:
            load_func = _imread

        sample, flat, dark = img_loader.execute(
            load_func, input_file_names, input_path_flat, input_path_dark,
            img_format, dtype, cores, chunksize, parallel_load, indices)

    h.check_data_stack(sample)

    return sample, flat, dark
