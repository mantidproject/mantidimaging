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

This will print out the whole help, containing each available command line parameter that can be passed. For examples below the first syntax for calling is assumed:

`imgpy -h`

------------
Loading Data
------------

^^^^^^^^^^^^^^^^^^^^^^
Specifying Sample data
^^^^^^^^^^^^^^^^^^^^^^
`-i /some/path`

`--input-path /some/path`

^^^^^^^^^^^^^^^^^^^^^^
Specifying Flat images
^^^^^^^^^^^^^^^^^^^^^^
`-F /some/path`

`--input-path-flat /some/path`

^^^^^^^^^^^^^^^^^^^^^^
Specifying Dark images
^^^^^^^^^^^^^^^^^^^^^^
`-D /some/path`

`--input-path-dark /some/path`

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Loading Sample, Flat and Dark at once
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Only Sample can be loaded, but you can't load just Flat or just Dark images. Both Flat and Dark must be specified at the same time.

`imgpy -i /some/path/to/sample -F /some/path/to/flat -D /some/path/to/dark`

^^^^^^^^^^^^^^^^
Running a filter
^^^^^^^^^^^^^^^^
Available filters can be listed using the help command `imgpy -h`. This example will show how to run a median filter on the loaded images.

From the `imgpy -h` we can see that the Median filter has the following commands:

`--median-size <number>` and `--median-mode <string>`

The one we are interested in `--median-size`.

To run the median filter we want to load a stack with `-i` and then pass the `--median-size` flag. The full command line will look like this:

`imgpy -i /some/path/ --median-size 3`

This will load in the data, execute median filter.. and do nothing else.

^^^^^^^^^^^^^^^^^^^^^^^^^^^
Saving pre-processed images
^^^^^^^^^^^^^^^^^^^^^^^^^^^
If we want to save out the pre-processed images we need to provide the one of the following flags:

`-s` or `--save-preproc`

If they are not specified the data will be processed, and then **the result will be discarded**. However this also requires an output path specified. Please refer to `Specifying output folder`_.


^^^^^^^^^^^^^^^^^^^^^^^^
Specifying output folder
^^^^^^^^^^^^^^^^^^^^^^^^
If we want anything saved out we need to specify the output path. This can be done via one of the following flags:

`-o folder_name` or `--output-path folder_name`


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Customising pre-processed folder 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default the pre-processing will be saved out in a folder called `pre_processed`. This can be customised using one of the following flags:

`-p folder_name` or `--preproc-subdir folder_name`


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Specifying indices to be processed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The package supports specifying only certain indices to be processed, for faster testing and execution. This functionality can be accessed with:

`--indices <start> <stop> <step>`

The flag also supports a few additional usages:

`--indices <stop>` - This will assume the start is 0, and step is 1

`--indices <start> <stop` - This will assume the step is 1

Example usage on the command line:

`imgpy -i /some/data --indices 100 --median-size 3`

`imgpy -i /some/data --indices 0 100 --median-size 3`

`imgpy -i /some/data --indices 0 100 1 --median-size 3`

These 3 specify the same thing, and show off the different ways to use `--indices`.


^^^^^^^^^^^^^^^^^^^^
Saving out sinograms
^^^^^^^^^^^^^^^^^^^^
Finding the Center of Rotation and reconstructing a dataset requires the images to be converted to Sinograms first. 
This can be done in anything that involves saving images out, meaning that the images can be converted after being applied a filter:

`imgpy -i /some/path/ --median-size 3 --swap-axes -o /some/path -s`

For converting images that have already been saved out, use the following command:

`imgpy -i /some/path/ -o /output/path --convert --swap-axes`


^^^^^^^^^^^
Finding COR
^^^^^^^^^^^

- Note: This expects images as sinograms. Please refer to `Saving out sinograms`_.

To run one of the Tomopy's automatic COR finding algorithms use:

`--imopr cor --indices 1 10`
--imopr corwrite -o --indices 1 2


Running reconstruction
--reconstruct
--cor-slices --cors
--cors only

Selecting tool
-t --tool
Selecting algorithm
-a --algorithm

