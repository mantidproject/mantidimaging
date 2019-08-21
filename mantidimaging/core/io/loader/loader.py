from logging import getLogger

import numpy as np

from mantidimaging.core.io.loader import img_loader, stack_loader
from mantidimaging.core.io.utility import (DEFAULT_IO_FILE_FORMAT, get_file_names)
from mantidimaging.core.utility.progress_reporting import Progress

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
    from mantidimaging.core.utility.special_imports import import_skimage_io
    skio = import_skimage_io()
    return skio.imread(filename)


def supported_formats():
    # ignore errors for unused import/variable, we are only checking
    # availability
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

    try:
        import astropy.io.fits as fits  # noqa: F401
        fits_available = True
    except ImportError:
        fits_available = False

    avail_list = \
        (['nxs'] if h5nxs_available else []) + \
        (['fits', 'fit'] if fits_available else []) + \
        (['tif', 'tiff', 'png', 'jpg'] if skio_available else [])

    return avail_list


def read_in_shape(input_path,
                  in_prefix='',
                  in_format=DEFAULT_IO_FILE_FORMAT,
                  data_dtype=np.float32,
                  cores=None,
                  chunksize=None):
    input_file_names = get_file_names(input_path, in_format, in_prefix)
    images = load(input_path, None, None, in_prefix, in_format,
                  data_dtype, cores, chunksize, indices=[0, 1, 1], file_names=input_file_names)

    # construct and return the new shape
    return (len(input_file_names),) + images.sample.shape[1:]


def read_in_shape_from_config(config):
    """
    This function is intended for internal usage.

    Read in ONLY the first image in the specified directory, and return the
    total shape that all the images in that folder will have after loaded. This
    is determined by the number of images, and the loaded image's width and
    height.

    It is assumed all images are the same. If they are not the loader will fail
    on runtime.

    :param config: The reconstruction config from which the parameters are
                   read.

    :returns: The full shape of the images in the specified directory in a
              tuple of (Length, X, Y)
    """
    input_path = config.func.input_path
    in_prefix = config.func.in_prefix
    in_format = config.func.in_format
    data_dtype = config.func.data_dtype
    cores = config.func.cores
    chunksize = config.func.chunksize

    return read_in_shape(
        input_path, in_prefix, in_format, data_dtype, cores, chunksize)


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
    img_prefix = config.func.in_prefix
    img_format = config.func.in_format
    data_dtype = config.func.data_dtype
    cores = config.func.cores
    chunksize = config.func.chunksize
    parallel_load = config.func.parallel_load
    indices = config.func.indices
    construct_sinograms = config.func.construct_sinograms

    return load(input_path, input_path_flat, input_path_dark, img_prefix,
                img_format, data_dtype, cores, chunksize, parallel_load,
                indices=indices, construct_sinograms=construct_sinograms)


def load(input_path=None,
         input_path_flat=None,
         input_path_dark=None,
         in_prefix='',
         in_format=DEFAULT_IO_FILE_FORMAT,
         dtype=np.float32,
         cores=None,
         chunksize=None,
         parallel_load=False,
         file_names=None,
         indices=None,
         construct_sinograms=False,
         progress=None):
    """
    Loads a stack, including sample, white and dark images.

    :param input_path: Path for the input data folder

    :param input_path_flat: Optional: Path for the input Flat images folder

    :param input_path_dark: Optional: Path for the input Dark images folder

    :param in_prefix: Optional: Prefix for loaded files

    :param in_format: Default:'tiff', format for the input images

    :param dtype: Default:np.float32, data type for the input images

    :param cores: Default:None (max available), cores to be used if
                  parallel_load is True

    :param chunksize: Default:None (auto calculated), chunk of work per worker

    :param parallel_load: Default: False, if set to true the loading of the
                          data will be done in parallel.
                          This could be faster depending on the IO system.
                          For local runs (with HDD) recommended setting is
                          False

    :param file_names: Use provided file names for loading

    :param indices: Specify which indices are loaded from the found files.
                    This **DOES NOT** check for the number in the image
                    filename, but removes all indices from the filenames list
                    that are not selected

    :param construct_sinograms: The loaded images will be used to construct the
                                sinograms during loading

    :param progress: The progress reporting instance

    :return: a tuple with shape 3: (sample, flat, dark), if no flat and dark
             were loaded, they will be None
    """
    if in_format not in supported_formats():
        raise ValueError("Image format {0} not supported!".format(in_format))

    if indices and len(indices) < 3:
        raise ValueError(
            "Indices at this point MUST have 3 elements: [start, stop, step]!")

    if not file_names:
        input_file_names = get_file_names(input_path, in_format, in_prefix)
    else:
        input_file_names = file_names

    if in_format in ['nxs']:
        # pass only the first filename as we only expect a stack
        input_file = input_file_names[0]
        images = stack_loader.execute(_nxsread, input_file, dtype, "NXS Load",
                                      cores, chunksize, parallel_load, indices,
                                      progress)
    else:
        if in_format in ['fits', 'fit']:
            load_func = _fitsread
        else:
            load_func = _imread

        images = img_loader.execute(
            load_func, input_file_names, input_path_flat, input_path_dark,
            in_format, dtype, cores, chunksize, parallel_load, indices,
            construct_sinograms, progress)

    images.check_data_stack(images)

    # Search for and load metadata file
    metadata_filename = get_file_names(input_path, 'json', in_prefix,
                                       essential=False)
    metadata_filename = metadata_filename[0] if metadata_filename else None
    if metadata_filename:
        with open(metadata_filename) as f:
            images.metadata_load(f)
            LOG.debug('Loaded metadata from: {}'.format(metadata_filename))
    else:
        LOG.debug('No metadata file found')

    return images


def load_sinogram(input_path=None,
                  sinogram_number=0,
                  in_prefix='',
                  in_format=DEFAULT_IO_FILE_FORMAT,
                  dtype=np.float32,
                  progress=None):
    """
    This function is not be exposed to the CLI.

    It can only be accessed internally and through IPython interface.

    The reason is because this function will have a lot slower performance than
    the normal load.
    """
    progress = Progress.ensure_instance(progress,
                                        task_name='Sinogram Load')

    if in_format not in supported_formats():
        raise ValueError("Image format {0} not supported!".format(in_format))

    if in_format == 'nxs':
        raise NotImplementedError(
            "This functionality is not yet implemented for NXS files")

    input_file_names = get_file_names(input_path, in_format, in_prefix)

    num_images = len(input_file_names)
    progress.add_estimated_steps(num_images)

    sample_image = _imread(input_file_names[0])

    img_shape = sample_image.shape

    from mantidimaging.core.parallel import utility as pu

    # allocate memory for a single sinogram
    output_data = pu.create_shared_array(
        (1, num_images, img_shape[1]), dtype=dtype)

    LOG.info("Output data shape: {}".format(output_data.shape))

    with progress:
        for idx, input_file in enumerate(input_file_names):
            # read a single row from each projection, very wasteful but can
            # quickly create a sinogram
            loaded_image = _imread(input_file)
            output_data[0, idx, :] = loaded_image[:, sinogram_number]

            progress.update(msg='Loading sinogram {} of {}'.format(
                idx, num_images))

    return output_data
