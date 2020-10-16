A common workflow
=================

Operations window
-----------------

    1. Load a dataset
    2. Scroll through all operations and ensure their previews are calculated correctly
        - Note that not all operations have a preview - Monitor normalisation does not
        - Some filters will not show a difference image with the default parameters
    3. Do the most common pre-processing steps
        - Remove outliers with Apply to All
        - Flat-fielding on Sample (but not on Flat or Dark images)
        - ROI normalisation with a region that does not contain any part of the sample
        - Crop coordinates
            - Right click on stack -> Toggle show average image to select a good ROI
            - Crop and disable the average image


Reconstruction window
---------------------

    1. Correlate a COR
    2. If needed, further minimise it by changing the automatic COR algorithm
        - This step is needed if the 180 degree projection is not exactly at 180 degrees, making the COR not align correctly
    3. Go to Reconstruct tab and check that each algorithm changes the reconstruction preview
    4. If known - enter the pixel size of the dataset
    4. Run the reconstruction


Post-reconstruction operations
------------------------------

    1. If pixel size wasn't provided in the reconstruction, then manually divide by pixel size
    2. Save out in int-16