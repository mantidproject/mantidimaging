from __future__ import (absolute_import, division, print_function)

NAME = 'Circular Mask'

from .circular_mask import execute, _cli_register  # noqa:F401
from .circular_mask_gui import _gui_register, _gui_register_2  # noqa:F401

del absolute_import, division, print_function  # noqa:F821
