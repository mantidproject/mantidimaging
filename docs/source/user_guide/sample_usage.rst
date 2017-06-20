.. Sample usage master file
   See http://sphinx-doc.org/tutorial.html#defining-document-structure

.. Sample usage contents:

=============
Sample usage
=============
-----------------
Printing the help
-----------------

The help can be printed by passing the `-h` flag.

Depending on how you're accessing the package it will be either:

`imgpy -h`

or

`. imgpy.sh -h`

This will print out the whole help, containing each available command line parameter that can be passed.

------------
Loading Data
------------
* Note: For the longer argument names it's two slashes at the front, without a space in between.

^^^^^^^^^^^^^^^^^^^^^^
Specifying Sample data
^^^^^^^^^^^^^^^^^^^^^^
`-i /some/path`

`- -input-path /some/path`

^^^^^^^^^^^^^^^^^^^^^^
Specifying Flat images
^^^^^^^^^^^^^^^^^^^^^^
`-F /some/path`

`- -input-path-flat /some/path`

^^^^^^^^^^^^^^^^^^^^^^
Specifying Dark images
^^^^^^^^^^^^^^^^^^^^^^
`-D /some/path`

`- -input-path-dark /some/path`

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Loading Sample, Flat and Dark at once
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Only Sample can be loaded, but you can't load just Flat or just Dark images. Both Flat and Dark must be specified at the same time.

`imgpy -i /some/path/to/sample -F /some/path/to/flat -D /some/path/to/dark`

^^^^^^^^^^^^^^^^
Running a filter
^^^^^^^^^^^^^^^^


Specifying output folder
-> If not specified nothing will be saved out. This is for testing purposes
-o --output-path
Saving pre-processed images
-s --save-preproc
Specifying pre-processed folder 
-p

Finding COR
--imopr cor --indices 1 2
--imopr corwrite -o --indices 1 2

Saving out sinograms
--convert
--swap-axes

Running reconstruction
--reconstruct
--cor-slices --cors
--cors only

Selecting tool
-t --tool
Selecting algorithm
-a --algorithm

