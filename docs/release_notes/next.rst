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
- #1197 : Dataset Tree View: Delete image stack
- #1197 : Dataset Tree View : Show tab from treeview
- #1200 : Default save option set to float32
- #1235 : Improvements to input value defaults and spin box step sizes
- #1230 : Update CIL to 21.3 reducing memory requirements


Fixes
-----

- #1138 : Improve version number handling
- #1134 : NeXus Loader: OSError
- #1178 : --operation argument sometimes opens wrong operation
- #1117 : Median operation preserves NaNs
- #1151 : IndexError with sinograms and stripe tools
- #1174 : TypeError in link_before_after_histogram_scales
- #1161 : Remove run_ring_removal argument from Ring Removal operation and always run filter


Developer Changes
-----------------

- #1022 : Switch to use Mambaforge
- #1085 : Fix rotation of images in GUI tests
- #1045 : Command line argument to open Operation or Reconstruction windows
- #1154 : collections.abc is deprecated
- #1155 : DeprecationWarning an integer is required self.progressBar.setValue
- #1153 : Remove package_name argument from load_filter_packages
- #1172 : Add MIMiniImageView widget
- #1070 : Remove pytest repeat
- #1182 : Handle exception in _post_filter
- #1173 : Sometimes tests open many operations windows
- #860  : Clean up super calls to use python 3 syntax
- #1181 : Version check update command uses mamba if available
- #1212 : Model Change: Put everything in datasets
