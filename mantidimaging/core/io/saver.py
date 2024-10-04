# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import datetime
import os
from logging import getLogger
from typing import TYPE_CHECKING
from collections.abc import Callable

import h5py
from pathlib import Path

import numpy as np
from tifffile import tifffile

from mantidimaging.core.operation_history.const import TIMESTAMP
import astropy.io.fits as fits

from .utility import DEFAULT_IO_FILE_FORMAT, NEXUS_PROCESSED_DATA_PATH
from ..operations.rescale import RescaleFilter
from ..utility.progress_reporting import Progress
from ..utility.version_check import CheckVersion

if TYPE_CHECKING:
    from ..data.dataset import Dataset
    from ..data.imagestack import ImageStack
    from ..utility.data_containers import Indices

LOG = getLogger(__name__)

DEFAULT_ZFILL_LENGTH = 6
DEFAULT_NAME_PREFIX = 'image'
DEFAULT_NAME_POSTFIX = ''
INT16_SIZE = 65536

package_version = CheckVersion().get_version()


def write_fits(data: np.ndarray, filename: str, overwrite: bool = False, description: str | None = "") -> None:
    hdu = fits.PrimaryHDU(data)
    hdulist = fits.HDUList([hdu])
    hdulist.writeto(filename, overwrite=overwrite)


def write_img(data: np.ndarray, filename: str, overwrite: bool = False, description: str | None = "") -> None:
    tifffile.imwrite(filename, data, description=description, metadata=None, software="Mantid Imaging")


def write_nxs(data: np.ndarray,
              filename: str,
              projection_angles: np.ndarray | None = None,
              overwrite: bool = False) -> None:
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
               custom_idx: int | None = None,
               zfill_len: int = DEFAULT_ZFILL_LENGTH,
               name_postfix: str = DEFAULT_NAME_POSTFIX,
               indices: list[int] | Indices | None = None,
               pixel_depth: str | None = None,
               progress: Progress | None = None) -> list[str]:
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
        rescale_params: dict[str, str | float] | None = None
        rescale_info = ""
    elif pixel_depth == "int16":
        # turn the offset to string otherwise json throws a TypeError when trying to save float32
        rescale_params = {"offset": str(min_value), "slope": int_16_slope}
        rescale_info = "offset = {offset} \n slope = {slope}".format(**rescale_params)
    else:
        raise ValueError("The pixel depth given is not handled: " + pixel_depth)

    # Save metadata
    metadata_filename = os.path.join(output_dir, name_prefix + '.json')
    LOG.debug(f'Metadata filename: {metadata_filename}')
    with open(metadata_filename, 'w+') as f:
        images.save_metadata(f, rescale_params)

    data = images.data

    if swap_axes:
        data = np.swapaxes(data, 0, 1)

    if out_format in ['nxs']:
        filename = os.path.join(output_dir, name_prefix + name_postfix)
        write_nxs(data, filename + '.nxs', overwrite=overwrite_all)
        return [filename]
    else:
        if out_format in ['fit', 'fits']:
            write_func: Callable[[np.ndarray, str, bool, str | None], None] = write_fits
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
                    output_data = RescaleFilter.filter_array(np.copy(images.data[idx]),
                                                             min_input=min_value,
                                                             max_input=max_value,
                                                             max_output=INT16_SIZE - 1).astype(np.uint16)
                    write_func(output_data, names[idx], overwrite_all, rescale_info)
                else:
                    write_func(data[idx, :, :], names[idx], overwrite_all, rescale_info)

                progress.update(msg='Image')

        return names


def nexus_save(dataset: Dataset, path: str, sample_name: str, save_as_float: bool) -> None:
    """
    Uses information from a StrictDataset to create a NeXus file.
    :param dataset: The dataset to save as a NeXus file.
    :param path: The NeXus file path.
    :param sample_name: The sample name.
    """
    try:
        nexus_file = h5py.File(path, "w", driver="core")
    except OSError as exc:
        raise RuntimeError("Unable to save NeXus file. " + str(exc)) from exc

    try:
        _nexus_save(nexus_file, dataset, sample_name, save_as_float)
    except OSError as exc:
        nexus_file.close()
        os.remove(path)
        raise RuntimeError("Unable to save NeXus file. " + str(exc)) from exc

    nexus_file.close()


