Mantid Imaging next release
===========================

This contains changes for the next not yet released Mantid Imaging versions.

New Features
------------

- #1044 : Command line argument to load a dataset
- #1023 : Switch from Sarepy to Algotom
- #1049 : NeXus Loader: 180deg images
- #1167 : Bad data indicator icons
- #1185 : Bad data overlays
- #1168 : Dataset tree view
- #1202 : NaN Removal filter - replace with median
- #1205 : Linearisation correction for beam hardening

Fixes
-----

- #1138 : Improve version number handling
- #1134 : NeXus Loader: OSError
- #1178 : --operation argument sometimes opens wrong operation
- #1117 : Median operation preserves NaNs
- #1151 : IndexError with sinograms and stripe tools


Developer Changes
-----------------

- #1022 : Switch to use Mambaforge
- #1085 : Fix rotation of images in GUI tests
- #1045 : Command line argument to open Operation or Reconstruction windows
- #1154 : collections.abc is deprecated
- #1155 : DeprecationWarning an integer is required self.progressBar.setValue
- #1153 : Remove package_name argument from load_filter_packages
- #1172 : Add MIMiniImageView widget
