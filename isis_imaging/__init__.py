from __future__ import absolute_import, division, print_function

# Copyright &copy; 2017-2018 ISIS Rutherford Appleton Laboratory, NScD
# Oak Ridge National Laboratory & European Spallation Source
#
# This file is part of Mantid.
# Mantid is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Mantid is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Dimitar Tasev, Mantid Development Team
#
# File change history is stored at: <https://github.com/mantidproject/mantid>.
# Code Documentation is available at: <http://doxygen.mantidproject.org>

# import all the submodules of core, and they can be accessed directly via
# isis_imaging.<module>, e.g. isis_imaging.filters.median_filter,
# without going through isis_imaging.**core**.filters.median_filter

__all__ = [
    'aggregate', 'algorithms', 'configs', 'configurations', 'convert',
    'filters', 'imgdata', 'imopr', 'parallel', 'tools'
]

# modules part of public API
from isis_imaging.core import aggregate
from isis_imaging.core import algorithms
from isis_imaging.core import configs
from isis_imaging.core import configurations
from isis_imaging.core import convert
from isis_imaging.core import filters
from isis_imaging.core import imgdata
from isis_imaging.core import imopr
from isis_imaging.core import parallel
from isis_imaging.core import tools

# delete 'core' even though we've never imported it!
# this hides the core from being directly accessed with isis_imaging.core
# however it messes up ipython's reload functionality and is not worth it
# del core  # noqa: F821
