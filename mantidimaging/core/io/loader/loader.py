# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from typing import Tuple, List, Optional, Union, TYPE_CHECKING, Callable

import numpy as np
import astropy.io.fits as fits
from tifffile import tifffile

from mantidimaging.core.io.loader import img_loader
from mantidimaging.core.io.utility import (DEFAULT_IO_FILE_FORMAT, get_file_names,
                                           find_first_file_that_is_possibly_a_sample)
from mantidimaging.core.utility.data_containers import Indices, FILE_TYPES
from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile
from mantidimaging.core.io.filenames import FilenameGroup

if TYPE_CHECKING:
    import numpy.typing as npt
    from mantidimaging.core.data import ImageStack
    from mantidimaging.core.utility.progress_reporting import Progress

LOG = getLogger(__name__)

DEFAULT_IS_SINOGRAM = False
DEFAULT_PIXEL_SIZE = 0
DEFAULT_PIXEL_DEPTH = "float32"


@dataclass
class NewImageParameters:
    file_group: FilenameGroup
    log_file: Optional[Path] = None
    indices: Optional[Indices] = None


@dataclass
class NewLoadingParameters:
    image_stacks: dict[FILE_TYPES, NewImageParameters] = field(default_factory=dict)

    pixel_size: int = DEFAULT_PIXEL_SIZE
    name: str = ""
    dtype: str = DEFAULT_PIXEL_DEPTH
    sinograms: bool = DEFAULT_IS_SINOGRAM


def _fitsread(filename: str) -> np.ndarray:
    """
    Read one image and return it as a 2d numpy array

    :param filename :: name of the image file, can be relative or absolute path
    :param img_format: format of the image ('fits')
    """
    image = fits.open(filename)
    if len(image) < 1:
        raise RuntimeError("Could not load at least one FITS image/table file from: {0}".format(filename))

    # get the image data
    return image[0].data


def _imread(filename: str) -> np.ndarray:
    return tifffile.imread(filename)


def supported_formats() -> List[str]:
    return ['fits', 'fit', 'tif', 'tiff']


def get_loader(in_format: str) -> Callable[[str], np.ndarray]:
    if in_format in ['fits', 'fit']:
        load_func = _fitsread
    elif in_format in ['tiff', 'tif']:
        load_func = _imread
    else:
        raise NotImplementedError("Loading not implemented for:", in_format)
    return load_func


@dataclass
class FileInformation:
    filenames: List[str]
    shape: Tuple[int, int, int]
    sinograms: bool


def read_in_file_information(input_path: str,
                             in_prefix: str = '',
                             in_format: str = DEFAULT_IO_FILE_FORMAT,
                             data_dtype: 'npt.DTypeLike' = np.float32) -> FileInformation:
    input_file_names = get_file_names(input_path, in_format, in_prefix)
    image_stack = load(input_path,
                       in_prefix=in_prefix,
                       in_format=in_format,
                       dtype=data_dtype,
                       indices=[0, 1, 1],
                       file_names=input_file_names)

    # construct and return the new shape
    shape: Tuple[int, int, int] = (len(input_file_names), ) + image_stack.data[0].shape

    fi = FileInformation(filenames=input_file_names, shape=shape, sinograms=image_stack.is_sinograms)
    return fi


def load_log(log_file: Path) -> IMATLogFile:
    with open(log_file, 'r') as f:
        return IMATLogFile(f.readlines(), log_file)


def load_stack_from_group(group: FilenameGroup, progress: Optional[Progress] = None) -> ImageStack:
    file_names = [str(p) for p in group.all_files()]
    return load(file_names=file_names, progress=progress)


def load_stack_from_image_params(image_params: NewImageParameters,
                                 progress: Optional[Progress] = None,
                                 dtype: npt.DTypeLike = np.float32):
    file_names = [str(p) for p in image_params.file_group.all_files()]
    return load(file_names=file_names, progress=progress, dtype=dtype, indices=image_params.indices)


def load(input_path: Optional[str] = None,
         in_prefix: str = '',
         in_format: str = DEFAULT_IO_FILE_FORMAT,
         dtype: 'npt.DTypeLike' = np.float32,
         file_names: Optional[List[str]] = None,
         indices: Optional[Union[List[int], Indices]] = None,
         progress: Optional[Progress] = None) -> ImageStack:
    """

    Loads a stack, including sample, white and dark images.

    :param input_path: Path for the input data folder
    :param in_prefix: Optional: Prefix for loaded files
    :param in_format: Default:'tiff', format for the input images
    :param dtype: Default:np.float32, data type for the input images
    :param file_names: Use provided file names for loading
    :param indices: Specify which indices are loaded from the found files.
                    This **DOES NOT** check for the number in the image
                    filename, but removes all indices from the filenames list
                    that are not selected
    :param progress: The progress reporting instance
    :return: an ImageStack
    """
    if indices and len(indices) < 3:
        raise ValueError("Indices at this point MUST have 3 elements: [start, stop, step]!")

    if not file_names:
        input_file_names = get_file_names(input_path, in_format, in_prefix)
    else:
        input_file_names = file_names

    load_func = get_loader(in_format)

    image_stack = img_loader.execute(load_func, input_file_names, in_format, dtype, indices, progress)

    # Search for and load metadata file
    metadata_found_filenames = get_file_names(input_path, 'json', in_prefix, essential=False)
    metadata_filename = metadata_found_filenames[0] if metadata_found_filenames else None
    if metadata_filename:
        with open(metadata_filename) as f:
            image_stack.load_metadata(f)
            LOG.debug('Loaded metadata from: {}'.format(metadata_filename))
    else:
        LOG.debug('No metadata file found')

    return image_stack


def create_loading_parameters_for_file_path(file_path: Path) -> Optional[NewLoadingParameters]:
    sample_file = find_first_file_that_is_possibly_a_sample(str(file_path))
    if sample_file is None:
        return None

    loading_parameters = NewLoadingParameters()
    loading_parameters.name = os.path.basename(sample_file)

    sample_fg = FilenameGroup.from_file(sample_file)
    sample_fg.find_all_files()
    sample_fg.find_log_file()
    loading_parameters.image_stacks[FILE_TYPES.SAMPLE] = NewImageParameters(sample_fg, sample_fg.log_path)

    for file_type in [ft for ft in FILE_TYPES if ft.mode in ["images", "180"]]:
        fg = sample_fg.find_related(file_type)
        if fg is None:
            continue

        fg.find_all_files()
        if file_type.tname == "Flat":
            fg.find_log_file()
        loading_parameters.image_stacks[file_type] = NewImageParameters(fg, fg.log_path)

    return loading_parameters
