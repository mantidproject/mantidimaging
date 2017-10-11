Gaussian
========

Applies SciPy's `Gaussian filter`__
(:code:`scipy.ndimage.filters.gaussian_filter`).

Command line examples
---------------------

    - :code:`mantidimaging -i /some/data --gaussian-size 3`

    - :code:`mantidimaging -i /some/data --gaussian-size 3 --gaussian-mode
      'nearest'`

    - :code:`mantidimaging -i /some/data --gaussian-size 3 --gaussian-mode
      'nearest' --gaussian-order 1`

Python API
----------

.. autofunction:: mantidimaging.core.filters.gaussian.execute

.. _FilterDocs: https://docs.scipy.org/doc/scipy-0.16.1/reference/generated/scipy.ndimage.filters.gaussian_filter.html

__ FilterDocs_
