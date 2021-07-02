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
- #1010 : Write slope and offset into int tiffs
- #987 : Allow Flat-fielding without dark subtraction
- #1011 : Pixel size should allow setting decimal places
- #1013 : NeXus Loading Window
- #904 : Default to using image center for ring removal COR

Fixes
-----

- #939 : median: NameError: name 'cp' is not defined
- #957 : Crop Coordinates ROI not changing
- #961 : Test failure: ImportError: libcuda.so.1
- #953 : NaNs in result when reconstructing with FBP_CUDA
- #959 : Median GPU does not work with even values
- #990 : Remove combine histogram checkbox
- #989 : Remove legend checkbox
- #1001 : Exception when selecting Log in Load Dataset dialog
- #991 : Handle longer running previews better
- #1021 : Prevent simultaneous Astra calls
- #1036 : Exception in ReconstructWindowView.show_recon_volume prevents recon closing

Developer Changes
-----------------

- #917 : Intermittent failure of StripeRemovalTest.test_memory_executed_wf
- #980 : Use pre-commit
- #978 : Update Qt API usage
- #998 : setup.py command to install current developer requirements
- #969 : Improve mypy coverage in core.io
- #1007 : Change applitools check level to content

Dependency updates
------------------

- pyqtgraph 0.12, scikit-image 0.18, tomopy 1.9, numpy 1.20
