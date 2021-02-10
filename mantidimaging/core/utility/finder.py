# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os

ROOT_PACKAGE = 'mantidimaging'


def get_external_location(module_file, root_package=ROOT_PACKAGE):
    """
    Find the external MantidImaging location for the whole package
    :param module_file: The module whose package we're looking for
    :param root_package: The top level package of mantidimaging
    """
    s = os.path.dirname(os.path.realpath(module_file))
    return s[:s.rfind(root_package)]
