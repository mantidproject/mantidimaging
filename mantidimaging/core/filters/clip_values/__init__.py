from __future__ import (absolute_import, division, print_function)

NAME = 'Clip Values'

from .clip_values import execute, _cli_register  # noqa:F401
from .clip_values_gui import _gui_register  # noqa:F401

del absolute_import, division, print_function  # noqa:F821
