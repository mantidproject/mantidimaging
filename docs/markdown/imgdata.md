# IO package

The `io` module provides easy modules to load and save stacks of data.

## Loading data

The `core.io.loader` module provides a `load` method, that takes a path, and img_format (the default is tiff, if different it needs to be specified) and will load _ALL_ of the images in that folder.

## Saving data

The `core.io.saver` module provides a `save` method, that takes a numpy ndarray and a path, and will save out all the images in the path. The function also has additional parameters to specify output image format.