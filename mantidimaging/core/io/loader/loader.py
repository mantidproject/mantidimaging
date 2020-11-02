from dataclasses import dataclass
from logging import getLogger
from typing import Tuple, List

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io.loader import img_loader
from mantidimaging.core.io.utility import (DEFAULT_IO_FILE_FORMAT, get_file_names)
from mantidimaging.core.utility.data_containers import ImageParameters
from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile

LOG = getLogger(__name__)


def _fitsread(filename):
    """
    Read one image and return it as a 2d numpy array

    :param filename :: name of the image file, can be relative or absolute path
    :param img_format: format of the image ('fits')
    """
    import astropy.io.fits as fits
    image = fits.open(filename)
    if len(image) < 1:
        raise RuntimeError("Could not load at least one FITS image/table file from: {0}".format(filename))

    # get the image data
    return image[0].data


def _nxsread(filename):
    import h5py
    nexus = h5py.File(filename, 'r')
    data = nexus["tomography/sample_data"]
    return data


def _imread(filename):
    from mantidimaging.core.utility.special_imports import import_skimage_io
    skio = import_skimage_io()
    return skio.imread(filename)


def supported_formats():
    # ignore errors for unused import/variable, we are only checking
    # availability

    try:
        from skimage import io as skio  # noqa: F401
        skio_available = True
    except ImportError:
        skio_available = False

    try:
        import astropy.io.fits as fits  # noqa: F401
        fits_available = True
    except ImportError:
        fits_available = False

    avail_list = \
        (['fits', 'fit'] if fits_available else []) + \
        (['tif', 'tiff'] if skio_available else [])

    return avail_list


@dataclass
class FileInformation:
    filenames: List[str]
    shape: Tuple[int, int, int]
    sinograms: bool


def read_in_file_information(input_path,
                             in_prefix='',
                             in_format=DEFAULT_IO_FILE_FORMAT,
                             data_dtype=np.float32) -> FileInformation:
    input_file_names = get_file_names(input_path, in_format, in_prefix)
    dataset = load(input_path,
                   in_prefix=in_prefix,
                   in_format=in_format,
                   dtype=data_dtype,
                   indices=[0, 1, 1],
                   file_names=input_file_names)
    images = dataset.sample

    # construct and return the new shape
    shape = (len(input_file_names), ) + images.data[0].shape
    images.free_memory()

    fi = FileInformation(filenames=input_file_names, shape=shape, sinograms=images.is_sinograms)
    return fi


def load_log(log_file) -> IMATLogFile:
    data = []
    with open(log_file, 'r') as f:
        for line in f:
            data.append(line.strip().split("   "))

    return IMATLogFile(data)


def load_p(parameters: ImageParameters, dtype, progress) -> Images:
    return load(input_path=parameters.input_path,
                in_prefix=parameters.prefix,
                in_format=parameters.format,
                indices=parameters.indices,
                dtype=dtype,
                progress=progress).sample


def load(input_path=None,
         input_path_flat_before=None,
         input_path_flat_after=None,
         input_path_dark_before=None,
         input_path_dark_after=None,
         in_prefix='',
         in_format=DEFAULT_IO_FILE_FORMAT,
         dtype=np.float32,
         file_names=None,
         indices=None,
         progress=None) -> Dataset:
    """

    Loads a stack, including sample, white and dark images.

    :param input_path: Path for the input data folder
    :param input_path_flat_before: Optional: Path for the input Flat Before images folder
    :param input_path_flat_after: Optional: Path for the input Flat After images folder
    :param input_path_dark_before: Optional: Path for the input Dark Before images folder
    :param input_path_dark_after: Optional: Path for the input Dark After images folder
    :param in_prefix: Optional: Prefix for loaded files
    :param in_format: Default:'tiff', format for the input images
    :param dtype: Default:np.float32, data type for the input images
    :param file_names: Use provided file names for loading
    :param indices: Specify which indices are loaded from the found files.
                    This **DOES NOT** check for the number in the image
                    filename, but removes all indices from the filenames list
                    that are not selected
    :param progress: The progress reporting instance
    :return: a tuple with shape 3: (sample, flat, dark), if no flat and dark
             were loaded, they will be None
    """
    if in_format not in supported_formats():
        raise ValueError("Image format {0} not supported!".format(in_format))

    if indices and len(indices) < 3:
        raise ValueError("Indices at this point MUST have 3 elements: [start, stop, step]!")

    if not file_names:
        input_file_names = get_file_names(input_path, in_format, in_prefix)
    else:
        input_file_names = file_names

    if in_format in ['nxs']:
        raise NotImplementedError("TODO this needs to be adapted to the new changes")
        # pass only the first filename as we only expect a stack
        # input_file = input_file_names[0]
        # images = stack_loader.execute(_nxsread, input_file, dtype, "NXS Load", indices, progress)
    else:
        if in_format in ['fits', 'fit']:
            load_func = _fitsread
        else:
            load_func = _imread

        dataset = img_loader.execute(load_func, input_file_names, input_path_flat_before, input_path_flat_after,
                                     input_path_dark_before, input_path_dark_after, in_format, dtype, indices, progress)

    # Search for and load metadata file
    metadata_found_filenames = get_file_names(input_path, 'json', in_prefix, essential=False)
    metadata_filename = metadata_found_filenames[0] if metadata_found_filenames else None
    if metadata_filename:
        with open(metadata_filename) as f:
            dataset.sample.load_metadata(f)
            LOG.debug('Loaded metadata from: {}'.format(metadata_filename))
    else:
        LOG.debug('No metadata file found')

    return dataset
