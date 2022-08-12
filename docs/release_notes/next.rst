Mantid Imaging next release
===========================

This contains changes for the next not yet released Mantid Imaging versions.

New Features
------------

- #1340 : ROI norm - remove preserve max option
- #1379 : Add angle/z axis slider in the operations window
- #1217 : Basic NeXus Saving
- #1385 : Load all NeXus rotation angles
- #1394 : NeXus Busy Indicator
- #1394 : Add .nxs extension to NeXus save path
- #1399 : NeXus Saving OSError message
- #1331 : Make MI Windows compatible
- #1430 : Provide an Anaconda package that is compatible with Windows
- #1398 : Save recons to NeXus file
- #1444 : CIL PDHG non-negativity constraint
- #1483 : Add line profile to reconstruction window
- #1480 : Automatic sinograms for sinogram operations
- #1523 : Lock zoom and lock scale selected by default in operations window
- #1524 : Flat fielding after histogram locks to appropriate range when using lock scale
- #1583 : Remove sinogram Stripe Removal filter as it is not needed

Fixes
-----
- #1381 : Don't use console progress bar in GUI application
- #1405 : MedianFilter work inplace on ImageStack
- #1395 : Delete file when NeXus saving fails
- #1397 : Only use real NeXus projection angles
- #1473 : Tomopy COR finder use -log
- #1475 : Fix scaling when saving to int
- #1484 : Clear image previews in open windows when there are no stacks to select
- #1496 : OutliersFilter IndexError when using sinograms
- #1515 : Unlink axis in recon window
- #1351 : Double clicking reconstruct buttons can cause RunTimeError
- #1562 : Stop reconstruction previews updating when window is closed
- #1564 : 180 stack not removed from main window when projection stack is deleted
- #1561 : IndexError in Reconstruction window if select a slice or projection index that's too high


Developer Changes
-----------------

- #1272 : Consistent test class filenames
- #1352 : Update astra-toolbox and cudatoolkit to allow windows installation
- #1317 : Unify auto color palette code between MIMiniImageView and MIImageView
- #1363 : Add auto color menu from constructor in MIMiniImageView
- #1362 : Rename Images class to ImageStack
- #1148 : Re-enable coverage checking
- #1375 : Leak tracking tool
- #1376 : Fix leak in StackChoiceView
- #1387 : Fix async task leak
- #1384 : Remove StackSelectorWidget and StackSelectorDialog
- #1420 : Save NeXus data without concatenate
- #1402 : Add GitHub Actions tests for Windows
- #1449 : Update CIL to 21.4, Astra to 2.0
- #1341 : Update to python 3.9, numpy 1.20
- #1509 : Change nametuples to use NamedTuples from typing
- #1495 : Document the harmless libdlfaker.so errors on IDAaaS
