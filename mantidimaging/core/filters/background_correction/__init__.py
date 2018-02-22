NAME = 'Background Correction'

from .background_correction import execute, _cli_register  # noqa:F401
from .background_correction_gui import _gui_register  # noqa:F401

del absolute_import, division, print_function  # noqa:F821
