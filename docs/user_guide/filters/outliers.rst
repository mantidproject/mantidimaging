Outliers
========

.. important::

    This filter requires TomoPy to be available.

Removes bright or dark spots (outliers) from an image (or stack of images).

This uses the TomoPy implementation (:code:`tomopy.misc.corr.remove_outlier`)
(docs_).

There is the option to run the outlier filter on the GPU. For more information see :doc:`GPU Mode <../gpu_mode.rst>`.

Python API
----------

.. autoclass:: mantidimaging.core.filters.outliers.OutliersFilter

.. _docs: http://tomopy.readthedocs.io/en/latest/api/tomopy.misc.corr.html#tomopy.misc.corr.remove_outlier
