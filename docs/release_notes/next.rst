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
- #1191 : Loading 180 should only show datasets
- #1279 : Add auto update checkbox option to turn off live reconstruction
- #1273 : Move sinograms into the Dataset
- #1220 : Make reconstruction window side bar scrollable for smaller screens


Fixes
-----

- #1138 : Improve version number handling
- #1134 : NeXus Loader: OSError
- #1178 : --operation argument sometimes opens wrong operation
- #1117 : Median operation preserves NaNs
- #1151 : IndexError with sinograms and stripe tools
- #1174 : TypeError in link_before_after_histogram_scales
- #1161 : Remove run_ring_removal argument from Ring Removal operation and always run filter
- #1226 : AttributeError when trying to open reconstruction auto colour dialog
- #1236 : Aspect ratio not preserved in COR inspector or operations window
- #1162 : Raise exceptions when invalid parameter values are passed to filter functions
- #1248 : Rebin operations not working for small image dimensions
- #1190 : Add recon item to right part of tree view
- #1239 : 180 warning when applying ring removal to recon
- #1297 : Auto colour dialog not working in compare images
- #1292 : Attribute error if apply filter after closing and re-opening Operations window
- #1294 : Dataset Tree View: Allow for deleting recons
- #1289 : Trigger recon redraws when stack is modified
- #1299 : CIL: when reconstructing from sinograms use right dimensions and ordering
- #1305 : Delete recon group from tree view
- #1285 : Error when load two 180 stacks
- #1278 : It should not be possible to attempt loading 180 projections to a MixedDataset


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
- #1245 : Remove empty init methods from test classes
- #1251 : System tests: test_correlate ValueError
- #1259 : Update license year in code files and add pre-commit check
- #1243  #1276 : Stack selector based on datasets
- #1184 : Make more use of QTest in gui testing
