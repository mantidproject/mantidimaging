Mantid Imaging next release
===========================

This contains changes for the next not yet released Mantid Imaging versions.

New Features
------------
- #1798 : Allow for toggling of ROI visibility in the table of ROIs within the spectrum viewer.

Fixes
-----
- #1777 : More consistent menu and window naming for comparing image stack data.
- #1776 : Fix Redrawing of ROIs within Compare Image Stack Window
- #1815 : Improve handling of NaN data within Spectrum Viewer, resolving exception error dialog pop-up within Spectrum Viewer if only dataset loaded into Mantid Imaging is removed.

Developer Changes
-----------------
- #1796 : Add MyPy to pre-commit checks.
- #1799 : Speed up packaged builds with boa
- #1792 : Update python to 3.10
- #962 : Type annotation improvements
