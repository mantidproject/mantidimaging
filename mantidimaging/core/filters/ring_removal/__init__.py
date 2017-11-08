from __future__ import (absolute_import, division, print_function)

NAME = 'Ring Removal'

from .ring_removal import execute, _cli_register  # noqa:F401
from .ring_removal_gui import _gui_register  # noqa:F401

from mantidimaging.core.utility.optional_imports import tomopy_available as available  # noqa: F401

del absolute_import, division, print_function  # noqa:F821
