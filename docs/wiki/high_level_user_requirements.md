<!-- TOC -->

- [High Level Requirements](#high-level-requirements)
- [Use Cases](#use-cases)
    - [Loading data](#loading-data)
    - [Image Processing](#image-processing)
    - [Finding Center of Rotation and Tilt](#finding-center-of-rotation-and-tilt)
    - [Reconstruction](#reconstruction)
- [Use Cases ( Energy Selective )](#use-cases--energy-selective-)
    - [Aggregating energy levels](#aggregating-energy-levels)

<!-- /TOC -->

# High Level Requirements
- Load and visualise a single image
- Load and visualise a volume/stack of images
- Save out data
- Selecting Region of Interest
- Apply filters to a single slice or the whole loaded data
- Reconstruct a single slice or the whole loaded data
- Calculating and visualising a histogram of the Region of Interest
  - Histogram for the current slice
  - Histogram for the same Region of interest of the whole loaded data
- Remote submission to a cluster

# Use Cases

- Load assumes **both loading and visualising** the image volume!

- Images in volume that are considered have dimension 2048x2048.

- The full volume considered will have 1800 images. 

The reason only 1800 images are used is to be able to fit all of the images into memory on a workstation with 32GB RAM (whole volume is 28.125GB) for visualisation. 
For volumes larger than available memory something called a _virtual stack_ will be used, however that will not be part of the initial implementation.

- Pixels per image: 4,194,304
- Bits per 16 bit image: 67,108,864
- Bits per 32 bit image: 134,217,728
- Bytes per 16 bit image: 8,388,608
- Bytes per 32 bit image: 16,777,216

## Loading data
1. Load full image volume. Optionally save it out again as different format.
2. Load only a range of slices (e.g. indices 0 to 100).

## Image Processing

Image Processing is relevant to both _Pre_ and _Post_ processing, and is generally considered as the application of one or multiple filters to an image or the whole volume. Example pre-processing filters could be:

- Background correction with flat and dark images 
- Contrast Normalisation

1. Load image volume, apply a filter to a single image and undo.
2. Load image volume, apply a filter to a single image, and then apply to the whole stack _locally_.
3. Load only a range of slices, apply a filter to a single image, and then apply to the whole stack _locally_ (even though the whole stack was NOT loaded in memory).
4. Load only a range of slices, apply a filter to the images loaded, then submit job to be performed cluster for the same range of slices.
4. Load only a range of slices, apply a filter to the images loaded, then submit job to be performed cluster for ALL the slices.

## Finding Center of Rotation and Tilt
1. Load a range of sinograms, do automatic finding of center of rotation, get a number back.
2. Load a range of sinograms, do automatic finding of center of rotation, do manual reconstruction with different centers of rotation, until the best one is found for each sinogram. Tilt correction will be calculated automatically.

## Reconstruction
1. Load only a range of slices, reconstruct _only_ the range of slices loaded locally.
2. Load only a range of slices, reconstruct the whole volume locally.
3. Load only a range of slices, submit job to be performed on the cluster to reconstruct the same range of slices as were loaded.
4. Load only a range of slices, submit job to be performed on the cluster to reconstruct **ALL** slices.

# Use Cases ( Energy Selective )
This shares _all_ steps with the previous use case section, but has an additional one for aggregating energy levels.

## Aggregating energy levels
1. Load all angles and all energy levels (expected to be slow).
2. Load all angles, but only _specific_ energy levels from _each_ angle.
3. Load only specific angles, and all energy levels per angle.
4. Load only specific angles and only _specific_ energy levels per angle.
5. At any point save out the aggregated images.