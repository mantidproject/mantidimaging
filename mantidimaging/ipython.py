from __future__ import absolute_import, division, print_function

import sys

print("\nISIS_Imaging iPython")
print("in ipython.py", sys.path[0])
sys.path[0] = sys.path[0]

# import after the path has been corrected
import mantidimaging  # noqa
