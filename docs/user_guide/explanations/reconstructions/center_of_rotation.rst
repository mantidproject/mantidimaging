.. _Center of Rotation:

Center of Rotation and Tilt
===========================

Center of Rotation (COR) and Tilt Usage
---------------------------------------

The correct center of rotation is required for a good reconstruction.
We provide two automatic ways of getting a center of rotation.
However, sometimes the values they find are not accurate, so there is also a manual way
to adjust the center of rotation.

The algorithms used for reconstruction require a COR for each sinogram,
i.e., a list of CORs equal to the number of sinograms (also equal to the number of rows in a projection).
This is abstracted away, and the two final values that are used are: center of rotation and tilt.

In that case, the COR refers to the value at sinogram 0 (also referred to as slice 0).
Using the tilt, we then use a linear regression to calculate the COR for each sinogram in the data.

What is the Center of Rotation (COR)?
-------------------------------------
The **Center of Rotation (COR)** is a reference point that defines the axis around which the object rotates
during image acquisition in tomography. It is the midpoint of the rotational axis when looking at
a slice of the data (a sinogram).

.. image:: ../../../_static/cor_bad.png
    :alt: Misaligned Center of Rotation (COR) causing artifacts
    :width: 47%
    :align: left

.. image:: ../../../_static/cor_good.png
    :alt: Correctly aligned Center of Rotation (COR) for artifact-free reconstruction
    :width: 47%
    :align: right


The left image shows a misaligned COR causing artifacts and distortions,
while the right image depicts a properly aligned COR ensuring accurate and artifact-free reconstruction.

Why COR Matters:
  - If the COR is incorrect, the projections will not align correctly during reconstruction,
    leading to artifacts and blurred images.
  - COR is specific for each sinogram (i.e., each slice of the object being scanned).

How COR is Used:
  - For accurate reconstruction, the COR for the first sinogram (sinogram 0, also called slice 0) is determined.
  - Using the **Tilt** parameter, CORs for subsequent sinograms are calculated through a linear adjustment.

What is Tilt?
-------------

**Tilt** describes the gradual change in the Center of Rotation (COR) along the axis perpendicular
to the rotation plane (typically corresponding to the rows in a projection).Without considering tilt,
the reconstructed slices may not align correctly, causing distortions or streaking artifacts.

Key Points:
  - Tilt is measured in degrees.
  - A tilt value of zero means the rotation axis is vertical, and the COR is the same for every sinogram.
  - Using the COR of the first sinogram and the tilt value, the COR for each subsequent sinogram is interpolated or extrapolated.

GUI:
  - The GUI also displays **Slope**, which represents how far the COR moves from one slice to the next.

Entering Known COR and Tilt
---------------------------

If the COR and tilt are already known, you can enter them in the "Enter known COR/Tilt manually here" section
and press "Use COR/Tilt values from above." In this case, you can go immediately to reconstruction.

Correlate 0 and 180
-------------------

This automatic COR algorithm finds the shift between the projections at 0 and 180 degrees.
The projection exactly at 180 degrees is necessary for the best result. We provide the option
of loading a 180-degree projection in the load dialog.

The algorithm will not run unless a 180-degree projection has been loaded.

This is not a problem and could be rectified either by adding a manual COR or using
the minimisation algorithm.

Minimise Error
--------------

This automatic COR algorithm uses the square sum of the projection as a noise heuristic.
It minimises the noise in order to find the best COR for that sinogram.

It does so for a number of sinograms (slices) and adds the result in the COR table.

This algorithm may not work well on noisy data or with very bright outliers, as the
minimisation can get lost in a local minima and not find the best reconstructed slice.
As the same heuristic is also used in the manual "Refine" window to highlight
one of the choices as the best, the behaviour can also be seen there.

In this case, the best action is to use the correlate as a starting point and
go immediately to manual COR correction.

Manual COR Correction
---------------------

Due to the limitations of the algorithms above, there is also a manual way of calculating the COR—
using the "COR Table - refine manually" part of the GUI.

In that table, you can click Add to add a new COR for the currently selected slice. Once added,
you can click the row and then "Refine," which will take you to a window that reconstructs
the sinogram with multiple CORs simultaneously, and allows you to visually pick the best one.

After you have two or more CORs in the table, a fit will be performed in order to find the COR and tilt
using the data from the table rows.

It is sometimes good enough to add a COR at the top of your data and the bottom.
Once the best CORs for those are found, the resulting tilt should be accurate.
To increase the accuracy further, add more COR rows.

To Reconstruction
-----------------

Once you have a satisfactory value of COR or tilt, you are ready to proceed to the "Reconstruct" tab.

Information about the filters and algorithms can be found in the other pages of the :ref:`Reconstruction Help page`.
