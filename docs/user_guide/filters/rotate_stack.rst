Rotate Stack
============

Rotates an image (or each image in a stack) clockwise by a multiple of 90
degrees.

.. note:: This filter only works with "square" images (i.e. images where the X
          and Y dimensions are equal).

Through the Python API the flat and dark images can also be provided to process
them in a single call to :code:`execute()`.

Python API
----------

.. autoclass:: mantidimaging.core.filters.rotate_stack.RotateFilter
