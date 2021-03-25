Mantid Imaging next release
===========================

This contains changes for the next not yet released Mantid Imaging versions.

New features
------------

- #823: Automatically transpose colour palette
- #567: Add new user wizard

Fixes
-----

- #816 : Error finding screen size in some dual screen set ups
- #820 : Help links go to wrong page
- #836 : Median filter returning data from wrong images
- #846 : Fixing AstropyDeprecationWarning
- #843 : Error loading stack
- #856 : Move shared array allocation to `multiprocessing.Array` when on Python 3.8
- #854 : Ops window, image selector in preview section skips by 2
- #856 : Operations auto update not triggered on spinbox changes
- #874 : Widgets in Operations window need minimum sizes
- #866 : Warning if running Flat-fielding again
- #878 : Update update instructions in version check
- #885 : RuntimeError after closing wizard
- #805, #875, #891 : Fix segmentation fault due to object lifetime
- #886 : Don't reset zoom when changing operation parameters
- #873 : Link histogram scales in operations window
