.. _dataset:

Example Neutron Datasets
========================

This page provides example neutron (and related) datasets for use with Mantid Imaging.
These datasets are intended to help users quickly get started with visualization,
corrections, and reconstruction workflows.

The datasets listed here are small, open-access, or synthetic where possible, and are
suitable for tutorials, testing, and continuous integration (CI) workflows.

Overview
--------

The datasets included or referenced here are designed to:

- Demonstrate visualization in Mantid Imaging
- Show typical correction workflows (dark/flat correction, normalization, etc.)
- Provide reproducible examples for tutorials and testing

Test Datasets Repository
------------------------

A small collection of test datasets is available via GitHub:

https://github.com/mantidproject/mantidimaging-data

This repository currently includes:

- **Neutron tomography of a flower**

  - Acquired at IMAT at ISIS Neutron and Muon Source
  - Format: TIFF image stack
  - Suitable for:

    - Basic visualization
    - Reconstruction workflows
    - Testing correction pipelines

- **X-ray tomography of a wire sample**

  - Acquired at beamline i13 at Diamond Light Source
  - Format: NXTomo (NeXus) file
  - Useful for:

    - Testing NeXus file handling
    - Comparing neutron vs X-ray workflows

These datasets are intentionally small to allow fast download and use in CI environments.

Recommended Open Datasets
-------------------------

A larger collection of open-access tomography datasets is available via Zenodo:

https://zenodo.org/collection/user-ccpi

Recommended neutron datasets include:

**Lego Man Neutron Tomography Dataset**

- DOI: https://doi.org/10.5281/zenodo.17814677
- Description:

  A neutron tomography dataset of a Lego figure, acquired with both equidistant
  and golden angle sampling strategies.

- Use cases:

  - Reconstruction algorithm comparison
  - Sampling strategy studies
  - Visualization examples

**Aluminium Cylinder – Flexible Neutron Tomography Dataset**

- DOI: https://doi.org/10.5281/zenodo.18956581
- Description:

  A flexible neutron tomography dataset acquired with multiple exposure times and
  a highly composite number of projection angles.

- Use cases:

  - Studying trade-offs between exposure time and number of projections
  - Optimizing acquisition strategies
  - Testing reconstruction robustness

**Cone Beam CT Dataset**

- DOI: https://doi.org/10.5281/zenodo.11397266
- Description:

  X-ray cone-beam CT dataset of a walnut acquired at multiple dose levels.
  Includes TIFF projections and scan metadata describing scan geometry and parameters.

- Use cases:

  - Testing cone-beam reconstruction workflows
  - Exploring dose vs image quality trade-offs
  - Practicing correction steps (dark/flat field)


Internal ISIS Datasets
----------------------

Additional datasets are available internally via the ISIS Data Analysis
as a Service `Ada <https://ada.stfc.ac.uk/login>`_ system.

- Location:

  ``/mnt/ceph/auxiliary/tomography/example_data``

- Access:

  Available to ISIS users and STFC staff

- Notes:

  - See :ref:`getting-started-with-ada` in **Tutorials** if you're new to using Ada.

