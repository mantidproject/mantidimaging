Overview
========

Mantid Imaging contains tools for loading data from neutron imaging experiments, preprocessing to enhance images and tomographic reconstruction into 3 dimensional data that can be output for further analysis.

Mantid Imaging makes use of a range of algorithms, some from external tools including `Astra <http://www.astra-toolbox.com/>`_, `Tomopy <https://tomopy.readthedocs.io/en/latest/>`_, `Algotom <https://github.com/algotom/algotom>`_ and the `Core Imaging Library <https://github.com/TomographicImaging/CIL>`_. Many of these are optimised for multithreading and GPU computing.

Mantid Imaging is written in Python and requires a CUDA capable GPU for full functionality. It runs on Linux and Windows. See :ref:`Installation` for more details.

See the :ref:`User Guide` for an example taking data from a set of images to full reconstruction.

Features
--------

Operations
^^^^^^^^^^

The Operations Window provides a selection of tools and filters to process and enhance the 2D images before running the reconstruction.

* Crop Coordinates
* Flat-fielding
* Remove Outliers
* ROI Normalisation

* Arithmetic
* Circular Mask
* Clip Values
* Divide
* Gaussian
* Median
* Monitor Normalisation
* NaN Removal
* Rebin
* Rescale
* Ring Removal
* Rotate Stack

* Remove all stripes
* Remove dead stripes
* Remove large stripes
* Remove stripes with filtering
* Remove stripes with sorting and fitting

More details on using these are available in the :ref:`API Reference` and :ref:`User Guide`.


Reconstruction
^^^^^^^^^^^^^^

Mantid Imaging offers several reconstruction algorithms

* FBP_CUDA - Filtered Backprojection
* SIRT_CUDA - Simultaneous Iterative Reconstruction Technique
* CIL: PDHG-TV - Core Imaging Library
* gridrec

Spectrum Viewer
^^^^^^^^^^^^^^

Mantid Imaging offers a spectrum viewer where users can select many regions of interest (ROI) for time of flight (TOF) data and view the spectrum of each ROI. 
The spectrum viewer can be used to export the spectrum of each ROI and its respective coordinates to a separate csv file.

The spectrum viewer can be accessed from the main menu under "Workflow" > "Spectrum Viewer".

Glossary
--------

COR
   Centre of Rotation.

Dataset
   Consists of images stacks plus additional files or metadata, such as flat and dark frames, and log files.

Image
   A single 2D recorded by the experiment. Typically loaded from TIFF files.

Image Stack
   A set of multiple related images, for example images of the same object from a range of angles.

Projection
   The original image formed by the unscattered/unabsorbed neutrons reaching the imaging detector.

ROI
   Region of Interest. A cropped part of an image.

Sinogram
   A projection of all rotations of a single slice through an object. Each point in the slice becomes a sinusoidal line. Also known as a Radon transform.

Tomography
   The process of creating a 3D model if an object from a series 2D images taken at a range angles through it.

TOF
   Time of Flight. The time taken for a neutron to travel from the source to the detector.

