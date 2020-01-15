from .minus_log import MinusLogFilter, _cli_register  # noqa:F401

FILTER_CLASS = MinusLogFilter
from mantidimaging.core.utility.optional_imports import (  # noqa: F401
    tomopy_available as available)  # noqa:F821
