<!-- TOC -->

- [Requirements](#requirements)
    - [Requirements for GUI](#requirements-for-gui)
    - [Requirements for CORE](#requirements-for-core)
- [Guidelines](#guidelines)

<!-- /TOC -->

# Requirements
- Main language Python
- Future interfacing with C++
- Two separate main packages:
  - Package for GUI.
  - Package for CORE functionality.
- Normal stack (all images in memory) and virtual stack
- Dynamic registering of filter with both CLI and GUI
- Snapping of visualising window to and away from main window
- Filter application preview and undo
- Single slice reconstruction
- Remote submission
- ROI selection
- COR calculation + manual tailoring
- Aggregate mode exposed
- Reconstruction tools support

## Requirements for GUI
- Must use MVP pattern.
- Must have mocking and unit testing.
- Must have a modular structure.

## Requirements for CORE
- Must have unit testing.
- Must have a modular structure.

# Guidelines
- Filters and Algorithms _DO NOT_ depend directly on [`ReconstructionConfig`](https://github.com/mantidproject/isis_imaging/blob/master/isis_imaging/core/configs/recon_config.py#L41).
- Every filter must provide sequential implementation, and parallel if possible.