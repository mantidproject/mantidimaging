<!-- TOC -->

- [Pre-processing](#pre-processing)
    - [Loading data](#loading-data)
    - [Saving pre-processed images](#saving-pre-processed-images)
    - [Selecting filters](#selecting-filters)
    - [Running _only_ pre-processing](#running-_only_-pre-processing)
    - [Saving pre-processed images](#saving-pre-processed-images-1)
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
Sample image data can be loaded with the `-i` or `--input-path` command.

Dark image data can be loaded with the `-D` or `--input-path-dark` command.

Flat image data can be loaded with the `-F` or `--input-path-flat` command.

The image files must be in separate folders for each (sample, dark, flat).
All the Dark and Flat image files will be loaded, and then averaged before applying any normalisations.

Both Flat and Dark images must be provided, or both must be absent. A pre-processing run cannot be ran with only one.

Examples:

`python main.py -i ~/some/folders/sample`

`python main.py -i ~/some/folders/sample -D ~/some/folders/dark -F ~/some/folders/flat`

---

## Saving pre-processed images
In order for any output to be produced, an output folder needs to be specified using `-o` or `--output-path`. Otherwise _no images will be saved_.

`python main.py -i ~/some/folders/sample -D ~/some/folders/dark -F ~/some/folders/flat -o /tmp/imgpy/`

## Selecting filters
The available filters can be found in the filters.md document. To add a filter to the pre-processing just add it to the command line and it will be executed:

`python main.py -i ~/some/folders/sample -D ~/some/folders/dark -F ~/some/folders/flat -o /tmp/imgpy/ --rotate 1 --pre-median-size 3 --pre-outliers 8 --pre-outliers-radius 8`

## Running _only_ pre-processing
If you want to do _only_ the pre-processing and then **exit** you can do so by adding -s or --only-preproc to the command line.

`python main.py -i ~/some/folders/sample -D ~/some/folders/dark -F ~/some/folders/flat -o /tmp/imgpy/ --rotate 1 --pre-median-size 3 --pre-outliers 8 --pre-outliers-radius 8 --only-preproc`

## Saving pre-processed images
With the current command line so far, the pre-processing images _will not be saved_. To save out the pre-processing images the user has to specify explicitly that they want the images to be saved, and an output directory **must** be provided.

To save out the pre-processed images, the flag `-s` or `--save-preproc` needs to be added.
The subdirectory can be specified using the `-p` or `--preproc-subdir` flags, and it will be created inside the output folder. This allows to save out images with different pre-processing parameters without flooding the folder space.

`python main.py -i ~/some/folders/sample -D ~/some/folders/dark -F ~/some/folders/flat -o /tmp/imgpy/ --rotate 1 --pre-median-size 3 --pre-outliers 8 --pre-outliers-radius 8 --only-preproc --save-preproc`

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