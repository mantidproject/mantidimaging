Stripe Removal
==============

.. important::

    This filter requires TomoPy to be available.

TODO

Command line examples
---------------------

    - :code:`mantidimaging -i /some/data --stripe-removal-wf level=1`

    - :code:`mantidimaging -i /some/data --stripe-removal-wf level=3 pad=False`

    - :code:`mantidimaging -i /some/data --stripe-removal-wf level=3 pad=False
      wname=db5`

    - :code:`mantidimaging -i /some/data --stripe-removal-wf level=3 pad=False
      wname=db5 sigma=2`

    - :code:`mantidimaging -i /some/data --stripe-removal-ti nblock=3`

    - :code:`mantidimaging -i /some/data --stripe-removal-ti nblock=3 alpha=2`

    - :code:`mantidimaging -i /some/data --stripe-removal-sf size=3`

Python API
----------

.. autofunction:: mantidimaging.core.filters.stripe_removal.execute
