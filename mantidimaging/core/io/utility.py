# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import glob
import itertools
import os
import re

from logging import getLogger
from pathlib import Path
from typing import List, Optional

DEFAULT_IO_FILE_FORMAT = 'tif'

SIMILAR_FILE_EXTENSIONS = (('tif', 'tiff'), ('fit', 'fits'))


def get_file_extension(file):
    """
    >>> get_file_extension("/home/user/file_path.test")
    'test'
    >>> get_file_extension("/home/user/file.path.test")
    'test'
    >>> get_file_extension("/home/")

    # above is expecting a None which.. well doesn't show as anything so just
    # an empty line with a comment explaining it
    """
    if os.path.isdir(file):
        return None
    # [1] gets the extension, [1:] returns it without the dot
    return os.path.splitext(file)[1][1:]


def get_candidate_file_extensions(ext):
    """
    Gets a list of file extensions which can be used to load files.
    :param ext: User provided file extension
    :returns: List of extensions in the order they should be tested
    """
    # Get all tuples of similar extensions that the provided extension appears
    # in
    candidates = [e for e in SIMILAR_FILE_EXTENSIONS if ext in e]

    # Concatenate them all into a single list
    candidates = list(itertools.chain(*candidates))

    # Remove the provided extension from the list
    if ext in candidates:
        candidates.remove(ext)

    # Return candidates, provided extension is always first to give it priority
    return [ext] + candidates


def get_file_names(path, img_format, prefix='', essential=True) -> List[str]:
    """
    Get all file names in a directory with a specific format.
    :param path: The path to be checked.

    :param img_format: The image format used as a postfix after the .

    :param prefix: A specific prefix for the images

    :param essential: Flag indicating if failure to find file should raise and
                      exception

    :return: All the file names, sorted by ascending
    """
    log = getLogger(__name__)

    # Return no found files on None path
    if path is None:
        return []

    path = os.path.abspath(os.path.expanduser(path))
    extensions = get_candidate_file_extensions(img_format)
    files_match = []
    for ext in extensions:
        files_match = glob.glob(os.path.join(path, "{0}*.{1}".format(prefix, ext)))

        if len(files_match) > 0:
            break

    if len(files_match) == 0 and essential:
        raise RuntimeError(f"Could not find any image files in '{path}' with extensions: {extensions}")

    # This is a necessary step, otherwise the file order is not guaranteed to
    # be sequential and we get randomly ordered stack of names
    files_match.sort(key=_alphanum_key_split)

    log.debug(f'Found {len(files_match)} files with common prefix: {os.path.commonprefix(files_match)}')

    return files_match


def find_images_in_same_directory(sample_dirname: Path, type: str, suffix: str, image_format: str) -> Optional[List[str]]:
    prefix_list = [f"*{type}", f"*{type.lower()}", f"*{type}_{suffix}", f"*{type.lower()}_{suffix}"]

    for prefix in prefix_list:
        try:
            if suffix != "After":
                return get_file_names(sample_dirname.absolute(), image_format, prefix=prefix)
        except RuntimeError:
            getLogger(__name__).info(f"Could not find {prefix} files in {sample_dirname.absolute()}")

    return None


def get_folder_names(path):
    """
    Get all folder names in a specific path.

    :param path: The path to be checked.

    :return: All the folder names, sorted by ascending

    """

    path = os.path.abspath(os.path.expanduser(path))

    # os.walk returns a tuple (dirpath, dirnames, filenames), we only want
    # dirnames
    folders = next(os.walk(path))[1]

    if len(folders) <= 0:
        raise RuntimeError("Could not find any folders in {0}".format(path))

    # this is a necessary step, otherwise the file order is not guaranteed to
    # be sequential and we get randomly ordered stack of names
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
    alpha_num_split_re = re.compile('([0-9]+)')
    return [int(c) if c.isdigit() else c for c in alpha_num_split_re.split(path_str)]


if __name__ == '__main__':
    import doctest

    doctest.testmod()


def get_prefix(path: str, separator="_"):
    return path[:path.rfind(separator)]