def _nexus_save(nexus_file: h5py.File, dataset: Dataset, sample_name: str, save_as_float: bool) -> None:
    """
    Takes a NeXus file and writes the StrictDataset information to it.
    :param nexus_file: The NeXus file.
    :param dataset: The StrictDataset.
    :param sample_name: The sample name.
    """
    # Top-level group
    entry = nexus_file.create_group("entry1")
    _set_nx_class(entry, "NXentry")

    # Tomo entry
    tomo_entry = entry.create_group("tomo_entry")
    _set_nx_class(tomo_entry, "NXsubentry")

    # definition field
    tomo_entry.create_dataset("definition", data=np.bytes_("NXtomo"))

    # instrument field
    instrument_group = tomo_entry.create_group("instrument")
    _set_nx_class(instrument_group, "NXinstrument")

    # instrument/detector field
    detector = instrument_group.create_group("detector")
    _set_nx_class(detector, "NXdetector")
    detector.create_dataset("image_key", data=dataset.image_keys)

    # sample field
    sample_group = tomo_entry.create_group("sample")
    _set_nx_class(sample_group, "NXsample")
    sample_group.create_dataset("name", data=np.bytes_(sample_name))

    # rotation angle
    rotation_angle = sample_group.create_dataset("rotation_angle", data=np.concatenate(dataset.nexus_rotation_angles))
    rotation_angle.attrs["units"] = "rad"

    if dataset.is_processed:
        _save_processed_data_to_nexus(nexus_file, dataset, rotation_angle, detector["image_key"], save_as_float)
    else:
        _save_image_stacks_to_nexus(dataset, detector, save_as_float)

    # data field
    data = tomo_entry.create_group("data")
    _set_nx_class(data, "NXdata")
    data["rotation_angle"] = rotation_angle
    data["image_key"] = detector["image_key"]

    for recon in dataset.recons:
        assert dataset.sample is not None
        assert dataset.sample.filenames is not None
        _save_recon_to_nexus(nexus_file, recon, dataset.sample.filenames[0])


def _save_processed_data_to_nexus(nexus_file: h5py.File, dataset: Dataset, rotation_angle: h5py.Dataset,
                                  image_key: h5py.Dataset, save_as_float: bool) -> None:
    data = nexus_file.create_group(NEXUS_PROCESSED_DATA_PATH)
    data["rotation_angle"] = rotation_angle
    data["image_key"] = image_key
    _set_nx_class(data, "NXdata")
    _save_image_stacks_to_nexus(dataset, data, save_as_float)

    process = data.create_group("process")
    _set_nx_class(process, "NXprocess")
    process.create_dataset("program", data=np.bytes_("Mantid Imaging"))
    process.create_dataset("date", data=np.bytes_(datetime.datetime.now().isoformat()))
    process.create_dataset("version", data=np.bytes_(package_version))


def _save_image_stacks_to_nexus(dataset: Dataset, data_group: h5py.Group, save_as_float: bool) -> None:
    combined_data_shape = (sum([len(arr) for arr in dataset.nexus_arrays]), ) + dataset.nexus_arrays[0].shape[1:]

    index = 0
    if save_as_float:
        data = dataset.nexus_arrays
        dtype = "float32"
    else:
        data, _ = _convert_float_to_int(dataset.nexus_arrays)
        dtype = "int16"

    data_group.create_dataset("data", shape=combined_data_shape, dtype=dtype)

    for arr in data:
        data_group["data"][index:index + arr.shape[0]] = arr
        index += arr.shape[0]


def _convert_float_to_int(arrays: list[np.ndarray]) -> tuple[list[np.ndarray], list[int]]:
    """
    Scales a float array to convert it to ints.
    :param arrays: The dataset arrays.
    :return: A list of int arrays and a list of scaling factors.
    """
    converted = []
    factors = []

    def scale_row(row):
        return np.round(row * scaling_factor).astype("int16")

    for arr in arrays:
        scaling_factor = np.iinfo("int16").max / max(abs(arr.min()), abs(arr.max()))
        scaled_arr = np.apply_along_axis(scale_row, axis=1, arr=arr)
        converted.append(scaled_arr)
        factors.append(scaling_factor)

    return converted, factors


