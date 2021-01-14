# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
from logging import getLogger
from typing import List, Union

import numpy as np

from .utility import DEFAULT_IO_FILE_FORMAT
from ..data.images import Images
from ..operations.rescale import RescaleFilter
from ..utility.progress_reporting import Progress

LOG = getLogger(__name__)

DEFAULT_ZFILL_LENGTH = 6
DEFAULT_NAME_PREFIX = 'image'
DEFAULT_NAME_POSTFIX = ''
INT16_SIZE = 65536


def write_fits(data, filename, overwrite=False):
    import astropy.io.fits as fits
    hdu = fits.PrimaryHDU(data)
    hdulist = fits.HDUList([hdu])
    hdulist.writeto(filename, clobber=overwrite)


def write_img(data, filename, overwrite=False):
    from mantidimaging.core.utility.special_imports import import_skimage_io
    skio = import_skimage_io()
    skio.imsave(filename, data)


def write_nxs(data, filename, projection_angles=None, overwrite=False):
    import h5py
    nxs = h5py.File(filename, 'w')

    # appending flat and dark images is disabled for now
    # new shape to account for appending flat and dark images
    # correct_shape = (data.shape[0] + 2, data.shape[1], data.shape[2])

    dset = nxs.create_dataset("tomography/sample_data", data.shape)
    dset[:data.shape[0]] = data[:]
    # left here if we decide to start appending the flat and dark images again
    # dset[-2] = flat[:]
    # dset[-1] = dark[:]

    if projection_angles is not None:
        rangle = nxs.create_dataset("tomography/rotation_angle", data=projection_angles)
        rangle[...] = projection_angles


def save(images: Images,
         output_dir,
         name_prefix=DEFAULT_NAME_PREFIX,
         swap_axes=False,
         out_format=DEFAULT_IO_FILE_FORMAT,
         overwrite_all=False,
         custom_idx=None,
         zfill_len=DEFAULT_ZFILL_LENGTH,
         name_postfix=DEFAULT_NAME_POSTFIX,
         indices=None,
         pixel_depth=None,
         progress=None) -> Union[str, List[str]]:
    """
    Save image volume (3d) into a series of slices along the Z axis.
    The Z axis in the script is the ndarray.shape[0].

    :param images: Data as images/slices stores in numpy array
    :param output_dir: Output directory for the files
    :param name_prefix: Prefix for the names of the images,
           appended before the image number
    :param swap_axes: Swap the 0 and 1 axis of the images
           (convert from radiograms to sinograms on saving)
    :param out_format: File format of the saved out images
    :param overwrite_all: Overwrite existing images with conflicting names
    :param custom_idx: Single index to be used for the file name,
           instead of incremental numbers
    :param zfill_len: This option is ignored if custom_idx is specified!
           Prepend zeros to the output file names to have a
           constant file name length. Example:
           - saving out an image with zfill_len = 6:
           saved_image000001,...saved_image000201 and so on
           - saving out an image with zfill_len = 3:
           saved_image001,...saved_image201 and so on
    :param name_postfix: Postfix for the name after the index
    :param indices: Only works if custom_idx is not specified.
           Specify the start and end range of the indices
           which will be used for the file names.
    :param progress: Passed to ensure progress during saving is tracked properly
    :param pixel_depth: Defines the target pixel depth of the save operation so
           np.float32 or np.int16 will ensure the values are scaled
           correctly to these values.
    :returns: The filename/filenames of the saved data.
    """
    progress = Progress.ensure_instance(progress, task_name='Save')

    # expand the path for plugins that don't do it themselves
    output_dir = os.path.abspath(os.path.expanduser(output_dir))
    make_dirs_if_needed(output_dir, overwrite_all)

    # Define current parameters
    min_value = np.nanmin(images.data)
    max_value = np.nanmax(images.data)
    int_16_slope = max_value / INT16_SIZE

    # Do rescale if needed.
    if pixel_depth is None or pixel_depth == "float32":
        rescale_params = None
    elif pixel_depth == "int16":
        # turn the offset to string otherwise json throws a TypeError when trying to save float32
        rescale_params = {"offset": str(min_value), "slope": int_16_slope}
    else:
        raise ValueError("The pixel depth given is not handled: " + pixel_depth)

    # Save metadata
    metadata_filename = os.path.join(output_dir, name_prefix + '.json')
    LOG.debug('Metadata filename: {}'.format(metadata_filename))
    with open(metadata_filename, 'w+') as f:
        images.save_metadata(f, rescale_params)

    data = images.data

    if swap_axes:
        data = np.swapaxes(data, 0, 1)

    if out_format in ['nxs']:
        filename = os.path.join(output_dir, name_prefix + name_postfix)
        write_nxs(data, filename + '.nxs', overwrite=overwrite_all)
        return filename
    else:
        if out_format in ['fit', 'fits']:
            write_func = write_fits
        else:
            # pass all other formats to skimage
            write_func = write_img

        num_images = data.shape[0]
        progress.set_estimated_steps(num_images)

        names = generate_names(name_prefix, indices, num_images, custom_idx, zfill_len, name_postfix, out_format)

        for i in range(len(names)):
            names[i] = os.path.join(output_dir, names[i])

        with progress:
            min_value = images.data.min()
            for idx in range(num_images):
                # Overwrite images with the copy that has been rescaled.
                if pixel_depth == "int16":
                    write_func(
                        rescale_single_image(np.copy(images.data[idx]),
                                             min_input=min_value,
                                             max_input=max_value,
                                             max_output=INT16_SIZE - 1), names[idx], overwrite_all)
                else:
                    write_func(data[idx, :, :], names[idx], overwrite_all)

                progress.update(msg='Image')

        return names


