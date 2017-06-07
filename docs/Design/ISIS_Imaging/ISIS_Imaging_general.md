<!-- TOC -->

- [Implementation design for ISIS_Imaging GUI](#implementation-design-for-isis_imaging-gui)
- [Motivation](#motivation)
- [Requirements](#requirements)
- [Design](#design)
    - [General structure](#general-structure)
    - [Loading](#loading)
    - [Handling multiple stacks in dialogues](#handling-multiple-stacks-in-dialogues)
    - [Visualisation](#visualisation)
    - [Applying a filter](#applying-a-filter)
    - [Undoing an operation](#undoing-an-operation)
    - [Histograms](#histograms)
    - [Processing a full volume](#processing-a-full-volume)
    - [Issues with Finding Center of Rotation and Reconstruction](#issues-with-finding-center-of-rotation-and-reconstruction)
        - [Automatic Center of Rotation (COR) with imopr cor](#automatic-center-of-rotation-cor-with-imopr-cor)
        - [Center of Rotation (COR) with imopr corwrite](#center-of-rotation-cor-with-imopr-corwrite)
    - [Reconstruction](#reconstruction)
    - [Remote submission](#remote-submission)
        - [Remote compute resource used at ISIS: SCARF](#remote-compute-resource-used-at-isis-scarf)

<!-- /TOC -->

The user requirements for the interface have been listed [here](https://github.com/mantidproject/isis_imaging/wiki/High-Level-User-Requirements-and-Use-Cases) and have been reviewed and confirmed by the imaging scientists.

The development requirements, following from the user requirements, are listed [here](https://github.com/mantidproject/isis_imaging/wiki/High-Level-Development-Requirements-and-Guidelines)

# Motivation
The current [Tomography Reconstruction](https://github.com/mantidproject/mantid/tree/043095a619bc8851942a31253a1a8f8b820ab30f/MantidQt/CustomInterfaces/inc/MantidQtCustomInterfaces/Tomography) interface was found to not satisfy the current imaging requirements. An easy solution to the problems was not found. With the agreement of the IMAT imaging scientists and senior members of the Mantid team, work is to be started on this design for a rewrite of the interface. Python is the preferred language here, in order to be able to make use of visualising libraries like Matplotlib and interactions with Python based reconstruction packages like Tomopy.

# Requirements
1. Visualisation of single or volume of images.
    - Contrast adjustment on the visualised image
2. Selection of region of interest(ROI) on the visualisation
3. Applying an operation to the visualised image
    - This could be a filter or a single slice reconstruction
4. Storing history of applied filters in a Process List
    - can be used to process the whole volume independently (on a remote cluster or locally)
5. Histogram computation for the ROI on the visualised image
6. Processing a full volume locally or on a remote computer via job submission
7. Finding the Center of Rotation
8. Reconstruction
9. Remote submission


# Project setup
## Continous Integration with Coverage
The package should have a continous integration flow on Pull Requests, which runs all of the CORE and GUI tests. This should also include coverage.

After sphinx documentation is added, the contiguous integration could also check if it builds successfully.

## Installation
The package should be installable using `python setup.py install`, making it available system wide.

# Guidelines for ISIS_Imaging CORE
## CUDA filter expansion
Integrating a package that supports CUDA has potential for improvement and expansion of the imaging filters.

A potential problem for CUDA is for machines with low VRAM, transferring the data multiple times might be slower that just doing it in a bulk in the CPU, if it has a lot of RAM.

### CuPy
This package supports CUDA and nicely implements most of the `numpy` API, meaning it can make transition over to GPU processing easy, for filters that only use `numpy` functions (background correction, contrast normalisation, etc).

For filters requiring custom code, kernels for other filters like Median, Gaussian, etc, can be written additionaly. [Related issue on repository.](https://github.com/mantidproject/isis_imaging/issues/50) 

I would recommend asking on the [CuPy repository](https://github.com/cupy/cupy) for implementation (and performance wise) advice before finalising the implementation of any filter.

### OpenCV
This is a library for image processing and computer vision, it has a lot of features, but is also quite large. I have added it here as it should be considered if there is anything available that is needed. It is available on the SCARF/Emerald cluster, making it potentially usable. 

Something that might cause issues - I am not sure how well it integrates with `numpy` arrays, for C++ they use their own internal type `cv::Mat` and I have not used the Python bindings.

## Reconstruction tools expansion
- [Astra Toolbox](http://www.astra-toolbox.com/)
- [MuhRec](http://www.imagingscience.ch/downloadsection/)

## File Structure
The aim is to make use of Pyhton's modular structure as much as possible. There is very little actual Object Oriented Programming used within the files, and I would discourage its use, unless it makes sense, for example the `core.imgdata.saver.Saver` is a class that can store all necessary information about the saving, so that when used in `core.configurations.default_flow_handler` we don't have to repeatedly pass in arguments, however the `save` function is globally available without needing to create instance of the class, making it very convenient to use through command line.

Another example is in the `core.tools` module, we want the tools to implement a common API, so that if we want to change the tool we can just import another one, and it _should_ work. This is done via having an `AbtractTool` that the other tools should inherit from, and should implement its interface.

---

Currently the scripts expect the folder structure to be:
```
<repository_folder>/
└── isis_imaging
    ├── core
    │   ├── aggregate
    │   ├── algorithms
    │   ├── configs
    │   ├── configurations
    │   ├── convert
    │   ├── filters
    │   ├── imgdata
    │   ├── imopr
    │   ├── parallel
    │   └── tools
    ├── gui
    ├── systemtests
    └── tests
```

It is not expected to have many changes of this top level structure. Any changes to this top level structure will break `registrator` and `finder` from `core.algorithms`. They expect to have this structure in order to dynamically register

### iPython / Public API exposure

## Filters - General implementation structure
- Have execute function that takes data as first parameter

# Implementation for ISIS_Imaging GUI
## General structure
Main Window (parent)

Image stacks are child objects to the Main Window. The stack handles it's own process list/history. Saving out saves out the images, and the history. Reloading then reads back the history.

## .ui Compiling
Currently the `.ui` is compiled dynamically while running. This should be changed to the mslice approach where all of the `.ui` files are compiled during 'build' and `.uic` files are created. 

## Loading
Loading of the images must be done via the `core.imgdata` module, which already handles loading of any supported image types. Any future extensions for new file types must be a part of the core module.

The Loading will be done via a dialogue:
- It will ask for the paths for the images.
- The selection will require the user to select a file, NOT a directory.
- The image format will be determined from the selected file.
- The absolute path to the directory will be determined from the selected file.
- An option for ImageJ-like virtual stack should be available.
- The user can specify indices in 3 spinboxes for [Start, Stop, Step]. Boundaries are: 
    - The spinboxes cannot be negative. 
    - Max value of Start is Stop - 1. 
    - Min value of Step is 1, and max value of Step is the value of Stop.
    - Max value of Stop is the number of files with the extension (detected dynamically after selection of the file). 
        - Stop does not have a lower bound, meaning the user can select a Stop value lower than the Start value. Doing so will result in a ValueError. 
        - This can be avoided with a signal triggered by changing the Start spinbox, that changes the setMinimum of the Stop spinbox. (low priority)

## Handling multiple stacks in dialogues
This is a consequence of being able to load multiple stack inside the program. How does the user select on which stack to apply the operation? 

This produces problems when trying to sync in after a window has been closed. The naive approach of keeping them in a list does not work, as it would require every stack window to know it's position inside the list, but if the one that is closed is _not_ the last, they all get out of sync. Thus it's going to be a nightmare to implement and test.

The current desing for the solution is to generate a unique ID for each stack, and store that plus a reference to the stack object in a dictionary. Qt provides `closeEvent` which is triggered when the user clicks the `X` button. Each stack window will know it's own unique ID, and then deletion (and sync) is just a `del dict[uid]`. 

To answer the initial question, building the selection for the user is now just a matter of iterating the dict and getting the (user friendly) name, not the uuid, and displaying that.

The unique ID will be generated using python's `uuid` package.

A future upgrade on this will take into account which is the _current focus_ of the user, and when applying an operation will automatically select _that_ stack as the default choice.

## Saving
## Visualisation
Visualisation will be done using Matplotlib. Each stack will be a separate part of a QDockWidget, so the users will be able to arrange the visualised stacks in any way they want. This also means that there can be more than one stack loaded at a time.

This must allow for the user to go to any index from the volume. 

The visualisation must allow for a rectangle ROI selection, that is persistent if the image underneath is changed. It also must allow for the visualisation of a histogram of the selected ROI (computation should be done in the `core` package).

Currently the idea is to use `FigureCanvasQtAgg` with the default drawing algorithms, for visusalisation of the images. Matplotlib provides a `RectangleSelector` class which will be used to do the ROI selection. If this proves to be too slow, a solution may be to tailor the drawing function, while still retaining the ROI selection functionality.

## Applying a filter
Applying a filter will bring up a dialogue in which the user has to select on which stack to apply the filter via a dropdown menu, and fill in the required parameters the filter has.

Any filters should be dynamically registered using the [registrator](https://github.com/mantidproject/isis_imaging/blob/master/isis_imaging/core/algorithms/registrator.py) style approach. Filters will have to implement `cli_register` and `gui_register` functions that register them with the command line and graphical interface, respectively, in order to be visible on each of the interfaces.

Current issues for this section:
- Dynamic dialogue building
  - Solution is to use an approach like the `cli_registrator`, but pass in the QObject in which the filters will register themselves in
  - Dialogue registration is a bit more complicated, because we have to connect the dropdown menu to the dialogue's `.show()` method.
- Transferring information from the dialogue (the parameters) to the execution
  - Current solution is to use a partial function, decorated with all of the parameters. No other function down the chain of execution will have to worry about the parameters that way.
- Handling filters with multiple steps
  - Background correction and contrast normalisation need to calculate values for scaling, do the filter execution, and then apply the scaling to the images.
     - Currently the solution is to apply a monad style approach.

## Undoing an operation
Building the Undo operation may be complicated, but here are a few high level approaches:
- Storing the original state as a deepcopy, and then applying the filter inplace on the volume of images, works best with single image.
    - Serious memory implications for _very_ large volumes.
    - Should be decent for small stacks, or when loading images with a large step.
    - Can easily store a single undo (like imagej), multiple undos can be hard to implement efficiently because of all the memory being copied
        - Naive implementation is to append all the consecutive changes in a list.
        - Or we can just not provide an undo if the operation was applied to the STACK.
    - Multiple undos implementation is to store it as part of the History in the process list.
        - Store slice index, operation(+params) and result(deepcopy) as an entry in a process list
            - Pro: Can easily revert an image to any state (if we don't delete the newer states we can switch between them to see the difference)
            - Cons: Memory and might be convoluted to handle the history
            - Option to open the saved image in a new stack
        - This means every slice in a volume has unique history.
            - That might be something that will potentially cause problems as it is complicated ( and error prone? ). It needs to be well implemented and tested.
            - But also provides the opportunity for the user to easily visualise different operations' results.

## Histograms
Computation of the histograms should be done only on the ROI, if no ROI is selected do the whole image. The computation itself should ideally take place in the `core.algorithms` package.

Visualisation can be one of the two:
- As a small widget inside the stack window
- As a small independent widget floating around.

A problem that needs to be considered is, should we allow for more than _one_ histogram to be active at a time? For example ImageJ does not.

## Processing a full volume
A process list should provide the option to be applied to the whole stack locally. Details for the implementation need to be considerend alondside the [Undoing an operation](#undoing-an-operation) implementation. 

The process list will store the operation(+params) that needs to be applied. Doing this for the whole stack would simply require walking through the process list. There is _nothing_ currently implemented in the `core` module that allows for that. 

A new configuration might have to be added in `core.configurations` to handle this type of ordered filter application. A class that takes the name and dynamically imports/applies the operation might also be required.

## Issues with Finding Center of Rotation and Reconstruction
Normally the data volume will be loaded in as radiograms. During the pre-processing stage not all images need to be present for the filter results to be seen. 

Doing operations like finding the Center of Rotation requires the image to be Sinograms (the Z and X axis are flipped to give a top to down view/iteration of the images). This cannot be done with a simple `np.swapaxes(data, 0, 1)` because the memory needs to be in contiguous order, and swapaxes breaks that. `np.ascontiguousarray` solves that, but it increases the memory usage by about 30-50%. It also **requires** that the whole stack be loaded into the memory _at least_ at one point, otherwise we cannot get a full sinograms, if some of the projections are missing. 

Currently this is handled by avoiding loading the whole stack for as long as possible:
- Do the whole pre-processing, until happy, pre-process the volume
- ONLY THEN load the whole stack into memory, the pre-processing usually crops the dataset so this operation is also a lot faster, then immediatelly flip the axis and saves out the sinograms.
- Following COR or reconstruction operations are done on the previously saved out sinograms.

A feature that might help is the ROI load, meaning we do the ROI crop immediatelly on load. For example this will help us load only the first row from every projection, constructing the first sinogram. However this is complicated and error prone, and will require extensive changes to the load module.

<!-- Handle like a filter? -->
### Automatic Center of Rotation (COR) with imopr cor
Once the sinogram issue has been resolved, we will have the sinograms in contiguous memory. This section will assume we already have solved that.

Currently the automatic COR calculation is done on the sinograms and uses `core.imopr.cor`. Ideally we want to keep that behaviour. Slight change might be necessary to the `core.imopr.cor` module, as currently it does not return the CORs, but only prints them in the console.

### Center of Rotation (COR) with imopr corwrite
Once the sinogram issue has been resolved, we will have the sinograms in contiguous memory. This section will assume we already have solved that.

The `core.imopr.corwrite` module works with sinograms. It saves out reconstructed slices with a range of CORs. We want to keep that behaviour as is, with the addition that after the process of saving out is finished, we visualise them back from the user, so they can select the best COR by seeing which is the best reconstructed slice.

## Reconstruction
Once the sinogram issue has been resolved, we will have the sinograms in contiguous memory. This section will assume we already have solved that.

The reconstruction works on sinograms and will be done via third party tools Tomopy, Astra Toolbox, MuhRec, etc.

Specific dialogues might have to be created for each tool, to handle the different parameters each one has.

## Remote submission
The package needs to support submission to remote cluster. This section will be updated at a later point.

### Remote compute resource used at ISIS: SCARF
General information on the SCARF cluster, which uses the Platform LSF
scheduler, can be found at http://www.scarf.rl.ac.uk. It can be used
via:

* remote login
* a web portal: https://portal.scarf.rl.ac.uk
* a web service

The IMAT GUI utilizes a RESTFul web service provided by Platforms
LSF's Platform Application Center, as described here:
https://github.com/mantidproject/documents/tree/master/Design/Imaging_IMAT/SCARF_Platform_LSF/
(with Python client scripts).