def _save_recon_to_nexus(nexus_file: h5py.File, recon: ImageStack, sample_path: str) -> None:
    """
    Saves a recon to a NeXus file.
    :param nexus_file: The NeXus file.
    :param recon: The recon data.
    """
    recon_entry = nexus_file.create_group(recon.name)
    _set_nx_class(recon_entry, "NXentry")

    recon_entry.create_dataset("title", data=np.bytes_(recon.name))
    recon_entry.create_dataset("definition", data=np.bytes_("NXtomoproc"))

    instrument = recon_entry.create_group("INSTRUMENT")
    _set_nx_class(instrument, "NXinstrument")

    source = instrument.create_group("SOURCE")
    _set_nx_class(source, "NXsource")

    source.create_dataset("type", data=np.bytes_("Neutron source"))
    source.create_dataset("name", data=np.bytes_("ISIS"))
    source.create_dataset("probe", data=np.bytes_("neutron"))

    sample = recon_entry.create_group("SAMPLE")
    _set_nx_class(sample, "NXsample")
    sample.create_dataset("name", data=np.bytes_(recon.name))

    reconstruction = recon_entry.create_group("reconstruction")
    _set_nx_class(reconstruction, "NXprocess")

    reconstruction.create_dataset("program", data=np.bytes_("Mantid Imaging"))
    reconstruction.create_dataset("version", data=np.bytes_(package_version))
    recon_timestamp = recon.metadata.get(TIMESTAMP)
    if recon_timestamp is None:
        recon_timestamp = datetime.datetime.now().isoformat()
    reconstruction.create_dataset("date", data=np.bytes_(recon_timestamp))

    parameters = reconstruction.create_group("parameters")
    parameters.create_dataset("raw_file", data=np.bytes_(sample_path))

    data = recon_entry.create_group("data")
    _set_nx_class(data, "NXdata")

    data.create_dataset("data", shape=recon.data.shape, dtype="float32")
    data["data"][:] = recon.data

    x_arr, y_arr, z_arr = _create_pixel_size_arrays(recon)
    data.create_dataset("x", shape=x_arr.shape, dtype="float16", data=x_arr)
    data.create_dataset("y", shape=y_arr.shape, dtype="float16", data=y_arr)
    data.create_dataset("z", shape=z_arr.shape, dtype="float16", data=z_arr)


def _create_pixel_size_arrays(recon: ImageStack) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create the pixel size arrays for the NXtomproc x/y/z fields.
    :param recon: The recon data.
    :return: The tuple of the x/y/z arrays.
    """
    pixel_size = recon.pixel_size
    x_arr = np.arange(recon.data.shape[0]) * pixel_size
    y_arr = np.arange(recon.data.shape[1]) * pixel_size
    z_arr = np.arange(recon.data.shape[2]) * pixel_size
    return x_arr, y_arr, z_arr


def _set_nx_class(group: h5py.Group, class_name: str) -> None:
    """
    Sets the NX_class attribute of data in a NeXus file.
    :param group: The h5py group.
    :param class_name: The class name.
    """
    group.attrs["NX_class"] = np.bytes_(class_name)


def _rescale_recon_data(data: np.ndarray) -> np.ndarray:
    """
    Rescales recon data so that it can be converted to uint.
    :param data: The recon data.
    :return: The rescaled recon data.
    """
    min_value = np.min(data)
    if min_value < 0:
        data -= min_value
    data *= (np.iinfo("uint16").max / np.max(data))
    return data


def generate_names(name_prefix: str,
                   indices: list[int] | Indices | None,
                   num_images: int,
                   custom_idx: int | None = None,
                   zfill_len: int = DEFAULT_ZFILL_LENGTH,
                   name_postfix: str = DEFAULT_NAME_POSTFIX,
                   out_format: str = DEFAULT_IO_FILE_FORMAT) -> list[str]:
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


def make_dirs_if_needed(dirname: str | None = None, overwrite_all: bool = False) -> None:
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
        raise RuntimeError(f"The output directory is NOT empty:{path}\nThis can be "
                           "overridden by specifying 'Overwrite on name conflict'.")


def create_rits_format(tof: np.ndarray, transmission: np.ndarray, transmission_error: np.ndarray) -> str:
    """
    create a RITS format ready for exporting to a .dat file

    :param tof: time of flight
    :param transmission: transmission value
    :param transmission_error: transmission_error value
    :return: RITS format ascii

    """
    return '\n'.join(
        ['\t'.join([str(x) for x in row]) for row in zip(tof, transmission, transmission_error, strict=True)])


def export_to_dat_rits_format(rits_formatted_data: str, path: Path) -> None:
    """
    export a RITS formatted data to a .dat file

    :param rits_formatted_data: RITS formatted data
    :param path: path to save the .dat file
    :return: None

    """
    with path.open('w') as f:
        f.write(rits_formatted_data)
    LOG.info(f'RITS formatted data saved to: {path}')
