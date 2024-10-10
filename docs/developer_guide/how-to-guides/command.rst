Command Line Arguments
----------------------

- :code:`--log-level` - Set the log verbosity level. Available options are: TRACE, DEBUG, INFO, WARN, CRITICAL
- :code:`--version` - Print the version number and exit.
- :code:`--path` - Set the path for the data you wish to load.
- :code:`-lv` `--live-view` - Set the directory to open the live view window on start up. The live view window will automatically update when new images are added to the directory.

The following command line arguments will only work if a valid path containing images has been given:

- :code:`--operation` - Opens the operation window on start up with the given operation selected in the combo box. The operation name should the same was what appears in Mantid Imaging but joined with hyphens in place of spaces. Case insensitive.
- :code:`--recon` - Shows the recon window on start up.
- :code:`-sv` `--spectrum_viewer` - Opens the spectrum viewer window on start up. A path to a dataset must be provided with the :code:`--path` argument for the spectrum viewer to open.


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   documentation
   developer_conventions
   debugging
   conda_packaging_and_docker_image
   release
   testing
