# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
from logging import getLogger
from typing import List, Union, Optional, Dict, Callable

import h5py
import numpy as np

from .utility import DEFAULT_IO_FILE_FORMAT
from ..data.dataset import StrictDataset
from ..data.imagestack import ImageStack
from ..operations.rescale import RescaleFilter
from ..utility.data_containers import Indices
from ..utility.progress_reporting import Progress

LOG = getLogger(__name__)

DEFAULT_ZFILL_LENGTH = 6
DEFAULT_NAME_PREFIX = 'image'
DEFAULT_NAME_POSTFIX = ''
INT16_SIZE = 65536


def write_fits(data: np.ndarray, filename: str, overwrite: bool = False, description: Optional[str] = ""):
    import astropy.io.fits as fits
    hdu = fits.PrimaryHDU(data)
    hdulist = fits.HDUList([hdu])
    hdulist.writeto(filename, overwrite=overwrite)


def write_img(data: np.ndarray, filename: str, overwrite: bool = False, description: Optional[str] = ""):
    from mantidimaging.core.utility.special_imports import import_skimage_io
    skio = import_skimage_io()
    skio.imsave(filename, data, description=description, metadata=None, software="Mantid Imaging")


def write_nxs(data: np.ndarray, filename: str, projection_angles: Optional[np.ndarray] = None, overwrite: bool = False):
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


def image_save(images: ImageStack,
               output_dir: str,
               name_prefix: str = DEFAULT_NAME_PREFIX,
               swap_axes: bool = False,
               out_format: str = DEFAULT_IO_FILE_FORMAT,
               overwrite_all: bool = False,
               custom_idx: Optional[int] = None,
               zfill_len: int = DEFAULT_ZFILL_LENGTH,
               name_postfix: str = DEFAULT_NAME_POSTFIX,
               indices: Union[List[int], Indices, None] = None,
               pixel_depth: Optional[str] = None,
               progress: Optional[Progress] = None) -> Union[str, List[str]]:
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
    min_value: float = np.nanmin(images.data)
    max_value: float = np.nanmax(images.data)
    int_16_slope = max_value / INT16_SIZE

    # Do rescale if needed.
    if pixel_depth is None or pixel_depth == "float32":
        rescale_params: Optional[Dict[str, Union[str, float]]] = None
        rescale_info = ""
    elif pixel_depth == "int16":
        # turn the offset to string otherwise json throws a TypeError when trying to save float32
        rescale_params = {"offset": str(min_value), "slope": int_16_slope}
        rescale_info = "offset = {offset} \n slope = {slope}".format(**rescale_params)
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
            write_func: Callable[[np.ndarray, str, bool, Optional[str]], None] = write_fits
        else:
            # pass all other formats to skimage
            write_func = write_img

        num_images = data.shape[0]
        progress.set_estimated_steps(num_images)

        names = generate_names(name_prefix, indices, num_images, custom_idx, zfill_len, name_postfix, out_format)

        for i in range(len(names)):
            names[i] = os.path.join(output_dir, names[i])

        with progress:
            for idx in range(num_images):
                # Overwrite images with the copy that has been rescaled.
                if pixel_depth == "int16":
                    write_func(
                        rescale_single_image(np.copy(images.data[idx]),
                                             min_input=min_value,
                                             max_input=max_value,
                                             max_output=INT16_SIZE - 1), names[idx], overwrite_all, rescale_info)
                else:
                    write_func(data[idx, :, :], names[idx], overwrite_all, rescale_info)

                progress.update(msg='Image')

        return names


def nexus_save(dataset: StrictDataset, path: str, sample_name: str):
    """
    Uses information from a StrictDataset to create a NeXus file.
    :param dataset: The dataset to save as a NeXus file.
    :param path: The NeXus file path.
    :param sample_name: The sample name.
    """
    try:
        with h5py.File(path, "w", driver="core") as nexus_file:
            _nexus_save(nexus_file, dataset, sample_name)
    except OSError:
        pass


def _nexus_save(nexus_file: h5py.File, dataset: StrictDataset, sample_name: str):

    # Top-level group
    entry = nexus_file.create_group("entry1")
    _set_nx_class(entry, "NXentry")

    # Tomo entry
    tomo_entry = entry.create_group("tomo_entry")
    _set_nx_class(tomo_entry, "NXsubentry")

    # definition field
    tomo_entry.create_dataset("definition", data=np.string_("NXtomo"))

    # instrument field
    instrument_group = tomo_entry.create_group("instrument")
    _set_nx_class(instrument_group, "NXinstrument")

    # instrument/detector field
    detector = instrument_group.create_group("detector")
    _set_nx_class(detector, "NXdetector")

    # instrument data
    combined_data = np.concatenate(dataset.nexus_arrays)
    detector.create_dataset("data", data=combined_data)
    detector.create_dataset("image_key", data=dataset.image_keys)

    # sample field
    sample_group = tomo_entry.create_group("sample")
    _set_nx_class(sample_group, "NXsample")
    sample_group.create_dataset("name", data=np.string_(sample_name))

    # rotation angle
    rotation_angle = sample_group.create_dataset("rotation_angle", data=np.concatenate(dataset.rotation_angles))
    rotation_angle.attrs["units"] = "rad"

    # data field
    data = tomo_entry.create_group("data")
    _set_nx_class(data, "NXdata")
    data["data"] = detector["data"]
    data["rotation_angle"] = rotation_angle
    data["image_key"] = detector["image_key"]


def _set_nx_class(group: h5py.Group, class_name: str):
    group.attrs["NX_class"] = np.string_(class_name)


def rescale_single_image(image: np.ndarray, min_input: float, max_input: float, max_output: float) -> np.ndarray:
    return RescaleFilter.filter_single_image(image, min_input, max_input, max_output, data_type=np.uint16)


def generate_names(name_prefix: str,
                   indices: Union[List[int], Indices, None],
                   num_images: int,
                   custom_idx: Optional[int] = None,
                   zfill_len: int = DEFAULT_ZFILL_LENGTH,
                   name_postfix: str = DEFAULT_NAME_POSTFIX,
                   out_format: str = DEFAULT_IO_FILE_FORMAT) -> List[str]:
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


def make_dirs_if_needed(dirname: Optional[str] = None, overwrite_all: bool = False):
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