def rescale_single_image(image: np.ndarray, min_input: float, max_input: float, max_output: float):
    return RescaleFilter.filter_single_image(image, min_input, max_input, max_output, data_type=np.uint16)


def generate_names(name_prefix,
                   indices,
                   num_images,
                   custom_idx=None,
                   zfill_len=DEFAULT_ZFILL_LENGTH,
                   name_postfix=DEFAULT_NAME_POSTFIX,
                   out_format=DEFAULT_IO_FILE_FORMAT):
    start_index = indices[0] if indices else 0
    if custom_idx:
        index = custom_idx
        increment = 0
    else:
        index = int(start_index)
        increment = indices[2] if indices else 1

    names = []
    for _ in range(num_images):
        # create the file name, and use the format as extension
        names.append(name_prefix + '_' + str(index).zfill(zfill_len) + name_postfix + "." + out_format)
        index += increment
    return names


def make_dirs_if_needed(dirname=None, overwrite_all=False):
    """
    Makes sure that the directory needed (for example to save a file)
    exists, otherwise creates it.

    :param dirname :: (output) directory to check
    """
    if dirname is None:
        return

    path = os.path.abspath(os.path.expanduser(dirname))

    if not os.path.exists(path):
        os.makedirs(path)
    elif os.listdir(path) and not overwrite_all:
        raise RuntimeError("The output directory is NOT empty:{0}\nThis can be "
                           "overridden by specifying 'Overwrite on name conflict'.".format(path))


