from __future__ import absolute_import, division, print_function

import glob
import os
import re

DEFAULT_IO_FILE_FORMAT = 'tif'


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
            "Could not find any image files in '{0}' with extension: {1}".format(
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

    path = os.path.abspath(os.path.expanduser(path))

    # os.walk returns a tuple (dirpath, dirnames, filenames), we only want dirnames
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
    alpha_num_split_re = re.compile('([0-9]+)')
    return [
        int(c) if c.isdigit() else c
        for c in alpha_num_split_re.split(path_str)
    ]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
