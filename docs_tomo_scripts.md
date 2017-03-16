<!-- TOC -->

- [Pre-processing](#pre-processing)
    - [Loading data](#loading-data)
    - [Selecting filters](#selecting-filters)
    - [Saving pre-processed images](#saving-pre-processed-images)
    - [Running _only_ pre-processing](#running-_only_-pre-processing)
- [Reconstruction](#reconstruction)
    - [Preparing center of rotation](#preparing-center-of-rotation)
        - [Usage of --imopr ... cor](#usage-of---imopr--cor)
        - [Usage of --imopr ... corwrite](#usage-of---imopr--corwrite)
    - [Specifying centers of rotation for reconstruction](#specifying-centers-of-rotation-for-reconstruction)
    - [Running _only_ a reconstruction](#running-_only_-a-reconstruction)
    - [Running a reconstruction](#running-a-reconstruction)
- [Post-processing](#post-processing)
    - [Running _only_ post-processing](#running-_only_-post-processing)
    - [Selecting filters](#selecting-filters-1)

<!-- /TOC -->

# Pre-processing
## Loading data
Sample image data can be loaded with the -i or --input-path command.

Dark image data can be loaded with the -D or --input-path-dark command.

Flat image data can be loaded with the -F or --input-path-flat command.

The image files must be in separate folders for each (sample, dark, flat).
All the Dark and Flat image files will be loaded, and then averaged before applying any normalisations.

Both Flat and Dark images must be provided, or both must be absent. A pre-processing run cannot be ran with only one.

Examples:

`python main.py -i ~/some/folders/`

`python main.py -i ~/some/folders/ -D ~/some/folders/dark -F ~/some/folders/flat`

---

## Selecting filters
## Saving pre-processed images
## Running _only_ pre-processing

# Reconstruction
## Preparing center of rotation
### Usage of --imopr ... cor
### Usage of --imopr ... corwrite
## Specifying centers of rotation for reconstruction
## Running _only_ a reconstruction
## Running a reconstruction
<!-- ^ add -o -->
# Post-processing
## Running _only_ post-processing
## Selecting filters