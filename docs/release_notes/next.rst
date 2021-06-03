Mantid Imaging next release
===========================

This contains changes for the next not yet released Mantid Imaging versions.


New features
------------

- #927 : ROI norm: use averaged view in ROI selector
- #925 : Jenks / Otsu everywhere
- #926 : Manual arithmetic filter
- #988 : Use averaged view in ROI selector for crop
- #964 : Open NeXus files

Fixes
-----

- #939 : median: NameError: name 'cp' is not defined
- #957 : Crop Coordinates ROI not changing
- #961 : Test failure: ImportError: libcuda.so.1
- #953 : NaNs in result when reconstructing with FBP_CUDA
- #959 : Median GPU does not work with even values
- #990 : Remove combine historgram checkbox
- #989 : Remove legend checkbox

Developer Changes
-----------------

- #917 : Intermittent failure of StripeRemovalTest.test_memory_executed_wf
- #980 : Use pre-commit
- #978 : Update Qt API usage
- #998 : setup.py command to install current developer requirements

Dependency updates
------------------

- pyqtgraph 0.12, scikit-image 0.18, tomopy 1.9
