# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import glob
import itertools
import os
import re
import numpy as np
from logging import getLogger, Logger
from pathlib import Path
from typing import List, Optional, Union, Tuple

from mantidimaging.core.io.filenames import FilenameGroup

log = getLogger(__name__)

DEFAULT_IO_FILE_FORMAT = 'tif'

SIMILAR_FILE_EXTENSIONS = (('tif', 'tiff'), ('fit', 'fits'))

THRESHOLD_180 = np.radians(1)


def get_file_extension(file: str) -> str:
    """
    >>> get_file_extension("/home/user/file_path.test")
    'test'
    >>> get_file_extension("/home/user/file.path.test")
    'test'
    >>> get_file_extension("/home/")
    ''

    """
    # [1] gets the extension, [1:] returns it without the dot
    return os.path.splitext(file)[1][1:]


def get_candidate_file_extensions(ext: str) -> List[str]:
    """
    Gets a list of file extensions which can be used to load files.
    :param ext: User provided file extension
    :returns: List of extensions in the order they should be tested
    """
    # Get all tuples of similar extensions that the provided extension appears
    # in
    similar_extensions = [e for e in SIMILAR_FILE_EXTENSIONS if ext in e]

    # Concatenate them all into a single list
    candidates = list(itertools.chain(*similar_extensions))

    # Remove the provided extension from the list
    if ext in candidates:
        candidates.remove(ext)

    # Return candidates, provided extension is always first to give it priority
    return [ext] + candidates


def get_file_names(path: Optional[Union[Path, str]],
                   img_format: str,
                   prefix: str = '',
                   essential: bool = True) -> List[str]:
    """
    Get all file names in a directory with a specific format.
    :param path: The path to be checked.

    :param img_format: The image format used as a postfix after the .

    :param prefix: A specific prefix for the images

    :param essential: Flag indicating if failure to find file should raise and
                      exception

    :return: All the file names, sorted by ascending
    """

    # Return no found files on None path
    if path is None:
        return []

    path = os.path.abspath(os.path.expanduser(path))
    extensions = get_candidate_file_extensions(img_format)
    files_match = []
    for ext in extensions:
        files_match = glob.glob(os.path.join(path, "{0}*{1}".format(prefix, ext)))

        if len(files_match) > 0:
            break

    if len(files_match) == 0 and essential:
        raise RuntimeError(f"Could not find any image files in '{path}' with extensions: {extensions}")

    # This is a necessary step, otherwise the file order is not guaranteed to
    # be sequential and we get randomly ordered stack of names
    files_match.sort(key=_alphanum_key_split)

    log.debug(f'Found {len(files_match)} files with common prefix: {os.path.commonprefix(files_match)}')

    return files_match


def find_images_in_same_directory(sample_dirname: Path, type: str, suffix: str,
                                  image_format: str) -> Optional[List[str]]:
    prefix_list = [f"*{type}", f"*{type.lower()}", f"*{type}_{suffix}", f"*{type.lower()}_{suffix}"]

    for prefix in prefix_list:
        try:
            if suffix != "After":
                return get_file_names(sample_dirname.absolute(), image_format, prefix=prefix)
        except RuntimeError:
            getLogger(__name__).info(f"Could not find {prefix} files in {sample_dirname.absolute()}")

    return None


def _alphanum_key_split(path_str: str) -> List[Union[int, str]]:
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
    alpha_num_split_re = re.compile('([0-9]+)')
    return [int(c) if c.isdigit() else c for c in alpha_num_split_re.split(path_str)]


def get_prefix(path: str, separator: str = "_") -> str:
    return path[:path.rfind(separator)]


def find_images(sample_dirname: Path,
                image_type: str,
                suffix: str,
                image_format: str,
                look_without_suffix: bool = False) -> List[str]:
    # same folder
    file_names = find_images_in_same_directory(sample_dirname, image_type, suffix, image_format)
    if file_names is not None:
        return file_names

    # look into different directories 1 level above
    dirs = [
        f"{image_type} {suffix}", f"{image_type.lower()} {suffix}", f"{image_type}_{suffix}",
        f"{image_type.lower()}_{suffix}"
    ]
    if look_without_suffix:
        dirs.extend([f"{image_type.lower()}", image_type])

    for d in dirs:
        expected_folder_path = sample_dirname / ".." / d
        try:
            return get_file_names(expected_folder_path.absolute(), image_format)
        except RuntimeError:
            log.info(f"Could not find {image_format} files in {expected_folder_path.absolute()}")

    return []


def find_log_for_image(image_file_name: Path) -> Optional[Path]:
    filename_group = FilenameGroup.from_file(image_file_name)
    filename_group.find_log_file()
    if filename_group.log_path is None:
        log.info(f"Could not find a log file for {image_file_name}")
        return None
    return filename_group.log_path


def find_180deg_proj(sample_dirname: Path, image_format: str, logger: Optional[Logger] = None) -> str:
    expected_path = sample_dirname / '..' / '180deg'
    try:
        return get_file_names(expected_path.absolute(), image_format)[0]
    except RuntimeError:
        if logger is not None:
            logger.info(f"Could not find 180 degree projection in {expected_path}")
    return ""


def find_first_file_that_is_possibly_a_sample(file_path: str) -> Optional[str]:
    # Grab all .tif or .tiff files
    possible_files = glob.glob(os.path.join(file_path, "**/*.tif*"), recursive=True)

    for possible_file in possible_files:
        lower_filename = os.path.basename(possible_file).lower()
        if "flat" not in lower_filename and "dark" not in lower_filename and "180" not in lower_filename:
            return possible_file
    return None


def find_projection_closest_to_180(projections: np.ndarray, projection_angles: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Finds the projection closest to 180 and returns it with the difference.
    :param projections: The array of projection images.
    :param projection_angles: The array of projection angles.
    :return: The 180 projection/the closest non-180 projection and the difference between its angle and 180.
    """
    diff = np.abs(projection_angles - np.pi)
    return projections[diff.argmin()], np.amin(diff)