class Saver(object):
    """
    This class doesn't have any try: ... except: ... because when called
    it's usually at an end point, where there would be no point in recovering.

    However if the directory in which the output should be written out does
    not exist, it will be created on the first call of make_dirs_if_needed.

    This class should always fail early before any
    expensive operations have been attempted.
    """
    @staticmethod
    def supported_formats():
        # reuse supported formats, they currently share them
        from mantidimaging.core.io.loader import supported_formats
        return supported_formats()

    def __init__(self, config):
        self._output_path = config.func.output_path
        if self._output_path is not None:
            self._output_path = os.path.abspath(os.path.expanduser(self._output_path))

        self._out_format = config.func.out_format
        self._overwrite_all = config.func.overwrite_all
        self._swap_axes = config.func.swap_axes
        self._indices = config.func.indices

        self._preproc_dir = config.func.preproc_subdir
        self._save_preproc = config.func.save_preproc

        self._out_slices_prefix = config.func.out_slices_prefix
        self._out_horiz_slices_prefix = config.func.out_horiz_slices_prefix
        self._out_horiz_slices_subdir = config.func.out_horiz_slices_subdir
        self._save_horiz_slices = config.func.save_horiz_slices

        # assign package functions for ease of access
        self.save = save
        self.make_dirs_if_needed = make_dirs_if_needed

    def should_save_output(self):
        return self._output_path is not None

    def get_output_path(self):
        return self._output_path

    def save_single_image(self,
                          data,
                          subdir=None,
                          name='saved_image',
                          swap_axes=False,
                          custom_index=None,
                          zfill_len=0,
                          name_postfix='',
                          use_preproc_folder=True,
                          progress=None):
        """
        Save a single image to a single image file.
        THIS SHOULD NOT BE USED WITH A 3D STACK OF IMAGES.

        :param subdir: Specify an additional subdirectory
               inside the output directory
        :param data: Data volume with pre-processed images
        :param name: Image name to be appended
        :param custom_index: Index that will be appended at the end of the image filename
        :param zfill_len: Prepend zeros to the output file names to have a
               constant file name length. Example:
               - saving out an image with zfill_len = 6:
               saved_image000001,...saved_image000201 and so on
               - saving out an image with zfill_len = 3:
               saved_image001,...saved_image201 and so on
        :param name_postfix: String to be appended after the zero fill.
               This is not recommended and might confuse
               imaging programs (including this script) as to
               the order of the images, and they could
               end up not loading all of the images.
        """
        assert data.ndim == 2, \
            "This should not be used with a 3D stack of images!"

        progress = Progress.ensure_instance(progress, task_name='Save Image')

        # reshape so that it works with the internals
        data = data.reshape(1, data.shape[0], data.shape[1])
        if self._output_path is None:
            LOG.info("Not saving a single image, " "because no output path is specified.")
            return

        # using the config's output dir
        if use_preproc_folder:
            output_dir = os.path.join(self._output_path, self._preproc_dir)
        else:
            output_dir = self._output_path

        if subdir is not None:
            # using the provided subdir
            output_dir = os.path.join(output_dir, subdir)
            output_dir = os.path.abspath(output_dir)

        with progress:
            progress.update(msg="Saving single image {0} dtype: {1}".format(output_dir, data.dtype))

            save(data,
                 output_dir,
                 name,
                 swap_axes,
                 out_format=self._out_format,
                 overwrite_all=self._overwrite_all,
                 zfill_len=zfill_len,
                 name_postfix=name_postfix,
                 custom_idx=custom_index,
                 indices=self._indices)

    def save_preproc_images(self, data, progress=None):
        """
        Specialised save function to save out the pre-processed images.

        This will save the images out in a subdir /pre-processed/.

        :param data: The pre-processed data that will be saved
        """
        progress = Progress.ensure_instance(progress, task_name='Save Preprocessed')

        if self._save_preproc and self._output_path is not None:
            preproc_dir = os.path.join(self._output_path, self._preproc_dir)

            with progress:
                progress.update(msg="Saving all pre-processed images into {0} "
                                "dtype: {1}".format(preproc_dir, data.dtype))

                save(data,
                     preproc_dir,
                     'out_preproc_image',
                     self._swap_axes,
                     self._out_format,
                     self._overwrite_all,
                     indices=self._indices)

    def save_recon_output(self, data, progress=None):
        """
        Specialised method to save out the reconstructed data
        depending on the configuration options.

        This will save out the data in a subdirectory /reconstructed/.
        If --save-horiz-slices is specified, the axis will be flipped and
        the result will be saved out in /reconstructed/horiz.
        ^ This means that the data usage will double as
        numpy.swapaxes WILL COPY AND DOUBLE the data!

        :param data: Reconstructed data volume that will be saved out.
        """
        progress = Progress.ensure_instance(progress, task_name='Save Reconstruction')

        if self._output_path is None:
            LOG.warning("Not saving reconstruction output, " "because no output path is specified.")
            return

        out_recon_dir = os.path.join(self._output_path, 'reconstructed')

        with progress:
            progress.update(msg="Starting saving slices of the reconstructed "
                            "volume in: {0}...".format(out_recon_dir))

            save(data,
                 out_recon_dir,
                 self._out_slices_prefix,
                 self._swap_axes,
                 self._out_format,
                 self._overwrite_all,
                 indices=self._indices)

            # Sideways slices:
            if self._save_horiz_slices:
                out_horiz_dir = os.path.join(out_recon_dir, self._out_horiz_slices_subdir)

                LOG.info("Saving horizontal slices in: {0}".format(out_horiz_dir))

                # save out the horizontal slices by flipping the axes
                save(data, out_horiz_dir, self._out_horiz_slices_prefix, not self._swap_axes, self._out_format,
                     self._overwrite_all)
