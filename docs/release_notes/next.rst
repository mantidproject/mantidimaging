Mantid Imaging next release
===========================

This contains changes for the next not yet released Mantid Imaging versions.

New Features and improvements
-----------------------------
- #1601 : arithmetic filter optimisation
- #1620 : Add multiple ROI to spectrum viewer
- #1616 : Change selected stack with single click on tree widget
- #1625 : Allow adding extra stacks to a dataset
- #1625 : Load recons to an existing dataset
- #1625 : Change selection in tree view when switching tabs
- #1626 : Move stacks between datasets
- #1622 : Add, Remove and Rename ROIs in spectrum viewer
- #1464 : NeXus Recon: Add entry/reconstruction/date information
- #1463 : NeXus Recon: Add entry/SAMPLE/name information
- #1468 : NeXus Recon: Load recons
- #1467 : NeXus Recon: Add other entry/data information
- #1661 : Use `tifffile` for writing and reading tiff files
- #1512 : Speedups for CIL setup
- #1465 : NeXus Recon: Add entry/reconstruction/parameters information

Fixes
-----
- #1589 : Recommend new update command
- #1330 : Initial ROI box is sometimes much larger than image for relevant filters
- #1602 : Prevent multiple ROI selector windows opening from Operations window
- #1610 : Apply bug fix to disable Spectrum Viewer export button when no data is loaded
- #1659 : PyInstaller missing cupy files
- #1657 : PyInstaller: order of operations in menu is not sorted

Developer Changes
-----------------
- #1472 : Investigate issues reported by flake8-bugbear
- #1607 : Add flake8-bugbear to environment, github actions and precommit
- #1613 : Refactor Operations window ROI selector to be in its own class
- #1652 : PEP440 compliant versions for alpha builds
- #1595 : Store version number in package
- #1663 : Postponed Evaluation of Annotations
- #1670 : `tostring()` Deprecation Warning
- #1673 : Update license year across the repository from 2022 to 2023
