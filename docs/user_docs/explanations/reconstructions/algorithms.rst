.. _Reconstruction Algorithms:

Reconstruction Algorithms
=========================

Overview
--------

This page gives explanations of different reconstruction algorithms available in Mantid Imaging, including implementation details, hardware requirements, and links to the upstream documentation for the algorithms.

ASTRA Toolbox
-------------

The ASTRA Toolbox provides GPU-accelerated tomographic reconstruction algorithms.

This implementation supports 2D data sets, and requires a CUDA-compatible graphics card to run.

Mantid Imaging automatically creates the required projector and geometry configurations for ASTRA reconstruction workflows.

Parallel beam vector geometry is used, allowing tilt correction to be accounted for through the centres of rotation for each slice. This means manual rotation of the images to correct the tilt shouldn't be necessary.


The vector creation implementation is adapted from `ToMoBAR <https://github.com/dkazanc/ToMoBAR/blob/master/src/Python/tomobar/supp/astraOP.py#L20-L70>`_.


FBP_CUDA
^^^^^^^^

Overview
""""""""

- Filtered back projection reconstruction algorithm
- Supports multiple reconstruction filters 
- Requires a CUDA-compatible GPU

When to use FBP_CUDA
""""""""""""""""""""

- High-quality, well-sampled tomography data
- Cases where speed is a priority and iterative reconstruction is not necessary
- When classical FBP is preferred for its simplicity and interpretability

`Link to the original documentation for FBP_CUDA <http://www.astra-toolbox.com/docs/algs/FBP_CUDA.html>`_

Interface Preview
"""""""""""""""""

.. image:: /_static/FBP_CUDA_light.png
    :alt: FBP CUDA in reconstruction window
    :width: 60%
    :align: center
    :class: only-light

.. image:: /_static/FBP_CUDA_dark.png
    :alt: FBP CUDA in reconstruction window
    :width: 60%
    :align: center
    :class: only-dark

Parameters
""""""""""

.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Parameter
      - Description
    * - Reconstruction filter
      - The filter applied during filter back projection. Different filters affect the sharpness and noise characteristics of the reconstruction. For an evaluation of the filters please go to the :ref:`Reconstruction Filters` page.
    * - Pixel size (microns)
      - Defines the physical pixel spacing used to convert image distances into real-world units, ensuring correct scaling of attenuation coefficients (e.g. cm⁻¹).

SIRT_CUDA
^^^^^^^^^

Overview
""""""""

- Simultaneous iterative reconstruction technique (SIRT) algorithm
- Reconstruction quality is controlled through iteration count 
- Requires a CUDA-compatible GPU

When to use SIRT_CUDA
"""""""""""""""""""""

- Noisy or low-dose tomography data
- Sparse or limited-angle datasets
- Cases where classical FBP produces strong artefacts
- When iterative reconstruction is preferred for improved image quality

`Link to the original documentation for SIRT_CUDA <http://www.astra-toolbox.com/docs/algs/SIRT_CUDA.html>`_.

Interface Preview
"""""""""""""""""

.. image:: /_static/SIRT_CUDA_light.png
    :alt: SIRT CUDA in reconstruction window
    :width: 60%
    :align: center
    :class: only-light

.. image:: /_static/SIRT_CUDA_dark.png
    :alt: SIRT CUDA in reconstruction window
    :width: 60%
    :align: center
    :class: only-dark

Parameters
""""""""""

.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Parameter
      - Description
    * - Number of iterations
      - The number of iterations to perform. Higher iteration counts can improve reconstruction quality but will increase computation time. Mantid Imaging provides a refine iterations tool to assist with selecting an appropriate iteration count.
    * - Pixel size (microns)
      - Defines the physical pixel spacing used to convert image distances into real-world units, ensuring correct scaling of attenuation coefficients (e.g. cm⁻¹).

TomoPy
------

gridrec
^^^^^^^

Overview
""""""""

- CPU-based reconstruction algorithm 
- Does not require CUDA support
- Implemented through the TomoPy package

When to use gridrec
"""""""""""""""""""
- When GPU resources are not available
- For smaller datasets where CPU reconstruction is sufficient

`Link to original documentation for gridrec <https://tomopy.readthedocs.io/en/latest/api/tomopy.recon.algorithm.html#module-tomopy.recon.algorithm>`_.

Interface Preview
"""""""""""""""""

