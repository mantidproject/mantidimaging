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

Fixes
-----

- #1138 : Improve version number handling
- #1134 : NeXus Loader: OSError
- #1178 : --operation argument sometimes opens wrong operation


Developer Changes
-----------------

- #1022 : Switch to use Mambaforge
- #1085 : Fix rotation of images in GUI tests
- #1045 : Command line argument to open Operation or Reconstruction windows
- #1154 : collections.abc is deprecated
- #1155 : DeprecationWarning an integer is required self.progressBar.setValue
- #1153 : Remove package_name argument from load_filter_packages
- #1172 : Add MIMiniImageView widget
