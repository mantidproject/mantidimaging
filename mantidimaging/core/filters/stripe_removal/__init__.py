from __future__ import (absolute_import, division, print_function)

NAME = 'Stripe Removal'

from .stripe_removal import execute, wavelet_names, _cli_register  # noqa:F401
from .stripe_removal_gui import _gui_register  # noqa:F401

del absolute_import, division, print_function  # noqa:F821
