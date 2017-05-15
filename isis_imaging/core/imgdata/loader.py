from __future__ import absolute_import, division, print_function

import glob
import os

import numpy as np

import helper as h


def fitsread(filename):
    """
    Read one image and return it as a 2d numpy array

    :param filename :: name of the image file, can be relative or absolute path
    :param img_format: format of the image ('fits')
    """
    pyfits = import_pyfits()
    image = pyfits.open(filename)
    if len(image) < 1:
        raise RuntimeError(
            "Could not load at least one FITS image/table file from: {0}".
            format(filename))

    # get the image data
    return image[0].data


def nxsread(filename):
    import h5py
    nexus = h5py.File(filename, 'r')
    data = nexus["tomography/sample_data"]
    return data


def imread(filename):
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
    input_path = config.func.input_path
    img_format = config.func.in_format
    data_dtype = config.func.data_dtype
    cores = config.func.cores
    chunksize = config.func.chunksize
    parallel_load = config.func.parallel_load

    input_file_names = get_file_names(input_path, img_format)
    sample, flat, dark = load(input_path, None, None,
                              img_format, data_dtype, cores, chunksize,
                              parallel_load, indices=[0, 1])
    return (len(input_file_names),) + sample.shape[1:]


def load_data(config):
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


def load(input_path=None,
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
    :return: if flat and dark are loaded:
                a tuple with shape 3: (sample, flat, dark)
             if no flat and dark:
                a single 3d numpy ndarray
    """

    if img_format is None:
        # assume only images in directory, inb4 loading text files
        img_format = '*'

    if file_names is None:
        input_file_names = get_file_names(input_path, img_format)
    else:
        input_file_names = file_names

    if img_format in ['nxs']:
        from core.imgdata import stack_loader
        # pass only the first filename as we only expect a stack
        input_file = input_file_names[0]
        sample = stack_loader.execute(nxsread, input_file, dtype, "NXS Load",
                                      cores, chunksize, parallel_load, indices)
        flat = dark = None
    else:
        if img_format in ['fits', 'fit']:
            load_func = fitsread
        else:
            load_func = imread

        from core.imgdata import img_loader
        sample, flat, dark = img_loader.execute(
            load_func, input_file_names, input_path_flat, input_path_dark,
            img_format, dtype, cores, chunksize, parallel_load, indices)

    h.check_data_stack(sample)

    # don't return a tuple, just a single value
    if flat is None and dark is None:
        return sample

    return sample, flat, dark


def import_pyfits():
    try:
        import pyfits
    except ImportError:
        # In Anaconda python, the pyfits package is in a different place,
        # and this is what you frequently find on windows.
        try:
            import astropy.io.fits as pyfits
        except ImportError:
            raise ImportError(
                "Cannot find the package 'pyfits' which is required to "
                "read/write FITS image files")

    return pyfits


def import_skimage_io():
    """
    To import skimage io only when it is/can be used
    """
    try:
        from skimage import io as skio
        # tifffile works better on local, but not available on scarf
        # no plugin will use the default python imaging library (PIL)
        # This behaviour might need to be changed when switching to python 3
        skio.use_plugin('tifffile')
    except ImportError as exc:
        raise ImportError(
            "Could not find the package skimage, its subpackage "
            "io and the pluging freeimage which are required to support "
            "several image formats. Error details: {0}".format(exc))
    return skio


<<<<<<< Updated upstream
||||||| merged common ancestors
def get_file_extension(file):
    """
    >>> get_file_extension("/home/user/file_path.test")
    'test'
    >>> get_file_extension("/home/user/file.path.test")
    'test'
    >>> get_file_extension("/home/")  # oh boy I can't wait for this to fail miserably on windows

    # above is expecting a None which.. well doesn't show as anything so just an empty line with a comment explaining it
    """
    if os.path.isdir(file):
        return None

    # find the last dot in the file
    just_after_dot_index = file.rfind('.') + 1
    return file[just_after_dot_index:]


=======
def get_file_extension(file):
    """
    Return the extension of the parameter file. Uses string.rfind('.')
    >>> get_file_extension("/home/user/file_path.test")
    'test'
    >>> get_file_extension("/home/user/file.path.test")
    'test'
    >>> get_file_extension("/home/")  # line below is empty, because python doesnt print None for a None

    """
    if os.path.isdir(file):
        return None

    # find the last dot in the file
    just_after_dot_index = file.rfind('.') + 1
    return file[just_after_dot_index:]


>>>>>>> Stashed changes
def get_file_names(path, img_format, prefix=''):
    """
    Get all file names in a directory with a specific format.
    :param path: The path to be checked.
    :param img_format: The image format used as a postfix after the .
    :param prefix: A specific prefix for the images
    :return: All the file names, sorted by ascending
    """

    path = os.path.abspath(os.path.expanduser(path))

    files_match = glob.glob(
        os.path.join(path, "{0}*.{1}".format(prefix, img_format)))

    if len(files_match) <= 0:
        raise RuntimeError(
            "Could not find any image files in {0} with extension: {1}".format(
                path, img_format))

    # this is a necessary step, otherwise the file order is not guaranteed to be
    # sequential and we get randomly ordered stack of names
    files_match.sort(key=_alphanum_key_split)

    return files_match


def get_folder_names(path):
    """
    Get all folder names in a specific path.
    :param path: The path to be checked.
    :return: All the folder names, sorted by ascending
    """
    import os

    path = os.path.abspath(os.path.expanduser(path))

    folders = next(os.walk(path))[1]

    if len(folders) <= 0:
        raise RuntimeError("Could not find any folders in {0}".format(path))

    # this is a necessary step, otherwise the file order is not guaranteed to be
    # sequential and we get randomly ordered stack of names
    folders.sort(key=_alphanum_key_split)

    return folders


def _alphanum_key_split(path_str):
    """
    From a string to a list of alphabetic and numeric elements. Intended to
    be used for sequence number/natural sorting. In list.sort() the
    key can be a list, so here we split the alpha/numeric fields into
    a list. For example (in the final order after sort() would be applied):

    "angle4" -> ["angle", 4]
    "angle31" -> ["angle", 31]
    "angle42" -> ["angle", 42]
    "angle101" -> ["angle", 101]

    Several variants compared here:
    https://dave.st.germa.in/blog/2007/12/11/exception-handling-slow/
    """
    import re
    alpha_num_split_re = re.compile('([0-9]+)')
    return [
        int(c) if c.isdigit() else c
        for c in alpha_num_split_re.split(path_str)
    ]
