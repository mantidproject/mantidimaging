# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING
from collections.abc import Callable

import numpy as np
import astropy.io.fits as fits
from tifffile import tifffile

from mantidimaging.core.io.instrument_log import InstrumentLog, ShutterCount
from mantidimaging.core.io.loader import img_loader
from mantidimaging.core.io.utility import find_first_file_that_is_possibly_a_sample
from mantidimaging.core.utility.data_containers import Indices, FILE_TYPES, ProjectionAngles
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
class ImageParameters:
    """
    Dataclass to hold info about an image stack that is to be loaded. Used with LoadingParameters
    """
    file_group: FilenameGroup
    log_file: Path | None = None
    shutter_count_file: Path | None = None
    indices: Indices | None = None


@dataclass
class LoadingParameters:
    """
    Dataclass to hold info about a dataset that is about to be loaded. Used to transfer information from ImageLoadDialog
    to the loading code.
    """
    image_stacks: dict[FILE_TYPES, ImageParameters] = field(default_factory=dict)

    pixel_size: int = DEFAULT_PIXEL_SIZE
    name: str = ""
    dtype: str = DEFAULT_PIXEL_DEPTH
    sinograms: bool = DEFAULT_IS_SINOGRAM


def _fitsread(filename: Path | str) -> np.ndarray:
    """
    Read one image and return it as a 2d numpy array

    :param filename :: name of the image file, can be relative or absolute path
    :param img_format: format of the image ('fits')
    """
    image = fits.open(filename)
    if len(image) < 1:
        raise RuntimeError(f"Could not load at least one FITS image/table file from: {filename}")

    # get the image data
    image_data = image[0].data
    image.close(filename)
    return image_data


def _imread(filename: Path | str) -> np.ndarray:
    try:
        return tifffile.imread(filename)
    except tifffile.TiffFileError as e:
        raise RuntimeError(f"TiffFileError {e.args[0]}: {filename}") from e


def get_loader(in_format: str) -> Callable[[Path | str], np.ndarray]:
    if in_format in ['fits', 'fit']:
        load_func = _fitsread
    elif in_format in ['tiff', 'tif']:
        load_func = _imread
    else:
        raise NotImplementedError("Loading not implemented for:", in_format)
    return load_func


def read_image_dimensions(file_path: Path) -> tuple[int, int]:
    load_func = get_loader(file_path.suffix.replace(".", ""))
    img = load_func(file_path)
    assert len(img.shape) == 2
    return img.shape


def load_log(log_file: Path) -> InstrumentLog:
    with open(log_file) as f:
        return InstrumentLog(f.readlines(), log_file)


def load_shutter_counts(shutter_count_file: Path) -> ShutterCount:
    with open(shutter_count_file, encoding='utf-8') as f:
        return ShutterCount(f.readlines(), shutter_count_file)


def load_stack_from_group(group: FilenameGroup, progress: Progress | None = None) -> ImageStack:
    return load(filename_group=group, progress=progress)


def load_stack_from_image_params(image_params: ImageParameters,
                                 progress: Progress | None = None,
                                 dtype: npt.DTypeLike = np.float32) -> ImageStack:
    return load(filename_group=image_params.file_group,
                progress=progress,
                dtype=dtype,
                indices=image_params.indices,
                log_file=image_params.log_file,
                shutter_count_file=image_params.shutter_count_file)


def load(filename_group: FilenameGroup,
         dtype: npt.DTypeLike = np.float32,
         indices: list[int] | Indices | None = None,
         progress: Progress | None = None,
         log_file: Path | None = None,
         shutter_count_file: Path | None = None) -> ImageStack:
    """
    Loads a stack, including sample, white and dark images.

    :param dtype: Default: np.float32, data type for the input images
    :param filename_group: FilenameGroup to provide file names for loading
    :param indices: Specify which indices are loaded from the found files.
                    This **DOES NOT** check for the number in the image
                    filename, but removes all indices from the filenames list
                    that are not selected
    :param progress: The progress reporting instance
    :return: an ImageStack
    """
    if indices and len(indices) < 3:
        raise ValueError("Indices at this point MUST have 3 elements: [start, stop, step]!")

    file_names = list(filename_group.all_files())
    in_format = filename_group.first_file().suffix.lstrip('.')
    load_func = get_loader(in_format)

    if log_file is not None:
        log_data = load_log(log_file)
        if log_data.has_projection_angles():
            angles = log_data.projection_angles().value
            angle_order = np.argsort(angles)
            angles = angles[angle_order]
            file_names = [file_names[i] for i in angle_order]

    image_stack = img_loader.execute(load_func, file_names, in_format, dtype, indices, progress)

    if log_file is not None:
        image_stack.log_file = log_data
        if log_data.has_projection_angles():
            angles = angles[indices[0]:indices[1]:indices[2]] if indices else angles
            image_stack.set_projection_angles(ProjectionAngles(angles))

    if shutter_count_file is not None:
        image_stack.shutter_count_file = load_shutter_counts(shutter_count_file)

    metadata_filename = filename_group.metadata_path
    if metadata_filename:
        with open(metadata_filename) as f:
            image_stack.load_metadata(f)
            LOG.debug(f'Loaded metadata from: {metadata_filename}')
    else:
        LOG.debug('No metadata file found')

    return image_stack


def create_loading_parameters_for_file_path(file_path: Path) -> LoadingParameters | None:
    sample_file = find_first_file_that_is_possibly_a_sample(file_path)
    if sample_file is None:
        return None

    loading_parameters = LoadingParameters()
    loading_parameters.name = sample_file.name
    sample_fg = FilenameGroup.from_file(sample_file)
    sample_fg.find_all_files()
    sample_fg.find_shutter_count_file()
    sample_fg.find_log_file()
    loading_parameters.image_stacks[FILE_TYPES.SAMPLE] = ImageParameters(sample_fg, sample_fg.log_path,
                                                                         sample_fg.shutter_count_path)

    for file_type in [ft for ft in FILE_TYPES if ft.mode in ["images", "180"]]:
        fg = sample_fg.find_related(file_type)
        if fg is None:
            continue

        fg.find_all_files()
        if file_type.tname == "Flat":
            fg.find_log_file()
        loading_parameters.image_stacks[file_type] = ImageParameters(fg, fg.log_path, fg.shutter_count_path)

    return loading_parameters
