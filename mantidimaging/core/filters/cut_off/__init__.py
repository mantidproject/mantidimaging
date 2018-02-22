NAME = 'Intensity Cut Off'

from .cut_off import execute, _cli_register  # noqa:F401
from .cut_off_gui import _gui_register  # noqa:F401

del absolute_import, division, print_function  # noqa:F821