Parameters
""""""""""

.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Parameter
      - Description
    * - Reconstruction filter
      - The filter applied during gridrec. Different filters affect the sharpness and noise characteristics of the reconstruction. For an evaluation of the filters please go to the :ref:`Reconstruction Filters` page.
    * - Pixel size (microns)
      - Defines the physical pixel spacing used to convert image distances into real-world units, ensuring correct scaling of attenuation coefficients (e.g. cm⁻¹).

References
^^^^^^^^^^

- Dowd BA, Campbell GH, Marr RB, Nagarkar VV, Tipnis SV, Axe L, and Siddons DP. Developments in synchrotron x-ray computed microtomography at the national synchrotron light source. In Proc. SPIE, volume 3772, 224–236. 1999.
- Rivers ML. Tomorecon: high-speed tomography reconstruction on workstations using multi-threading. In Proc. SPIE, volume 8506, 85060U–85060U–13. 2012.

Core Imaging Library
--------------------

The `Core Imaging Library (CIL) <https://www.ccpi.ac.uk/cil>`_ is an open-source Python framework for tomographic imaging with particular emphasis on reconstruction of challenging datasets.

PDHG-TV
^^^^^^^

Overview
""""""""

- Primal Dual Hybrid Gradient (PDHG) optimiser
- Total Variation (TV) regularised reconstruction method
- Iterative algorithm designed for noise suppression and sparse/noisy data
- Typically produces smoother reconstructions with edge preservation

When to use PDHG-TV
"""""""""""""""""""

- Noisy or low-dose tomography data
- Sparse or limited-angle datasets
- Cases where classical FBP produces strong artefacts
- When edge-preserving smoothing is required

Interface Preview
"""""""""""""""""

Parameters
""""""""""

.. list-table::
    :widths: 25 75
    :header-rows: 1

    * - Parameter
      - Description
    * - Number of iterations
      - The number of iterations to perform. Higher iteration counts can improve reconstruction quality but will increase computation time.
    * - Alpha (regularisation parameter)
      - Controls the strength of the TV regularisation. Higher alpha values lead to smoother reconstructions with stronger edge preservation, while lower alpha values allow more noise but can preserve finer details.
    * - Non-negativity constraint
      - Enforces reconstructed values to be greater than or equal to zero. Negative values are projected to zero during the optimisation process. This is often appropriate for physical quantities such as attenuation in absorption tomography.
    * - Stochastic
      - Enables a stochastic variant of the PDHG optimisation algorithm (SPDHG). Instead of using the full dataset at each iteration, the algorithm operates on randomly selected subsets of data. This reduces the computational cost per iteration, which can improve performance for large datasets. However, it may require more iterations to converge compared to the full (deterministic) version.
    * - Projections per subset
      - When stochastic is enabled, this parameter specifies the number of projections to include in each randomly selected subset. A smaller number of projections per subset can lead to faster iterations but may increase the total number of iterations needed for convergence.
    * - Regularisation percent
      - When stochastic is enabled, this parameter specifies the percentage of the total number of projections to include in each subset for regularisation. This allows the regularisation step to be performed on a representative subset of the data, which can help maintain reconstruction quality while reducing computational cost.
    * - Pixel size (microns)
      - Defines the physical pixel spacing used to convert image distances into real-world units, ensuring correct scaling of attenuation coefficients (e.g. cm⁻¹).

References
^^^^^^^^^^

The figure shows two values of alpha applied to a reconstructed slice.

.. figure:: ../../../_static/pdhg_tv_alpha.png
    :alt: PDHG-TV with alpha=0.1 on the left and alpha=10 on the right
    :width: 90%
    :align: center

    PDHG-TV with alpha=0.1 on the left and alpha=10 on the right


- Jørgensen JS et al. 2021 `Core Imaging Library Part I: a versatile python framework for tomographic imaging <https://doi.org/10.1098/rsta.2020.0192>`_. Phil. Trans. R. Soc. A 20200192. Code.
