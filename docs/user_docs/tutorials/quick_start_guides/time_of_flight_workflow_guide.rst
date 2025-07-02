.. _quick-start-time-of-flight-workflow-guide:

Quick start: Example Time of Flight Analysis
--------------------------------------------

Example data that can be used for this tutorial can be downloaded from `github.com/mantidproject/mantidimaging-data <https://github.com/mantidproject/mantidimaging-data/archive/refs/heads/main.zip>`_


Spectrum Viewer
###############

.. image:: ../../../_static/spectrum_viewer.png
    :alt: Spectrum Viewer Window
    :align: center

The spectrum viewer is a tool that allows you to view spectrum data within a Time of flight (TOF) image stack. To open the spectrum viewer go to Workflow > Spectrum Viewer.

**Export Spectrum Data**:

#. Resize the ROI to just cover the size of the sample within your data or a particular area of interest within your sample. This will allow you to see the spectrum within the ROI which you will be able to see in the spectrum line plot at the bottom of the window.

#. Click the "Add" button on the left to add another ROI which you can position over a particular detail of your choosing on the sample.

#. Within the ROI Table, double click "roi_1" to rename to something more descriptive of what the ROI is covering.

#. To remove an ROI, you can select the ROI you would like to remove within the ROI Table and click the "Remove" button on the left.

#. To export spectrum data, you can click the "Export spectrum" button and select a location and filename. Two files will be saved to this location <filename>.csv and <filename>_roi_coords.csv. <filename>.csv contains the spectrum data for each ROI. <filename>_roi_coords.csv contains the coordinates of the ROIs in the image stack.

#. If you have a TOF dataset loaded where you would like to normalise to the open beam, you can do so by toggling the "Normalise to open beam" checkbox. This will normalise the spectrum to the open beam spectrum. The greyed out drop down menu will become available and you can select which dataset you would like to use as the open beam.

**Export Single or Binned Spectrum Data in RITS Format**

#. To enter IMAGE mode to export single or binned spectrum data in RITS format, you can click the "IMAGE" tab at the top of the table of ROIs.

#. Resize the ROI in the same way as before for exporting regular spectrum data to cover an area of the sample you would like to acquire the spectrum for.

#. Select the output mode from the top drop down menu on the left which replaces the table of ROIs, either "Single Spectrum" or 2D Binned" depending on what you would like to export. 2D binned will bin within the ROI and export the binned data as multi-spectrum data.

    #. If you choose to export as a "2D Binned", you can choose the size of your bin in pixels squared from the drop down menu on the left. You can also select the step size of the bin from the drop down menu. If the step size if the same as the bin size, the binned data will be non-overlapping tiled binning. If the step size is smaller than the bin size, the binned data will be overlapping which will achieve a rolling average.

#. Choose between "Propagated" and "Standard Deviation" from the "Error Mode" drop down box. Propagated will calculate the error from the propagated error of the counts in the spectrum. Standard Deviation will calculate the error from the standard deviation of the counts in the spectrum. The mode you choose will depend on the data you are working with. Optionally, you could export to both modes separately to compare the results.
